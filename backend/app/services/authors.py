from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Author
from app.repositories.authors import AuthorRepository
from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.common import Page, PageInput


class AuthorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuthorRepository(db)

    def list(self, pagination: PageInput) -> Page[AuthorRead]:
        authors = self.repository.list(
            limit=pagination.page_size, offset=(pagination.page - 1) * pagination.page_size
        )

        return Page[AuthorRead](
            items=[AuthorRead.model_validate(author) for author in authors],
            total=self.repository.count(),
            page=pagination.page,
            page_size=pagination.page_size
        )

    def get(self, author_id: int) -> AuthorRead:
        return AuthorRead.model_validate(self._require_author(author_id))

    def create(self, data: AuthorCreate) -> AuthorRead:
        with self.db.begin():
            result = AuthorRead.model_validate(self.repository.add(data))

        return result

    def update(self, author_id: int, data: AuthorUpdate) -> AuthorRead:
        with self.db.begin():
            author = self._require_author(author_id, for_update=True)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(author, field, value)

            self.db.flush()

            result = AuthorRead.model_validate(author)

        return result

    def delete(self, author_id: int) -> None:
        try:
            with self.db.begin():
                self._require_author(author_id, for_update=True)

                if self.repository.is_used(author_id):
                    raise self._in_use_conflict()

                self.repository.delete(author_id)
        except IntegrityError as error:
            if error.orig.args[0] == 1451:
                raise self._in_use_conflict() from None

            raise

    def _require_author(self, author_id: int, *, for_update: bool = False) -> Author:
        author = self.repository.get_by_id(author_id, for_update=for_update)

        if author is None:
            raise NotFoundError('author_not_found', 'Автор не найден.')

        return author

    @staticmethod
    def _in_use_conflict() -> ConflictError:
        return ConflictError('author_in_use', 'Автор используется книгами. Сначала измените их авторов.')
