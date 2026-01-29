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

Input Object for queries to the KAFKA Subscription
"""

from typing import Annotated

import strawberry
from pydantic import BaseModel, StringConstraints

from uns_graphql.graphql_config import REGEX_FOR_KAFKA_TOPIC


class KAFKATopic(BaseModel):
    topic: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=REGEX_FOR_KAFKA_TOPIC, min_length=1, max_length=100)
    ]


@strawberry.experimental.pydantic.input(
    model=KAFKATopic, all_fields=True, description="Valid Kafka Topic to subscribe to. Accepts wildcards or RegEx"
)
class KAFKATopicInput:
    pass
