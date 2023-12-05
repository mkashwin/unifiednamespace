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
from confluent_kafka import OFFSET_BEGINNING, Consumer
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.graphql_config import KAFKAConfig, MQTTConfig
from uns_graphql.input.kafka_subscription import KAFKATopicInput
from uns_graphql.input.mqtt_subscription import MQTTTopicInput
from uns_graphql.type.streaming_event import StreamingMessage
from uns_graphql.type.uns_event import UNSEvent

LOGGER = logging.getLogger(__name__)


@strawberry.type
class Subscription:
    """
    Subscription class providing methods for subscribing to MQTT and Kafka messages.
    """

    @strawberry.subscription
    async def get_mqtt_messages(self, topics: typing.List[MQTTTopicInput]) -> typing.AsyncGenerator[UNSEvent, None]:
        """
        Subscribe to MQTT messages based on provided topics.

        Args:
            topics (List of MQTTTopicInput): List of Topics to subscribe to. Supports wildcards

        Yields:
            typing.AsyncGenerator[UNSEvent, None]: Asynchronously generates UNS event messages
        """
        client_id = (f"graphql-{time.time()}-{random.randint(0, 1000)}",)  # noqa: S311
        # Connect to MQTT broker and subscribe to the specified topics
        client: UnsMQTTClient = UnsMQTTClient(
            client_id=client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.version,
            transport=MQTTConfig.transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure,
        )

        client.run(
            host=MQTTConfig.host,
            port=MQTTConfig.port,
            username=MQTTConfig.username,
            password=MQTTConfig.password,
            tls=MQTTConfig.tls,
            keepalive=MQTTConfig.keep_alive,
            topics=[x.topic for x in topics],
            qos=MQTTConfig.qos,
        )

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
    async def get_kafka_messages(self, topics: typing.List[KAFKATopicInput]) -> typing.AsyncGenerator[StreamingMessage, None]:
        """
        Subscribe to Kafka messages based on provided topics.

        Args:
            topics (List of KAFKATopicInput): Kafka topics to subscribe to.
                                  Doesn't supports wildcards or regEx

        Yields:
            typing.AsyncGenerator[StreamingMessage, None]: Asynchronously generates UNS event messages
        """

        # Connect to Kafka broker and subscribe to the specified topic
        # Set up a callback to handle the '--reset' flag.
        def reset_offset(consumer, partitions):
            for part in partitions:
                part.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

        consumer: Consumer = Consumer(KAFKAConfig.config_map)
        consumer.subscribe([x.topic for x in topics], on_assign=reset_offset)

        async def kafka_listener() -> typing.AsyncGenerator[UNSEvent, None]:
            try:
                while True:
                    msg = consumer.poll(timeout=KAFKAConfig.consumer_poll_timeout)  # Poll for messages
                    if msg is None:
                        continue

                    if msg.error():
                        # Handle errors here if needed
                        LOGGER.error(f"Error Message received from Kafka Broker msg:{msg.error()!s}")
                        raise ValueError(msg.error())

                    yield StreamingMessage(topic=msg.topic(), payload=msg.value())
            finally:
                consumer.close()  # Close the consumer when done

        async for message in kafka_listener():
            yield message
