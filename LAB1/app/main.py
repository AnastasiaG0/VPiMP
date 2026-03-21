from fastapi import FastAPI
from datetime import datetime
from typing import Dict

app = FastAPI(title="Счетчик дней до Нового года 2027")

@app.get("/")
async def root():
    """Корневой маршрут для проверки работы сервера"""
    return {
        "message": "Сервер работает",
        "endpoints": {
            "/": "Это сообщение",
            "/info": "Получить количество дней до Нового года",
            "/health": "Проверка здоровья сервера"
        }
    }

@app.get("/info")
async def get_days_until_new_year() -> Dict[str, int]:
    today = datetime.now()
    print(f"Текущая дата: {today}")
    
    next_year = today.year + 1
    new_year = datetime(next_year, 1, 1)
    print(f"Дата Нового года: {new_year}")
    
    # Вычисляем разницу в днях
    days_difference = (new_year - today).days
    print(f"Осталось: {days_difference} дней")
    
    return {"days_before_new_year": days_difference}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Проверка состояния сервера"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4200)