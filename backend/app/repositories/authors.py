from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.models import Author, book_authors
from app.schemas.author import AuthorCreate


class AuthorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, limit: int, offset: int) -> list[Author]:
        query = select(Author).order_by(Author.id).limit(limit).offset(offset)

        return list(self.db.scalars(query).all())

    def count(self) -> int:
        return self.db.execute(select(func.count()).select_from(Author)).scalar_one()

    def get_by_id(self, author_id: int, *, for_update: bool = False) -> Author | None:
        query = select(Author).where(Author.id == author_id)

        if for_update:
            query = query.with_for_update()

        return self.db.scalar(query)

    def get_by_ids(self, author_ids: list[int], *, for_share: bool = False) -> list[Author]:
        query = select(Author).where(Author.id.in_(author_ids)).order_by(Author.id)

        if for_share:
            query = query.with_for_update(read=True)

        return list(self.db.scalars(query).all())

    def is_used(self, author_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(book_authors.c.author_id == author_id))))

    def add(self, data: AuthorCreate) -> Author:
        author = Author(**data.model_dump())

        self.db.add(author)
        self.db.flush()

        return author

    def delete(self, author_id: int) -> None:
        self.db.execute(delete(Author).where(Author.id == author_id))
