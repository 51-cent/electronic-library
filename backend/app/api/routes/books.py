from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.deps import DatabaseSession, require_catalog_write_access
from app.schemas.book import BookCreate, BookDetail, BookQuery, BookRead, BookUpdate
from app.schemas.common import ErrorResponse, Page
from app.services.books import BookService

router = APIRouter(prefix='/books', tags=['Книги'])
write_access = [Depends(require_catalog_write_access)]
BookId = Annotated[int, Path(gt=0, description='Идентификатор книги')]


def get_book_service(db: DatabaseSession) -> BookService:
    return BookService(db)


BookServiceDep = Annotated[BookService, Depends(get_book_service)]


@router.get(
    path='',
    response_model=Page[BookDetail],
    summary='Каталог: поиск, фильтры, сортировка и пагинация',
    description=(
        'Архивные книги исключаются. q ищет подстроку в названии книги, имени автора и названии категории. '
        'Все переданные фильтры применяются совместно. Даты должны содержать часовой пояс: '
        'created_from включается, created_to исключается. При равенстве значений сортировка идёт по id.'
    ),
)
def list_books(service: BookServiceDep, filters: Annotated[BookQuery, Query()]) -> Page[BookDetail]:
    return service.list(filters)


@router.get(
    path='/{book_id}',
    response_model=BookDetail,
    summary='Карточка книги с рейтингом',
    responses={404: {'model': ErrorResponse}},
)
def get_book(book_id: BookId, service: BookServiceDep) -> BookDetail:
    return service.get(book_id)


@router.post(
    path='',
    response_model=BookRead,
    status_code=201,
    dependencies=write_access,
    summary='Создать книгу с авторами и категориями',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def create_book(data: BookCreate, service: BookServiceDep) -> BookRead:
    return service.create(data)


@router.patch(
    path='/{book_id}',
    response_model=BookRead,
    dependencies=write_access,
    summary='Изменить метаданные и связи книги',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
)
def update_book(book_id: BookId, data: BookUpdate, service: BookServiceDep) -> BookRead:
    return service.update(book_id, data)


@router.delete(
    path='/{book_id}',
    status_code=204,
    response_class=Response,
    dependencies=write_access,
    summary='Архивировать книгу',
    responses={403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}},
)
def delete_book(book_id: BookId, service: BookServiceDep) -> Response:
    service.delete(book_id)

    return Response(status_code=204)
