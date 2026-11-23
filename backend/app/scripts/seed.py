import argparse
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.exceptions import ApplicationError
from app.scripts._common import CommandError, database_session, validation_message
from app.services.seed import SeedService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Добавить демонстрационный каталог без дублей.')
    parser.parse_args(argv)
    try:
        if get_settings().app_env == 'production':
            raise CommandError('Демонстрационный seed разрешён только в development и test.')

        with database_session(seed_lock=True) as db:
            result = SeedService(db).run()

        print(f'Создано категорий: {result.categories_created}; авторов: {result.authors_created}; книг: {result.books_created}.')

        return 0
    except ValidationError as error:
        print(validation_message(error), file=sys.stderr)
    except (CommandError, ApplicationError) as error:
        print(str(error), file=sys.stderr)
    except SQLAlchemyError:
        print('Не удалось выполнить seed. Проверьте подключение к MySQL и миграции.', file=sys.stderr)

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
