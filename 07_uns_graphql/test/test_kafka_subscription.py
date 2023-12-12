import asyncio
from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
from uns_graphql.graphql_config import KAFKAConfig
from uns_graphql.input.kafka_subscription import KAFKATopicInput
from uns_graphql.subscriptions import Subscription
from uns_graphql.type.streaming_event import StreamingMessage

TWO_TOPICS_MULTIPLE_MSGS = (
    [KAFKATopicInput(topic="a.b.c"), KAFKATopicInput(topic="abc")],
    [
        ("a.b.c", b'{"timestamp": 123456, "val1": 1234}'),
        ("a.b.c", b'{"timestamp": 234567, "val1": 2345}'),
        ("abc", b'{"timestamp": 123987, "val1": 9876}'),
        ("abc", b'{"timestamp": 456789, "val2": "test different"}'),
    ],
)

ONE_TOPIC_MULTIPLE_MSGS = (
    [KAFKATopicInput(topic="l.m.n")],
    [
        ("l.m.n", b'{"timestamp": 123456, "val1": 1234}'),
        ("l.m.n", b'{"timestamp": 123457, "val1": 5678}'),
        ("l.m.n", b'{"timestamp": 123458, "val1": 9012}'),
    ],
)

ONE_TOPIC_ONE_MSG = ([KAFKATopicInput(topic="x.y.z")], [("x.y.z", b'{"timestamp": 123456, "val1": 1234}')])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics, message_vals",
    [
        TWO_TOPICS_MULTIPLE_MSGS,
        ONE_TOPIC_MULTIPLE_MSGS,
        ONE_TOPIC_ONE_MSG,
    ],
)
async def test_get_kafka_messages_mock(topics: list[KAFKATopicInput], message_vals: tuple):
    # create the input for the subscription

    # pick a topic to associate the message with in the mock
    mock_messages: list[MagicMock] = []
    for msg_val in message_vals:
        mock_message = MagicMock()
        mock_message.value.return_value = msg_val[1]
        mock_message.error.return_value = False
        mock_message.topic.return_value = msg_val[0]
        mock_messages.append(mock_message)

    # Mock the Kafka consumer
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = mock_messages  # loop through the messages
    mock_consumer.subscribe.return_value = True
    mock_consumer.connect.return_value = True

    with patch("uns_graphql.subscriptions.Consumer", return_value=mock_consumer):
        subscription = Subscription()
        received_messages = []
        try:
            index: int = 0
            async for message in subscription.get_kafka_messages(topics):
                assert isinstance(message, StreamingMessage)
                assert message == StreamingMessage(message_vals[index][0], message_vals[index][1])
                received_messages.append(message)
                index = index + 1
                if index == len(message_vals):
                    break
        except RuntimeError as ex:
            # That happens when the mock async generator exhausts its content
            assert str(ex) == "async generator raised StopIteration"
            pytest.warns(ex)
        assert index == len(message_vals), "Not all messages were processed"
        for topic, msg in message_vals:
            # order of messages may not be same hence check after all messages were provided
            assert any(
                StreamingMessage(topic=topic, payload=msg) == received_message for received_message in received_messages
            )


@pytest.mark.asyncio
@pytest.mark.integrationtest()
@pytest.mark.xdist_group(name="graphql_kafka")
@pytest.mark.parametrize(
    "kafka_topics, message_vals",
    [
        TWO_TOPICS_MULTIPLE_MSGS,
        ONE_TOPIC_MULTIPLE_MSGS,
        ONE_TOPIC_ONE_MSG,
    ],
)
async def test_get_kafka_messages_integration(kafka_topics: list[KAFKATopicInput], message_vals: list[tuple]):
    kafka_config = {
        "bootstrap.servers": KAFKAConfig.config_map["bootstrap.servers"],
    }

    # Create Kafka admins
    admin = AdminClient(kafka_config)
    try:
        # Delete topics if present
        existing_topics = admin.list_topics().topics  # Get a list of existing topics
        for topic in existing_topics:
            if topic in [msg_val[0] for msg_val in message_vals]:
                admin.delete_topics([topic])

        # Create Kafka producer inside a context manager to ensure proper cleanup
        async def produce_messages():
            # Create Kafka producer
            producer = Producer(kafka_config)

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
        subscription = Subscription()
        try:
            index: int = 0
            async for message in subscription.get_kafka_messages(kafka_topics):
                assert isinstance(message, StreamingMessage)
                received_messages.append(message)
                index = index + 1
                if index == len(message_vals):
                    break
        except RuntimeError:
            assert index == len(message_vals), "Not all messages were processed"

        # Validate that all published messages were received
        assert len(received_messages) == len(message_vals)
        for topic, msg in message_vals:
            # order of messages may not be same hence check after all messages were provided
            assert any(
                StreamingMessage(topic=topic, payload=msg) == received_message for received_message in received_messages
            )
    finally:
        # Delete topics after the tests
        admin.delete_topics([msg_val[0] for msg_val in message_vals])
