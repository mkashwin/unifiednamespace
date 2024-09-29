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

"""

import base64
import json

import pytest
import strawberry

from uns_graphql.type.basetype import BytesPayload, Int64, JSONPayload


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        ('{"key": "value"}', {"key": "value"}),  # valid JSON
        ({"key": "value"}, {"key": "value"}),  # dict
        (None, None),  # dict
        ("invalid_json", json.JSONDecodeError),  # Invalid JSON string
    ],
)
def test_json_payload(input_data, expected_output):
    if isinstance(expected_output, type) and issubclass(expected_output, Exception):
        # Handling cases where an exception is expected
        with pytest.raises(expected_output):
            JSONPayload(data=input_data)
    else:
        # Test cases where initialization should succeed
        payload = JSONPayload(data=input_data)
        assert json.loads(payload.data) == expected_output

        @strawberry.type
        class Query:
            payload: JSONPayload

        query = "{ payload { data} }"
        schema = strawberry.Schema(query=Query)
        result = schema.execute_sync(query, root_value=Query(payload=payload))
        assert not result.errors
        assert result.data.get("payload").get("data") == json.dumps(expected_output)


@pytest.mark.parametrize(
    "input_data",
    [
        # Test cases for valid Base64 encoded strings
        (b"hello"),
        (b"test123"),
    ],
)
def test_bytes_payload(input_data):
    @strawberry.type
    class Query:
        payload: BytesPayload

    query = "{ payload { data} }"
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, root_value=Query(payload=BytesPayload(data=input_data)))
    assert not result.errors
    assert result.data.get("payload").get("data") == base64.b64encode(input_data).decode()


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        ("9223372036854775800", 9223372036854775800),  # int 64
        (9235245, 9235245),  # int 32
    ],
)
def test_int64_type(input_data, expected_output):
    @strawberry.type
    class Query:
        value: Int64  # type: ignore

    query = "{ value }"
    schema = strawberry.Schema(query=Query)
    # schema = strawberry.Schema(query=Query,scalar_overrides={int: Int64})
    result = schema.execute_sync(query, root_value=Query(value=input_data))

    assert not result.errors
    assert result.data == {"value": expected_output}
