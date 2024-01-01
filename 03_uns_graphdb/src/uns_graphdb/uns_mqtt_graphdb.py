"""
MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the GraphDB
"""
import logging
import random
import time

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphdb.graphdb_config import GraphDBConfig, MQTTConfig
from uns_graphdb.graphdb_handler import GraphDBHandler

LOGGER = logging.getLogger(__name__)


class UnsMqttGraphDb:
    # pylint: disable=too-many-instance-attributes
    """
    Class instantiating MQTT listener that listens to ISA-95 UNS and SparkplugB and
    persists all messages to the GraphDB
    """

    def __init__(self):
        self.graph_db_handler = None
        self.uns_client: UnsMQTTClient = None
        self.client_id = f"graphdb-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.version,
            transport=MQTTConfig.transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        # Connect to the database
        self.graph_db_handler = GraphDBHandler(uri=GraphDBConfig.db_url,
                                               user=GraphDBConfig.user,
                                               password=GraphDBConfig.password,
                                               database=GraphDBConfig.database)

        self.uns_client.run(host=MQTTConfig.host,
                            port=MQTTConfig.port,
                            username=MQTTConfig.username,
                            password=MQTTConfig.password,
                            tls=MQTTConfig.tls,
                            keepalive=MQTTConfig.keepalive,
                            topics=MQTTConfig.topics,
                            qos=MQTTConfig.qos)

    # end of init

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{"
                     "Client: %s,"
                     "Userdata: %s,"
                     "Message: %s,"
                     "}", str(client), str(userdata), str(msg))
        try:
            if msg.topic.startswith(UnsMQTTClient.SPARKPLUG_NS):
                node_types = GraphDBConfig.spb_node_types
            else:
                node_types = GraphDBConfig.uns_node_types
            # get the payload as a dict object
            filtered_message = self.uns_client.get_payload_as_dict(
                topic=msg.topic,
                payload=msg.payload,
                mqtt_ignored_attributes=MQTTConfig.ignored_attributes)

            # save message
            self.graph_db_handler.persist_mqtt_msg(
                topic=msg.topic,
                message=filtered_message,
                timestamp=filtered_message.get(MQTTConfig.timestamp_key,
                                               time.time()),
                node_types=node_types,
                attr_node_type=GraphDBConfig.nested_attributes_node_type)
        except SystemError as system_error:
            LOGGER.error(
                "Fatal Error while parsing Message: %s\nTopic: %s \nMessage:%s\nExiting.........",
                str(system_error),
                msg.topic,
                msg.payload,
                stack_info=True,
                exc_info=True)

        except Exception as ex:
            # pylint: disable=broad-exception-caught
            LOGGER.error(
                "Error persisting the message to the Graph DB: %s \nTopic: %s \nMessage:%s",
                str(ex),
                msg.topic,
                msg.payload,
                stack_info=True,
                exc_info=True)

    # end of on_message----------------------------------------------------------------------------

    def on_disconnect(
            self,
            client,  # noqa: ARG002
            userdata,  # noqa: ARG002
            result_code,
            properties=None):  # noqa: ARG002
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # pylint: disable=unused-argument
        if result_code != 0:
            LOGGER.error("Unexpected disconnection.:%s",
                         str(result_code),
                         stack_info=True,
                         exc_info=True)

    # end of on_disconnect-------------------------------------------------------------------------


# end of class ------------------------------------------------------------------------------------
def main():
    """
    Main function invoked from command line
    """
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = UnsMqttGraphDb()
        uns_mqtt_graphdb.uns_client.loop_forever()
    finally:
        if uns_mqtt_graphdb is not None:
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


# end of main()------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
