from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import payload_type

import pytest
from aiomqtt import Message
from uns_graphql.input.mqtt_subscription import MQTTTopicInput
from uns_graphql.subscriptions import Subscription
from uns_graphql.type.mqtt_event import MQTTMessage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics, messages",
    [
        (  # Test multiple topics
            [MQTTTopicInput(topic="topic_1"), MQTTTopicInput(topic="topic_2")],
            [("topic_1", b'{"timestamp": 123456, "val1": 1234}'), ("topic_2", b'{"timestamp": 123457, "val1": 5678}')],
        ),
        (  # Test wild cards
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                ("topic/1", b'{"timestamp": 123456, "val1": 1234}'),
                ("topic/2", b"payload_1"),
                ("topic/2/3", b'{"timestamp": 123457, "val1": 5678}'),
            ],
        ),
        (  # Test multiple messages to the same topic
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                ("topic/1", b'{"timestamp": 123456, "val1": 1234}'),
                ("topic/1", b'{"timestamp": 2345678, "val1": 4567}'),
                ("topic/2/3", b'{"timestamp": 123457, "val1": 5678}'),
            ],
        ),
        # Add more test cases as needed
    ],
)
async def test_get_mqtt_messages(topics: List[MQTTTopicInput], messages: List[tuple[str, bytes]]):
    # Mock the Client context manager and its return values
    # Create an instance of AsyncContextManagerMock to act as an async context manager
    # Mock necessary components from aiomqtt
    mock_client = MagicMock()
    mock_client.subscribe = AsyncMock()
    async_context_manager = AsyncContextManagerMock(mock_client)

    # Patch Client and mock the messages context manager
    with patch("uns_graphql.subscriptions.Client", return_value=async_context_manager), patch(
        "uns_graphql.subscriptions.MQTTMessage", autospec=True
    ):
        subscription = Subscription()
        received_messages: List[MQTTMessage] = []

        # Mock the client.messages context manager to return an async generator
        mock_messages = MagicMock()
        mock_messages.__aenter__.return_value = async_message_generator(messages)
        mock_client.messages.return_value = mock_messages

        # Await the subscription result directly to collect the messages
        async for message in subscription.get_mqtt_messages(topics):
            received_messages.append(message)  # noqa: PERF402

    assert len(received_messages) == len(messages)


class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc, tb):
        pass


# Function to create an async generator from the provided messages
async def async_message_generator(messages):
    for msg in messages:
        mqtt_msg = Message(topic=msg[0], payload=msg[1], qos=1, retain=False, mid=1, properties=None)
        yield mqtt_msg
