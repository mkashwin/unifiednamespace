"""*******************************************************************************
* Copyright (c) 2021 Ashwin Krishnan
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of MIT and  is provided "as is",
* without warranty of any kind, express or implied, including but
* not limited to the warranties of merchantability, fitness for a
* particular purpose and noninfringement. In no event shall the
* authors, contributors or copyright holders be liable for any claim,
* damages or other liability, whether in an action of contract,
* tort or otherwise, arising from, out of or in connection with the software
* or the use or other dealings in the software.
*
* Contributors:
*    -
*******************************************************************************

Common basetype needed across all graphQL queries and subscriptions to the UNS
"""

import json
from enum import Enum

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class JSONPayload:
    """
    Represents an dict and/or a JSON String
    """

    data: JSON

    def __init__(self, data: str | dict):
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


# This is needed because GraphQL does not support int64
Int64 = strawberry.scalar(
    name="Int64",
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
