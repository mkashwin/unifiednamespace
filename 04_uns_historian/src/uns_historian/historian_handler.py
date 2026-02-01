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

Encapsulate logic of persisting messages to the historian database
"""

import json
import logging
from datetime import UTC, datetime

import asyncpg
from asyncpg import Pool, Record
from asyncpg.connection import Connection
from asyncpg.prepared_stmt import PreparedStatement

from uns_historian.historian_config import HistorianConfig

LOGGER = logging.getLogger(__name__)


class HistorianHandler:
    """
    Class to encapsulate logic of persisting messages to the historian database
    """

    # Class variable to hold the shared pool
    _shared_pool: Pool = None

    @classmethod
    async def get_shared_pool(cls) -> Pool:
        """
        Retrieves the shared connection pool.
        Creates a new pool if it doesn't exist.

        Returns:
            Pool: The shared connection pool.
        """
        try:
            LOGGER.debug("DB Shared connection pool requested")
            if cls._shared_pool is None:
                cls._shared_pool = await cls.create_pool()
            return cls._shared_pool
        except Exception as ex:
            LOGGER.error(f"Error while getting shared pool: {ex}")
            raise

    @classmethod
    async def create_pool(cls) -> Pool:
        """
        Creates a connection pool.
        Returns:
            Pool: The created connection pool.
        Raises:
            asyncpg.PostgresError: If there's an error creating the pool.
        """
        try:
            pool: Pool = await asyncpg.create_pool(
                host=HistorianConfig.hostname,
                user=HistorianConfig.user,
                password=HistorianConfig.password,
                database=HistorianConfig.database,
                port=HistorianConfig.port,
                ssl=HistorianConfig.get_ssl_context(),
            )
            LOGGER.info("Connection pool created successfully")
            return pool
        except asyncpg.PostgresError as e:
            LOGGER.error(f"Error creating connection pool: {e}")
            raise

    @classmethod
    async def close_pool(cls):
        """
        Close the connection pool
        """
        if cls._shared_pool is not None and not cls._shared_pool.is_closing():
            await cls._shared_pool.close()
            cls._shared_pool = None
            LOGGER.info("Connection pool closed successfully")
        else:
            LOGGER.warning("Connection pool was already closed ")

    async def __aenter__(self):
        # Acquire the shared pool directly
        self._pool: Pool = await self.get_shared_pool()
        # Acquire a connection from the pool
        self._conn: Connection = await self._pool.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._pool.release(self._conn)  # Release the acquired connection

    async def __aiter__(self):
        """
        Allow usage in asynchronous for loops.
        """
        self._conn: Connection = await self.get_shared_pool().acquire()
        return self

    async def __anext__(self) -> Connection:
        """
        Use with asynchronous for loops.
        """
        return self._conn

    async def execute_prepared(self, query: str, *args) -> list:
        """
        Executes a prepared query to fetch historical events.
        Returns a list of Records

        Args:
            query (str): The SQL query to execute.
            *args: Query parameters.

        Returns:
            list[HistoricalUNSEvent]: list of historical events.

        Raises:
            asyncpg.PostgresError: If there's an error executing the prepared statement.
        """
        try:
            if self._conn is None or self._conn.is_closed():
                self._conn = await self._pool.acquire()
            stmt: PreparedStatement = await self._conn.prepare(query)
            results: Record = await stmt.fetch(*args)
            return results

        except asyncpg.PostgresError as ex:
            LOGGER.error(f"Error executing prepared statement: {ex}")
            raise

    async def persist_mqtt_msg(self, client_id: str, topic: str, timestamp: float | None, message: dict):
        """
        Persists all mqtt message in the historian
        ----------
        client_id:
            Identifier for the Subscriber
        topic: str
            The topic on which the message was sent
        timestamp
            The timestamp of the message received in milliseconds
        message: str
            The MQTT message. String is expected to be JSON formatted
        """
        if timestamp is None:
            db_timestamp = datetime.now(UTC)
        else:
            # Timestamp is normally in milliseconds and needs to be converted prior to insertion
            db_timestamp = datetime.fromtimestamp(timestamp / 1000, UTC)
        # sometimes when qos is not 2, the mqtt message may be delivered multiple times. in such case avoid duplicate inserts
        sql_cmd = (
            f"INSERT INTO {HistorianConfig.table} ( time, topic, client_id, mqtt_msg ) \n"  # noqa:S608:
            + "VALUES ($1,$2,$3,$4) \n"
            + "ON CONFLICT DO NOTHING \n"
            + "RETURNING *;"
        )  # This is a prepared statement and the values are sanitized
        params = [db_timestamp, topic, client_id, json.dumps(message)]
        return await self.execute_prepared(sql_cmd, *params)
