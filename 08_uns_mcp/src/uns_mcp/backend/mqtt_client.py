"""MQTT Publisher Client."""

import json
import logging
import random
import time

from aiomqtt import Client

from uns_mcp.config import MQTTConfig

LOGGER = logging.getLogger(__name__)


class MQTTPublisher:
    """Async MQTT client for publishing."""

    def __init__(self):
        self.client: Client | None = None
        self.client_id = f"uns_mcp_{time.time()}_{random.randint(0, 1000)}"  # noqa: S311

    async def connect(self) -> None:
        """Establish MQTT connection."""
        try:
            self.client = Client(
                identifier=self.client_id,
                hostname=MQTTConfig.host,
                port=MQTTConfig.port,
                username=MQTTConfig.username,
                password=MQTTConfig.password,
                protocol=MQTTConfig.version,
                transport=MQTTConfig.transport,
                keepalive=MQTTConfig.keep_alive,
                tls_params=MQTTConfig.tls_params,
                tls_insecure=MQTTConfig.tls_insecure,
                clean_session=MQTTConfig.clean_session
            )
            await self.client.__aenter__()
            LOGGER.info(f"Connected to MQTT broker at {MQTTConfig.host}")
        except Exception as e:
            LOGGER.error(f"Failed to connect to MQTT: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MQTT."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                LOGGER.info("MQTT connection closed")
            except Exception as e:
                LOGGER.error(f"Error closing MQTT: {e}")
            finally:
                self.client = None

    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        return self.client is not None

    async def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        """Publish data to UNS."""
        if not self.client:
            raise ValueError("MQTT client not connected")

        if MQTTConfig.mqtt_timestamp_key not in payload:
            payload[MQTTConfig.mqtt_timestamp_key] = time.time() * 1000

        json_payload = json.dumps(payload)
        await self.client.publish(topic, json_payload.encode('utf-8'), qos=qos, properties=MQTTConfig.properties)
        LOGGER.info(f"Published to {topic}")
