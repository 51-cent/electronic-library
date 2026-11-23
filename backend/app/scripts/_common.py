from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_engine


class CommandError(Exception):
    pass


def validation_message(error: ValidationError) -> str:
    errors = error.errors(include_input=False, include_url=False, include_context=False)
    return '; '.join(f"{'.'.join(map(str, item['loc']))}: {item['msg']}" for item in errors)


@contextmanager
def database_session(*, seed_lock: bool = False) -> Iterator[Session]:
    engine = get_engine()
    try:
        with engine.connect() as connection:
            config_path = Path(__file__).resolve().parents[2] / 'alembic.ini'
            head = ScriptDirectory.from_config(Config(str(config_path))).get_current_head()
            current = MigrationContext.configure(connection).get_current_revision()

            if current != head:
                raise CommandError('Нет миграции')

            connection.commit()

            lock_name = None
            if seed_lock:
                suffix = sha256((engine.url.database or '').encode()).hexdigest()[:16]
                lock_name = 'library_seed_' + suffix
                acquired = connection.scalar(text('SELECT GET_LOCK(:name, 10)'), {'name': lock_name})
                connection.commit()

                if acquired != 1:
                    raise CommandError('Другой seed ещё выполняется')
            try:
                with Session(bind=connection, expire_on_commit=False) as db:
                    yield db
            finally:
                if lock_name is not None:
                    connection.execute(text('SELECT RELEASE_LOCK(:name)'), {'name': lock_name})
                    connection.commit()
    finally:
        engine.dispose()
