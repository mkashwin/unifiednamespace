import asyncio
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from uns_graphql.graphql_config import KAFKAConfig
from uns_graphql.input.kafka_subscription import KAFKATopicInput
from uns_graphql.subscriptions import Subscription
from uns_graphql.type.streaming_event import StreamingMessage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics, message_vals",
    [
        (
            [KAFKATopicInput(topic="a.b.c"), KAFKATopicInput(topic="abc")],
            [("a.b.c", b'{"timestamp": 123456, "val1": 1234}')],
        ),
        (
            [KAFKATopicInput(topic="a.b.c")],
            [
                ("a.b.c", b'{"timestamp": 123456, "val1": 1234}'),
                ("a.b.c", b'{"timestamp": 123457, "val1": 5678}'),
                ("a.b.c", b'{"timestamp": 123458, "val1": 9012}'),
            ],
        ),
        ([KAFKATopicInput(topic="x.y.z")], ("x.y.z", b'{"timestamp": 123456, "val1": 1234}')),
    ],
)
async def test_get_kafka_messages(topics: List[KAFKATopicInput], message_vals: tuple):
    # create the input for the subscription

    # pick a topic to associate the message with in the mock
    mock_messages: List[MagicMock] = []
    if isinstance(message_vals, List):
        for msg_val in message_vals:
            mock_message = MagicMock()
            mock_message.value.return_value = msg_val[1]
            mock_message.error.return_value = False
            mock_message.topic.return_value = msg_val[0]
            mock_messages.append(mock_message)

    else:
        mock_message = MagicMock()
        mock_message.value.return_value = message_vals[1]
        mock_message.error.return_value = False
        mock_message.topic.return_value = message_vals[0]
        mock_messages.append(mock_message)
        # convert to a list for simpler checks later on
        message_vals = [message_vals]

    # Mock the Kafka consumer
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = mock_messages  # loop through the messages
    mock_consumer.subscribe.return_value = True
    mock_consumer.connect.return_value = True

    with patch("uns_graphql.subscriptions.Consumer", return_value=mock_consumer):
        subscription = Subscription()
        try:
            index: int = 0
            async for message in subscription.get_kafka_messages(topics):
                assert isinstance(message, StreamingMessage)
                assert message == StreamingMessage(message_vals[index][0], message_vals[index][1])
                index = index + 1
        except RuntimeError as ex:
            # That happens when the mock async generator exhausts its content
            assert str(ex) == "async generator raised StopIteration"
        assert index == len(message_vals), "Not all messages were processed"


@pytest.mark.asyncio
@pytest.mark.integrationtest()
@pytest.mark.parametrize(
    "kafka_topics, message_vals",
    [
        (
            [KAFKATopicInput(topic="a.b.c"), KAFKATopicInput(topic="abc")],
            [("a.b.c", b'{"timestamp": 123456, "val1": 1234}')],
        ),
        (
            [KAFKATopicInput(topic="a.b.c")],
            [
                ("a.b.c", b'{"timestamp": 123456, "val1": 1234}'),
                ("a.b.c", b'{"timestamp": 123457, "val1": 5678}'),
                ("a.b.c", b'{"timestamp": 123458, "val1": 9012}'),
            ],
        ),
        ([KAFKATopicInput(topic="x.y.z")], [("x.y.z", b'{"timestamp": 123456, "val1": 1234}')]),
    ],
)
async def test_get_kafka_messages_integration(kafka_topics: List[KAFKATopicInput], message_vals: List[tuple]):
    async def produce_messages():
        # Kafka producer configuration
        producer_config = {
            "bootstrap.servers": KAFKAConfig.config_map["bootstrap.servers"],
        }

        # Create Kafka producer
        producer = Producer(producer_config)

        def delivery_report(err, msg):  # noqa: ARG001
            pass

        # Produce messages
        for topic, msg in message_vals:
            producer.produce(topic, value=msg, callback=delivery_report)

        producer.flush()

    # Run message producer in a separate thread
    await asyncio.gather(produce_messages())

    # Retrieve messages from the subscription
    received_messages = []
    async for message in Subscription().get_kafka_messages(kafka_topics):
        received_messages.append(message)
        if len(received_messages) == len(sum(message_vals, ())):
            break  # Exit the loop once all messages are received

    # Validate that all published messages were received
    assert len(received_messages) == len(sum(message_vals, ()))
    for topic, msg in message_vals:
        assert any(StreamingMessage(topic=topic, payload=msg) == received_message for received_message in received_messages)
