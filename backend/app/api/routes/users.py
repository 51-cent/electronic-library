from fastapi import APIRouter, Response

from app.api.deps import CurrentUser
from app.schemas.common import ErrorResponse
from app.schemas.user import UserRead

router = APIRouter(tags=['Пользователь'])


@router.get(path='/me', response_model=UserRead, summary='Личный профиль', responses={401: {'model': ErrorResponse}})
def read_me(principal: CurrentUser, response: Response) -> UserRead:
    response.headers['Cache-Control'] = 'no-store'

    return principal.user
