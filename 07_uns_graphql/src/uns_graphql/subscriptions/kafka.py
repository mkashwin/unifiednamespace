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

This module contains subscription methods for GraphQL
It provides asynchronous generators for subscribing to KAFKA topics.
"""

import asyncio
import logging
import typing

import strawberry
from confluent_kafka import OFFSET_BEGINNING, Consumer

from uns_graphql.graphql_config import KAFKAConfig
from uns_graphql.input.kafka import KAFKATopicInput
from uns_graphql.type.streaming_event import StreamingMessage

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Subscribe to all streaming events in the UNS i.e. from KAFKA.")
class KAFKASubscription:
    """
    Subscription class providing methods for subscribing to Kafka messages.
    """

    @strawberry.subscription(description="Subscribe to Kafka messages based on provided topics. Wildcards/Regex not supported")
    async def get_kafka_messages(self, topics: list[KAFKATopicInput]) -> typing.AsyncGenerator[StreamingMessage]:
        """
        Subscribe to Kafka messages based on provided topics.

        Args:
            topics (list[KAFKATopicInput]): List of Kafka topics to subscribe to.
                                            Does not support wildcards or regex.

        Yields:
            typing.AsyncGenerator[StreamingMessage, None]: Asynchronously generates UNS event messages.
        """

        def reset_offset(consumer, partitions):
            """
            Inner function to reset the offset of the consumer to the beginning
            Connect to Kafka broker and subscribe to the specified topic
            Set up a callback to handle the '--reset' flag.
            """
            for part in partitions:
                part.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

        # Initialize the Kafka consumer with the configuration
        consumer: Consumer = Consumer(KAFKAConfig.config_map)
        consumer.subscribe([x.topic for x in topics], on_assign=reset_offset)

        # Inner async function to poll and yield messages from Kafka
        async def kafka_listener() -> typing.AsyncGenerator[StreamingMessage]:
            try:
                while True:
                    # Poll for messages with a specified timeout
                    msg = consumer.poll(
                        timeout=KAFKAConfig.consumer_poll_timeout)
                    if msg is None:
                        await asyncio.sleep(KAFKAConfig.consumer_poll_timeout)
                        continue

                    if msg.error():
                        # Log and raise an error if there is an issue with the message
                        LOGGER.error(
                            f"Error Message received from Kafka Broker msg: {msg.error()!s}")
                        raise ValueError(msg.error())

                    # Yield the received message as a StreamingMessage
                    yield StreamingMessage(topic=msg.topic(), payload=msg.value())
            except asyncio.CancelledError:
                LOGGER.info("Kafka listener cancelled.")
            except Exception as e:
                LOGGER.error(
                    f"Unexpected error in Kafka listener: {e!s}", exc_info=True)
            finally:
                # Ensure the consumer is closed properly
                LOGGER.info("Closing Kafka consumer.")
                consumer.close()

        # Yield messages from the Kafka listener
        async for message in kafka_listener():
            yield message

    @classmethod
    async def on_shutdown(cls):
        """
        Clean up KAFKA subscription if required
        """
        # Not needed as the consumer is closed in #kafka_listener()
        pass
