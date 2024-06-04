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

Entry point for all GraphQL queries to the UNS
"""

import logging

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from uns_graphql.queries import historic_events, uns_events
from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.subscriptions.mqtt import MQTTSubscription
from uns_graphql.type.basetype import Int64

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Query the UNS for current or historic Nodes/Events ")
class Query(historic_events.Query):  # , uns_events.Query):
    pass


@strawberry.type(description="Subscribe to UNS Events or Streams")
class Subscription(MQTTSubscription, KAFKASubscription):
    pass


class UNSGraphql:
    """
    Class providing the entry point for all GraphQL queries to the UNS & SPB Namespaces
    """

    schema = strawberry.Schema(query=Query, subscription=Subscription, scalar_overrides={int: Int64})
    graphql_app = GraphQLRouter(schema)
    LOGGER.info("GraphQL app created")
    app = FastAPI()
    app.include_router(graphql_app, prefix="/graphql")


def main():
    #     """
    #     Main function invoked from command line
    #     """
    LOGGER.error(
        "Dont invoke main. Invoke via Uvicorn in the manner below. Adapt host and port appropriately \n\n"
        "uvicorn uns_graphql.uns_graphql_app:UNSGraphql.app --host 0.0.0.0 --port 8000\n\n"
    )


#     try:
#         graphql_server = UNSGraphql()
#         LOGGER.info("GraphQL server started successfully")

#         # Add Strawberry ASGI application
#         graphql_app = GraphQLRouter(graphql_server.schema)
#         graphql_app.include_schema = False  # Ensure the schema is not included in the response

#         @graphql_server.app.get("/")  # Expose GraphQL endpoint
#         async def graphql():
#             return graphql_app

#     except Exception as e:
#         LOGGER.exception("Failed to start GraphQL server: %s", str(e))


if __name__ == "__main__":
    main()
