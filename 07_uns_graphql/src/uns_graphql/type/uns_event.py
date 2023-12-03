"""
Type of data to be retrieved from the UNS
"""
import json
import logging
import typing

import strawberry
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.type.basetype import BytesPayload, JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type
class UNSEvent:
    """
    Model of a UNS Events
    """
    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    topic: str

    # The payload which was published was either a JSON string or bytes
    payload: typing.Optional[typing.Union[JSONPayload, BytesPayload]]

    @strawberry.field(name="payload")
    def resolve_payload(
            self,
            info  # noqa: ARG002
    ) -> typing.Union[JSONPayload, BytesPayload]:
        if (self.topic.startswith(UnsMQTTClient.SPARKPLUG_NS)
                and not UnsMQTTClient.is_topic_matched(
                    UnsMQTTClient.SPB_STATE_MSG_TYPE, self.topic)):
            try:
                return self.payload.decode("utf-8")
            except json.JSONDecodeError:
                LOGGER.error("Expected JSON String")
        else:
            return self.payload
