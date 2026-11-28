from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str, *, for_update: bool = False) -> User | None:
        query = select(User).where(User.username == username)

        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)

        return self.db.scalar(query)

    def get_by_id(self, user_id: int, *, for_update: bool = False) -> User | None:
        query = select(User).where(User.id == user_id)

        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)

        return self.db.scalar(query)

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()

        return user
