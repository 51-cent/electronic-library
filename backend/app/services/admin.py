from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.enum.user import Role
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserRead


@dataclass(frozen=True)
class AdminResult:
    user: UserRead
    created: bool


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = UserRepository(db)

    def create(self, data: UserCreate) -> AdminResult:
        try:
            with self.db.begin():
                existing = self.repository.get_by_username(data.username)

                if existing is not None:
                    if existing.role != Role.admin or not existing.is_active:
                        raise ConflictError('admin_username_conflict', 'Логин занят. Существующая учётная запись не изменена.')

                    return AdminResult(user=UserRead.model_validate(existing), created=False)

                values = data.model_dump()

                user = self.repository.add(User(
                    **values,
                    password=hash_password(data.password.get_secret_value()),
                    role=Role.admin,
                    is_active=True,
                ))

                result = AdminResult(user=UserRead.model_validate(user), created=True)

            return result
        except IntegrityError as error:
            if error.orig.args[0] == 1062:
                raise ConflictError('admin_username_conflict', 'Пользователь с таким логином уже существует.') from None

            raise
