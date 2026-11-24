from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.models import Category, book_categories


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, limit: int, offset: int) -> list[Category]:
        query = select(Category).order_by(Category.id).limit(limit).offset(offset)

        return list(self.db.scalars(query).all())

    def count(self) -> int:
        return self.db.execute(select(func.count()).select_from(Category)).scalar_one()

    def get_by_id(self, category_id: int, *, for_update: bool = False) -> Category | None:
        query = select(Category).where(Category.id == category_id)

        if for_update:
            query = query.with_for_update()

        return self.db.scalar(query)

    def get_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.name == name))

    def get_by_ids(self, category_ids: list[int], *, for_share: bool = False) -> list[Category]:
        query = select(Category).where(Category.id.in_(category_ids)).order_by(Category.id)
        if for_share:
            query = query.with_for_update(read=True)
        return list(self.db.scalars(query).all())

    def is_used(self, category_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(book_categories.c.category_id == category_id))))

    def add(self, name: str) -> Category:
        category = Category(name=name)

        self.db.add(category)
        self.db.flush()

        return category

    def delete(self, category_id: int) -> None:
        self.db.execute(delete(Category).where(Category.id == category_id))
