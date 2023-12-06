from typing import List
from unittest.mock import MagicMock, patch

import pytest
from uns_graphql.input.kafka_subscription import KAFKATopic, KAFKATopicInput
from uns_graphql.subscriptions import Subscription
from uns_graphql.type.streaming_event import StreamingMessage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics, message_vals",
    [
        (["a.b.c", "abc"], [b'{"timestamp": 123456, "val1": 1234}']),
        (
            ["a.b.c"],
            [
                b'{"timestamp": 123456, "val1": 1234}',
                b'{"timestamp": 123457, "val1": 5678}',
                b'{"timestamp": 123458, "val1": 9012}',
            ],
        ),
        (["a.b.c"], b'{"timestamp": 123456, "val1": 1234}'),
    ],
)
async def test_get_kafka_messages(topics: List[str], message_vals: List[bytes] | bytes):
    # create the input for the subscription
    input_topics: List[KAFKATopicInput] = [KAFKATopicInput.from_pydantic(instance=KAFKATopic(topic=x)) for x in topics]

    # pick a topic to associate the message with in the mock
    output_topic = topics[0]
    mock_messages: List[MagicMock] = []
    if isinstance(message_vals, List):
        for msg_val in message_vals:
            mock_message = MagicMock()
            mock_message.value.return_value = msg_val
            mock_message.error.return_value = False
            mock_message.topic.return_value = output_topic
            mock_messages.append(mock_message)

    else:
        mock_message = MagicMock()
        mock_message.value.return_value = message_vals
        mock_message.error.return_value = False
        mock_message.topic.return_value = output_topic
        mock_messages.append(mock_message)

    # Mock the Kafka consumer
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = mock_messages  # loop through the messages
    mock_consumer.subscribe.return_value = True
    mock_consumer.connect.return_value = True

    with patch("uns_graphql.subscriptions.Consumer", return_value=mock_consumer):
        subscription = Subscription()
        async for message in subscription.get_kafka_messages(input_topics):
            assert isinstance(message, StreamingMessage)
            break  # Break the loop after the first iteration
