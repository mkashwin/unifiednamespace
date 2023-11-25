"""
Base class for all the MQTT listeners to be implemented for the Unified Name Space
Implements basic functionality of establishing connection, subscription on connection and
handle various MQTT versions
"""
import json
import logging
import re
import ssl
from os import path
from typing import Optional

import paho.mqtt.client as mqtt_client
from google.protobuf.json_format import MessageToDict
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_sparkplugb.generated import sparkplug_b_pb2

# Logger
LOGGER = logging.getLogger(__name__)


class UnsMQTTClient(mqtt_client.Client):
    """
    Wrapper over te paho.mqtt.client to implement most common MQTT related functionality
    The call only needs to implement the callback function on_message
    """

    MQTTv5 = mqtt_client.MQTTv5
    MQTTv311 = mqtt_client.MQTTv311
    MQTTv31 = mqtt_client.MQTTv31

    SPARKPLUG_NS = "spBv1.0/"
    SPB_STATE_MSG_TYPE = "spBv1.0/+/STATE"

    def __init__(self,
                 client_id: str,
                 clean_session: Optional[bool] = None,
                 userdata: Optional[dict] = None,
                 protocol: int = mqtt_client.MQTTv5,
                 transport: Optional[str] = "tcp",
                 reconnect_on_failure: bool = True):
        # pylint: disable=too-many-arguments
        """
        Creates an instance of an MQTT client

        Parameters
        ----------
        client_id: the unique client id string used when connecting to the
        broker. Must be provided

        clean_session: a boolean that determines the client type. If True,
        the broker will remove all information about this client when it
        disconnects. clean_session applies to MQTT versions v3.1.1 and v3.1.

        userdata: user defined data of any type that is passed as the "userdata"
        parameter to callbacks.

        protocol: allows explicit setting of the MQTT version to use for this client.
        Can be paho.mqtt.client.MQTTv311 (v3.1.1), paho.mqtt.client.MQTTv31 (v3.1) or
        paho.mqtt.client.MQTTv5 (v5.0). Defaults to MQTTv5

        transport: sets the transport mechanism as either "websockets" or  "tcp" to use raw TCP.

        topic : the fully qualified topic to listen to. Supports wild cards # , +
        """
        LOGGER.debug(
            """{'client_id': %s,
                 'clean_session': %s,
                 'userdata': %s,
                 'protocol': %s,
                 'transport': %s,
                 'reconnect_on_failure': %s
                 }""", str(client_id), str(clean_session), str(userdata),
            str(protocol), str(transport), str(reconnect_on_failure))

        if (protocol not in (mqtt_client.MQTTv5, mqtt_client.MQTTv311,
                             mqtt_client.MQTTv31)):
            raise SystemError(f"Unknown MQTT Protocol Id:{protocol}")
        # Need these values in the connect operation
        self.protocol = protocol
        self.clean_session = clean_session

        if protocol == mqtt_client.MQTTv5:
            # if MQTT version is v5.0 the ignore clean_session in the constructor
            clean_session = None

        super().__init__(client_id, clean_session, userdata, protocol,
                         transport, reconnect_on_failure)
        self.topics: list = None
        self.qos: int = 0

        # call back methods
        def on_uns_connect(client,
                           userdata,
                           flags,
                           return_code,
                           properties=None):
            """
            Call back method when a mqtt connection happens
            """
            LOGGER.debug("{ Client: %s, Userdata: %s, Flags: %s, rc: %s}",
                         str(client), str(userdata), str(flags),
                         str(return_code))
            if return_code == 0:
                LOGGER.debug("Connection established. Returned code=%s",
                             str(return_code))
                for topic in self.topics:
                    self.subscribe(topic,
                                   self.qos,
                                   options=None,
                                   properties=properties)

                LOGGER.info("Successfully connected %s to MQTT Broker",
                            str(self))
            else:
                LOGGER.error("Bad connection. Returned code=%s",
                             str(return_code))
                client.bad_connection_flag = True

        def on_uns_subscribe(client: mqtt_client,
                             userdata,
                             mid,
                             granted_qos,
                             properties=None):
            """
            Callback method when client subscribes to a topic
            Unfortunately information about the topic subscribed to is not available here
            """
            LOGGER.info(
                "Successfully connected: %s with QOS: %s, userdata:%s , mid:%s, properties:%s",
                str(client), str(granted_qos), str(userdata), str(mid),
                str(properties))

        self.on_connect = on_uns_connect
        self.on_subscribe = on_uns_subscribe

    def run(self,
            host,
            port=1883,
            username: Optional[str] = None,
            password: Optional[str] = None,
            tls: Optional[dict] = None,
            keepalive=60,
            topics=None,
            qos=2):
        # pylint: disable=too-many-arguments
        """
        Main method to invoke after creating and instance of UNS_MQTT_Listener
        After this function invoke loop_forever() or loop start()

        Parameters
        ----------
        username & password: credentials to connect to the  broker
        topics: Array / list of topics to subscribe to
        tls: Dict containing the following attributed needed for an SSL connection
            "ca_certs" - a string path to the Certificate Authority certificate files
            that are to be treated as trusted by this client.

            "certfile" and "keyfile" - strings pointing to the PEM encoded client
            certificate and private keys respectively.

            "cert_reqs" -  boolean. If None then  ssl.CERT_NONE is used
                           if True the ssl.CERT_REQUIRED is used
                           else ssl.CERT_OPTIONAL is used

            "ciphers" - specifying which encryption ciphers are allowed for this connection

            "keyfile_password" - pass phrase used to decrypt certfile and
                                 keyfile incase it is encrypted

            "insecure_cert" - Boolean to allow self signed certificates.
                              When true, hostname matching will be skipped

        """
        try:
            self.topics = topics
            # Handle scenarios where only one topic or no topic is provided
            if isinstance(topics, str):
                self.topics = [topics]
            elif topics is None:
                self.topics = ["#"]

            self.qos = qos

            properties = None
            if self.protocol == mqtt_client.MQTTv5:
                properties = Properties(PacketTypes.CONNECT)
            self.setup_tls(tls)

            # Set username & password only if it was specified
            if username is not None:
                super().username_pw_set(username, password)
            self.connect(host=host,
                         port=port,
                         keepalive=keepalive,
                         properties=properties)
        except Exception as ex:
            LOGGER.error("Unable to connect to MQTT broker: %s",
                         str(ex),
                         stack_info=True,
                         exc_info=True)
            raise SystemError(ex) from ex

    def setup_tls(self, tls):
        """
        Setup the TLS connection (encrypted secure connection) to the MQTT broker
        if configured. If no TLS configurations are provided then do nothing
        """
        if ((tls is not None) and (tls.get("ca_certs") is not None)):
            ca_certs = tls.get("ca_certs")
            certfile = tls.get("certfile")
            keyfile = tls.get("keyfile")
            cert_reqs = None
            if tls.get("cert_reqs") is None:  # key not present
                cert_reqs = ssl.CERT_NONE
            elif tls.get("cert_reqs"):  # Value is true
                cert_reqs = ssl.CERT_REQUIRED
            else:
                cert_reqs = ssl.CERT_OPTIONAL

            ciphers = tls.get("ciphers")
            keyfile_password = tls.get("keyfile_password")

            LOGGER.debug("Connection with MQTT Broker is over SSL")
            # Force ssl.PROTOCOL_TLS_CLIENT
            if path.exists(ca_certs):
                super().tls_set(ca_certs=ca_certs,
                                certfile=certfile,
                                keyfile=keyfile,
                                cert_reqs=cert_reqs,
                                tls_version=ssl.PROTOCOL_TLS_CLIENT,
                                ciphers=ciphers,
                                keyfile_password=keyfile_password)
                if tls.get("insecure_cert"):
                    super().tls_insecure_set(True)
                    cert_reqs = ssl.CERT_NONE
            else:
                raise FileNotFoundError(
                    f"Certificate file for SSL connection not found 'cert_location':{ca_certs} ",
                )

    def get_payload_as_dict(self, topic: str, payload: any,
                            mqtt_ignored_attributes: dict) -> dict:
        """
        Converts the message payload into a dictionary.

        For UNS messages, the JSON string is converted to a dictionary.
        For sPB messages, the protocol buffer is converted to a dictionary.

        If any attributes are to be ignored, they will be removed from the returned dictionary.

        Parameters
        ----------
            topic (str): The topic of the message.
            payload (any): The payload of the message.
            mqtt_ignored_attributes (dict): A dictionary of attributes to be ignored.

        Returns
        -------
            dict: The payload as a dictionary.
        """
        if (topic.startswith(UnsMQTTClient.SPARKPLUG_NS)
                and not UnsMQTTClient.is_topic_matched(
                    UnsMQTTClient.SPB_STATE_MSG_TYPE, topic)):
            # This message was to the sparkplugB namespace in protobuf format
            inbound_payload = sparkplug_b_pb2.Payload()
            inbound_payload.ParseFromString(payload)
            decoded_payload = MessageToDict(inbound_payload)
        else:
            # TODO Assuming all messages to UNS or the STATE message type in sparkplugB
            # are json hence convertible to dict
            decoded_payload = json.loads(payload.decode("utf-8"))

        filtered_message = UnsMQTTClient.filter_ignored_attributes(
            topic, decoded_payload, mqtt_ignored_attributes)
        return filtered_message

    @staticmethod
    def filter_ignored_attributes(topic: str, mqtt_message: dict,
                                  mqtt_ignored_attributes) -> dict:
        """
        Removed the attributes configured to be ignored in the mqtt message and topic
        """
        resulting_message = mqtt_message
        if mqtt_ignored_attributes is not None:

            for topic_key in mqtt_ignored_attributes:
                # Match Topic in ignored list with current topic and
                # fetch associated ignored attributes

                ignored_topic = topic_key
                if UnsMQTTClient.is_topic_matched(ignored_topic, topic):
                    # This could be either a single string or a list of strings
                    ignored_attr_list = mqtt_ignored_attributes.get(
                        ignored_topic, [])

                    ignored_attr = None
                    # if the attribute is a single key. But this could be a nested key
                    # e.g. parent_key.child_key
                    # so split that into a list
                    if isinstance(ignored_attr_list, str):
                        UnsMQTTClient.del_key_from_dict(
                            resulting_message, ignored_attr_list.split("."))
                    # if the attribute is a list of keys
                    elif isinstance(ignored_attr_list, (list, tuple)):
                        for ignored_attr in ignored_attr_list:
                            UnsMQTTClient.del_key_from_dict(
                                resulting_message, ignored_attr.split("."))
        return resulting_message

    @staticmethod
    def is_topic_matched(topic_with_wildcard: str, topic: str) -> bool:
        """
        Checks if the actual topic matches with a wild card expression
        e.g. "a/b" matches with "a/+" and "a/#"
             "a/b/c" matches wit "a/#" but not with "a/+"
        """
        if topic_with_wildcard is not None:
            regex_list = topic_with_wildcard.split("/")
            # Using Regex to do matching
            # replace all occurrences of "+" wildcard with [^/]*
            #                           -> any set of characters except "/"
            # replace all occurrences of "#" wildcard with (.)*
            #                           -> any set of characters including "/"
            regex_exp = ""
            for value in regex_list:
                if value == "+":
                    regex_exp += "[^/]*/"
                elif value == "#":
                    regex_exp += "(.)*/"
                else:
                    regex_exp += value + "/"
            if (len(regex_exp) > 1 and regex_exp[-1] == "/"):
                regex_exp = regex_exp[:-1]
            return bool(re.fullmatch(regex_exp, topic))
        return False

    @staticmethod
    def del_key_from_dict(message: dict, ignored_attr: list) -> dict:
        """
        Deletes the list of keys recursively through nested dicts
        Params
        ------
        message:
            the dict from which the keys need to be deleted
        ignored_attr:
            list of keys which need to be removed from message
        """
        msg_cursor = message
        count = 0
        for key in ignored_attr:
            if msg_cursor.get(key) is None:
                # If a key is not found break the loop as we cant proceed further
                # to search for child nodes
                LOGGER.warning(
                    "Unable to find attribute %s in %s. Skipping !!!", key,
                    str(message))
                break

                # descent into the nested key
            if count == len(ignored_attr) - 1:
                # we are at leaf node hence can delete the key & value
                LOGGER.info("%s deleted and will not be persisted",
                            str((key, msg_cursor[key])))
                del msg_cursor[key]
            else:
                msg_cursor = msg_cursor[key]
            if not isinstance(msg_cursor, dict):
                LOGGER.warning(
                    "key: %s should return a dict but found:%s. Cant proceed hence skipping !!!",
                    key, str(message))
                break
            count += 1
        return message
