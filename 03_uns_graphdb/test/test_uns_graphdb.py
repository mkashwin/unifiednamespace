import inspect
import os
import sys
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_graphdb"))

from uns_graphdb.uns_mqtt_graphdb import Uns_MQTT_GraphDb

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_graphdb.username")))


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_Uns_MQTT_GraphDb():
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = Uns_MQTT_GraphDb()
        assert uns_mqtt_graphdb is not None, "Connection to either the MQTT Broker or the Graph DB did not happen"
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
        )
    finally:
        if (uns_mqtt_graphdb is not None):
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()
