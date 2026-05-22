import hashlib
import secrets
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from app.core.config import settings


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Хеширует пароль с солью.
    Если соль не предоставлена, генерирует новую.
    Возвращает (хеш_пароля, соль)
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    # Используем PBKDF2-HMAC-SHA256 для хеширования пароля с солью
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # кол-во итераций
    ).hex()
    
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Проверяет пароль"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed


def hash_token(token: str) -> str:
    """Хеширует токен для хранения в БД (одностороннее хеширование)"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_jti() -> str:
    """Генерирует уникальный JWT ID (JTI)"""
    return str(uuid.uuid4())


def generate_access_token(user_id: str) -> Tuple[str, str]:
    """
    Генерирует JWT Access Token.
    Возвращает (token, jti)
    """
    jti = generate_jti()
    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRATION)
    }
    token = jwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm="HS256")
    return token, jti

def generate_refresh_token(user_id: str) -> str:
    """Генерирует JWT Refresh Token"""
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm="HS256")


def verify_access_token(token: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Проверяет и декодирует Access Token.
    Возвращает (user_id, jti) или (None, None) при ошибке.
    """
    try:
        payload = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None, None
        user_id = payload.get("sub")
        jti = payload.get("jti")
        return user_id, jti
    except jwt.InvalidTokenError:
        return None, None


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Проверяет Refresh Token.
    Возвращает user_id или None при ошибке.
    """
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None