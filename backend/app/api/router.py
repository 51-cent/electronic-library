from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.authors import router as authors_router
from app.api.routes.books import router as books_router
from app.api.routes.health import router as health_router
from app.api.routes.library import router as library_router
from app.api.routes.categories import router as categories_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(library_router)
api_router.include_router(categories_router)
api_router.include_router(authors_router)
api_router.include_router(books_router)
