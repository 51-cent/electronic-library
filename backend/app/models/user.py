from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enum.user import Role
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.auth_session import AuthSession
    from app.models.review import Review
    from app.models.user_book import UserBook


class User(CreatedAtMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(254))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name='user_role', values_callable=lambda values: [v.value for v in values], validate_strings=True),
        default=Role.user, server_default=Role.user.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates='user', cascade='all, delete-orphan', passive_deletes=True,
    )
    library: Mapped[list[UserBook]] = relationship(
        back_populates='user', cascade='all, delete-orphan', passive_deletes=True,
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates='user', cascade='all, delete-orphan', passive_deletes=True,
    )
