
import inspect
import os
import sys
import time
import paho.mqtt.client as mqtt_client
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(
                inspect.getfile(inspect.currentframe()))[0],
            '..', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
from uns_mqtt.mqtt_listner import UNS_MQTT_Listener

DEFAULT_HOST = "broker.emqx.io" # test the client against the hosted broker
DEFAULT_PORT = 1883 # 
DEFAULT_TOPIC = "test/uns/#" # as the hosted broker doesn't allow subscription to # 
DEFAULT_QOS = 1 # Default value is 1. Recommend 1 or 2. Do not use 0
keep_alive = 60
reconnect_on_failure = True

def test_01_defaults():
    uns_client = UNS_MQTT_Listener("test_01")

    try :
        uns_client.run(DEFAULT_HOST,DEFAULT_PORT, keep_alive ,DEFAULT_TOPIC,DEFAULT_QOS)
        uns_client.loop()
        time.sleep(20)
        assert uns_client.protocol == mqtt_client.MQTTv5,  "Default protocol should be MQTTv5"
        assert uns_client.connected_flag == True , "Client should have connected "
    finally:
        uns_client.loop_stop()
