import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, render_metrics
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
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc
    openapi_url="/openapi.json",
)

app.include_router(notifications.router)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}


@app.get("/metrics")
def metrics():
    return render_metrics()
