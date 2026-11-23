import argparse
from getpass import getpass
import os
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ApplicationError
from app.schemas.user import UserCreate
from app.scripts._common import CommandError, database_session, validation_message
from app.services.admin import AdminService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Создать администратора электронной библиотеки.')
    parser.add_argument('--username', help='Логин')
    parser.add_argument('--first-name', help='Имя')
    parser.add_argument('--last-name', help='Фамилия')
    parser.add_argument('--email', help='Электронная почта')
    args = parser.parse_args(argv)

    try:
        values = {}
        for field, label in [('username', 'Логин'), ('first_name', 'Имя'), ('last_name', 'Фамилия'), ('email', 'Email')]:
            value = getattr(args, field)

            if value is None:
                if not sys.stdin.isatty():
                    raise CommandError(f'Передайте --{field.replace("_", "-")} или запустите команду в терминале.')

                value = input(label + ': ')

            values[field] = value

        password = os.environ.get('ADMIN_PASSWORD')
        if not password:
            if not sys.stdin.isatty():
                raise CommandError('Для скрытого ввода пароля нужен терминал; для автоматизации задайте ADMIN_PASSWORD.')

            password = getpass('Пароль: ')

            if password != getpass('Повторите пароль: '):
                raise CommandError('Пароли не совпадают.')

        data = UserCreate(**values, password=password)
        with database_session() as db:
            result = AdminService(db).create(data)

        if result.created:
            print(f'Администратор {result.user.username} создан, id={result.user.id}.')
        else:
            print(f'Администратор {result.user.username} уже существует. Пароль и профиль не изменены.')

        return 0
    except ValidationError as error:
        print(validation_message(error), file=sys.stderr)
    except (CommandError, ApplicationError) as error:
        print(str(error), file=sys.stderr)
    except SQLAlchemyError:
        print('Не удалось создать администратора. Проверьте подключение к MySQL и миграции.', file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print('Создание администратора отменено.', file=sys.stderr)

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
