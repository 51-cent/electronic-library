from app.enum.book import ReadingStatus
from app.schemas.book import BookSummary
from app.schemas.common import InputSchema, PositiveId, ReadSchema, UtcDatetime


class UserBookUpdate(InputSchema):
    reading_status: ReadingStatus


class UserBookRead(ReadSchema):
    user_id: PositiveId
    book_id: PositiveId
    is_favorite: bool
    reading_status: ReadingStatus
    finished_at: UtcDatetime | None
    created_at: UtcDatetime
    updated_at: UtcDatetime
    book: BookSummary
