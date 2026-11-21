from typing import Annotated

from pydantic import Field, StringConstraints

from app.schemas.common import InputSchema, PositiveId, ReadSchema, UpdateSchema, UtcDatetime
from app.schemas.user import UserSummary


Rating = Annotated[int, Field(strict=True, ge=1, le=5)]
ReviewText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]


class ReviewCreate(InputSchema):
    rating: Rating
    text: ReviewText | None = None


class ReviewUpdate(UpdateSchema):
    non_nullable_fields = ('rating',)

    rating: Rating | None = None
    text: ReviewText | None = None


class ReviewRead(ReadSchema):
    id: PositiveId
    book_id: PositiveId
    rating: Rating
    text: str | None
    created_at: UtcDatetime
    updated_at: UtcDatetime
    user: UserSummary
