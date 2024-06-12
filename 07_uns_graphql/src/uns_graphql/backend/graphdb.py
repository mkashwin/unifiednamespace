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

Encapsulates integration with the Graph database database
"""

import logging

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncResult, Record

from uns_graphql.graphql_config import GraphDBConfig

LOGGER = logging.getLogger(__name__)


class GraphDB:
    """
    Encapsulates the connection and queries to the graph database.
    Provides methods to get and release the Neo4j async driver.
    """

    # Class variable to hold the shared driver for the graph DB
    _graphdb_driver: AsyncDriver = None

    @classmethod
    async def get_graphdb_driver(cls) -> AsyncDriver:
        """
        Returns the Neo4j async driver which is the connection to the database.

        Validates if the current driver is still connected, and if not, creates a new connection.
        The driver is cached and reused for subsequent requests to avoid creating multiple connections.

        Returns:
            AsyncDriver: The Neo4j async driver.
        """
        LOGGER.debug("GraphDB driver requested")
        if cls._graphdb_driver is None:
            LOGGER.info("Creating a new GraphDB driver")
            cls._graphdb_driver = AsyncGraphDatabase.driver(
                uri=GraphDBConfig.conn_url, auth=(GraphDBConfig.user, GraphDBConfig.password)
            )
        try:
            await cls._graphdb_driver.verify_connectivity()
            LOGGER.debug("GraphDB driver connectivity verified")
        except Exception as ex:
            LOGGER.error("Failed to verify GraphDB driver connectivity: %s", str(ex), stack_info=True, exc_info=True)
            # In case of connectivity failure, close the existing driver and create a new one
            await cls.release_graphdb_driver()
            cls._graphdb_driver = AsyncGraphDatabase.driver(
                uri=GraphDBConfig.conn_url, auth=(GraphDBConfig.user, GraphDBConfig.password)
            )
            await cls._graphdb_driver.verify_connectivity()
            LOGGER.info("Reconnected to GraphDB driver")

        return cls._graphdb_driver

    @classmethod
    async def release_graphdb_driver(cls):
        """
        Closes the Neo4j async driver and releases the connection.
        Ensures that any exceptions during the close process are logged.
        """
        if cls._graphdb_driver is not None:
            LOGGER.debug("Releasing GraphDB driver")
            try:
                await cls._graphdb_driver.close()
                LOGGER.info("GraphDB driver closed successfully")
            except Exception as ex:
                LOGGER.error("Error closing the GraphDB driver: %s", str(ex), stack_info=True, exc_info=True)
            finally:
                cls._graphdb_driver = None
        else:
            LOGGER.warning("Trying to close an already closed driver")

    async def execute_read_query(self, query: str, *args, **kwargs) -> list[Record]:  # -> list:
        """
        Executes a read (CQL) query with the provided positional and keyword parameters.

        Args:
            query (str): The CQL query to execute.
            *args: Positional parameters for the CQL query.
            **kwargs: Keyword parameters for the CQL query.

        Returns:
            list: The results of the query.
        """

        LOGGER.debug("Executing query: %s with args: %s and kwargs: %s", query, args, kwargs)
        async with self.get_graphdb_driver().session() as session:
            try:
                result: AsyncResult = await session.run(query, *args, **kwargs)
                records: list[Record] = [record async for record in result]
                LOGGER.debug("Query executed successfully, retrieved records: %s", records)
                return records
            except Exception as ex:
                LOGGER.error("Error executing query: %s", str(ex), stack_info=True, exc_info=True)
                raise

    async def execute_write_query(self, query: str, *args, **kwargs):
        """
        Executes a write (CQL) query with the provided positional and keyword parameters.
        Supports transactional operations.

        Args:
            query (str): The CQL query to execute.
            *args: Positional parameters for the CQL query.
            **kwargs: Keyword parameters for the CQL query.

        Returns:
            list: The results of the query.
        """

        LOGGER.debug("Executing write query: %s with args: %s and kwargs: %s", query, args, kwargs)
        async with self.get_graphdb_driver().session() as session:
            try:
                async with session.begin_transaction() as tx:
                    result = await tx.run(query, *args, **kwargs)
                    await tx.commit()
                    records = [record async for record in result]
                    LOGGER.debug("Write query executed successfully, committed records: %s", records)
                    return records
            except Exception as ex:
                LOGGER.error("Error executing write query: %s", str(ex), stack_info=True, exc_info=True)
                raise
