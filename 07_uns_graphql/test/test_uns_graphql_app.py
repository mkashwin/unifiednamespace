import pytest
import pytest_asyncio
from uns_graphql.uns_graphql_app import UNSGraphql


def test_uns_graphql_app_attributes():
    """
    Test validity of key attributes of  UNSGraphql needed to start run the GraphQL server
    """
    assert UNSGraphql.schema is not None
    assert UNSGraphql.app is not None
