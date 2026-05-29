import io
import os
import tempfile
from typing import Optional, Tuple
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException, status
import uuid

from app.core.config import settings


class MinIOService:
    """Сервис для работы с MinIO Object Storage"""
    
    def __init__(self):
        self.client = None
        self.bucket = settings.MINIO_BUCKET
        self._connect()
        self._ensure_bucket()
    
    def _connect(self):
        """Устанавливает соединение с MinIO"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL
            )
            print(f"✅ Connected to MinIO at {settings.MINIO_ENDPOINT}")
        except Exception as e:
            print(f"❌ MinIO connection failed: {e}")
            raise
    
    def _ensure_bucket(self):
        """Создает бакет, если он не существует"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"✅ Created bucket: {self.bucket}")
            else:
                print(f"✅ Bucket already exists: {self.bucket}")
        except Exception as e:
            print(f"⚠️ Bucket creation error: {e}")
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: str,
        custom_filename: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Загружает файл в MinIO используя потоковую передачу.
        
        Аргументы:
            file: Загружаемый файл (UploadFile)
            user_id: ID пользователя
            custom_filename: Пользовательское имя файла (опционально)
            
        Возвращает:
            Tuple (object_key, original_name, file_size)
        """
        # Генерируем уникальный ключ объекта
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_id = str(uuid.uuid4())
        object_key = f"users/{user_id}/{unique_id}.{file_ext}"
        
        # Сохраняем оригинальное имя
        original_name = custom_filename or file.filename
        
        tmp_file_path = None
        file_size = 0
        
        try:
            # Создаем временный файл для потоковой загрузки
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file_path = tmp_file.name
                
                # Потоковое чтение по 8KB, не загружая весь в память
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    tmp_file.write(chunk)
                    file_size += len(chunk)
                
                tmp_file.flush()
            
            # Загружаем из временного файла в MinIO
            self.client.fput_object(
                bucket_name=self.bucket,
                object_name=object_key,
                file_path=tmp_file_path,
                content_type=file.content_type,
                metadata={
                    "original-name": original_name,
                    "user-id": user_id,
                    "uploaded-at": datetime.utcnow().isoformat()
                }
            )
            
            print(f"✅ File uploaded: {object_key} ({file_size} bytes)")
            return object_key, original_name, file_size
            
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload error: {str(e)}"
            )
        finally:
            # Удаляем временный файл
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    print(f"⚠️ Failed to delete temp file: {e}")
    
    async def get_file_stream(self, object_key: str):
        """
        Получает поток файла из MinIO.
        
        Аргументы:
            object_key: Ключ объекта в MinIO
            
        Возвращает:
            Tuple (stream, content_type, size, metadata)
        """
        try:
            # Потоковое получание
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_key
            )
            
            # Получаем информацию об объекте
            stat = self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_key
            )
            
            return response, stat.content_type, stat.size, stat.metadata
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in storage"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file: {str(e)}"
            )
    
    async def delete_file(self, object_key: str) -> bool:
        """
        Удаляет файл из MinIO.
        
        Аргументы:
            object_key: Ключ объекта в MinIO
            
        Возвращает:
            bool: True если удаление успешно
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_key
            )
            print(f"✅ File deleted: {object_key}")
            return True
        except S3Error as e:
            print(f"❌ Failed to delete file {object_key}: {e}")
            return False
    
    async def file_exists(self, object_key: str) -> bool:
        """
        Проверяет существование файла в MinIO.
        
        Аргументы:
            object_key: Ключ объекта в MinIO
            
        Возвращает:
            bool: True если файл существует
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_key
            )
            return True
        except S3Error:
            return False


# Создаем глобальный экземпляр
minio_service = MinIOService()