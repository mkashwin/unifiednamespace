import pytest
from uns_graphql.type.basetype import JSONPayload
from uns_graphql.type.historical_event import HistoricalUNSEvent


@pytest.fixture
def sample_historical_event():
    return HistoricalUNSEvent(
        published_by="Publisher", timestamp=1234567890, topic="sample/topic", payload=JSONPayload(data={"key": "value"})
    )


def test_historical_event_instance(sample_historical_event):
    assert isinstance(sample_historical_event, HistoricalUNSEvent)


def test_historical_event_published_by(sample_historical_event):
    assert sample_historical_event.published_by == "Publisher"


def test_historical_event_timestamp(sample_historical_event):
    assert sample_historical_event.timestamp == 1234567890


def test_historical_event_topic(sample_historical_event):
    assert sample_historical_event.topic == "sample/topic"


def test_historical_event_payload(sample_historical_event):
    assert isinstance(sample_historical_event.payload, JSONPayload)
    assert sample_historical_event.payload.data == {"key": "value"}


# data validations not implemented on types returning data from back end
# def test_historical_event_invalid_payload():
#     with pytest.raises(TypeError):
#         HistoricalUNSEvent(
#             published_by="Publisher",
#             timestamp=1234567890,
#             topic="sample/topic",
#             payload={"invalid": "payload"},  # Providing an invalid payload
#         )
