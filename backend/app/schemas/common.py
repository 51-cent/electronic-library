from datetime import UTC
from typing import Annotated, ClassVar, Generic, Self, TypeVar

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator


PositiveId = Annotated[int, Field(gt=0)]
Year = Annotated[int, Field(ge=1, le=9999)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
UtcDatetime = Annotated[AwareDatetime, AfterValidator(lambda value: value.astimezone(UTC))]


class InputSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UpdateSchema(InputSchema):
    non_nullable_fields: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode='after')
    def reject_null_for_required_fields(self) -> Self:
        for name in self.non_nullable_fields:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f'Поле {name} не может быть null.')
        return self


Item = TypeVar('Item')


class Page(ReadSchema, Generic[Item]):
    items: list[Item]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
