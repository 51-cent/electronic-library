from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.deps import DatabaseSession, require_catalog_write_access
from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.common import ErrorResponse, Page, PageInput
from app.services.authors import AuthorService

router = APIRouter(prefix='/authors', tags=['Авторы'])
write_access = [Depends(require_catalog_write_access)]
AuthorId = Annotated[int, Path(gt=0, description='Идентификатор автора')]


def get_author_service(db: DatabaseSession) -> AuthorService:
    return AuthorService(db)


AuthorServiceDep = Annotated[AuthorService, Depends(get_author_service)]


@router.get('', response_model=Page[AuthorRead], summary='Получить авторов с пагинацией')
def list_authors(service: AuthorServiceDep, pagination: Annotated[PageInput, Query()]) -> Page[AuthorRead]:
    return service.list(pagination)


@router.get(
    path='/{author_id}',
    response_model=AuthorRead,
    summary='Получить автора',
    responses={404: {'model': ErrorResponse}},
)
def get_author(author_id: AuthorId, service: AuthorServiceDep) -> AuthorRead:
    return service.get(author_id)


@router.post(
    path='',
    response_model=AuthorRead,
    status_code=201,
    dependencies=write_access,
    summary='Создать автора',
    responses={403: {'model': ErrorResponse}},
)
def create_author(data: AuthorCreate, service: AuthorServiceDep) -> AuthorRead:
    return service.create(data)


@router.patch(
    path='/{author_id}',
    response_model=AuthorRead,
    dependencies=write_access,
    summary='Изменить автора',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}},
)
def update_author(author_id: AuthorId, data: AuthorUpdate, service: AuthorServiceDep) -> AuthorRead:
    return service.update(author_id, data)


@router.delete(
    path='/{author_id}',
    status_code=204,
    response_class=Response,
    dependencies=write_access,
    summary='Удалить неиспользуемого автора',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def delete_author(author_id: AuthorId, service: AuthorServiceDep) -> Response:
    service.delete(author_id)

    return Response(status_code=204)
