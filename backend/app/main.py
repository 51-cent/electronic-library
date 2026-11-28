from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import ApplicationError
from app.db.session import get_engine


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    yield
    get_engine().dispose()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API электронной библиотеки",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ApplicationError)
def application_error_handler(_request: Request, error: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={'detail': {'code': error.code, 'message': error.message}},
        headers={'Cache-Control': 'no-store', **getattr(error, 'headers', {})},
    )


@app.exception_handler(RequestValidationError)
def request_validation_error_handler(_request: Request, error: RequestValidationError) -> JSONResponse:
    details = [{key: item[key] for key in ('type', 'loc', 'msg')} for item in error.errors()]
    return JSONResponse(status_code=422, content={'detail': details}, headers={'Cache-Control': 'no-store'})
