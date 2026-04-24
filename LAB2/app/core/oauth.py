import secrets
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings

# Хранилище для state-параметров (в production используйте Redis или БД)
_states = {}


def generate_oauth_state() -> str:
    """Генерирует state для защиты от CSRF"""
    state = secrets.token_urlsafe(32)
    _states[state] = True
    return state


def verify_oauth_state(state: str) -> bool:
    """Проверяет state"""
    if state in _states:
        del _states[state]
        return True
    return False


def get_yandex_auth_url(state: str) -> str:
    """Формирует URL для редиректа на Yandex ID"""
    return (
        "https://oauth.yandex.ru/authorize"
        f"?response_type=code&client_id={settings.YANDEX_CLIENT_ID}"
        f"&redirect_uri={settings.YANDEX_CALLBACK_URL}&state={state}"
    )


async def exchange_yandex_code_for_token(code: str) -> Optional[str]:
    """Обменивает код на Access Token провайдера"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_CLIENT_ID,
                "client_secret": settings.YANDEX_CLIENT_SECRET,
                "redirect_uri": settings.YANDEX_CALLBACK_URL,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return data.get("access_token")


async def get_yandex_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о пользователе от Yandex"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"}
        )
        if response.status_code != 200:
            return None
        return response.json()