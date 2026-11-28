from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import hmac
from uuid import UUID, uuid4

import jwt
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError, ForbiddenError
from app.core.security import (
    create_access_token, create_csrf_token, create_refresh_token, decode_access_token,
    dummy_password_hash, hash_password, hash_refresh_token, valid_refresh_token, verify_csrf_token, verify_password,
)
from app.db.types import utc_now
from app.enum.user import Role
from app.models import AuthSession, User
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginInput, PasswordChange, TokenRead
from app.schemas.user import UserCreate, UserRead


@dataclass(frozen=True)
class AuthenticatedUser:
    user: UserRead
    session_id: UUID


@dataclass(frozen=True)
class RefreshCredentials:
    refresh_token: str | None = field(default=None, repr=False)
    csrf_cookie: str | None = field(default=None, repr=False)
    csrf_header: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class IssuedTokens:
    token: TokenRead
    refresh_token: str = field(repr=False)
    csrf_token: str = field(repr=False)
    refresh_expires_at: datetime


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)
        self.sessions = AuthSessionRepository(db)

    def register(self, data: UserCreate) -> UserRead:
        try:
            with self.db.begin():
                if self.users.get_by_username(data.username) is not None:
                    raise self._username_conflict()

                user = self.users.add(User(
                    **data.model_dump(),
                    password=hash_password(data.password.get_secret_value()),
                    role=Role.user,
                    is_active=True,
                ))

                result = UserRead.model_validate(user)

            return result
        except IntegrityError as error:
            if error.orig.args[0] == 1062:
                raise self._username_conflict() from None

            raise

    def login(self, username: str, password: str) -> IssuedTokens:
        fallback_hash = dummy_password_hash()

        try:
            data = LoginInput(username=username, password=password)
        except ValidationError:
            verify_password('invalid-login-input', fallback_hash)

            raise self._invalid_credentials() from None

        with self.db.begin():
            user = self.users.get_by_username(data.username, for_update=True)

            password_valid = verify_password(
                data.password.get_secret_value(),
                user.password if user is not None else fallback_hash,
            )

            if user is None or not password_valid or not user.is_active:
                raise self._invalid_credentials()

            now = utc_now()
            refresh = create_refresh_token()
            session = self.sessions.add(AuthSession(
                id=uuid4(),
                user_id=user.id,
                refresh_token_hash=hash_refresh_token(refresh),
                created_at=now,
                expires_at=now + timedelta(days=self.settings.refresh_token_days),
            ))

            result = self._issue_tokens(user, session, refresh)

        return result

    def authenticate_access(self, token: str | None) -> AuthenticatedUser:
        if not token:
            raise AuthenticationError('authentication_required', 'Требуется вход в систему.')

        try:
            claims = decode_access_token(token, self.settings.jwt_secret_key.get_secret_value())
        except jwt.InvalidTokenError:
            raise self._invalid_session() from None

        with self.db.begin():
            user = self.users.get_by_id(claims.user_id)
            session = self.sessions.get_by_id(claims.session_id)
            user, session = self._require_live_session(user, session)

            result = AuthenticatedUser(user=UserRead.model_validate(user), session_id=session.id)

        return result

    def refresh(self, credentials: RefreshCredentials) -> IssuedTokens:
        with self.db.begin():
            user, session = self._lock_refresh_session(credentials)

            refresh = create_refresh_token()
            session.refresh_token_hash = hash_refresh_token(refresh)

            self.db.flush()

            result = self._issue_tokens(user, session, refresh)

        return result

    def logout(self, credentials: RefreshCredentials) -> None:
        with self.db.begin():
            _user, session = self._lock_refresh_session(credentials)
            session.revoked_at = utc_now()

            self.db.flush()

    def change_password(self, principal: AuthenticatedUser, data: PasswordChange) -> None:
        with self.db.begin():
            user = self.users.get_by_id(principal.user.id, for_update=True)
            session = self.sessions.get_by_id(principal.session_id, for_update=True)

            user, session = self._require_live_session(user, session)

            if not verify_password(data.old_password.get_secret_value(), user.password):
                raise AuthenticationError('invalid_current_password', 'Текущий пароль неверен.')

            user.password = hash_password(data.new_password.get_secret_value())

            self.sessions.revoke_all(user.id, utc_now())
            self.db.flush()

    def _lock_refresh_session(self, credentials: RefreshCredentials) -> tuple[User, AuthSession]:
        if not valid_refresh_token(credentials.refresh_token):
            raise self._invalid_session()

        token_hash = hash_refresh_token(credentials.refresh_token)
        candidate = self.sessions.get_by_refresh_hash(token_hash)

        if candidate is None:
            raise self._invalid_session()

        user = self.users.get_by_id(candidate.user_id, for_update=True)
        session = self.sessions.get_by_id(candidate.id, for_update=True)
        user, session = self._require_live_session(user, session)

        if not hmac.compare_digest(session.refresh_token_hash, token_hash):
            raise self._invalid_session()
        if not verify_csrf_token(
                session.id, credentials.csrf_cookie, credentials.csrf_header,
                self.settings.jwt_secret_key.get_secret_value(),
        ):
            raise ForbiddenError('csrf_invalid', 'Проверка CSRF не пройдена.')

        return user, session

    def _issue_tokens(self, user: User, session: AuthSession, refresh: str) -> IssuedTokens:
        now = utc_now()
        expires = min(
            int(now.timestamp()) + self.settings.access_token_minutes * 60,
            int(session.expires_at.timestamp()),
        )

        if expires <= int(now.timestamp()):
            raise self._invalid_session()

        secret_key = self.settings.jwt_secret_key.get_secret_value()
        access = create_access_token(
            user.id, session.id, secret_key, now, datetime.fromtimestamp(expires, UTC)
        )

        return IssuedTokens(
            token=TokenRead(access_token=access, expires_in=expires - int(now.timestamp())),
            refresh_token=refresh, csrf_token=create_csrf_token(session.id, secret_key),
            refresh_expires_at=session.expires_at
        )

    @staticmethod
    def _require_live_session(user: User | None, session: AuthSession | None) -> tuple[User, AuthSession]:
        if (
                user is None or not user.is_active or session is None or session.user_id != user.id
                or session.revoked_at is not None or session.expires_at <= utc_now()
        ):
            raise AuthService._invalid_session()

        return user, session

    @staticmethod
    def _invalid_session() -> AuthenticationError:
        return AuthenticationError('invalid_session', 'Токен или сессия недействительны. Войдите заново.')

    @staticmethod
    def _invalid_credentials() -> AuthenticationError:
        return AuthenticationError('invalid_credentials', 'Неверный логин или пароль.')

    @staticmethod
    def _username_conflict() -> ConflictError:
        return ConflictError('username_conflict', 'Пользователь с таким логином уже существует.')
