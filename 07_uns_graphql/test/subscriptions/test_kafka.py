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

from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
from uns_graphql.graphql_config import KAFKAConfig
from uns_graphql.input.kafka import KAFKATopicInput
from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.type.streaming_event import StreamingMessage

TWO_TOPICS_MULTIPLE_MSGS = (
    [KAFKATopicInput(topic="graphql_test_a.b.c"), KAFKATopicInput(topic="graphql_test_abc")],
    [
        ("graphql_test_a.b.c", b'{"timestamp": 123456, "val1": 1234}'),
        ("graphql_test_a.b.c", b'{"timestamp": 234567, "val1": 2345}'),
        ("graphql_test_abc", b'{"timestamp": 123987, "val1": 9876}'),
        ("graphql_test_abc", b'{"timestamp": 456789, "val2": "test different"}'),
    ],
)

ONE_TOPIC_MULTIPLE_MSGS = (
    [KAFKATopicInput(topic="graphql_test_l.m.n")],
    [
        ("graphql_test_l.m.n", b'{"timestamp": 123456, "val1": 1234}'),
        ("graphql_test_l.m.n", b'{"timestamp": 123457, "val1": 5678}'),
        ("graphql_test_l.m.n", b'{"timestamp": 123458, "val1": 9012}'),
    ],
)

ONE_TOPIC_ONE_MSG = (
    [KAFKATopicInput(topic="graphql_test_x.y.z")],
    [("graphql_test_x.y.z", b'{"timestamp": 123456, "val1": 1234}')],
)


@pytest_asyncio.fixture(scope="function")
async def create_topics(message_vals):
    kafka_config = {
        "bootstrap.servers": KAFKAConfig.config_map["bootstrap.servers"],
    }

    # Function to Delete topics if present
    async def delete_existing_topics():  # noqa: RUF029
        # Create Kafka admins
        admin = AdminClient(kafka_config)
        existing_topics = admin.list_topics().topics  # Get a list of existing topics
        for topic in existing_topics:
            if topic in [msg_val[0] for msg_val in message_vals]:
                admin.delete_topics([topic])

    # Function to Create Kafka producer inside a context manager to ensure proper cleanup
    async def produce_messages():  # noqa: RUF029
        # Create Kafka producer
        producer = Producer(kafka_config)

        def delivery_report(err, msg):  # noqa: ARG001
            pass

        # Produce messages
        for topic, msg in message_vals:
            producer.produce(topic, value=msg, callback=delivery_report)
            producer.flush()

    # Delete topics
    await delete_existing_topics()
    # Run message producer in a separate thread
    await produce_messages()
    yield
    # Delete topics
    await delete_existing_topics()


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

    with patch("uns_graphql.subscriptions.kafka.Consumer", return_value=mock_consumer):
        subscription = KAFKASubscription()
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
# FIXME not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# Comment this marker and run test individually in VSCode. Uncomment for running from command line / CI
@pytest.mark.xdist_group(name="graphql_kafka")
@pytest.mark.parametrize(
    "kafka_topics, message_vals",
    [
        TWO_TOPICS_MULTIPLE_MSGS,
        ONE_TOPIC_MULTIPLE_MSGS,
        ONE_TOPIC_ONE_MSG,
    ],
)
async def test_get_kafka_messages_integration(create_topics, kafka_topics: list[KAFKATopicInput], message_vals: list[tuple]):  # noqa: ARG001
    #    create_topics(message_vals)
    received_messages = []
    subscription = KAFKASubscription()
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
        assert any(StreamingMessage(topic=topic, payload=msg) == received_message for received_message in received_messages)
