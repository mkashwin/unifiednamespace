import strawberry
from strawberry.scalars import JSON


@strawberry.type
class JSONPayload:
    data: JSON


@strawberry.type
class BytesPayload:
    data: strawberry.scalars.Base64
