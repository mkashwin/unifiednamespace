from typing import Union

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class JSONPayload:
    data: JSON


@strawberry.type
class BytesPayload:
    data: strawberry.scalars.Base64


# This is needed because GraphQL does not support int64
Int64 = strawberry.scalar(
    Union[int, str],  # type: ignore
    description="Int 64 field since GraphQL doesn't support int64, only int 32",
    serialize=lambda v: int(v),
    parse_value=lambda v: str(v),
)
