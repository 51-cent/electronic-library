from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.deps import DatabaseSession, require_catalog_write_access
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import ErrorResponse, Page, PageInput
from app.services.categories import CategoryService

router = APIRouter(prefix='/categories', tags=['Категории'])
write_access = [Depends(require_catalog_write_access)]
CategoryId = Annotated[int, Path(gt=0, description='Идентификатор категории')]


def get_category_service(db: DatabaseSession) -> CategoryService:
    return CategoryService(db)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


@router.get('', response_model=Page[CategoryRead], summary='Получить категории с пагинацией')
def list_categories(
    service: CategoryServiceDep,
    pagination: Annotated[PageInput, Query()],
) -> Page[CategoryRead]:
    return service.list(pagination)


@router.get(
    '/{category_id}',
    response_model=CategoryRead,
    summary='Получить категорию',
    responses={404: {'model': ErrorResponse, 'description': 'Категория не найдена'}},
)
def get_category(category_id: CategoryId, service: CategoryServiceDep) -> CategoryRead:
    return service.get(category_id)


@router.post(
    '', response_model=CategoryRead,
    status_code=201,
    dependencies=write_access,
    summary='Создать категорию',
    responses={403: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def create_category(data: CategoryCreate, service: CategoryServiceDep) -> CategoryRead:
    return service.create(data)


@router.patch(
    '/{category_id}',
    response_model=CategoryRead,
    dependencies=write_access,
    summary='Изменить категорию',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def update_category(
    category_id: CategoryId, data: CategoryUpdate, service: CategoryServiceDep,
) -> CategoryRead:
    return service.update(category_id, data)


@router.delete(
    '/{category_id}',
    status_code=204,
    response_class=Response,
    dependencies=write_access,
    summary='Удалить неиспользуемую категорию',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def delete_category(category_id: CategoryId, service: CategoryServiceDep) -> Response:
    service.delete(category_id)

    return Response(status_code=204)
