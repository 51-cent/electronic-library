from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class Review(TimestampMixin, Base):
    __tablename__ = 'reviews'
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id'),
        CheckConstraint('rating BETWEEN 1 AND 5', name='rating_range'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id', ondelete='CASCADE'), index=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    text: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates='reviews')
    book: Mapped[Book] = relationship(back_populates='reviews')
