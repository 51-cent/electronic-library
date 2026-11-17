from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuthSession(CreatedAtMixin, Base):
    __tablename__ = 'auth_sessions'
    __table_args__ = (
        CheckConstraint('expires_at > created_at', name='expiration_after_creation'),
    )

    id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False), primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(back_populates='sessions')
