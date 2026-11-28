from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.common import ErrorResponse, Page, PageInput
from app.schemas.user_book import LibraryQuery, UserBookRead, UserBookUpdate
from app.services.library import LibraryService


def disable_caching(response: Response) -> None:
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(
    prefix='/me',
    tags=['Личная библиотека'],
    dependencies=[Depends(disable_caching)],
    responses={401: {'model': ErrorResponse}}
)
BookId = Annotated[int, Path(gt=0, description='Идентификатор книги')]


def get_library_service(db: DatabaseSession) -> LibraryService:
    return LibraryService(db)


LibraryServiceDep = Annotated[LibraryService, Depends(get_library_service)]


@router.get(
    path='/library',
    response_model=Page[UserBookRead],
    summary='Личная библиотека с фильтрами',
    description='Статус чтения и избранное фильтруются совместно. Архивные книги остаются в истории.'
)
def list_library(
        principal: CurrentUser, service: LibraryServiceDep, filters: Annotated[LibraryQuery, Query()]
) -> Page[UserBookRead]:
    return service.list(principal.user.id, filters)


@router.get(path='/favorites', response_model=Page[UserBookRead], summary='Избранное с пагинацией')
def list_favorites(
        principal: CurrentUser, service: LibraryServiceDep, pagination: Annotated[PageInput, Query()],
) -> Page[UserBookRead]:
    return service.list_favorites(principal.user.id, pagination)


@router.put(
    path='/favorites/{book_id}',
    response_model=UserBookRead,
    summary='Добавить в избранное',
    description='Первое добавление создаёт статус planned. Повторное не меняет статус и даты.',
    responses={201: {'model': UserBookRead, 'description': 'Создана запись библиотеки'}, 404: {'model': ErrorResponse}}
)
def add_favorite(
        book_id: BookId, principal: CurrentUser, service: LibraryServiceDep, response: Response
) -> UserBookRead:
    result = service.add_favorite(principal.user.id, book_id)
    response.status_code = 201 if result.created else 200

    return result.entry


@router.delete(
    path='/favorites/{book_id}',
    status_code=204,
    summary='Убрать из избранного, сохранив историю',
    description='Повторное снятие допустимо. Архивную книгу можно убрать из своего избранного.',
    responses={404: {'model': ErrorResponse}}
)
def remove_favorite(book_id: BookId, principal: CurrentUser, service: LibraryServiceDep) -> None:
    service.remove_favorite(principal.user.id, book_id)


@router.put(
    path='/library/{book_id}',
    response_model=UserBookRead,
    summary='Установить статус чтения',
    description='При переходе в finished дата задаётся сервером; повтор сохраняет её, выход очищает.',
    responses={201: {'model': UserBookRead, 'description': 'Создана запись библиотеки'}, 404: {'model': ErrorResponse}}
)
def set_reading_status(
        book_id: BookId, data: UserBookUpdate, principal: CurrentUser, service: LibraryServiceDep, response: Response
) -> UserBookRead:
    result = service.set_status(principal.user.id, book_id, data)
    response.status_code = 201 if result.created else 200

    return result.entry
