from math import ceil

from fastapi import Request, Response

from app.core.config import Settings
from app.db.types import utc_now
from app.services.auth import IssuedTokens, RefreshCredentials

REFRESH_COOKIE = 'library_refresh'
CSRF_COOKIE = 'library_csrf'
REFRESH_PATH = '/api/v1/auth'


def refresh_credentials(request: Request, csrf_header: str | None) -> RefreshCredentials:
    return RefreshCredentials(
        refresh_token=request.cookies.get(REFRESH_COOKIE),
        csrf_cookie=request.cookies.get(CSRF_COOKIE),
        csrf_header=csrf_header,
    )


def set_auth_cookies(response: Response, tokens: IssuedTokens, settings: Settings) -> None:
    max_age = max(0, ceil((tokens.refresh_expires_at - utc_now()).total_seconds()))

    response.set_cookie(
        REFRESH_COOKIE, tokens.refresh_token, max_age=max_age, expires=tokens.refresh_expires_at,
        path=REFRESH_PATH, httponly=True, secure=settings.auth_cookie_secure, samesite='lax',
    )
    response.set_cookie(
        CSRF_COOKIE, tokens.csrf_token, max_age=max_age, expires=tokens.refresh_expires_at,
        path='/', httponly=False, secure=settings.auth_cookie_secure, samesite='lax',
    )

    response.headers['Cache-Control'] = 'no-store'


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        REFRESH_COOKIE, path=REFRESH_PATH, httponly=True, secure=settings.auth_cookie_secure, samesite='lax',
    )
    response.delete_cookie(
        CSRF_COOKIE, path='/', httponly=False, secure=settings.auth_cookie_secure, samesite='lax',
    )

    response.headers['Cache-Control'] = 'no-store'
