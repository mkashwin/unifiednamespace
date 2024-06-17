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

# Fixture to handle event loop
import asyncio

import pytest
import pytest_asyncio
from uns_historian.historian_handler import HistorianHandler


@pytest.fixture(scope="session")
def my_event_loop(request):  # noqa: ARG001
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def historian_pool(my_event_loop):  # noqa: ARG001
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianHandler.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianHandler.close_pool()
