"""*******************************************************************************
* Copyright (c) 2024 Ashwin Krishnan
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

GraphQL queries to the graph database
"""

import logging
from typing import Optional

import strawberry

from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.type.basetype import BinaryOperator
from uns_graphql.type.isa95_node import UNSNode

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Query GraphDB for current consolidated UNS Nodes created by merging multiple UNS Events ")
class Query:
    """
    All Queries for latest consolidated node from the Unified Namespace
    """

    @strawberry.field(description="Get consolidation of nodes for given array of topics. MQTT wildcards are supported")
    def get_uns_nodes(
        self,
        topics: list[MQTTTopicInput],
    ) -> list[UNSNode]:
        LOGGER.debug("Query for Nodes in UNS with Params :\n" f"topics={topics}")
        if type(topics) is not list:
            # convert single topic to array for consistent handling
            topics = [topics]
        # TBD

    @strawberry.field(
        description="Get all UNSNodes published which have specific attributes."
        "Option binary_operator input allows chaining the list of property_keys. If NULL, property_keys will be ORed"
        "- OR: Either of the property_keys must exist in the same node. If only one property_keys provided will be ignored"
        "- AND:  All property_keys must exist in same node. If only one property_keys provided will be ignored"
        "- NOT: None of the provided property_keys should exist in the same node"
        "Other criteria - topics will always be ANDed to the query filter"
    )
    def get_uns_nodes_by_property(
        self,
        property_keys: list[str],
        binary_operator: Optional[BinaryOperator] = strawberry.UNSET,
        topics: Optional[list[MQTTTopicInput]] = strawberry.UNSET,
    ) -> list[UNSNode]:
        LOGGER.debug(
            "Query for historic events by properties, with params :\n"
            f"property_keys={property_keys}, binary_operator={binary_operator}, topics={topics},"
        )
        if type(topics) is not list:
            # convert single topic to array for consistent handling
            topics = [topics]
        # TBD

    @strawberry.field(
        description="Get consolidation of sparkplugB nodes. MQTT wildcards are supported"
        "Ensure that the topics are all in the SparkplugB namespace i.e. starts with 'spBv1.0/' "
        "Format of an SpB topic is spBv1.0/ <group_id> / <message_type> / <edge_node_id> / [<device_id>]"
    )
    def get_spb_nodes(
        self,
        topics: list[MQTTTopicInput],
    ) -> list[UNSNode]:
        LOGGER.debug("Query for Nodes in SpB with Params :\n" f"topics={topics}")
        if type(topics) is not list:
            # convert single topic to array for consistent handling
            topics = [topics]
        # TBD
