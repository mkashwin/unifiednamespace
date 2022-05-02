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
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_historian"))

from uns_historian.uns_mqtt_historian import Uns_Mqtt_Historian

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_historian.username")))


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_Uns_Mqtt_Historian():
    uns_mqtt_historian = None
    try:
        uns_mqtt_historian = Uns_Mqtt_Historian()
        assert uns_mqtt_historian is not None, "Connection to either the MQTT Broker or the Historian DB did not happen"
    finally:
        if (uns_mqtt_historian is not None):
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):

            uns_mqtt_historian.uns_historian_handler.close()
