from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.core.config import Settings, get_settings


def get_db() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def require_catalog_write_access() -> None:
    pass
