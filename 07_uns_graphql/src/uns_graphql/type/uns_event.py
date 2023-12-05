"""
Type of data to be retrieved from the UNS
Maps to MQTT messages to the UNS
"""
import json
import logging
import typing

import strawberry
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.type.basetype import BytesPayload, JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type
class UNSMessage:
    """
    Model of a UNS Events
    """
    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    topic: str

    # stores the raw data of the event
    _raw_payload: strawberry.Private[bytes]

    def __init__(self, topic, payload):
        self.topic = topic
        self._raw_payload = payload

    # # The payload which was published was either a JSON string or bytes
    # payload: typing.Union[JSONPayload, BytesPayload]

    @strawberry.field(name="payload")
    def resolve_payload(
            self,
            info  # noqa: ARG002
    ) -> typing.Union[JSONPayload, BytesPayload]:
        if (self.topic.startswith(UnsMQTTClient.SPARKPLUG_NS)
                and not UnsMQTTClient.is_topic_matched(
                    UnsMQTTClient.SPB_STATE_MSG_TYPE, self.topic)):
            # Message to sparkplug name space in protobuf i.e. BytesPayload
            return BytesPayload(data=self._raw_payload)
        else:
            # Message to UNS or spb STATE message f i.e. JSONPayload
            try:
                return JSONPayload(data=self._raw_payload.decode("utf-8"))
            except json.JSONDecodeError:
                LOGGER.error("Expected JSON String")
