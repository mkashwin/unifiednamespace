import logging
from datetime import datetime
from typing import Optional

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
        from_datetime: Optional[datetime] = strawberry.UNSET,
        to_datetime: Optional[datetime] = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        LOGGER.debug(
            "Query for historic events in UNS with Params :\n"
            f"topics={topics}, from_datetime={from_datetime}, to_datetime={from_datetime}"
        )
        if type and type(topics) is not list:
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
        topics: Optional[list[MQTTTopicInput]] = strawberry.UNSET,
        from_datetime: Optional[datetime] = strawberry.UNSET,
        to_datetime: Optional[datetime] = strawberry.UNSET,
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
        binary_operator: Optional[BinaryOperator] = strawberry.UNSET,
        topics: Optional[list[MQTTTopicInput]] = strawberry.UNSET,
        from_datetime: Optional[datetime] = strawberry.UNSET,
        to_datetime: Optional[datetime] = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        LOGGER.debug(
            "Query for historic events by properties, with params :\n"
            f"property_keys={property_keys}, binary_operator={binary_operator}, topics={topics},"
            f" from_datetime={from_datetime}, to_datetime={from_datetime} "
        )
        async with HistorianDBPool() as historian:
            result: list[HistoricalUNSEvent] = await historian.get_historic_events_for_property_keys(
                property_keys=property_keys,
                binary_operator=str(binary_operator) if binary_operator else str(BinaryOperator.OR),
                topics=[x.topic for x in topics] if topics else None,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
            return result
