import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config


def main() -> None:
    backend_dir = Path(__file__).resolve().parent
    command.upgrade(Config(str(backend_dir / 'alembic.ini')), 'head')
    os.execv(sys.executable, [
        sys.executable, '-m', 'uvicorn', 'app.main:app',
        '--app-dir', str(backend_dir), '--host', '0.0.0.0', '--port', '8000',
        '--reload', '--reload-dir', str(backend_dir),
    ])


if __name__ == '__main__':
    main()
