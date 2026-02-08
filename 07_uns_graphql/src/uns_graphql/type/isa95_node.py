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

Type of data to be retrieved from the UNS
Node are formed by the merging of multiple events
"""

import logging
from datetime import datetime

import strawberry

from uns_graphql.type.basetype import JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type
class UNSNode:
    """
    Model of a UNS Node,
    """

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
    created: datetime

    # Timestamp of when this node was last modified
    last_updated: datetime

    def __eq__(self, other):
        """
        Compare UNSNode instances based on their identifying attributes.
        Two nodes are equal if they have the same namespace and node_type.
        """
        if not isinstance(other, UNSNode):
            return NotImplemented

        return (
            self.namespace == other.namespace and
            self.node_type == other.node_type and
            self.node_name == other.node_name
        )

    def __hash__(self):
        """
        Generate hash based on immutable identifying attributes.
        Uses namespace and node_type as the unique identifier.
        """
        return hash((self.namespace, self.node_type, self.node_name))
