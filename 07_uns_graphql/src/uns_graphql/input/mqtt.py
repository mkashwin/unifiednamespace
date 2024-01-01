from typing import Annotated

import strawberry
from pydantic import BaseModel, StringConstraints

from uns_graphql.graphql_config import REGEX_FOR_MQTT_TOPIC


class MQTTTopic(BaseModel):
    topic: Annotated[str, StringConstraints(strip_whitespace=True, pattern=REGEX_FOR_MQTT_TOPIC, min_length=1, max_length=100)]


@strawberry.experimental.pydantic.input(model=MQTTTopic, description="Valid MQTT Topic to subscribe to. Accepts wild cards")
class MQTTTopicInput:
    topic: strawberry.auto
