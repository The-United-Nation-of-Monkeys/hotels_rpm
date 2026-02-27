from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.routers import notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Notification Service API",
    description="Сервис уведомлений. Приём события об оплате, вызов Booking confirm/cancel.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(notifications.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}
