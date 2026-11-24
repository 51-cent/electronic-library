from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BeforeValidator, Field, HttpUrl, StringConstraints, TypeAdapter, model_validator

from app.enum.book import Status
from app.schemas.author import AuthorRead
from app.schemas.category import CategoryRead
from app.schemas.common import InputSchema, PageInput, PositiveId, ReadSchema, UpdateSchema, UtcDatetime, Year


def normalize_isbn(value: object) -> object:
    if not isinstance(value, str):
        return value

    return value.replace('-', '').replace(' ', '')


def validate_isbn(value: str) -> str:
    checksum = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(value))
    if checksum % 10 or not value.startswith(('978', '979')):
        raise ValueError('Некорректный ISBN-13.')

    return value


def validate_cover_url(value: str) -> str:
    TypeAdapter(HttpUrl).validate_python(value)

    return value


def unique_ids(value: list[int]) -> list[int]:
    if len(set(value)) != len(value):
        raise ValueError('Идентификаторы не должны повторяться.')

    return value


ISBN = Annotated[
    str,
    BeforeValidator(normalize_isbn),
    StringConstraints(pattern=r'^[0-9]{13}$'),
    AfterValidator(validate_isbn)
]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
CoverUrl = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048), AfterValidator(validate_cover_url)]
RelatedIds = Annotated[list[PositiveId], Field(min_length=1), AfterValidator(unique_ids)]
SearchText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]


class BookQuery(PageInput):
    q: SearchText | None = Field(default=None, description='Подстрока названия книги, имени автора или категории.')
    author_id: PositiveId | None = None
    category_id: PositiveId | None = None
    year_from: Year | None = Field(default=None, description='Год издания: включительная нижняя граница.')
    year_to: Year | None = Field(default=None, description='Год издания: включительная верхняя граница.')
    created_from: UtcDatetime | None = Field(
        default=None, description='Добавлена не раньше этой даты; граница включена, часовой пояс обязателен.',
    )
    created_to: UtcDatetime | None = Field(
        default=None, description='Добавлена раньше этой даты; граница исключена, часовой пояс обязателен.',
    )
    sort_by: Literal['title', 'publication_year', 'created_at', 'rating'] = Field(
        default='created_at', description='Поле сортировки. Неизвестный год и отсутствие рейтинга идут в конце.',
    )
    sort_order: Literal['asc', 'desc'] = Field(default='desc', description='Направление сортировки.')

    @model_validator(mode='after')
    def validate_ranges(self) -> Self:
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError('year_from не может быть больше year_to.')

        if self.created_from is not None and self.created_to is not None and self.created_from >= self.created_to:
            raise ValueError('created_from должен быть раньше created_to.')

        return self


class BookCreate(InputSchema):
    title: Title
    description: Description
    isbn: ISBN | None = None
    publication_year: Year | None = None
    status: Status = Status.active
    cover_url: CoverUrl | None = None
    author_ids: RelatedIds
    category_ids: RelatedIds


class BookUpdate(UpdateSchema):
    non_nullable_fields = ('title', 'description', 'status', 'author_ids', 'category_ids')

    title: Title | None = None
    description: Description | None = None
    isbn: ISBN | None = None
    publication_year: Year | None = None
    status: Status | None = None
    cover_url: CoverUrl | None = None
    author_ids: RelatedIds | None = None
    category_ids: RelatedIds | None = None


class BookSummary(ReadSchema):
    id: PositiveId
    title: str
    cover_url: str | None
    is_archived: bool
    has_content: bool


class BookRead(BookSummary):
    description: str
    isbn: str | None
    publication_year: int | None
    status: Status
    authors: list[AuthorRead]
    categories: list[CategoryRead]
    created_at: UtcDatetime
    updated_at: UtcDatetime
    deleted_at: UtcDatetime | None


class BookDetail(BookRead):
    average_rating: float | None = Field(ge=1, le=5)
    ratings_count: int = Field(ge=0)
