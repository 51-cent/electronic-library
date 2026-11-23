from logging.config import fileConfig

from alembic import context
from alembic.autogenerate.api import AutogenContext
from sqlalchemy import Boolean, Connection, create_engine, pool

from app.core.config import get_settings
from app.db.types import UTCDateTime
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
if not target_metadata.tables:
    raise RuntimeError('Модели не загружены: Base.metadata пуст. Проверьте импорт app.models.')


def render_item(kind: str, item: object, autogen_context: AutogenContext) -> str | bool:
    if kind == 'type' and isinstance(item, UTCDateTime):
        autogen_context.imports.add('from sqlalchemy.dialects import mysql')
        return 'mysql.DATETIME(fsp=6)'

    return False


def compare_server_defaults(
        migration_context, _inspected_column, metadata_column,
        inspected_default, _metadata_default, rendered_metadata_default,
) -> bool | None:
    if migration_context.dialect.name == 'mysql' and isinstance(metadata_column.type, Boolean):
        equivalents = {'true': '1', '1': '1', 'false': '0', '0': '0'}

        def normalize(value: str | None) -> str | None:
            return equivalents.get(value.strip("()'\" ").lower()) if value is not None else None

        actual = normalize(inspected_default)
        expected = normalize(rendered_metadata_default)

        if actual is not None and expected is not None:
            return actual != expected

    return None


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        render_item=render_item,
        compare_type=True,
        compare_server_default=compare_server_defaults,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_with_connection(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,
        compare_type=True,
        compare_server_default=compare_server_defaults,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied_connection = config.attributes.get('connection')
    if supplied_connection is not None:
        run_with_connection(supplied_connection)
        return

    engine = create_engine(
        get_settings().database_url,
        poolclass=pool.NullPool,
        connect_args={'connect_timeout': 5},
    )
    try:
        with engine.connect() as connection:
            run_with_connection(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
