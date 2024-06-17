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
from fastapi.concurrency import asynccontextmanager
from strawberry.fastapi import GraphQLRouter

from uns_graphql.queries import graph, historian
from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.subscriptions.mqtt import MQTTSubscription
from uns_graphql.type.basetype import Int64

LOGGER = logging.getLogger(__name__)


@strawberry.type(description="Query the UNS for current or historic Nodes/Events ")
class Query(historian.Query, graph.Query):
    @classmethod
    async def on_shutdown(cls):
        """
        Clean up connections, db pools etc.
        """
        try:
            await historian.Query.on_shutdown()
        finally:
            await graph.Query.on_shutdown()


@strawberry.type(description="Subscribe to UNS Events or Streams")
class Subscription(MQTTSubscription, KAFKASubscription):
    @classmethod
    async def on_shutdown(cls):
        """
        Clean up connections, db pools etc.
        """
        await MQTTSubscription.on_shutdown()
        await KAFKASubscription.on_shutdown()


class UNSGraphql:
    """
    Class providing the entry point for all GraphQL queries to the UNS & SPB Namespaces
    """

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):  # noqa: ARG002
        """
        lifespan manager to ensure cleanup
        """
        try:
            yield
        finally:
            await Query.on_shutdown()
            await Subscription.on_shutdown()

    schema = strawberry.Schema(query=Query, subscription=Subscription, scalar_overrides={int: Int64})
    graphql_app = GraphQLRouter(schema)
    LOGGER.info("GraphQL app created")
    app = FastAPI(lifespan=lifespan)
    app.include_router(graphql_app, prefix="/graphql")
