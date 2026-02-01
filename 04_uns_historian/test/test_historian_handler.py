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

Test cases for historian_handler
"""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest

from uns_historian.historian_config import HistorianConfig
from uns_historian.historian_handler import HistorianHandler


@pytest.fixture(scope="function")
def mock_asyncpg():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Mock asyncpg module and its functions)
    with patch("asyncpg.create_pool") as create_pool_mock:
        create_pool_mock.return_value = asyncio.Future()
        pool_instance = AsyncMock(spec=asyncpg.Pool)
        pool_instance.is_closing.return_value = False
        create_pool_mock.return_value.set_result(pool_instance)

        yield create_pool_mock
    loop.close()


@pytest.mark.asyncio(loop_scope="function")
async def test_shared_pool(mock_asyncpg):
    """
    @FIXME This test is executing fine individually but fails when run in the test suite with xdist
    work around is to run the test with -n 4
    """
    pool1 = await HistorianHandler.get_shared_pool()
    pool2 = await HistorianHandler.get_shared_pool()

    assert pool1 is pool2
    mock_asyncpg.assert_called_once()

    # Clean up the shared pool so subsequent tests don't use the mock
    await HistorianHandler.close_pool()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integrationtest
@pytest.mark.xdist_group(name="uns_historian")
@pytest.mark.parametrize(
    "timestamp, topic, publisher, message, is_error",
    [
        (1701232000, "a/b/c", "client1", {"key1": "value1"}, False),
        (1701234000, "topic1", "client2", {"key2": "value2", "key3": 10}, False),
        # if timestamp not provided, current time should be used
        (None, "topic2", "client3", {"key4": "value4"}, False),
        # Topic cant be null
        (1701234600, None, "client3", {"key4": "value4"}, True),
        (1701234700, "topic3", "client4", "I am not a json dict", False),
        (1701234800, "topic4", "client5", 1234, False),
    ],
)
async def test_persist_mqtt_msg(
    timestamp: float,
    topic: str,
    publisher: str,
    message: dict,
    is_error: bool,
):
    # persist the data
    current_time = datetime.now(UTC)
    try:
        async with HistorianHandler() as uns_historian_writer:
            result = await uns_historian_writer.persist_mqtt_msg(
                client_id=publisher,
                topic=topic,
                timestamp=timestamp,
                message=message,
            )
        assert result is not None, "Should have gotten a result"
        assert len(result) == 1, "Should have gotten only one record because we inserted only one record"
        if timestamp is None:
            # since getting the exact timestamp in the function is difficult.
            # We check if the timestamp is greater or equal to the current timestamp recorded while entering this function
            # accounting for some processing time
            assert current_time <= result[0]["time"]
        else:
            # check for timestamp considering the  precision change done from milliseconds to microseconds
            assert timestamp / 1000 == result[0]["time"].timestamp(), "timestamps did not match"

        assert topic == result[0]["topic"], "topic stored is not what was received"
        result[0]["client_id"], "client_id stored is not what was received"
        result[0]["mqtt_msg"], "message payload  stored is not what was received"

    except asyncpg.PostgresError as ex:
        if is_error:
            assert True  # Error was expected because of incorrect params
        else:
            pytest.fail(f"Exception occurred while persisting Exception {ex}")
    finally:
        if not is_error:  # clean up only in the insert was successful
            async with HistorianHandler() as uns_historian_handler_cleaner:
                delete_sql_cmd = f""" DELETE FROM {HistorianConfig.table} WHERE
                                        topic = $1 AND
                                        client_id = $2 AND
                                        mqtt_msg = $3
                                        RETURNING *;"""  # noqa: S608
                # dont compare timestamps as when the timestamp is None, current time is inserted.
                await uns_historian_handler_cleaner.execute_prepared(delete_sql_cmd, *[topic, publisher, json.dumps(message)])


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integrationtest
@pytest.mark.xdist_group(name="uns_historian")
@pytest.mark.parametrize(
    "query, params, is_error",
    [
        (f"SELECT * from {HistorianConfig.table};", [], False),  # noqa: S608
        (
            f"INSERT INTO {HistorianConfig.table} ( time, topic, client_id, mqtt_msg ) VALUES ($1,$2,$3,$4) RETURNING *;",  # noqa: S608
            [datetime.fromtimestamp(1701232000, UTC), "a/b/c", "historian_test_client1", '{"key1": "value1"}'],
            False,
        ),
        (
            f"DELETE FROM {HistorianConfig.table} WHERE client_id=$1 RETURNING *;",  # noqa: S608
            ["historian_test_client1"],
            False,
        ),
        (
            f"SELECT * from {HistorianConfig.table} WHERE time <= $1;",  # noqa: S608
            [datetime.fromtimestamp(1701232000, UTC)],
            False,
        ),
        (
            f"SELECT * from {HistorianConfig.table} WHERE client_id = $1;",  # noqa: S608
            ["client_1"],
            False,
        ),
        (
            f"SELECT * from {HistorianConfig.table} WHERE client_id = $1;",  # noqa: S608
            [
                ";SELECT * from NONE_EXISTENT_TABLE;"
            ],  # attempt SQL insertion should not result in that being executed. i,e error cause pg_stat doesn't exist
            False,
        ),
        (
            f"SELECT * from {HistorianConfig.table} WHERE time <= $1;",  # noqa: S608
            ["I am not a Timestamp"],
            True,
        ),
    ],
)
async def test_execute_prepared(
    historian_pool,  # noqa: ARG001 fixture defined in ./conftest.py
    query: str,
    params: list,
    is_error: bool,
):
    try:
        async with HistorianHandler() as uns_historian_handler:
            result = await uns_historian_handler.execute_prepared(query, *params)
            assert result is not None
    except asyncpg.PostgresError as ex:
        if is_error:
            assert True  # Error was expected because of incorrect params
        else:
            pytest.fail(f"Exception occurred while persisting Exception {ex}")
