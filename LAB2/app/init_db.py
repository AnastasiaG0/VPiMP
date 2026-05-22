import asyncio
from app.core.database import mongodb

async def init_db():
    """Инициализирует базу данных и создает индексы"""
    await mongodb.connect()
    print("Database initialized successfully")
    await mongodb.disconnect()

if __name__ == "__main__":
    asyncio.run(init_db())