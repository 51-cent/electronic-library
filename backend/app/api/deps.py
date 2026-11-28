from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError
from app.enum.user import Role
from app.services.auth import AuthenticatedUser, AuthService


def get_db() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(db: DatabaseSession, settings: SettingsDep) -> AuthService:
    return AuthService(db, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login', auto_error=False)
AccessTokenDep = Annotated[str | None, Depends(oauth2_scheme)]


def get_current_user(service: AuthServiceDep, token: AccessTokenDep) -> AuthenticatedUser:
    return service.authenticate_access(token)


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_catalog_write_access(principal: CurrentUser) -> None:
    if principal.user.role != Role.admin:
        raise ForbiddenError('admin_required', 'Не достаточно прав для изменения каталога!')


def require_allowed_origin(request: Request, settings: SettingsDep) -> None:
    if request.headers.get('origin') not in settings.auth_allowed_origins:
        raise ForbiddenError('origin_not_allowed', 'Origin запроса отсутствует или не разрешён.')
