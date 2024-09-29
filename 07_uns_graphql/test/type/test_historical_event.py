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

from datetime import UTC, datetime

import pytest
import strawberry

from uns_graphql.type.basetype import JSONPayload
from uns_graphql.type.historical_event import HistoricalUNSEvent


@pytest.fixture
def sample_historical_event():
    return HistoricalUNSEvent(
        publisher="Publisher",
        timestamp=datetime.fromtimestamp(1234567890, UTC),
        topic="sample/topic",
        payload=JSONPayload(data={"key": "value"}),
    )


def test_historical_event_instance(sample_historical_event):
    assert isinstance(sample_historical_event, HistoricalUNSEvent)


def test_historical_event_published_by(sample_historical_event):
    assert sample_historical_event.publisher == "Publisher"


def test_historical_event_timestamp(sample_historical_event):
    assert sample_historical_event.timestamp == datetime.fromtimestamp(1234567890, UTC)


def test_historical_event_topic(sample_historical_event):
    assert sample_historical_event.topic == "sample/topic"


def test_historical_event_payload(sample_historical_event):
    assert isinstance(sample_historical_event.payload, JSONPayload)
    assert sample_historical_event.payload.data == '{"key": "value"}'


def test_strawberry_type(sample_historical_event):
    @strawberry.type
    class Query:
        value: HistoricalUNSEvent

    query = """
    {
        value {
            publisher,
            timestamp,
            topic,
            payload { data }
        }
    }"""
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, root_value=Query(value=sample_historical_event))
    assert not result.errors
