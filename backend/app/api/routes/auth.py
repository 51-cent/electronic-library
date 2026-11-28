from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.auth_cookies import clear_auth_cookies, refresh_credentials, set_auth_cookies
from app.api.deps import AuthServiceDep, CurrentUser, SettingsDep, require_allowed_origin
from app.schemas.auth import PasswordChange, TokenRead
from app.schemas.common import ErrorResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter(
    prefix='/auth',
    tags=['Аутентификация'],
    dependencies=[Depends(require_allowed_origin)],
    responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}},
)
CsrfHeader = Annotated[
    str | None, Header(alias='X-CSRF-Token', description='Значение cookie library_csrf для refresh и logout.'),
]


@router.post(
    path='/register',
    response_model=UserRead,
    status_code=201,
    summary='Регистрация обычного пользователя',
    responses={409: {'model': ErrorResponse}},
)
def register(data: UserCreate, service: AuthServiceDep, response: Response) -> UserRead:
    response.headers['Cache-Control'] = 'no-store'

    return service.register(data)


@router.post('/login', response_model=TokenRead, summary='Вход: access JWT и refresh-cookie')
def login(
        form: Annotated[OAuth2PasswordRequestForm, Depends()],
        service: AuthServiceDep,
        settings: SettingsDep,
        response: Response,
) -> TokenRead:
    tokens = service.login(form.username, form.password)
    set_auth_cookies(response, tokens, settings)

    return tokens.token


@router.post('/refresh', response_model=TokenRead, summary='Ротация refresh и новый access JWT')
def refresh(
        request: Request,
        response: Response,
        service: AuthServiceDep,
        settings: SettingsDep,
        csrf_header: CsrfHeader = None,
) -> TokenRead:
    tokens = service.refresh(refresh_credentials(request, csrf_header))
    set_auth_cookies(response, tokens, settings)

    return tokens.token


@router.post('/logout', status_code=204, summary='Отозвать текущую сессию и очистить cookies')
def logout(
        request: Request,
        response: Response,
        service: AuthServiceDep,
        settings: SettingsDep,
        csrf_header: CsrfHeader = None,
) -> None:
    service.logout(refresh_credentials(request, csrf_header))
    clear_auth_cookies(response, settings)


@router.post('/change-password', status_code=204, summary='Сменить пароль и отозвать все сессии')
def change_password(
        data: PasswordChange,
        principal: CurrentUser,
        service: AuthServiceDep,
        settings: SettingsDep,
        response: Response,
) -> None:
    service.change_password(principal, data)
    clear_auth_cookies(response, settings)
