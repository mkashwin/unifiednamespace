from genericpath import exists
import logging
import os.path as path
import ssl

import paho.mqtt.client as mqtt_client

from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

#Logger
LOGGER = logging.getLogger(__name__)


class UNS_MQTT_Listener(mqtt_client.Client):
    """
    Wrapper over te paho.mqtt.client to implement most commont MQTT related functionality
    The call only needs to implement the callback function on_message
    
    """

    def __init__(self,
                 client_id: str,
                 clean_session: bool = None,
                 userdata: dict = None,
                 protocol: int = mqtt_client.MQTTv5,
                 transport: str = "tcp",
                 reconnect_on_failure: bool = True,
                 username: str = None,
                 password: str = None,
                 tls: dict = None):
        """
        Creates an instance of an MQTT client
        Parameters
        ---------- 
        client_id:  the unique client id string used when connecting to the
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

        username & password: credentials to connect to the  broker

        tls: Dict containing the following attributed needed for an SSL connection  
            "ca_certs" - a string path to the Certificate Authority certificate files
            that are to be treated as trusted by this client. 

            "certfile" and "keyfile" - strings pointing to the PEM encoded client
            certificate and private keys respectively. 

            "cert_reqs" -  boolean. If None then  ssl.CERT_NONE is used
                           if True the ssl.CERT_REQUIRED is used
                           else ssl.CERT_OPTIONAL is used
                    
            "ciphers" - specifying which encryption ciphers are allowed for this connection

            "keyfile_password" - pass phrase used to decrypt certfile and keyfile incase it is encrypted

            "insecure_cert" - Boolean to allow self signed certificates. When true, hostname matching will be skipped

        Must be called before connect() or connect_async().        
        """
        LOGGER.debug(f"""{{'client_id': '{client_id}',
                 'clean_session': {clean_session},
                 'userdata': {userdata},
                 'protocol'{protocol}, 
                 'transport':'{transport}',
                 'reconnect_on_failure':{reconnect_on_failure},
                 'username':'{username}'
                 }}""")

        if (protocol not in (mqtt_client.MQTTv5, mqtt_client.MQTTv311, mqtt_client.MQTTv31) ):
            raise ValueError(f"Unknown MQTT Protocol Id:{protocol}")
        # Need these values in the connect operation
        self.protocol = protocol
        self.clean_session = clean_session

        if (protocol == mqtt_client.MQTTv5):
            # if MQTT version is v5.0 the ignore cleansession in the constructor
            clean_session = None

        super().__init__(client_id, clean_session, userdata, protocol,
                         transport, reconnect_on_failure)
        if ((tls is not None) and (tls.get("ca_certs") is not None)):
            ca_certs = tls.get("ca_certs")
            certfile = tls.get("certfile")
            keyfile = tls.get("keyfile")
            cert_reqs = None
            if (tls.get("cert_reqs") is None): # key not present
                cert_reqs = ssl.CERT_NONE
            elif (tls.get("cert_reqs")):    # Value is true
                cert_reqs = ssl.CERT_REQUIRED
            else:
                cert_reqs = ssl.CERT_OPTIONAL

            ciphers = tls.get("ciphers")
            keyfile_password = tls.get("keyfile_password")

            LOGGER.debug(f"""Connection with MQTT Broker is over SSL
                'ca_certs':{tls.get('ca_certs')},
                'certfile':{tls.get('certfile')},
                'keyfile':{tls.get('keyfile')},
                'cert_reqs':{tls.get('cert_reqs')},
                'ciphers':{tls.get('ciphers')}               
            """)
            #Force ssl.PROTOCOL_TLSv1_2
            if (path.exists(ca_certs)):
                super().tls_set(ca_certs=ca_certs,
                                certfile=certfile,
                                keyfile=keyfile,
                                cert_reqs=cert_reqs,
                                tls_version=ssl.PROTOCOL_TLSv1_2,
                                ciphers=ciphers,
                                keyfile_password=keyfile_password)
                if (tls.get("insecure_cert")):
                    super().tls_insecure_set(True)
                    cert_reqs = ssl.CERT_NONE
            else:
                raise FileNotFoundError(
                    f"Certificate file for SSL connection not found 'cert_location':{ca_certs} "
                )

        #Set username & password only if it was specified
        if (username is not None):
            super().username_pw_set(username, password)

    def run(self, host, port=1883, keepalive=60, topic="#", qos=2):
        """
        Main method to invoke after creating and instance of UNS_MQTT_Listener
        After this function invoke loop_forever() or loop start()
        """
        try:
            self.topic=topic
            self.qos=qos
            
            properties = None
            if (self.protocol == mqtt_client.MQTTv5):
                properties = Properties(PacketTypes.CONNECT)
            self.connect(host=host,
                         port=port,
                         keepalive=keepalive,
                         properties=properties)
        except Exception as ex:
            LOGGER.error("Unable to connect to MQTT broker: %s", ex)
            exit(1)
       
       

    ## call back methods
    def on_connect(self, client, userdata, flags, rc, properties=None):

        LOGGER.debug(
            f"{{Client: {client}, Userdata: {userdata},Flags: {flags}, rc: {rc}  }}"
        )
        if (rc == 0):
            LOGGER.debug("Connection established. Returned code=", rc)
            # subscribe to the topic only if connection was successful
            client.connected_flag = True
            self.subscribe(self.topic, self.qos, options=None, properties=properties)

            LOGGER.info(
                f"Successfully connect {self} to MQTT Broker"
            )
        else:
            LOGGER.error(f"Bad connection. Returned code=%s",rc)
            client.bad_connection_flag = True

    def on_subscribe(self,
                     client: mqtt_client,
                     userdata,
                     mid,
                     granted_qos,
                     properties=None):
        LOGGER.info(
            f"Successfully connect {self} to Topic: {self.topic} with QOS: {granted_qos} "
        )
