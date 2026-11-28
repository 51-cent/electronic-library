from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator

from app.schemas.common import InputSchema, ReadSchema
from app.schemas.user import Username


class LoginInput(InputSchema):
    username: Username
    password: SecretStr = Field(min_length=1, max_length=128, exclude=True)


class TokenRead(ReadSchema):
    access_token: str = Field(repr=False)
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int = Field(gt=0)


class PasswordChange(InputSchema):
    old_password: SecretStr = Field(min_length=1, max_length=128, exclude=True)
    new_password: SecretStr = Field(min_length=8, max_length=128, exclude=True)

    @model_validator(mode='after')
    def require_new_password(self) -> Self:
        if self.old_password.get_secret_value() == self.new_password.get_secret_value():
            raise ValueError('Новый пароль должен отличаться от старого.')

        return self
