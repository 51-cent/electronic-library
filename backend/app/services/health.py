"""Сервис проверки готовности приложения"""

from sqlalchemy.orm import Session

from app.repositories.health import ping_database
from app.schemas.health import HealthResponse


def check_health(db: Session) -> HealthResponse:
    ping_database(db)
    return HealthResponse()
