from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.elements import ColumnElement

from app.models import Book, UserBook
from app.schemas.user_book import LibraryQuery


class LibraryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user_id: int, filters: LibraryQuery) -> list[UserBook]:
        query = (
            select(UserBook)
            .where(*self._conditions(user_id, filters))
            .options(joinedload(UserBook.book, innerjoin=True))
            .order_by(UserBook.created_at.desc(), UserBook.book_id.desc())
            .limit(filters.page_size)
            .offset((filters.page - 1) * filters.page_size)
        )

        return list(self.db.scalars(query).all())

    def count(self, user_id: int, filters: LibraryQuery) -> int:
        query = select(func.count()).select_from(UserBook).where(*self._conditions(user_id, filters))

        return self.db.execute(query).scalar_one()

    def get_entry(self, user_id: int, book_id: int) -> UserBook | None:
        query = select(UserBook).where(
            UserBook.user_id == user_id, UserBook.book_id == book_id
        ).options(joinedload(UserBook.book, innerjoin=True)).execution_options(populate_existing=True)

        return self.db.scalar(query)

    def get_book(self, book_id: int, *, include_archived: bool = False, for_share: bool = False) -> Book | None:
        query = select(Book).where(Book.id == book_id)

        if not include_archived:
            query = query.where(Book.deleted_at.is_(None))
        if for_share:
            query = query.with_for_update(read=True).execution_options(populate_existing=True)

        return self.db.scalar(query)

    def add(self, entry: UserBook) -> UserBook:
        self.db.add(entry)

        return entry

    @staticmethod
    def _conditions(user_id: int, filters: LibraryQuery) -> list[ColumnElement[bool]]:
        conditions = [UserBook.user_id == user_id]

        if filters.reading_status is not None:
            conditions.append(UserBook.reading_status == filters.reading_status)
        if filters.is_favorite is not None:
            conditions.append(UserBook.is_favorite == filters.is_favorite)

        return conditions
