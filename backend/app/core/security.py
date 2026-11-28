from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from hashlib import sha256
import hmac
import re
import secrets
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except UnknownHashError:
        return False


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    return hash_password(secrets.token_urlsafe(32))


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    session_id: UUID


def create_access_token(
        user_id: int, session_id: UUID, secret_key: str, issued_at: datetime, expires_at: datetime
) -> str:
    return jwt.encode({
        'sub': str(user_id), 'sid': str(session_id),
        'iat': int(issued_at.timestamp()), 'exp': int(expires_at.timestamp()), 'jti': uuid4().hex,
    }, secret_key, algorithm='HS256')


def decode_access_token(token: str, secret_key: str) -> AccessClaims:
    if len(token) > 4096:
        raise jwt.InvalidTokenError('Слишком длинный токен.')

    try:
        payload = jwt.decode(
            token, secret_key, algorithms=['HS256'], options={'require': ['sub', 'sid', 'iat', 'exp']},
        )

        if not isinstance(payload['sub'], str) or not isinstance(payload['sid'], str):
            raise ValueError

        user_id = int(payload['sub'])

        if not 1 <= user_id <= 2147483647 or str(user_id) != payload['sub']:
            raise ValueError
        if type(payload['iat']) is not int or type(payload['exp']) is not int or payload['exp'] <= payload['iat']:
            raise ValueError

        return AccessClaims(user_id=user_id, session_id=UUID(payload['sid']))
    except (TypeError, ValueError, OverflowError):
        raise jwt.InvalidTokenError('Некорректные поля токена.') from None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def valid_refresh_token(token: str | None) -> bool:
    return isinstance(token, str) and re.fullmatch(r'[A-Za-z0-9_-]{43}', token) is not None


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode('utf-8')).hexdigest()


def _csrf_signature(session_id: UUID, nonce: str, secret_key: str) -> str:
    # Отдельный ключ HMAC выведен из общего секрета с назначением именно для CSRF.
    key = hmac.digest(secret_key.encode('utf-8'), b'library:csrf-key:v1', 'sha256')
    return hmac.digest(key, session_id.bytes + nonce.encode('ascii'), 'sha256').hex()


def create_csrf_token(session_id: UUID, secret_key: str) -> str:
    nonce = secrets.token_urlsafe(32)
    return nonce + '.' + _csrf_signature(session_id, nonce, secret_key)


def verify_csrf_token(session_id: UUID, cookie: str | None, header: str | None, secret_key: str) -> bool:
    if cookie is None or header is None or len(cookie) != 108 or len(header) != 108:
        return False
    if not hmac.compare_digest(cookie.encode('utf-8'), header.encode('utf-8')):
        return False
    if re.fullmatch(r'[A-Za-z0-9_-]{43}\.[0-9a-f]{64}', cookie) is None:
        return False

    nonce, signature = cookie.split('.', 1)

    return hmac.compare_digest(signature, _csrf_signature(session_id, nonce, secret_key))
