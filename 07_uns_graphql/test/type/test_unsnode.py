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

Unit tests for UNSNode class
"""

from collections import Counter
from datetime import datetime, timedelta

from uns_graphql.type.basetype import JSONPayload
from uns_graphql.type.isa95_node import UNSNode

"""Test cases for UNSNode equality comparison"""


def test_equal_nodes_with_same_identity():
    """Two nodes with same namespace, node_type, and node_name should be equal"""
    now = datetime.now()
    payload1 = JSONPayload({"temp": 25})
    payload2 = JSONPayload({"temp": 30})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload1,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload2,  # Different payload
        created=now - timedelta(hours=1),  # Different timestamps
        last_updated=now
    )

    assert node1 == node2


def test_not_equal_different_namespace():
    """Nodes with different namespaces should not be equal"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area2/sensor1",  # Different namespace
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 != node2


def test_not_equal_different_node_type():
    """Nodes with different node_type should not be equal"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="LINE",  # Different node_type
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 != node2


def test_not_equal_different_node_name():
    """Nodes with different node_name should not be equal"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor2",  # Different node_name
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 != node2


def test_equality_with_non_uns_node_object():
    """Comparing with non-UNSNode object should return NotImplemented/False"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node != "not a node"
    assert node != 123
    assert node is not None
    assert node != {"namespace": "ent1/fac1/area1/sensor1"}


def test_reflexive_equality():
    """A node should be equal to it"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node == node


def test_symmetric_equality():
    """If a == b, then b == a"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert node2 == node1


def test_transitive_equality():
    """If a == b and b == c, then a == c"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node3 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert node2 == node3
    assert node1 == node3


"""Test cases for UNSNode hash functionality"""


def test_equal_nodes_have_same_hash():
    """Equal nodes must have the same hash value"""
    now = datetime.now()
    payload1 = JSONPayload({"temp": 25})
    payload2 = JSONPayload({"temp": 30})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload1,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload2,
        created=now - timedelta(hours=1),
        last_updated=now
    )

    assert hash(node1) == hash(node2)


def test_different_nodes_likely_different_hash():
    """Different nodes should (likely) have different hash values"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor2",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor2",
        payload=payload,
        created=now,
        last_updated=now
    )

    # While hash collisions are possible, different nodes should generally have different hashes
    assert hash(node1) != hash(node2)


def test_hash_consistency():
    """Hash value should be consistent across multiple calls"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    hash1 = hash(node)
    hash2 = hash(node)
    hash3 = hash(node)

    assert hash1 == hash2 == hash3


def test_node_usable_in_set():
    """UNSNode should be usable in a set"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=JSONPayload({"temp": 30}),  # Different payload
        created=now,
        last_updated=now
    )

    node3 = UNSNode(
        node_name="sensor2",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor2",
        payload=payload,
        created=now,
        last_updated=now
    )

    node_set = {node1, node2, node3}

    # node1 and node2 are equal, so set should only have 2 elements
    assert len(node_set) == 2
    assert node1 in node_set
    assert node2 in node_set
    assert node3 in node_set


def test_node_usable_in_dict():
    """UNSNode should be usable as dictionary key"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor2",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor2",
        payload=payload,
        created=now,
        last_updated=now
    )

    node_dict = {
        node1: "first sensor",
        node2: "second sensor"
    }

    assert node_dict[node1] == "first sensor"
    assert node_dict[node2] == "second sensor"
    assert len(node_dict) == 2


def test_node_usable_with_counter():
    """UNSNode should work with collections.Counter"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=now,
        last_updated=now
    )

    # Create duplicate node (same identity)
    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=JSONPayload({"temp": 30}),
        created=now,
        last_updated=now
    )

    node3 = UNSNode(
        node_name="sensor2",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor2",
        payload=payload,
        created=now,
        last_updated=now
    )

    nodes = [node1, node2, node1, node3, node2]
    counter = Counter(nodes)

    # node1 and node2 are equal, so they should be counted together
    # node1 appears 1 time, node2 appears 2 times, plus node1 again = 4
    assert counter[node1] == 4
    assert counter[node3] == 1


"""Test edge cases and special scenarios"""


def test_all_node_types():
    """Test that different ISA-95 node types work correctly"""
    now = datetime.now()
    payload = JSONPayload({"data": "test"})

    node_types = ["ENTERPRISE", "FACILITY", "AREA",
                  "LINE", "DEVICE", "NESTED_ATTRIBUTE"]
    nodes = []

    for i, node_type in enumerate(node_types):
        node = UNSNode(
            node_name=f"node{i}",
            node_type=node_type,
            namespace=f"namespace{i}",
            payload=payload,
            created=now,
            last_updated=now
        )
        nodes.append(node)

    # All nodes should be different
    assert len(set(nodes)) == len(nodes)


def test_empty_strings():
    """Test nodes with empty string values"""
    now = datetime.now()
    payload = JSONPayload({})

    node1 = UNSNode(
        node_name="",
        node_type="DEVICE",
        namespace="",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="",
        node_type="DEVICE",
        namespace="",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


def test_unicode_characters():
    """Test nodes with unicode characters in names"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="センサー1",
        node_type="DEVICE",
        namespace="企業/施設/エリア/センサー1",
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="センサー1",
        node_type="DEVICE",
        namespace="企業/施設/エリア/センサー1",
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


def test_special_characters_in_namespace():
    """Test nodes with special characters in namespace"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    node = UNSNode(
        node_name="sensor-1",
        node_type="DEVICE",
        namespace="ent1/fac_1/area.1/line#1/sensor-1",
        payload=payload,
        created=now,
        last_updated=now
    )

    # Should be hashable and usable in sets
    node_set = {node}
    assert node in node_set


def test_very_long_namespace():
    """Test nodes with very long namespace strings"""
    now = datetime.now()
    payload = JSONPayload({"temp": 25})

    long_namespace = "/".join([f"level{i}" for i in range(100)])

    node1 = UNSNode(
        node_name="sensor",
        node_type="DEVICE",
        namespace=long_namespace,
        payload=payload,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor",
        node_type="DEVICE",
        namespace=long_namespace,
        payload=payload,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


"""Test that timestamps don't affect equality or hashing"""


def test_different_created_timestamps():
    """Nodes with different created timestamps should be equal if identity is same"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=base_time,
        last_updated=base_time
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=base_time + timedelta(days=365),  # One year later
        last_updated=base_time
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


def test_different_last_updated_timestamps():
    """Nodes with different last_updated timestamps should be equal if identity is same"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    payload = JSONPayload({"temp": 25})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=base_time,
        last_updated=base_time
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload,
        created=base_time,
        last_updated=base_time + timedelta(hours=5)
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


"""Test that different payloads don't affect equality or hashing"""


def test_different_payload_data():
    """Nodes with different payload data should be equal if identity is same"""
    now = datetime.now()

    payload1 = JSONPayload({"temp": 25, "humidity": 60})
    payload2 = JSONPayload({"temp": 30, "humidity": 70, "pressure": 1013})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload1,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload2,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)


def test_empty_vs_populated_payload():
    """Node with empty payload should equal node with populated payload if identity is same"""
    now = datetime.now()

    payload1 = JSONPayload({})
    payload2 = JSONPayload(
        {"temp": 25, "humidity": 60, "status": "active"})

    node1 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload1,
        created=now,
        last_updated=now
    )

    node2 = UNSNode(
        node_name="sensor1",
        node_type="DEVICE",
        namespace="ent1/fac1/area1/sensor1",
        payload=payload2,
        created=now,
        last_updated=now
    )

    assert node1 == node2
    assert hash(node1) == hash(node2)
