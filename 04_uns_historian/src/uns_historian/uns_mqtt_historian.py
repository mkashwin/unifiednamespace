import inspect
import random
import logging
import re
import time
import os
import sys
# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', '..', '02_mqtt-cluster', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

from config import settings
from historian_handler import HistorianHandler
from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper

LOGGER = logging.getLogger(__name__)


class Uns_Mqtt_Historian:

    def __init__(self):
        self.load_mqtt_configs()
        self.load_historian_config()
        self.uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)
        ## Connect to the database
        self.uns_historian_handler = HistorianHandler(
                                            hostname = self.historian_hostname,
                                            port = self.historian_port,
                                            database = self.historian_database,
                                            table = self.historian_table,
                                            user = self.historian_user,
                                            password = self.historian_password,
                                            sslmode = self.historian_sslmode)
        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.uns_client.run(host=self.mqtt_host,
                            port=self.mqtt_port,
                            username=self.mqtt_username,
                            password=self.mqtt_password,
                            tls=self.mqtt_tls,
                            keepalive=self.mqtt_keepalive,
                            topic=self.topic,
                            qos=self.mqtt_qos)

    def load_mqtt_configs(self):
        # generate client ID with pub prefix randomly
        self.client_id = f'historian-{time.time()}-{random.randint(0, 1000)}'

        self.mqtt_transport: str = settings.get("mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", Uns_MQTT_ClientWrapper.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 1)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: str = settings.mqtt["host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: str = settings.mqtt["username"]
        self.mqtt_password: str = settings.mqtt["password"]
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topic: str = settings.get("mqtt.topic", "#")
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
        if (self.mqtt_host is None):
            raise ValueError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'"
            )

    def load_historian_config(self):
        """ 
        Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
        """
        self.historian_hostname: str = settings.historian["hostname"]
        self.historian_port: int = settings.get("historian.port", None)
        self.historian_user: str = settings.historian["username"]
        self.historian_password: str = settings.historian["password"]
        self.historian_sslmode: str = settings.get("historian.sslmode", None)

        self.historian_database: str = settings.historian["database"]

        self.historian_table: str = settings.historian["table"]

        if (self.historian_hostname is None):
            raise ValueError(
                "Historian Url not provided. Update key 'historian.hostname' in '../../conf/settings.yaml'"
            )
        if (self.historian_database is None):
            raise ValueError(
                "Historian Database name  not provided. Update key 'historian.database' in '../../conf/settings.yaml'"
            )
        if (self.historian_table is None):
            raise ValueError(
                f"Table in Historian Database {self.historian_database} not provided. Update key 'historian.table' in '../../conf/settings.yaml'"
            )
        if ((self.historian_user is None)
                or (self.historian_password is None)):
            raise ValueError(
                "Historian DB  Username & Password not provided."
                "Update keys 'historian.username' and 'historian.password' in '../../conf/.secrets.yaml'"
            )

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber  
        """
        LOGGER.debug("{"
                     f"Client: {client},"
                     f"Userdata: {userdata},"
                     f"Message: {msg},"
                     "}")
        
        try:
            _message = msg.payload.decode("utf-8")
            self.filter_ignored_attributes(msg.topic,_message,self.mqtt_ignored_attributes) 
            ## save message
            self.uns_historian_handler.persistMQTTmsg(
                client_id = getattr(client,"_client_id"),
                topic=msg.topic,
                timestamp=getattr(_message, self.mqtt_timestamp_key, time.time()),
                message= _message
                )
        except Exception as ex:
            LOGGER.error(
                "Error persisting the message to the Historian DB: %s",
                str(ex),
                stack_info=True,
                exc_info=True)
            raise ex
    
    def on_disconnect(self, client, userdata, rc, properties=None):
        # Close the database connection when the MQTT broker gets disconnected
        if self.uns_historian_handler is not None:
            self.uns_historian_handler.close()
            self.uns_historian_handler = None
        if (rc != 0):
            LOGGER.error("Unexpected disconnection.:%s",str(rc),stack_info=True,exc_info=True)    
     
    @staticmethod
    def filter_ignored_attributes(topic:str, mqtt_message:dict, mqtt_ignored_attributes):
        """
        removed the attributes configured to be ignored in the mqtt message and topic
        """
        if (mqtt_ignored_attributes is not None) :
            message = mqtt_message
            for topic_key in mqtt_ignored_attributes :
                # Match Topic in ignored list with current topic and fetch associated ignored attributes

                ignored_topic = topic_key
                if (Uns_Mqtt_Historian.isTopicMatching(ignored_topic,topic)) :
                    # This could be either a single string or a list of strings
                    ignored_attr_list = mqtt_ignored_attributes.get(ignored_topic,[])

                    ignored_attr = None
                    # if the attribute is a single key.  
                    # But this could be a nested key e.g. parent_key.child_key so split that into a list 
                    if(type(ignored_attr_list) is str):
                        Uns_Mqtt_Historian.del_key_from_dict(message, ignored_attr_list.split("."))
                    # if the attribute is a list of keys  
                    elif(type(ignored_attr_list) is list): 
                        for ignored_attr in ignored_attr_list :
                            Uns_Mqtt_Historian.del_key_from_dict(message, ignored_attr.split("."))

    @staticmethod
    def isTopicMatching(topicWithWildcard :str, topic:str) -> bool:
        """
        Checks if the actual topic matches with a wild card expression 
        e.g. "a/b" matches with "a/+" and "a/#"
             "a/b/c" matches wit "a/#" but not with "a/+"   
        """
        if(topicWithWildcard is not None):
            regexList = topicWithWildcard.split('/')
            ## Using Regex to do matching
            # replace all occurrences of "+" wildcard with [^/]* -> any set of charecters except "/"
            # replace all occurrences of "#" wildcard with (.)*  -> any set of charecters including "/"
            regexExp = ""
            for value in regexList:
                if (value == "+"):
                    regexExp += "[^/]*"
                elif (value == "#") :
                    regexExp += "(.)*"
                else :
                    regexExp += value + "/"
            return bool(re.fullmatch(regexExp, topic))
        return False


    
    @staticmethod
    def del_key_from_dict(message:dict, ignored_attr:list) -> dict:
        msg_cursor = message
        count = 0
        for key in ignored_attr:
            if(msg_cursor.get(key) is None):
                # If a key is not found break the loop as we cant proceed further to search for child nodes
                LOGGER.warn("Unable to find attribute %s in %s. Skipping !!!",key,message)
                break
                            
                #descent into the nested key
            if(count == len(ignored_attr)-1 ) :
                #we are at leaf node hence can delete the key & value
                LOGGER.info("%s deleted and will not be persisted",msg_cursor[key],key)
                del msg_cursor[key]
            else :
                msg_cursor = msg_cursor[key]
            if (type(msg_cursor) is not dict):
                LOGGER.warn("key: %s should return a dict but fount:%s. Cant proceed hence skipping !!!",key,message)
                break
            count+=1
        return message

def main():
    try:
        uns_mqtt_historian = Uns_Mqtt_Historian()
        uns_mqtt_historian.uns_client.loop_forever()
    finally:
        if (uns_mqtt_historian is not None):
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian is not None) and (uns_mqtt_historian.uns_historian_handler is not None):
            # incase the on_disconnect message is not called
            uns_mqtt_historian.uns_historian_handler.close()

if __name__ == '__main__':
    main()
