"""
Entry point for all GraphQL queries to the UNS
"""

import logging

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.subscriptions.mqtt import MQTTSubscription
from uns_graphql.type.basetype import Int64
from uns_graphql.type.isa95_node import UNSNode

LOGGER = logging.getLogger(__name__)


@strawberry.type
class Query:
    @strawberry.field(description="")
    def resolve_all_topics(self, info: Info) -> list[UNSNode]:  # noqa: ARG002
        # Placeholder logic to fetch all topics from Neo4j
        # Implement actual logic in resolvers.py
        return []


@strawberry.type
class Subscription(MQTTSubscription, KAFKASubscription):
    pass


class UNSGraphql:
    """
    Class providing the entry point for all GraphQL queries to the UNS & SPB Namespaces
    """

    schema = strawberry.Schema(query=Query, subscription=Subscription, scalar_overrides={int: Int64})
    graphql_app = GraphQLRouter(schema)
    app = FastAPI()
    app.include_router(graphql_app, prefix="/graphql")


def main():
    """
    Main function invoked from command line
    """
    try:
        graphql_server = UNSGraphql()
        LOGGER.info("GraphQL server started successfully")

        # Add Strawberry ASGI application
        graphql_app = GraphQLRouter(graphql_server.schema)
        graphql_app.include_schema = False  # Ensure the schema is not included in the response

        @graphql_server.app.get("/")  # Expose GraphQL endpoint
        async def graphql():
            return graphql_app

    except Exception as e:
        LOGGER.exception("Failed to start GraphQL server: %s", str(e))


if __name__ == "__main__":
    main()
