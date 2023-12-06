"""
Schema for GraphQL apis for the UNS
"""

import logging
import typing

import strawberry
from strawberry.types import Info

from uns_graphql.type.isa95_node import UNSNode

LOGGER = logging.getLogger(__name__)


@strawberry.type
class Query:
    """ """

    @strawberry.field(description="")
    def resolve_all_topics(self, info: Info) -> typing.List[UNSNode]:  # noqa: ARG002
        # Placeholder logic to fetch all topics from Neo4j
        # Implement actual logic in resolvers.py
        return []

    @strawberry.field(description="")
    def resolve_specific_topics(
        self,
        info: Info,  # noqa: ARG002
        topics: typing.List[str],
    ) -> typing.List[UNSNode]:
        # Placeholder logic to fetch specific topics data from different sources
        # Implement actual logic in resolvers.py
        return []
