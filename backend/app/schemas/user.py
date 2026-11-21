from typing import Annotated

from pydantic import EmailStr, Field, SecretStr, StringConstraints

from app.enum.user import Role
from app.schemas.common import InputSchema, Name, PositiveId, ReadSchema, UpdateSchema, UtcDatetime


Username = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=64, pattern=r'^[a-zA-Z0-9_]+$')]
Email = Annotated[EmailStr, Field(max_length=254)]


class UserCreate(InputSchema):
    username: Username
    first_name: Name
    last_name: Name
    email: Email
    password: SecretStr = Field(min_length=8, max_length=128, exclude=True)


class UserUpdate(UpdateSchema):
    non_nullable_fields = ('username', 'first_name', 'last_name')

    username: Username | None = None
    first_name: Name | None = None
    last_name: Name | None = None
    email: Email | None = None


class UserSummary(ReadSchema):
    id: PositiveId
    username: str
    first_name: str
    last_name: str


class UserRead(UserSummary):
    email: Email | None
    role: Role
    is_active: bool
    created_at: UtcDatetime
