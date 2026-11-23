from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Author, Book, Category
from app.schemas.author import AuthorCreate
from app.schemas.book import BookCreate


class SeedRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_authors(self, full_name: str) -> list[Author]:
        return list(self.db.scalars(select(Author).where(Author.full_name == full_name)).all())

    def find_books(self, title: str) -> list[Book]:
        return list(self.db.scalars(select(Book).where(Book.title == title)).all())

    def add_author(self, data: AuthorCreate) -> Author:
        author = Author(**data.model_dump())

        self.db.add(author)
        self.db.flush()

        return author

    def add_book(self, data: BookCreate, authors: list[Author], categories: list[Category]) -> Book:
        values = data.model_dump(exclude={'author_ids', 'category_ids'})
        book = Book(**values, authors=authors, categories=categories)

        self.db.add(book)
        self.db.flush()

        return book
