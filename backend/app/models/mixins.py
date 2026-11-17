from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import UTCDateTime, utc_now


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, onupdate=utc_now,
    )
