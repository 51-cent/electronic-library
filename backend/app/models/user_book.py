from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime
from app.enum.book import ReadingStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class UserBook(TimestampMixin, Base):
    __tablename__ = 'user_books'
    __table_args__ = (
        CheckConstraint(
            "(reading_status = 'finished' AND finished_at IS NOT NULL) OR "
            "(reading_status <> 'finished' AND finished_at IS NULL)",
            name='finished_at_matches_status',
        ),
        Index('ix_user_books_user_id_reading_status', 'user_id', 'reading_status'),
        Index('ix_user_books_user_id_is_favorite', 'user_id', 'is_favorite'),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id', ondelete='CASCADE'), primary_key=True, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    reading_status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus, name='reading_status', values_callable=lambda values: [v.value for v in values], validate_strings=True),
        default=ReadingStatus.planned, server_default=ReadingStatus.planned.value,
    )
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(back_populates='library')
    book: Mapped[Book] = relationship(back_populates='library_entries')
