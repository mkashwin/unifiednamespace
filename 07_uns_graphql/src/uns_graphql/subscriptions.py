"""
This module contains subscription methods fro GraphQL
It provides asynchronous generators for subscribing to MQTT and Kafka messages.
"""

import asyncio
import logging
import random
import time
import typing

import strawberry
from confluent_kafka import Consumer
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.graphql_config import KAFKAConfig, MQTTConfig
from uns_graphql.input.kafka_subscription import KAFKATopicInput
from uns_graphql.input.mqtt_subscription import MQTTTopicInput
from uns_graphql.type.uns_event import UNSEvent

LOGGER = logging.getLogger(__name__)


@strawberry.type
class Subscription:
    """
    Subscription class providing methods for subscribing to MQTT and Kafka messages.
    """

    @strawberry.subscription
    async def get_mqtt_messages(
        self, topics: typing.List[MQTTTopicInput]
    ) -> typing.AsyncGenerator[UNSEvent, None]:
        """
        Subscribe to MQTT messages based on provided topics.

        Args:
            topics (List of MQTTTopicInput): List of Topics to subscribe to. Supports wildcards

        Yields:
            typing.AsyncGenerator[UNSEvent, None]: Asynchronously generates UNS event messages
        """
        # Convert a single topic to a list for uniform handling

        client_id = f"graphql-{time.time()}-{random.randint(0, 1000)}",  # noqa: S311
        # Connect to MQTT broker and subscribe to the specified topics
        client: UnsMQTTClient = UnsMQTTClient(
            client_id=client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.version,
            transport=MQTTConfig.transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure)
        client.topics = topics.mqtt_topics
        properties = None
        if MQTTConfig.protocol == client.MQTTv5:
            properties = Properties(PacketTypes.CONNECT)
        client.setup_tls(MQTTConfig.tls)
        # Set username & password only if it was specified
        if MQTTConfig.username is not None:
            client.username_pw_set(MQTTConfig.username, MQTTConfig.password)
        client.connect(host=MQTTConfig.host,
                       port=MQTTConfig.port,
                       keepalive=MQTTConfig.keepalive,
                       properties=properties)
        client.connect()

        async def mqtt_listener() -> typing.AsyncGenerator[UNSEvent, None]:
            queue = asyncio.Queue()

            def on_message(client, userdata, msg):  # noqa: ARG001
                mqtt_message = UNSEvent(topic=msg.topic, payload=msg.payload)
                queue.put_nowait(item=mqtt_message)

            client.on_message = on_message
            client.subscribe(topic=topics.mqtt_topics)

            while True:
                yield await queue.get()

        async for message in mqtt_listener():
            yield message

    @strawberry.subscription
    async def kafka_messages(
        self, topics: typing.List[KAFKATopicInput]
    ) -> typing.AsyncGenerator[UNSEvent, None]:
        """
        Subscribe to Kafka messages based on provided topics.

        Args:
            topics (List of KAFKATopicInput): Kafka topics to subscribe to.
                                  Doesn't supports wildcards or regEx

        Yields:
            typing.AsyncGenerator[UNSEvent, None]: Asynchronously generates UNS event messages
        """
        # Connect to Kafka broker and subscribe to the specified topic
        consumer: Consumer = Consumer(KAFKAConfig.config_map)
        consumer.subscribe(topics.kafka_topics)

        async def kafka_listener() -> typing.AsyncGenerator[UNSEvent, None]:
            for msg in consumer:
                yield UNSEvent(topic=msg.topic, payload=msg.value)

        async for message in kafka_listener():
            yield message
