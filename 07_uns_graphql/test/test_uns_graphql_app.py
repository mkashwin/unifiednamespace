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

"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from uns_graphql.queries import historic_events, uns_events
from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.subscriptions.mqtt import MQTTSubscription
from uns_graphql.uns_graphql_app import UNSGraphql


def test_uns_graphql_app_attributes():
    """
    Test validity of key attributes of  UNSGraphql needed to start run the GraphQL server
    """
    assert UNSGraphql.schema is not None
    assert UNSGraphql.app is not None


@pytest.mark.asyncio
async def test_uns_graphql_app_test_cleanup_on_shutdown():
    """
    Test to validate that the app calls the cleanup method on the query and subscription classes
    """
    # patch the classes
    # with patch.object(HistorianDBPool, "close_pool", new_callable=MagicMock) as mock_close_pool:
    with patch.object(historic_events.Query, "on_shutdown", new_callable=AsyncMock) as mock_historic_cleanup, patch.object(
        uns_events.Query, "on_shutdown", new_callable=AsyncMock
    ) as mock_uns_cleanup, patch.object(
        MQTTSubscription, "on_shutdown", new_callable=AsyncMock
    ) as mock_mqtt_cleanup, patch.object(KAFKASubscription, "on_shutdown", new_callable=AsyncMock) as mock_kafka_cleanup:
        # Initialize the UNSGraphql app
        uns_graphql_app = UNSGraphql()
        app: FastAPI = uns_graphql_app.app

        # Simulate the lifespan context
        @asynccontextmanager
        async def lifespan_context(app):
            async with uns_graphql_app.lifespan(app):
                yield

        # Simulate the startup and shutdown sequence
        async with lifespan_context(app):
            pass
    # Check if HistorianDBPool.close_pool was called
    # mock_close_pool.assert_called_once()
    mock_historic_cleanup.assert_called_once()
    mock_uns_cleanup.assert_called_once()
    mock_mqtt_cleanup.assert_called_once()
    mock_kafka_cleanup.assert_called_once()
