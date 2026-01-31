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

import os

import pytest
import pytest_asyncio

from uns_historian.historian_handler import HistorianHandler


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def historian_pool():
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianHandler.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianHandler.close_pool()


def pytest_collection_modifyitems(config, items):
    """
    Dynamically add xdist_group marker to uns_historian tests unless running in VSCode discovery
    or running individually.
    """
    # Check if we should skip adding the marker
    is_vscode = "VSCODE_PID" in os.environ
    if config.getoption("--collect-only") and is_vscode:
        return

    # If running individually (or small subset), xdist grouping is not needed and might cause overhead/issues
    if len(items) <= 1:
        return

    for item in items:
        # Check if the item belongs to the relevant test functions
        if item.name.startswith("test_persist_mqtt_msg") or item.name.startswith("test_execute_prepared"):
            item.add_marker(pytest.mark.xdist_group(name="uns_historian"))
