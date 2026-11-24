from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.db.types import utc_now
from app.models import Author, Book, Category
from app.repositories.authors import AuthorRepository
from app.repositories.books import BookRepository, BookWithRating
from app.repositories.categories import CategoryRepository
from app.schemas.book import BookCreate, BookDetail, BookQuery, BookRead, BookUpdate
from app.schemas.common import Page


class BookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = BookRepository(db)
        self.authors = AuthorRepository(db)
        self.categories = CategoryRepository(db)

    def list(self, filters: BookQuery) -> Page[BookDetail]:
        records = self.repository.list(filters)

        return Page[BookDetail](
            items=[self._to_detail(record) for record in records],
            total=self.repository.count(filters), page=filters.page, page_size=filters.page_size,
        )

    def get(self, book_id: int) -> BookDetail:
        record = self.repository.get_detail(book_id)

        if record is None:
            raise self._not_found()

        return self._to_detail(record)

    def create(self, data: BookCreate) -> BookRead:
        try:
            with self.db.begin():
                self._check_isbn(data.isbn)

                authors = self._resolve_authors(data.author_ids)
                categories = self._resolve_categories(data.category_ids)

                book = self.repository.add(data, authors, categories)
                result = BookRead.model_validate(book)

            return result
        except IntegrityError as error:
            self._raise_integrity_conflict(error)
            raise

    def update(self, book_id: int, data: BookUpdate) -> BookRead:
        try:
            with self.db.begin():
                book = self._require_book(book_id, for_update=True)
                changes = data.model_dump(exclude_unset=True)

                if 'isbn' in changes:
                    self._check_isbn(changes['isbn'], current_book_id=book.id)
                if 'author_ids' in changes:
                    book.authors = self._resolve_authors(changes.pop('author_ids'))
                if 'category_ids' in changes:
                    book.categories = self._resolve_categories(changes.pop('category_ids'))

                for field, value in changes.items():
                    setattr(book, field, value)

                if data.model_fields_set:
                    book.updated_at = utc_now()

                self.db.flush()

                result = BookRead.model_validate(book)

            return result
        except IntegrityError as error:
            self._raise_integrity_conflict(error)
            raise

    def delete(self, book_id: int) -> None:
        with self.db.begin():
            book = self._require_book(book_id, for_update=True)

            book.deleted_at = utc_now()
            book.updated_at = book.deleted_at

            self.db.flush()

    def _require_book(self, book_id: int, *, for_update: bool = False) -> Book:
        book = self.repository.get_by_id(book_id, for_update=for_update)

        if book is None:
            raise self._not_found()

        return book

    def _resolve_authors(self, author_ids: list[int]) -> list[Author]:
        authors = self.authors.get_by_ids(author_ids, for_share=True)
        missing = sorted(set(author_ids) - {author.id for author in authors})

        if missing:
            raise NotFoundError('author_not_found', f'Не найдены авторы: {missing}.')

        return authors

    def _resolve_categories(self, category_ids: list[int]) -> list[Category]:
        categories = self.categories.get_by_ids(category_ids, for_share=True)
        missing = sorted(set(category_ids) - {category.id for category in categories})

        if missing:
            raise NotFoundError('category_not_found', f'Не найдены категории: {missing}.')

        return categories

    def _check_isbn(self, isbn: str | None, *, current_book_id: int | None = None) -> None:
        if isbn is not None:
            existing = self.repository.get_by_isbn(isbn)

            if existing is not None and existing.id != current_book_id:
                raise self._isbn_conflict()

    @staticmethod
    def _to_detail(record: BookWithRating) -> BookDetail:
        fields = BookRead.model_validate(record.book).model_dump()

        return BookDetail(**fields, average_rating=record.average_rating, ratings_count=record.ratings_count)

    @staticmethod
    def _not_found() -> NotFoundError:
        return NotFoundError('book_not_found', 'Книга не найдена.')

    @staticmethod
    def _isbn_conflict() -> ConflictError:
        return ConflictError('book_isbn_conflict', 'Книга с таким ISBN уже существует, в том числе в архиве.')

    def _raise_integrity_conflict(self, error: IntegrityError) -> None:
        if error.orig.args[0] == 1062:
            raise self._isbn_conflict() from None

        if error.orig.args[0] == 1452:
            raise ConflictError(
                code='book_relations_conflict',
                message='Автор или категория больше не доступны. Повторите запрос.'
            ) from None
