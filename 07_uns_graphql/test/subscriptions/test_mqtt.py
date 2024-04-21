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

import random
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiomqtt import Client, Message, MqttError, ProtocolVersion
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_graphql.graphql_config import MQTTConfig
from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.subscriptions.mqtt import MQTTSubscription
from uns_graphql.type.mqtt_event import MQTTMessage

sample_spb_payload: bytes = (
    b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
    b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
    b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00"
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics, expected_messages",
    [
        (  # Test multiple topics
            [MQTTTopicInput(topic="topic_1"), MQTTTopicInput(topic="topic_2")],
            [
                Message(
                    topic="topic_1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=1,
                    properties=None,
                ),
                Message(
                    topic="topic_2",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=2,
                    properties=None,
                ),
            ],
        ),
        (  # Test wild cards
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=3,
                    properties=None,
                ),
                Message(
                    topic="topic/2",
                    payload=b'{"timestamp": 4567, "val1": "QWERTY"}',
                    qos=1,
                    retain=False,
                    mid=4,
                    properties=None,
                ),
                Message(
                    topic="topic/2/3",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=5,
                    properties=None,
                ),
            ],
        ),
        (  # Test multiple messages to the same topic
            [MQTTTopicInput(topic="topic/+")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=6,
                    properties=None,
                ),
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 2345678, "val1": 4567}',
                    qos=1,
                    retain=False,
                    mid=7,
                    properties=None,
                ),
                Message(
                    topic="topic/2/3",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=8,
                    properties=None,
                ),
            ],
        ),
        (  # Test with topics from  sparkplugB with protobuf responses
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=9,
                    properties=None,
                ),
                Message(
                    topic="spBv1.0/STATE/scada_1234",
                    payload=b'{ "online" : true,  "timestamp" : 1668114759262}',
                    qos=1,
                    retain=False,
                    mid=10,
                    properties=None,
                ),
                Message(
                    topic="spBv1.0/uns_group/NBIRTH/eon1",
                    payload=sample_spb_payload,
                    qos=1,
                    retain=False,
                    mid=11,
                    properties=None,
                ),
            ],
        ),
        # Add more test cases as needed
    ],
)
async def test_get_mqtt_messages(topics: list[MQTTTopicInput], expected_messages: list[Message]):
    # Mock the Client context manager and its return values
    # Create an instance of AsyncContextManagerMock to act as an async context manager
    # Mock necessary components from aiomqtt
    mock_client = MagicMock()
    mock_client.subscribe = AsyncMock()
    async_context_manager = AsyncContextManagerMock(mock_client)

    # Patch Client and mock the messages context manager
    with patch("uns_graphql.subscriptions.mqtt.Client", return_value=async_context_manager):
        # Mock the client.messages context manager to return an async generator
        mock_messages = async_message_generator(expected_messages)
        mock_client.messages = mock_messages

        subscription = MQTTSubscription()
        received_messages: list[MQTTMessage] = []
        # Await the subscription result directly to collect the messages
        async for message in subscription.get_mqtt_messages(topics):
            received_messages.append(message)  # noqa: PERF402

    assert len(received_messages) == len(expected_messages)


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
        yield msg


@pytest_asyncio.fixture(scope="function")
@pytest.mark.asyncio
@pytest.mark.integrationtest
async def publish_to_mqtt(expected_messages: list[Message]):
    client_id = f"test_graphql-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311
    publish_properties = None
    if MQTTConfig.version == ProtocolVersion.V5:
        publish_properties = Properties(PacketTypes.PUBLISH)

    client = Client(
        identifier=client_id,
        clean_session=MQTTConfig.clean_session,
        protocol=MQTTConfig.version,
        transport=MQTTConfig.transport,
        hostname=MQTTConfig.host,
        port=MQTTConfig.port,
        username=MQTTConfig.username,
        password=MQTTConfig.password,
        keepalive=MQTTConfig.keep_alive,
        tls_params=MQTTConfig.tls_params,
        tls_insecure=MQTTConfig.tls_insecure,
    )
    try:
        async with client:
            for msg in expected_messages:
                # Publish the test data
                await client.publish(
                    topic=str(msg.topic), payload=msg.payload, qos=msg.qos, retain=True, properties=publish_properties
                )
    except MqttError as ex:
        pytest.fail(f"Error publishing messages for the test: {ex!s}")

    yield client

    try:
        # clean up the test data. Publish None to delete retained message
        async with client:
            for msg in expected_messages:
                # Publish the test data
                await client.publish(topic=str(msg.topic), payload=None, properties=publish_properties)
    except MqttError as ex:
        pytest.fail(f"Error cleaning up messages after the test: {ex!s}")


@pytest.mark.asyncio
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "topics, expected_messages",
    [
        (  # Test multiple topics
            [MQTTTopicInput(topic="topic_1"), MQTTTopicInput(topic="topic_2")],
            [
                Message(
                    topic="topic_1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=1,
                    properties=None,
                ),
                Message(
                    topic="topic_2",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=2,
                    properties=None,
                ),
            ],
        ),
        (  # Test wild cards
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=3,
                    properties=None,
                ),
                Message(
                    topic="topic/2",
                    payload=b'{"timestamp": 4567, "val1": "QWERTY"}',
                    qos=1,
                    retain=False,
                    mid=4,
                    properties=None,
                ),
                Message(
                    topic="topic/2/3",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=5,
                    properties=None,
                ),
            ],
        ),
        (  # Test multiple messages to the same topic
            [MQTTTopicInput(topic="topic/+")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=6,
                    properties=None,
                ),
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 2345678, "val1": 4567}',
                    qos=1,
                    retain=False,
                    mid=7,
                    properties=None,
                ),
                Message(
                    topic="topic/2/3",
                    payload=b'{"timestamp": 123457, "val1": 5678}',
                    qos=1,
                    retain=False,
                    mid=8,
                    properties=None,
                ),
            ],
        ),
        (  # Test with topics from  sparkplugB with protobuf responses
            [MQTTTopicInput(topic="topic/+"), MQTTTopicInput(topic="topic/#")],
            [
                Message(
                    topic="topic/1",
                    payload=b'{"timestamp": 123456, "val1": 1234}',
                    qos=1,
                    retain=False,
                    mid=9,
                    properties=None,
                ),
                Message(
                    topic="spBv1.0/STATE/scada_2345",
                    payload=b'{ "online" : false,  "timestamp" : 1668114759262}',
                    qos=1,
                    retain=False,
                    mid=10,
                    properties=None,
                ),
                Message(
                    topic="spBv1.0/uns_group/NBIRTH/eon1",
                    payload=sample_spb_payload,
                    qos=1,
                    retain=False,
                    mid=11,
                    properties=None,
                ),
            ],
        ),
        # Add more test cases as needed
    ],
)
async def test_get_mqtt_messages_integration(publish_to_mqtt, topics: list[MQTTTopicInput], expected_messages: list[Message]):  # noqa: ARG001
    subscription = MQTTSubscription()
    received_messages: list[MQTTMessage] = []
    # Await the subscription result directly to collect the messages
    async for message in subscription.get_mqtt_messages(topics):
        received_messages.append(message)
        if len(received_messages) == len(expected_messages):
            break
    assert len(received_messages) == len(expected_messages)
