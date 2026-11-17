from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import book_categories

if TYPE_CHECKING:
    from app.models.book import Book


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    books: Mapped[list[Book]] = relationship(
        secondary=book_categories, back_populates='categories', passive_deletes=True,
    )
