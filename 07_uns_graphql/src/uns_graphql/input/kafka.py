from typing import Annotated

import strawberry
from pydantic import BaseModel, StringConstraints

from uns_graphql.graphql_config import REGEX_FOR_KAFKA_TOPIC


class KAFKATopic(BaseModel):
    topic: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=REGEX_FOR_KAFKA_TOPIC, min_length=1, max_length=100)
    ]


@strawberry.experimental.pydantic.input(
    model=KAFKATopic, all_fields=True, description="Valid Kafka Topic to subscribe to. Does not accept wildcards or RegEx"
)
class KAFKATopicInput:
    pass
