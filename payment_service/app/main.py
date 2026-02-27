from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.routers import payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Payment Service API",
    description="Сервис оплаты. Обработка оплаты, хранение статуса, события в Notification Service.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(payments.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "payment-service"}
