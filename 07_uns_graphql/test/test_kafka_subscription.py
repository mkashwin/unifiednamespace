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
    ],
)
async def test_get_kafka_messages(topics: List[str] | str, message_vals: List[bytes] | bytes):
    input_topics = get_kafka_inputs(topics)

    if isinstance(topics, List):
        topic = topics[0]
    else:
        topic = topics

    if isinstance(message_vals, List):
        # mock_messages = [MagicMock(value=x, error=None, topic=topic) for x in message_vals]
        mock_messages: List[MagicMock] = []
        for msg_val in message_vals:
            mock_message = MagicMock()
            mock_message.value.return_value = msg_val
            mock_message.error.return_value = False
            mock_message.topic.return_value = topic
            mock_messages.append(mock_message)

    else:
        mock_messages = MagicMock(value=message_vals, error=None, topic=topic)

    mock_consumer = MagicMock()

    mock_consumer.poll.side_effect = mock_messages  # loop through the messages
    mock_consumer.subscribe.return_value = True
    mock_consumer.connect.return_value = True

    with patch("uns_graphql.subscriptions.Consumer", return_value=mock_consumer):
        subscription = Subscription()
        async for message in subscription.get_kafka_messages(input_topics):
            assert isinstance(message, StreamingMessage)
            break  # Break the loop after the first iteration


def get_kafka_inputs(topics: List[str] | str) -> List[KAFKATopicInput]:
    """
    convert string array to KAFKATopicInput array
    """
    if isinstance(topics, str):
        return KAFKATopicInput.from_pydantic(instance=KAFKATopic(topics))
    return [KAFKATopicInput.from_pydantic(instance=KAFKATopic(topic=x)) for x in topics]
