import json
import redis
from typing import Optional, Any
from datetime import datetime, date
from app.core.config import settings

class CustomJSONEncoder(json.JSONEncoder):
    """Поддерживает сериализацию datetime и date объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

class CacheService:
    """Сервис для работы с Redis кешем"""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """Устанавливает соединение с Redis"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Проверяем соединение
            self.client.ping()
            print(f"[OK] Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            print(f"[WARN] Redis connection failed: {e}. Caching disabled.")
            self.client = None
    
    def is_available(self) -> bool:
        """Проверяет доступность Redis"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def _make_key(self, prefix: str, *parts) -> str:
        """Формирует ключ с префиксом"""
        key_parts = ["smart_home", prefix] + [str(p) for p in parts]
        return ":".join(key_parts)
    
    def get(self, prefix: str, *parts) -> Optional[Any]:
        """Получает значение из кеша"""
        if not self.is_available():
            return None
        
        key = self._make_key(prefix, *parts)
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, prefix: str, value: Any, ttl: int = None, *parts) -> bool:
        """Сохраняет значение в кеш с TTL"""
        if not self.is_available():
            return False
        
        key = self._make_key(prefix, *parts)
        ttl = ttl or settings.CACHE_TTL_DEFAULT
        try:
            serialized = json.dumps(value, cls=CustomJSONEncoder)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, prefix: str, *parts) -> bool:
        """Удаляет ключ из кеша"""
        if not self.is_available():
            return False
        
        key = self._make_key(prefix, *parts)
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern_prefix: str) -> int:
        """Удаляет все ключи по паттерну"""
        if not self.is_available():
            return 0
        
        pattern = self._make_key(pattern_prefix, "")
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
        return 0
    
    def set_jti(self, user_id: str, jti: str, ttl: int) -> bool:
        """Сохраняет JTI токена в Redis"""
        return self.set("auth:access", "valid", ttl, user_id, jti)

    def has_jti(self, user_id: str, jti: str) -> bool:
        """Проверяет наличие JTI в Redis (активен ли токен)"""
        if not self.is_available():
            return True
        
        key = self._make_key("auth:access", user_id, jti)
        try:
            return self.client.exists(key) > 0
        except:
            return True

    def delete_jti(self, user_id: str, jti: str) -> bool:
        """Удаляет JTI токена (logout)"""
        return self.delete("auth:access", user_id, jti)

    def delete_all_user_jti(self, user_id: str) -> int:
        """Удаляет все JTI токены пользователя (logout all)"""
        return self.delete_pattern(f"auth:access:{user_id}")

    def acquire_lock(self, lock_key: str, lock_value: str, ttl: int = 30) -> bool:
        """Распределённая блокировка в Redis"""
        if not self.is_available():
            return True
        
        try:
            return self.client.set(lock_key, lock_value, nx=True, ex=ttl)
        except Exception as e:
            print(f"Lock acquire error: {e}")
            return True

    def release_lock(self, lock_key: str, lock_value: str) -> bool:
        """Освобождает распределённую блокировку."""
        if not self.is_available():
            return True
        
        unlock_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            result = self.client.eval(unlock_script, 1, lock_key, lock_value)
            return result == 1
        except Exception as e:
            print(f"Lock release error: {e}")
            return True


# Создаем глобальный экземпляр
cache_service = CacheService()