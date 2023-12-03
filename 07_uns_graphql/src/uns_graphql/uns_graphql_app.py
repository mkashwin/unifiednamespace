"""
Entry point for all GraphQL queries to the UNS
"""
import logging

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from uns_graphql.query import Query
from uns_graphql.subscriptions import Subscription

LOGGER = logging.getLogger(__name__)


class UNSGraphql:
    """
    Class providing the entry point for all GraphQL queries to the UNS & SPB Namespaces
    """
    schema = strawberry.Schema(query=Query, subscription=Subscription)
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
