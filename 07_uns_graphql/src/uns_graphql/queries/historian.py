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

GraphQL queries to the historian
"""

import logging
from datetime import datetime

import strawberry

from uns_graphql.backend.historian import HistorianDBPool
from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.type.basetype import BinaryOperator
from uns_graphql.type.historical_event import HistoricalUNSEvent

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Query Historic Events")
class Query:
    """
    All Queries for historical events from the Unified Namespace
    """

    @strawberry.field(description="Get all historical published on the given array of topics and between the time slots.")
    async def get_historic_events_in_time_range(
        self,
        topics: list[MQTTTopicInput],
        from_datetime: datetime | None = strawberry.UNSET,
        to_datetime: datetime | None = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        LOGGER.debug(
            "Query for historic events in UNS with Params :\n"
            f"topics={topics}, from_datetime={from_datetime}, to_datetime={from_datetime}"
        )
        if type(topics) is not list:
            # convert single topic to array for consistent handling
            topics = [topics]

        async with HistorianDBPool() as historian:
            result: list[HistoricalUNSEvent] = await historian.get_historic_events(
                topics=(x.topic for x in topics),  # extract string from input object
                publishers=None,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
            return result

    @strawberry.field(description="Get all historical events published by specified clients.")
    async def get_historic_events_by_publishers(
        self,
        publishers: list[str],
        topics: list[MQTTTopicInput] | None = strawberry.UNSET,
        from_datetime: datetime | None = strawberry.UNSET,
        to_datetime: datetime | None = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        LOGGER.debug(
            "Query for historic events by publishers in UNS with Params :\n"
            f"publishers={publishers}, topics={topics}, from_datetime={from_datetime}, to_datetime={from_datetime}  "
        )
        async with HistorianDBPool() as historian:
            result: list[HistoricalUNSEvent] = await historian.get_historic_events(
                topics=[x.topic for x in topics] if topics else None,  # extract string from input object
                publishers=publishers,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
            return result

    @strawberry.field(
        description="Get all historical events published which have specific attributes."
        "Option binary_operator input allows chaining the list of property_keys. If NULL, property_keys will be ORed"
        "- OR: Either of the property_keys must exist in the same event.. If only one property_keys provided will be ignored"
        "- AND:  All property_keys must exist in same event. If only one property_keys provided will be ignored"
        "- NOT: None of the provided property_keys should exist in the same event"
        "Other criteria - topics, from_datetime & to_datetime will always be ANDed to the query filter"
    )
    async def get_historic_events_by_property(
        self,
        property_keys: list[str],
        binary_operator: BinaryOperator | None = strawberry.UNSET,
        topics: list[MQTTTopicInput] | None = strawberry.UNSET,
        from_datetime: datetime | None = strawberry.UNSET,
        to_datetime: datetime | None = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        LOGGER.debug(
            "Query for historic events by properties, with params :\n"
            f"property_keys={property_keys}, binary_operator={binary_operator}, topics={topics},"
            f" from_datetime={from_datetime}, to_datetime={from_datetime} "
        )
        async with HistorianDBPool() as historian:
            result: list[HistoricalUNSEvent] = await historian.get_historic_events_for_property_keys(
                property_keys=property_keys,
                binary_operator=binary_operator.value if binary_operator else BinaryOperator.OR.value,
                topics=[x.topic for x in topics] if topics else None,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
            return result

    @classmethod
    async def on_shutdown(cls):
        """
        Clean up Db connection pool
        """
        await HistorianDBPool.close_pool()
