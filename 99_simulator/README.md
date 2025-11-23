# UNS Simulator (99_simulator)

A lightweight MQTT device simulator used to generate synthetic device data for the Unified Namespace (UNS) project. Use this module to exercise MQTT consumers (graphdb, historian, Kafka bridge, SparkplugB mappers, etc.) with configurable device/metric payloads.

Features

- Configurable device templates and randomized metric values
- Publishes messages to MQTT broker(s) using settings from conf/settings.yaml
- Simple CLI entrypoint to run the simulator locally
- Unit tests under test/

Repository layout

- conf/
  - settings.yaml — main runtime configuration ([conf/settings.yaml](conf/settings.yaml))
  - .secrets_template.yaml — template for secrets ([conf/.secrets_template.yaml](conf/.secrets_template.yaml))
- src/uns_simulator/
  - config.py — configuration loader ([src/uns_simulator/config.py](src/uns_simulator/config.py))
  - devices.py — device template / helper functions ([src/uns_simulator/devices.py](src/uns_simulator/devices.py))
  - models.py — data models used by the simulator ([src/uns_simulator/models.py](src/uns_simulator/models.py))
  - simulator.py — core simulator implementation ([src/uns_simulator/simulator.py](src/uns_simulator/simulator.py))
  - main.py — CLI / entrypoint ([src/uns_simulator/main.py](src/uns_simulator/main.py))
- test/ — unit tests ([test/](test/))

Quick start (development)

1. Install and prepare the development venv (the repository uses the uv wrapper like other modules):

   ```bash
   python -m pip install --upgrade pip uv
   uv venv
   uv sync
   ```

2. Configure the simulator
   - Copy conf/.secrets_template.yaml -> conf/.secrets.yaml and fill any secrets required.
   - Edit [conf/settings.yaml](conf/settings.yaml) to point to your MQTT broker and tune simulator options.

3. Run locally
   - From the module folder (99_simulator) activate the venv and run:

   ```bash
   uv venv
   uv sync
   uv run uns_simulator
   ```

   - The module entrypoint is provided in `uns_simulator.main`.

Core code pointers

- Entrypoint / CLI: `uns_simulator.main`
- Simulator implementation: `uns_simulator.simulator.Simulator`
- Device templates & helpers: `uns_simulator.devices`
- Config loader: `uns_simulator.config`
- Models: `uns_simulator.models`

Configuration notes

- MQTT settings are loaded from conf/settings.yaml and secrets from conf/.secrets.yaml (based on the provided template).
- Typical keys:
  - mqtt.host (required)
  - mqtt.port (default 1883)
  - mqtt.transport ("tcp" or "websockets")
  - simulator.\* — device_count, publish_interval, device templates

Running tests

- Run unit tests (exclude integration tests):

  ```bash
  uv run pytest -m "not integrationtest" test/
  ```
