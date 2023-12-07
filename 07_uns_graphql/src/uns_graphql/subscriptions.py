"""
This module contains subscription methods fro GraphQL
It provides asynchronous generators for subscribing to MQTT and Kafka messages.
"""

import asyncio
import logging
import random
import time
import typing

import aiomqtt
import strawberry
from confluent_kafka import OFFSET_BEGINNING, Consumer

from uns_graphql.graphql_config import KAFKAConfig, MQTTConfig
from uns_graphql.input.kafka_subscription import KAFKATopicInput
from uns_graphql.input.mqtt_subscription import MQTTTopicInput
from uns_graphql.type.mqtt_event import MQTTMessage
from uns_graphql.type.streaming_event import StreamingMessage

LOGGER = logging.getLogger(__name__)


@strawberry.type
class Subscription:
    """
    Subscription class providing methods for subscribing to MQTT and Kafka messages.
    """

    @strawberry.subscription(
        description=" Subscribe to MQTT messages based on provided list of topics. MQTT wildcards are supported "
    )
    async def get_mqtt_messages(self, topics: typing.List[MQTTTopicInput]) -> typing.AsyncGenerator[MQTTMessage, None]:
        """
        Subscribe to MQTT messages based on provided topics.

        Args:
            topics (List of MQTTTopicInput): List of Topics to subscribe to. Supports wildcards

        Yields:
            typing.AsyncGenerator[UNSMessage, None]: Asynchronously generates UNS event messages
        """
        try:
            client_id = f"graphql-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311
            async with aiomqtt.Client(
                client_id=client_id,
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
            ) as client:
                async with client.messages() as messages:
                    for mqtt_topic in topics:
                        await client.subscribe(topic=mqtt_topic.topic, qos=MQTTConfig.qos, properties=MQTTConfig.properties)
                    async for msg in messages:
                        yield MQTTMessage(topic=str(msg.topic), payload=msg.payload)
        except aiomqtt.MqttError as ex:
            LOGGER.error("Error while connecting to MQTT Broker %s", str(ex), stack_info=True, exc_info=True)
            await asyncio.sleep(MQTTConfig.retry_interval)

    @strawberry.subscription(description="Subscribe to Kafka messages based on provided topics")
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

        async def kafka_listener() -> typing.AsyncGenerator[MQTTMessage, None]:
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
