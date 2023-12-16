import logging
from datetime import datetime
from typing import Optional

import strawberry

from uns_graphql.backend.historian import HistorianDBPool
from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.type.historical_event import HistoricalUNSEvent

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Query Historic")
class Query:
    """
    All Queries for historical information from the
    """

    @strawberry.field(
        description="Get all historical published on the given topics and between the time slots."
        "If time slots are not provided then fromDatetime defaults to 0 and toDatetime defaults to current time"
    )
    async def get_historic_events_in_time_range(
        self,
        topics: list[MQTTTopicInput],
        from_datetime: Optional[datetime] = strawberry.UNSET,
        to_datetime: Optional[datetime] = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
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

    @strawberry.field(description="Get all historical events published by specified client")
    async def get_events_by_publishers(
        self,
        publishers: list[str],
        topics: Optional[list[MQTTTopicInput]] = strawberry.UNSET,
        from_datetime: Optional[datetime] = strawberry.UNSET,
        to_datetime: Optional[datetime] = strawberry.UNSET,
    ) -> list[HistoricalUNSEvent]:
        async with HistorianDBPool() as historian:
            result: list[HistoricalUNSEvent] = await historian.get_historic_events(
                topics=[x.topic for x in topics] if topics else None,  # extract string from input object
                publishers=publishers,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
            return result
