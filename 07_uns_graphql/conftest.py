import os
import pytest
import sys

def pytest_collection_modifyitems(config, items):
    """
    Dynamically add xdist_group marker to graphql tests unless running in VSCode discovery
    or running individually.
    """
    # Check if we should skip adding the marker
    is_vscode = "VSCODE_PID" in os.environ
    if config.getoption("--collect-only") and is_vscode:
        return

    # If running individually (or small subset), xdist grouping is not needed and might cause overhead/issues
    if len(items) <= 1:
        return

    # Mapping of test functions to their xdist group names
    group_mapping = {
        "test_get_historic_events": "graphql_historian",
        "test_get_historic_events_for_property_keys": "graphql_historian",
        "test_get_uns_nodes_integration": "graphql_graphdb",
        "test_get_uns_nodes_by_property_integration": "graphql_graphdb",
        "test_get_spb_nodes_integration": "graphql_graphdb",
        "test_get_kafka_messages_integration": "graphql_kafka_1",
    }

    for item in items:
        # Check if the item belongs to the relevant test functions
        # item.name might include parametrization, so we check if it starts with the key
        # Also check item.originalname for parametrized tests
        func_name_in_item = item.originalname if hasattr(item, 'originalname') else item.name

        # Fallback to name if originalname is None (sometimes happens)
        if func_name_in_item is None:
            func_name_in_item = item.name

        for func_name, group_name in group_mapping.items():
            if func_name_in_item == func_name or item.name.startswith(func_name):
                item.add_marker(pytest.mark.xdist_group(name=group_name))
                break
