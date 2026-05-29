from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from datetime import datetime

from app.models.file import FileMetadata
from app.services.minio_service import minio_service
from app.core.database import mongodb
from app.core.cache import cache_service
from app.core.config import settings


class FileService:
    """Сервис для управления файлами"""
    
    def __init__(self, db, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def _get_files_collection(self):
        """Получает коллекцию файлов"""
        return mongodb.database["files"]
    
    def _validate_image_file(self, file: UploadFile):
        """Валидирует файл изображения"""
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )
        
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE // 1024 // 1024} MB)"
            )
        
        return True
    
    async def upload_file(self, file: UploadFile, is_avatar: bool = False) -> FileMetadata:
        """
        Загружает файл в MinIO и сохраняет метаданные в БД.
        """
        # Валидация для аватаров
        if is_avatar:
            self._validate_image_file(file)
        
        # Загружаем файл в MinIO
        object_key, original_name, file_size = await minio_service.upload_file(
            file=file,
            user_id=self.user_id
        )
        
        # Создаем метаданные файла
        file_metadata = FileMetadata(
            user_id=self.user_id,
            original_name=original_name,
            object_key=object_key,
            bucket=settings.MINIO_BUCKET,
            size=file_size,
            mimetype=file.content_type or "application/octet-stream"
        )
        
        # Сохраняем в БД
        collection = await self._get_files_collection()
        file_dict = file_metadata.dict(exclude={"_id", "id"})
        result = await collection.insert_one(file_dict)
        
        file_metadata.id = str(result.inserted_id)
        
        # Инвалидируем кеш списка файлов пользователя
        await self._invalidate_user_files_cache()
        
        return file_metadata
    
    async def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """
        Получает метаданные файла с проверкой владельца.
        """
        # Пытаемся получить из кеша
        cached = cache_service.get("file", "metadata", file_id)
        
        if cached:
            if cached.get("user_id") != self.user_id:
                return None
            return FileMetadata(**cached)
        
        # Получаем из БД
        collection = await self._get_files_collection()
        file_data = await collection.find_one({
            "file_id": file_id,
            "deleted_at": None
        })
        
        if not file_data:
            return None
        
        file_metadata = FileMetadata(**file_data)
        
        # Проверяем, что файл принадлежит пользователю
        if file_metadata.user_id != self.user_id:
            return None
        
        # Сохраняем в кеш
        cache_service.set("file", "metadata", file_metadata.dict(), settings.CACHE_TTL_DEFAULT, file_id)
        
        return file_metadata
    
    async def get_file_stream(self, file_id: str):
        """
        Получает поток файла для скачивания.
        """
        metadata = await self.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )
        
        stream, content_type, size, minio_metadata = await minio_service.get_file_stream(metadata.object_key)
        
        return stream, metadata
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Удаляет файл (Soft Delete + удаление из MinIO).
        """
        metadata = await self.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )
        
        # Удаляем из MinIO
        await minio_service.delete_file(metadata.object_key)
        
        # Soft Delete в БД
        collection = await self._get_files_collection()
        result = await collection.update_one(
            {"file_id": file_id},
            {"$set": {"deleted_at": datetime.utcnow()}}
        )
        
        if result.modified_count:
            cache_service.delete("file", "metadata", file_id)
            await self._invalidate_user_files_cache()
            return True
        
        return False
    
    async def get_user_files(self, skip: int = 0, limit: int = 10) -> List[FileMetadata]:
        """
        Получает список файлов пользователя.
        """
        try:
            # Пытаемся получить из кеша
            cache_key = f"{self.user_id}:{skip}:{limit}"
            cached = cache_service.get("user", "files", cache_key)
            
            if cached:
                return [FileMetadata(**f) for f in cached]
            
            # Получаем из БД
            collection = await self._get_files_collection()
            
            # Строим запрос
            query = {
                "user_id": self.user_id,
                "deleted_at": None
            }
            
            # Выполняем запрос с пагинацией
            cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            files = []
            
            async for file_data in cursor:
                files.append(FileMetadata(**file_data))
            
            # Сохраняем в кеш (используем to_response_dict для публичных данных)
            cache_service.set(
                "user", "files", 
                [f.to_response_dict() for f in files], 
                settings.CACHE_TTL_DEFAULT,
                cache_key
            )
            
            return files
            
        except Exception as e:
            print(f"Error in get_user_files: {e}")
            return []
    
    async def _invalidate_user_files_cache(self):
        """Инвалидирует кеш списка файлов пользователя"""
        cache_service.delete_pattern(f"user:files:{self.user_id}:*")