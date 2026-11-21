from app.schemas.common import InputSchema, Name, PositiveId, ReadSchema, UpdateSchema


class CategoryCreate(InputSchema):
    name: Name


class CategoryUpdate(UpdateSchema):
    non_nullable_fields = ('name',)

    name: Name | None = None


class CategoryRead(ReadSchema):
    id: PositiveId
    name: str
