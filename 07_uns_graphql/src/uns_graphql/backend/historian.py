"""
Encapsulates integration with the historian database
"""
import logging
from datetime import datetime
from typing import Optional

import asyncpg
from asyncpg import Pool
from asyncpg.connection import Connection
from asyncpg.prepared_stmt import PreparedStatement
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.graphql_config import HistorianConfig
from uns_graphql.type.basetype import JSONPayload
from uns_graphql.type.historical_event import HistoricalUNSEvent

LOGGER = logging.getLogger(__name__)


class HistorianDBPool:
    """
    Encapsulates the connection and queries to the historian database
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
        LOGGER.debug("DB Shared connection pool requested")
        if cls._shared_pool is None:
            cls._shared_pool = await cls.create_pool()
        return cls._shared_pool

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
                user=HistorianConfig.db_user,
                password=HistorianConfig.db_password,
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
        if not cls._shared_pool.is_closing():
            await cls._shared_pool.close()
            LOGGER.info("Connection pool closed successfully")
        else:
            LOGGER.warn("Connection pool was already closed ")

    async def __aenter__(self):
        self._pool: Pool = await self.get_shared_pool()  # Acquire the shared pool directly
        self._conn: Connection = await self._pool.acquire()  # Acquire a connection from the pool
        return self
        # return self._conn  # Returning the acquired connection

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

    async def execute_prepared(self, query: str, *args) -> list[HistoricalUNSEvent]:
        """
        Executes a prepared query to fetch historical events.

        Args:
            query (str): The SQL query to execute.
            *args: Query parameters.

        Returns:
            List[HistoricalUNSEvent]: List of historical events.

        Raises:
            asyncpg.PostgresError: If there's an error executing the prepared statement.
        """
        try:
            if self._conn is None or self._conn.is_closed():
                self._conn = await self.get_shared_pool().acquire()
            stmt: PreparedStatement = await self._conn.prepare(query)
            results = await stmt.fetch(*args)
            # Mapping logic
            # time TIMESTAMPTZ -> HistoricalUNSEvent.timestamp
            # topic text  -> HistoricalUNSEvent.topic
            # client_id text -> HistoricalUNSEvent.publisher
            # mqtt_msg JSONB -> HistoricalUNSEvent.payload
            # important to obscure the database details like column name in the output from a security perspective
            return [
                HistoricalUNSEvent(
                    timestamp=row["time"], topic=row["topic"], publisher=row["client_id"], payload=JSONPayload(row["mqtt_msg"])
                )
                for row in results
            ]
        except asyncpg.PostgresError as ex:
            LOGGER.error(f"Error executing prepared statement: {ex}")
            raise
        finally:
            # Ensure that the connection is released back to the pool
            if self._conn and not self._conn.is_closed():
                await self._shared_pool.release(self._conn)

    async def get_historic_events(
        self,
        topics: Optional[list[str]],
        publishers: Optional[list[str]],
        from_datetime: Optional[datetime],
        to_datetime: Optional[datetime],
    ) -> list[HistoricalUNSEvent]:
        """
        Retrieves historical events based on specified criteria.

        Args:
            topics (List[str]): List of topics.
            publishers (List[str]): List of publishers.
            from_datetime (datetime): Start date/time.
            to_datetime (datetime): End date/time.

        Returns:
            List[HistoricalUNSEvent]: List of historical events.

        Raises:
            asyncpg.PostgresError: If there's an error fetching historical events.
        """
        # check that at least one criteria is provided
        if topics is None and publishers is None and from_datetime is None and to_datetime is None:
            raise ValueError("At least one criteria for fetching historic events needs to be provided")

        # create the query
        # no risk of SQL injection because the input parameters have either been validated
        # or directly computed in this function, and we are using a prepared statement

        base_query: str = f"SELECT time, topic, client_id, mqtt_msg FROM {HistorianConfig.table} WHERE"  # noqa: S608
        conditions: list[str] = []
        query_params: list[list[str] | datetime] = []
        param_index = 1
        if topics:
            # if topics is not null we need to convert all MQTT wild cards to postgres wildcards
            query_params.append([UnsMQTTClient.get_regex_for_topic_with_wildcard(topic) for topic in topics])

            # convert the topics wild cards into regex to be used with SIMILAR instead of LIKE
            # conditions.append(f"( topic SIMILAR TO ANY (SELECT * FROM UNNEST( ${param_index}::text[]) ) ")
            conditions.append(f"( topic ~  ANY (  ${param_index}  ) ) ")
            param_index = param_index + 1

        if publishers:
            conditions.append(f"( client_id ~ ANY ( ${param_index} ) )")
            query_params.append(publishers)
            param_index = param_index + 1

        if from_datetime:
            conditions.append(f"( time >= ${param_index} ) ")
            query_params.append(from_datetime)
            param_index = param_index + 1

        if to_datetime:
            conditions.append(f"( time <= ${param_index} )  ")
            query_params.append(to_datetime)
            param_index = param_index + 1

        full_query: str = f"{base_query} {' AND '.join(conditions)}"
        LOGGER.debug(f"Query: {full_query} \n Params; {query_params}")

        return await self.execute_prepared(full_query, *query_params)
