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

import json

import pytest
import strawberry
from uns_graphql.type.basetype import BytesPayload, JSONPayload
from uns_graphql.type.mqtt_event import MQTTMessage

sample_spb_payload: bytes = (
    b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
    b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
    b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00"
)


@pytest.mark.parametrize(
    "topic, payload, expected_type, expected_data",
    [
        ("ent1/fac1/area5", b'{"key": "value"}', JSONPayload, {"key": "value"}),
        (
            "spBv1.0/STATE/scada_1",
            b'{ "online" : true,  "timestamp" : 1668114759262}',
            JSONPayload,
            {"online": True, "timestamp": 1668114759262},
        ),
        ("spBv1.0/uns_group/NBIRTH/eon1", sample_spb_payload, BytesPayload, sample_spb_payload),
        ("spBv1.0/uns_group/NDATA/eon1", sample_spb_payload, BytesPayload, sample_spb_payload),
    ],
)
def test_resolve_payload(
    topic: str,
    payload: JSONPayload | BytesPayload | str,
    expected_type: type[JSONPayload] | type[BytesPayload] | type[str],
    expected_data,
):
    mqtt_event = MQTTMessage(topic=topic, payload=payload)
    result = mqtt_event.resolve_payload(None)
    assert isinstance(result, expected_type)
    if isinstance(result, BytesPayload):
        assert result.data == expected_data
    else:
        assert json.loads(result.data) == expected_data


@pytest.mark.parametrize(
    "input_data",
    [
        MQTTMessage(topic="ent1/fac1/area5", payload=b'{"key": "value"}'),
        MQTTMessage(topic="spBv1.0/STATE/scada_1", payload=b'{ "online" : true,  "timestamp" : 1668114759262}'),
        MQTTMessage(topic="spBv1.0/uns_group/NBIRTH/eon1", payload=sample_spb_payload),
    ],
)
def test_strawberry_type(input_data: MQTTMessage):
    @strawberry.type
    class Query:
        value: MQTTMessage

    query = """
    {
        value {
            topic,
            payload {
                ... on JSONPayload {json: data}
                ... on BytesPayload {bytes: data}
            }
        }
    }"""
    schema = strawberry.Schema(query=Query, types=[JSONPayload, BytesPayload])
    result = schema.execute_sync(query, root_value=Query(value=input_data))
    assert not result.errors
