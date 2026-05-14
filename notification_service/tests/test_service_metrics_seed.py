import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("NOTIFICATION_DATABASE_URL", "sqlite:///./test_notification_service.db")
os.environ.setdefault("NOTIFICATION_BOOKING_SERVICE_URL", "http://testserver")

from app.database import Base, engine
from app.main import app


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    db_file = Path("test_notification_service.db")
    if db_file.exists():
        db_file.unlink()


def test_health_and_metrics():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["service"] == "notification-service"

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "notification_http_requests_total" in metrics.text
