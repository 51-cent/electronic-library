from typing import Annotated

from pydantic import StringConstraints

from app.schemas.common import InputSchema, PositiveId, ReadSchema, UpdateSchema, Year


AuthorName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
Biography = Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]


class AuthorCreate(InputSchema):
    full_name: AuthorName
    birth_year: Year | None = None
    biography: Biography | None = None


class AuthorUpdate(UpdateSchema):
    non_nullable_fields = ('full_name',)

    full_name: AuthorName | None = None
    birth_year: Year | None = None
    biography: Biography | None = None


class AuthorRead(ReadSchema):
    id: PositiveId
    full_name: str
    birth_year: int | None
    biography: str | None
