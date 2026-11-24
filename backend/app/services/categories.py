from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category
from app.repositories.categories import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import Page, PageInput


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CategoryRepository(db)

    def list(self, pagination: PageInput) -> Page[CategoryRead]:
        offset = (pagination.page - 1) * pagination.page_size
        categories = self.repository.list(limit=pagination.page_size, offset=offset)

        return Page[CategoryRead](
            items=[CategoryRead.model_validate(category) for category in categories],
            total=self.repository.count(),
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get(self, category_id: int) -> CategoryRead:
        return CategoryRead.model_validate(self._require_category(category_id))

    def create(self, data: CategoryCreate) -> CategoryRead:
        try:
            with self.db.begin():
                if self.repository.get_by_name(data.name) is not None:
                    raise self._name_conflict()

                category = self.repository.add(data.name)
                result = CategoryRead.model_validate(category)

            return result
        except IntegrityError as error:
            if error.orig.args[0] == 1062:
                raise self._name_conflict() from None

            raise

    def update(self, category_id: int, data: CategoryUpdate) -> CategoryRead:
        try:
            with self.db.begin():
                category = self._require_category(category_id, for_update=True)
                changes = data.model_dump(exclude_unset=True)

                if 'name' in changes:
                    existing = self.repository.get_by_name(changes['name'])

                    if existing is not None and existing.id != category.id:
                        raise self._name_conflict()

                    category.name = changes['name']

                    self.db.flush()

                result = CategoryRead.model_validate(category)

            return result
        except IntegrityError as error:
            if error.orig.args[0] == 1062:
                raise self._name_conflict() from None

            raise

    def delete(self, category_id: int) -> None:
        try:
            with self.db.begin():
                self._require_category(category_id, for_update=True)

                if self.repository.is_used(category_id):
                    raise self._in_use_conflict()

                self.repository.delete(category_id)
        except IntegrityError as error:
            if error.orig.args[0] == 1451:
                raise self._in_use_conflict() from None

            raise

    def _require_category(self, category_id: int, *, for_update: bool = False) -> Category:
        category = self.repository.get_by_id(category_id, for_update=for_update)

        if category is None:
            raise NotFoundError('category_not_found', 'Категория не найдена.')

        return category

    @staticmethod
    def _name_conflict() -> ConflictError:
        return ConflictError('category_name_conflict', 'Категория с таким названием уже существует.')

    @staticmethod
    def _in_use_conflict() -> ConflictError:
        return ConflictError('category_in_use', 'Категория используется книгами. Сначала измените их категории.')
