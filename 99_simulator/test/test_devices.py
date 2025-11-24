import json
import random

import pytest

# Import the module under test
from uns_simulator import devices


# Dummy replacements to avoid external dependencies and network I/O
class DummyClient:
    # trunk-ignore(ruff/ARG002)
    def __init__(self, *args, **kwargs):
        self.published = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    # trunk-ignore(ruff/ARG002)
    async def publish(self, topic, payload, *args, **kwargs):
        # store topic and parsed payload for assertions
        try:
            parsed = json.loads(payload)
        except Exception:
            parsed = payload
        self.published.append((topic, parsed))
        return True


class DummyEquipment:
    def __init__(self, name, sensors):
        self.name = name
        self.sensors = sensors


class FakeHierarchy:
    def get_parameter_topic(self, equipment, param_type, param_name):
        # simple deterministic topic for assertions
        return f"factory/{equipment}/{getattr(param_type, '__name__', str(param_type))}/{param_name}"


@pytest.fixture(autouse=True)
def patch_mqtt_and_models(monkeypatch):
    # Patch aiomqtt.Client used inside devices module
    # ensure attribute exists
    monkeypatch.setattr(devices, "aiomqtt", devices.aiomqtt)
    monkeypatch.setattr(devices, "Equipment", DummyEquipment)
    # replace the Client class used by AsyncMQTTDevice with DummyClient factory
    monkeypatch.setattr(devices.aiomqtt, "Client", DummyClient)
    yield


@pytest.mark.asyncio
async def test_publish_parameter_enriches_and_publishes():
    hierarchy = FakeHierarchy()
    mqtt_conf = {}
    # Create a PLC instance but we will call publish_parameter directly
    plc = devices.PLC("T1", hierarchy, mqtt_conf, equipment_config={
                      "name": "Boiler1", "sensors": {}})
    # Replace instance client with our DummyClient (constructed by patched aiomqtt.Client)
    plc.client = DummyClient()

    payload = {"value": 42}
    ok = await plc.publish_parameter("Boiler1", devices.ParameterType, "Temp", payload)
    assert ok is True
    # ensure one publish recorded
    assert len(plc.client.published) == 1
    topic, published_payload = plc.client.published[0]
    assert "factory/Boiler1" in topic
    # enriched fields present
    assert published_payload["value"] == 42
    assert published_payload["source"] == plc.device_id
    assert published_payload["equipment"] == "Boiler1"
    assert "timestamp" in published_payload


@pytest.mark.asyncio
async def test_plc_generate_sensor_status_and_alarm(monkeypatch):
    hierarchy = FakeHierarchy()
    mqtt_conf = {}

    sensors_cfg = {
        "Temp": {"base_value": 75.0, "variation": 2.0, "unit": "F"},
        "Pressure": {"base_value": 30.0, "variation": 1.0, "unit": "psi"},
    }

    # Patch random functions for deterministic outputs
    monkeypatch.setattr(random, "uniform", lambda a, b: (a + b) / 2.0)
    # ensure no alarm triggered by setting random.random to a value > 0.05 for sensor/status generation
    monkeypatch.setattr(random, "random", lambda: 0.5)
    # ensure deterministic randint used for operating_hours initial value
    monkeypatch.setattr(random, "randint", lambda a, _b: a)

    plc = devices.PLC("T2", hierarchy, mqtt_conf, equipment_config={
                      "name": "Unit1", "sensors": sensors_cfg})
    # Test sensor data generation
    sensors = await plc.generate_sensor_data()
    assert isinstance(sensors, list)
    assert any(s["param_name"] == "Temp" for s in sensors)
    assert any(s["param_name"] == "Pressure" for s in sensors)
    for m in sensors:
        assert "data" in m and "value" in m["data"] and "unit" in m["data"]

    # Test status data
    status = await plc.generate_status_data()
    assert status["param_type"] == devices.ParameterType.STATUS
    assert status["param_name"] == "EquipmentStatus"
    assert "operational" in status["data"]

    # Force alarm by returning a small random()
    monkeypatch.setattr(random, "random", lambda: 0.01)
    # deterministic choice and randint for alarm id
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", lambda _a, _b: 1234)

    alarm = await plc.generate_alarm_data()
    assert alarm is not None
    assert alarm["param_type"] == devices.ParameterType.ALARM
    assert alarm["param_name"] == "ActiveAlarms"
    assert "alarms" in alarm["data"]
    assert alarm["data"]["alarms"][0]["id"].startswith("ALM_")
    assert alarm["data"]["alarms"][0]["acknowledged"] is False


@pytest.mark.asyncio
async def test_hmi_operator_actions_and_publish(monkeypatch):
    hierarchy = FakeHierarchy()
    mqtt_conf = {}
    # Make HMI generate an action by forcing random.random < 0.3
    monkeypatch.setattr(random, "random", lambda: 0.1)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", lambda _a, _b: 1)
    monkeypatch.setattr(random, "uniform", lambda a, b: (a + b) / 2.0)

    hmi = devices.HMI("01", hierarchy, mqtt_conf)
    # replace client with DummyClient to capture publishes
    hmi.client = DummyClient()

    actions = await hmi.generate_operator_actions()
    assert "actions" in actions
    # If actions list non-empty, ensure publish_parameter works
    if actions["actions"]:
        ok = await hmi.publish_parameter("HMI", devices.ParameterType, "OperatorActions", actions)
        assert ok is True
        assert len(hmi.client.published) == 1
        _, payload = hmi.client.published[0]
        assert payload["workstation_id"] == hmi.device_id


@pytest.mark.asyncio
async def test_scada_system_status_sync():
    hierarchy = FakeHierarchy()
    mqtt_conf = {}
    scada = devices.SCADA(hierarchy, mqtt_conf, system_name="TestSCADA")
    # generate_system_status is async in implementation; call via asyncio.run if needed
    status = await scada.generate_system_status()
    assert isinstance(status, dict)
    expected_keys = {"system_name", "system_status", "connected_devices", "data_points_per_second",
                     "system_uptime_hours", "cpu_usage_percent", "memory_usage_percent", "alarms_active", "version"}
    assert expected_keys.issubset(set(status.keys()))
    assert status["system_name"] == "TestSCADA"
