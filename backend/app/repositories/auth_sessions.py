from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AuthSession


class AuthSessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, session_id: UUID, *, for_update: bool = False) -> AuthSession | None:
        query = select(AuthSession).where(AuthSession.id == session_id)

        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)

        return self.db.scalar(query)

    def get_by_refresh_hash(self, token_hash: str) -> AuthSession | None:
        return self.db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == token_hash))

    def add(self, session: AuthSession) -> AuthSession:
        self.db.add(session)
        self.db.flush()

        return session

    def revoke_all(self, user_id: int, revoked_at: datetime) -> None:
        self.db.execute(update(AuthSession).where(
            AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None),
        ).values(revoked_at=revoked_at))
