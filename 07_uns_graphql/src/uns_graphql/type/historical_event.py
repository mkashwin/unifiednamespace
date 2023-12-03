"""
Type of data to be retrieved from the UNS
"""
import logging

import strawberry

from uns_graphql.type.sparkplugb_node import UNSEvent

LOGGER = logging.getLogger(__name__)


@strawberry.type
class HistoricalUNSEvent(UNSEvent):
    """
    Model of a UNS Events
    """
    # Client id of the what/who published this messages
    published_by: str

    # Timestamp of when this event was published/historied
    timestamp: int
