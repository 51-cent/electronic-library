from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CHAR, CheckConstraint, Enum, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime
from app.enum.book import Status
from app.models.associations import book_authors, book_categories
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.category import Category
    from app.models.review import Review
    from app.models.user_book import UserBook


class Book(TimestampMixin, Base):
    __tablename__ = 'books'
    __table_args__ = (
        CheckConstraint('publication_year IS NULL OR publication_year BETWEEN 1 AND 9999', name='publication_year_range'),
        Index('ix_books_created_at', 'created_at'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[str | None] = mapped_column(CHAR(13), unique=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    status: Mapped[Status] = mapped_column(
        Enum(Status, name='book_status', values_callable=lambda values: [v.value for v in values], validate_strings=True),
        default=Status.active, server_default=Status.active.value,
    )
    cover_url: Mapped[str | None] = mapped_column(String(2048))
    content_path: Mapped[str | None] = mapped_column(String(512))
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    authors: Mapped[list[Author]] = relationship(secondary=book_authors, back_populates='books')
    categories: Mapped[list[Category]] = relationship(secondary=book_categories, back_populates='books')
    library_entries: Mapped[list[UserBook]] = relationship(
        back_populates='book', cascade='all, delete-orphan', passive_deletes=True,
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates='book', cascade='all, delete-orphan', passive_deletes=True,
    )

    @property
    def is_archived(self) -> bool:
        return self.deleted_at is not None

    @property
    def has_content(self) -> bool:
        return bool(self.content_path) and not self.is_archived and self.status == Status.active
