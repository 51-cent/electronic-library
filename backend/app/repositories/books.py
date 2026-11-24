from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import Author, Book, Category, Review
from app.schemas.book import BookCreate, BookQuery


@dataclass(frozen=True)
class BookWithRating:
    book: Book
    average_rating: float | None
    ratings_count: int


class BookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rating_stats = select(
            Review.book_id,
            func.avg(Review.rating).label('average_rating'),
            func.count(Review.id).label('ratings_count'),
        ).group_by(Review.book_id).subquery('rating_stats')

    def list(self, filters: BookQuery) -> list[BookWithRating]:
        query = self._select_with_ratings().where(*self._conditions(filters))
        sort_columns = {
            'title': Book.title,
            'publication_year': Book.publication_year,
            'created_at': Book.created_at,
            'rating': self.rating_stats.c.average_rating,
        }
        column = sort_columns[filters.sort_by]

        if filters.sort_by in ('publication_year', 'rating'):
            query = query.order_by(column.is_(None))
        if filters.sort_order == 'asc':
            query = query.order_by(column.asc(), Book.id.asc())
        else:
            query = query.order_by(column.desc(), Book.id.desc())

        query = query.limit(filters.page_size).offset((filters.page - 1) * filters.page_size)

        return [
            BookWithRating(book, float(average) if average is not None else None, int(count))
            for book, average, count in self.db.execute(query).all()
        ]

    def count(self, filters: BookQuery) -> int:
        query = select(func.count()).select_from(Book).where(*self._conditions(filters))

        return self.db.execute(query).scalar_one()

    def get_detail(self, book_id: int) -> BookWithRating | None:
        query = self._select_with_ratings().where(Book.id == book_id, Book.deleted_at.is_(None))
        row = self.db.execute(query).one_or_none()

        if row is None:
            return None

        book, average, count = row

        return BookWithRating(book, float(average) if average is not None else None, int(count))

    def get_by_id(self, book_id: int, *, for_update: bool = False) -> Book | None:
        query = select(Book).where(Book.id == book_id, Book.deleted_at.is_(None)).options(
            selectinload(Book.authors), selectinload(Book.categories),
        )
        if for_update:
            query = query.with_for_update()
        return self.db.scalar(query)

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.db.scalar(select(Book).where(Book.isbn == isbn))

    def add(self, data: BookCreate, authors: list[Author], categories: list[Category]) -> Book:
        values = data.model_dump(exclude={'author_ids', 'category_ids'})
        book = Book(**values, authors=authors, categories=categories)

        self.db.add(book)
        self.db.flush()

        return book

    def _select_with_ratings(self) -> Select:
        return select(
            Book,
            self.rating_stats.c.average_rating,
            func.coalesce(self.rating_stats.c.ratings_count, 0).label('ratings_count')
        ).outerjoin(
            self.rating_stats, self.rating_stats.c.book_id == Book.id,
        ).options(selectinload(Book.authors), selectinload(Book.categories))

    @staticmethod
    def _conditions(filters: BookQuery) -> list[ColumnElement[bool]]:
        conditions = [Book.deleted_at.is_(None)]

        if filters.q is not None:
            conditions.append(or_(
                Book.title.contains(filters.q, autoescape=True),
                Book.authors.any(Author.full_name.contains(filters.q, autoescape=True)),
                Book.categories.any(Category.name.contains(filters.q, autoescape=True)),
            ))
        if filters.author_id is not None:
            conditions.append(Book.authors.any(Author.id == filters.author_id))
        if filters.category_id is not None:
            conditions.append(Book.categories.any(Category.id == filters.category_id))
        if filters.year_from is not None:
            conditions.append(Book.publication_year >= filters.year_from)
        if filters.year_to is not None:
            conditions.append(Book.publication_year <= filters.year_to)
        if filters.created_from is not None:
            conditions.append(Book.created_at >= filters.created_from)
        if filters.created_to is not None:
            conditions.append(Book.created_at < filters.created_to)

        return conditions
