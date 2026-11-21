from uuid import UUID

from app.schemas.common import PositiveId, ReadSchema, UtcDatetime


class AuthSessionRead(ReadSchema):
    id: UUID
    user_id: PositiveId
    created_at: UtcDatetime
    expires_at: UtcDatetime
    revoked_at: UtcDatetime | None
