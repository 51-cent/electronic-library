from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = ""
    app_env: Literal["development", "test", "production"] = "development"
    mysql_host: str
    mysql_port: int = Field(default=3307, ge=1, le=65535)
    mysql_database: str = Field(min_length=1)
    mysql_user: str = Field(min_length=1)
    mysql_password: SecretStr = Field(min_length=1)
    jwt_secret_key: SecretStr = Field(min_length=32)
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=30)
    auth_cookie_secure: bool = False
    auth_allowed_origins: list[str]

    @field_validator('auth_allowed_origins')
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        if not origins:
            raise ValueError('Нужен хотя бы один разрешённый Origin.')

        result = []
        for origin in origins:
            parts = urlsplit(origin)

            if (
                parts.scheme not in ('http', 'https') or not parts.hostname or parts.username is not None
                or parts.password is not None or parts.path or parts.query or parts.fragment
            ):
                raise ValueError('Origin должен содержать только схему, хост и необязательный порт.')

            host = f'[{parts.hostname.lower()}]' if ':' in parts.hostname else parts.hostname.lower()
            port = parts.port
            default_port = 443 if parts.scheme == 'https' else 80

            result.append(f'{parts.scheme}://{host}' + (f':{port}' if port is not None and port != default_port else ''))

        return list(dict.fromkeys(result))

    @model_validator(mode='after')
    def validate_production_auth(self) -> 'Settings':
        if self.app_env == 'production':
            if not self.auth_cookie_secure or any(not origin.startswith('https://') for origin in self.auth_allowed_origins):
                raise ValueError('В production нужны Secure cookies и разрешённые Origin с HTTPS.')

        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.mysql_user,
            password=self.mysql_password.get_secret_value(),
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
