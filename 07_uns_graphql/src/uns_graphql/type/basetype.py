import json
from enum import Enum
from typing import Union

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class JSONPayload:
    """
    Represents an dict and/or a JSON String
    """

    data: JSON

    def __init__(self, data: Union[str, dict]):
        if type(data) is str:
            json.loads(data)
            # if it is already a JSON string then assign
            self.data = data
        else:
            # else convert dict to JSON
            self.data = json.dumps(data)


@strawberry.type
class BytesPayload:
    """
    Represents Bytes data encoded as base64. decode to get raw bytes
    """

    data: strawberry.scalars.Base64


@strawberry.type(description="Same as String. Needed because GraphQL does not support str for unions")
class StateString:
    """
    # This is needed because GraphQL does not support str for unions
    # use only in unions and not as a data field
    """

    data: str


# This is needed because GraphQL does not support int64
Int64 = strawberry.scalar(
    cls=Union[int, str],
    description="Int 64 field since GraphQL doesn't support int64, only int 32",
    serialize=lambda v: int(v),
    parse_value=lambda v: str(v),
)


@strawberry.enum
class BinaryOperator(Enum):
    # input binary operators in queries
    OR = "OR"
    AND = "AND"
    NOT = "NOT"
