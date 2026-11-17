from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import book_authors

if TYPE_CHECKING:
    from app.models.book import Book


class Author(Base):
    __tablename__ = 'authors'
    __table_args__ = (
        CheckConstraint('birth_year IS NULL OR birth_year BETWEEN 1 AND 9999', name='birth_year_range'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(256))
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    biography: Mapped[str | None] = mapped_column(Text)

    books: Mapped[list[Book]] = relationship(
        secondary=book_authors, back_populates='authors', passive_deletes=True,
    )
