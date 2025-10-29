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
It provides asynchronous generators for subscribing to MQTT topics.
"""

import asyncio
import logging
import random
import time
import typing

import strawberry
from aiomqtt import Client, MqttError

from uns_graphql.graphql_config import MQTTConfig
from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.type.mqtt_event import MQTTMessage

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Subscribe to all MQTT events in the UNS")
class MQTTSubscription:
    """
    Subscription class providing methods for subscribing to MQTT messages.
    """

    @strawberry.subscription(
        description=" Subscribe to MQTT messages based on provided list of topics. MQTT wildcards are supported "
    )
    async def get_mqtt_messages(self, topics: list[MQTTTopicInput]) -> typing.AsyncGenerator[MQTTMessage]:
        """
        Subscribe to MQTT messages based on provided topics.

        Args:
            topics (List of MQTTTopicInput): List of Topics to subscribe to. Supports wildcards

        Yields:
            typing.AsyncGenerator[UNSMessage, None]: Asynchronously generates UNS event messages
        """
        try:
            client_id = f"graphql-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311
            async with Client(
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
            ) as client:
                await client.subscribe(
                    topic=[(mqtt_topic.topic, MQTTConfig.qos) for mqtt_topic in topics], properties=MQTTConfig.properties
                )
                async for msg in client.messages:
                    yield MQTTMessage(topic=str(msg.topic), payload=msg.payload)
        except MqttError as ex:
            LOGGER.error("Error while connecting to MQTT Broker %s",
                         ex, stack_info=True, exc_info=True)
            await asyncio.sleep(MQTTConfig.retry_interval)

    @classmethod
    async def on_shutdown(cls):
        """
        Clean up MQTT subscription if required
        """
        # Not needed as the consumer is closed implicitly in client.__aexit__()
        pass
