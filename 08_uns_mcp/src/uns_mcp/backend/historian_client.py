"""Historian Client with health checking."""

import logging
from datetime import datetime
from typing import Any

import asyncpg
from asyncpg import Pool
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_mcp.config import HistorianConfig

LOGGER = logging.getLogger(__name__)


class HistorianClient:
    """Async client for TimescaleDB with connection pooling."""

    def __init__(self):
        self.pool: Pool | None = None

    async def connect(self) -> None:
        """Establish connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=HistorianConfig.hostname,
                port=HistorianConfig.port or 5432,
                user=HistorianConfig.db_user,
                password=HistorianConfig.db_password,
                database=HistorianConfig.database,
                ssl=HistorianConfig.get_ssl_context(),
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            LOGGER.info(
                f"Connected to Historian at {HistorianConfig.hostname}")
        except asyncpg.PostgresError as e:
            LOGGER.error(f"Failed to connect to Historian: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            try:
                await self.pool.close()
                LOGGER.info("Historian connection closed")
            except Exception as e:
                LOGGER.error(f"Error closing Historian: {e}")
            finally:
                self.pool = None

    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')  # cSpell:ignore fetchval
            return True
        except Exception:
            return False

    async def get_historic_events(
        self, topics: list[str], from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Query historical events."""
        if not self.pool:
            raise ValueError("Historian client not connected")

        topic_patterns = [UnsMQTTClient.get_regex_for_topic_with_wildcard(
            topic) for topic in topics]

        conditions = [f"topic ~ ANY(${1})"]
        params = [topic_patterns]
        param_idx = 2

        if from_datetime:
            conditions.append(f"time >= ${param_idx}")
            params.append(from_datetime)
            param_idx += 1

        if to_datetime:
            conditions.append(f"time <= ${param_idx}")
            params.append(to_datetime)

        # Using parameterized query to prevent SQL injection
        query = f"""
        SELECT time, topic, client_id, mqtt_msg
        FROM {HistorianConfig.table}
        WHERE {' AND '.join(conditions)}
        ORDER BY time DESC
        LIMIT 1000
        """  # noqa: S608

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            {
                "timestamp": row["time"],
                "topic": row["topic"],
                "publisher": row["client_id"],
                "payload": row["mqtt_msg"]
            }
            for row in rows
        ]

    async def get_historic_events_by_property(
        self, property_keys: list[str], binary_operator: str = "OR",
        topics: list[str] | None = None, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Query events by property."""
        if not self.pool:
            raise ValueError("Historian client not connected")

        conditions = []
        params = []
        param_idx = 1

        if topics:
            topic_patterns = [UnsMQTTClient.get_regex_for_topic_with_wildcard(
                topic) for topic in topics]
            conditions.append(f"topic ~ ANY(${param_idx})")
            params.append(topic_patterns)
            param_idx += 1

        if from_datetime:
            conditions.append(f"time >= ${param_idx}")
            params.append(from_datetime)
            param_idx += 1

        if to_datetime:
            conditions.append(f"time <= ${param_idx}")
            params.append(to_datetime)
            param_idx += 1

        property_conditions = []
        for key in property_keys:
            property_conditions.append(
                f"jsonb_path_exists(mqtt_msg, ${param_idx})")
            params.append(f'$.**"{key}"')
            param_idx += 1

        if binary_operator == "NOT":
            conditions.append(f"NOT ({' OR '.join(property_conditions)})")
        else:
            conditions.append(
                f"({f' {binary_operator} '.join(property_conditions)})")

        # Using parameterized query to prevent SQL injection
        query = f"""
        SELECT time, topic, client_id, mqtt_msg
        FROM {HistorianConfig.table}
        WHERE {' AND '.join(conditions)}
        ORDER BY time DESC
        LIMIT 1000
        """  # noqa: S608

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            {
                "timestamp": row["time"],
                "topic": row["topic"],
                "publisher": row["client_id"],
                "payload": row["mqtt_msg"]
            }
            for row in rows
        ]
