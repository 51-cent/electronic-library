import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DatabaseSession
from app.schemas.health import HealthResponse
from app.services.health import check_health

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Состояние приложения"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Проверка соединения с MySQL",
    responses={503: {"description": "Нет подключения к базе данных"}, 200: {"description": "Все ок"}},
)
def get_health(db: DatabaseSession) -> HealthResponse:
    try:
        return check_health(db)
    except SQLAlchemyError:
        logger.warning("Проверка соединения с MySQL завершилась ошибкой.")
        raise HTTPException(
            status_code=503,
            detail={
                "code": "database_unavailable",
                "message": "Нет подключения к MySQL.",
            }
        ) from None
