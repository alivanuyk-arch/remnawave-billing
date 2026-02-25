from fastapi import FastAPI
from app.database import engine, Base
from routers import clients
from app.config import settings
from routers import clients, operations

# Создаем таблицы в БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="Remnawave Billing Service")

@app.on_event("startup")
async def startup():
    await init_db()

# Подключаем роутеры
app.include_router(clients.router, prefix="/api/v1")
app.include_router(operations.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Remnawave Billing API", "docs": "/docs"}