from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, NotFoundError
from app.db.types import utc_now
from app.enum.book import ReadingStatus
from app.models import Book, UserBook
from app.repositories.library import LibraryRepository
from app.repositories.users import UserRepository
from app.schemas.common import Page, PageInput
from app.schemas.user_book import LibraryQuery, UserBookRead, UserBookUpdate


@dataclass(frozen=True)
class LibraryWriteResult:
    entry: UserBookRead
    created: bool


class LibraryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = LibraryRepository(db)
        self.users = UserRepository(db)

    def list(self, user_id: int, filters: LibraryQuery) -> Page[UserBookRead]:
        entries = self.repository.list(user_id, filters)

        return Page[UserBookRead](
            items=[UserBookRead.model_validate(entry) for entry in entries],
            total=self.repository.count(user_id, filters),
            page=filters.page,
            page_size=filters.page_size
        )

    def list_favorites(self, user_id: int, pagination: PageInput) -> Page[UserBookRead]:
        return self.list(user_id, LibraryQuery(
            page=pagination.page, page_size=pagination.page_size, is_favorite=True,
        ))

    def add_favorite(self, user_id: int, book_id: int) -> LibraryWriteResult:
        with self.db.begin():
            self._lock_user(user_id)

            book = self._require_book(book_id)
            entry = self.repository.get_entry(user_id, book_id)
            created = entry is None

            if created:
                entry = self._create_entry(user_id, book, ReadingStatus.planned, is_favorite=True)
            elif not entry.is_favorite:
                entry.is_favorite = True
                entry.updated_at = utc_now()

            self.db.flush()

            result = LibraryWriteResult(UserBookRead.model_validate(entry), created)

        return result

    def remove_favorite(self, user_id: int, book_id: int) -> None:
        with self.db.begin():
            self._lock_user(user_id)
            self._require_book(book_id, include_archived=True)

            entry = self.repository.get_entry(user_id, book_id)

            if entry is not None and entry.is_favorite:
                entry.is_favorite = False
                entry.updated_at = utc_now()

                self.db.flush()

    def set_status(self, user_id: int, book_id: int, data: UserBookUpdate) -> LibraryWriteResult:
        with self.db.begin():
            self._lock_user(user_id)

            book = self._require_book(book_id)
            entry = self.repository.get_entry(user_id, book_id)

            created = entry is None

            if created:
                entry = self._create_entry(user_id, book, data.reading_status)
            elif entry.reading_status != data.reading_status:
                now = utc_now()

                entry.reading_status = data.reading_status
                entry.finished_at = now if data.reading_status == ReadingStatus.finished else None
                entry.updated_at = now

            self.db.flush()

            result = LibraryWriteResult(UserBookRead.model_validate(entry), created)

        return result

    def _lock_user(self, user_id: int) -> None:
        user = self.users.get_by_id(user_id, for_update=True)

        if user is None or not user.is_active:
            raise AuthenticationError('invalid_session', 'Пользователь недоступен. Войдите заново.')

    def _require_book(self, book_id: int, *, include_archived: bool = False) -> Book:
        book = self.repository.get_book(book_id, include_archived=include_archived, for_share=True)

        if book is None:
            raise NotFoundError('book_not_found', 'Книга не найдена.')

        return book

    def _create_entry(
            self, user_id: int, book: Book, reading_status: ReadingStatus, *, is_favorite: bool = False
    ) -> UserBook:
        now = utc_now()

        return self.repository.add(UserBook(
            user_id=user_id,
            book=book,
            reading_status=reading_status,
            is_favorite=is_favorite,
            finished_at=now if reading_status == ReadingStatus.finished else None,
            created_at=now,
            updated_at=now
        ))
