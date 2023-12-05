"""
Type of data to be retrieved from the UNS
Node are formed by the merging of multiple events
"""
import logging

import strawberry

from uns_graphql.type.basetype import JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type
class UNSNode:
    """
    Model of a UNS Node,
    """

    # pylint: disable=too-few-public-methods
    # Name of the node. Also present as part of the namespace
    node_name: str
    # Type of the Node depending on the topic hierarchy in accordance with ISA-95 Part 2
    # ["ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE", "NESTED_ATTRIBUTE"]
    node_type: str

    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    namespace: str

    # Merged Composite of all properties published to this node
    payload: JSONPayload

    # Timestamp of when this node was created
    created: int

    # Timestamp of when this node was last modified
    last_updated: int
