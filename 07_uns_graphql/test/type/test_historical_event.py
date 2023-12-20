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
