[![Kafka bridge](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_kafka-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_kafka-app.yml)

# MQTT to Kafka Bridge
This module provides a bridge between an MQTT (Message Queuing Telemetry Transport) server and a Kafka broker, allowing messages received on the MQTT server to be published to the Kafka broker. 

## Mapping logic for MQTT Topic to Kafka Topic
Valid characters for Kafka topics are the ASCII alphanumerics, **.**, **_**, and **-** and it is better not to mix . and _ to avoid metric namespace collisions

Valid characters for MQTT topics are similar to above with the exception that **/** character is user to denote hierarchy.

Since  **/** is not allowed for Kafka topics, we replace all occurrences of  **/** in the MQTT topic name with *_*
see [kafka_handler.py.convert_MQTT_KAFKA_topic()](06_uns_kafka/src/uns_kafka/kafka_handler.py#convert_MQTT_KAFKA_topic)

## Key Configurations to provide
This application has two configuration file. 
1. [settings.yaml](./conf/settings.yaml):  Contain the key configurations need to connect with MQTT brokers
    **key** | **sub key** | **description**  | ***default value*** |
    ------ | ------ | ------ | ------
    **mqtt** | **host**\*| Hostname of the mqtt broker instant. Mandatory configuration | *None*
    mqtt | port | Port of the mqtt broker (int) | *1883*
    mqtt | topics | Array of topics to be subscribed to. Must be in the names space of SpB  i.e. **spBv1.0/#** | *["spBv1.0/#"]* 
    mqtt | qos | QOS for the subscription. Valid values are 0,1,2 | *1*
    mqtt | keep_alive | Maximum time interval in seconds between two control packet published by the client (int) | *60*
    mqtt | reconnect_on_failure | Makes the client handle reconnection(s). Recommend keeping this True  (True,False)| *True*
    mqtt | version | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31) | *5*
    mqtt | transport | Valid values are "websockets", "tcp" | *"tcp"*
    mqtt | ignored_attributes | Map of topic &  list of attributes which are to be ignored from persistance. supports wild cards for topics  and nested via . notation for the attributes <br /> e.g.<br />  {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } |  None 
    mqtt | timestamp_attribute | the attribute name which should contain the timestamp of the message's publishing| *"timestamp"*
    kafka | config  | Dict. see [kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). All non security configurations | *None*
    **dynaconf_merge**\*  |  | Mandatory param. Always keep value as true  |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster
    This file is not checked into the repository for security purposes. However there is a template file provided [**`.secrets_template.yaml`**](./conf/.secrets_template.yaml) which should be edited and renamed to **`.secrets.yaml`**
    **key** | **sub key** | **sub key** | **description**  | ***default value*** |
    :------ | :------ | :------ | :------ | :------
   mqtt | username | | The user id needed to authenticate with the MQTT broker | *None*
   mqtt | password | | The password needed to authenticate with the MQTT broker | *None*
   mqtt | tls | |Provide a map of attributes needed for a TLS connection to the MQTT broker. See below attributes | *None*
   mqtt | tls | ca_certs | fully qualified path to the ca cert file. Mandatory for an SSL connection | *None* 
   mqtt | tls | certfile | fully qualified path to the cert file | *None*
   mqtt | tls | keyfile | fully qualified path to the keyfile for the cert| *None*
   mqtt | tls | cert_reqs | Boolean. If note provided then  ssl.CERT_NONE is used. if True the ssl.CERT_REQUIRED is used. else ssl.CERT_OPTIONAL is used | *None*
   mqtt | tls | ciphers | Specify which encryption ciphers are allowed for this connection | *None*
   mqtt | tls | keyfile_password | Password used to encrypt your certfile and keyfile | *None*
   mqtt | tls | insecure_cert | Boolean. Skips hostname checking required for self signed certificates.  | *True*
   kafka | config | | Dict. see [kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). Only the security related settings   |  *None*

   **dynaconf_merge**\*  |  | | Mandatory param. Always keep value as true  |

# Setting up the development environment for this module 
This sub module can be independently setup as a dev environment in the folder [`05_sparkplugb`](.)
This has been tested on **Unix(bash)**, **Windows(powershell)** and **Mac(zsh)**
```bash
python -m pip install --upgrade pip
pip install poetry
# Ensure that the poetry shell is activated
poetry shell 
poetry install
python ./src/uns_kafka/uns_kafka_listener.py
```
> While importing the folder into VSCode remember to do the following steps the first time
>   1. Open a terminal in VSCode
>   1. Activate the poetry shell.  
        ```bash
        poetry shell 
        poetry install
        ```    
>   1. Select the correct python interpreter in VSCode (should automatically detect the poetry virtual environment)

## Running the python script
This function is executed by the following command with the current folder as [`06_uns_kafka`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance
```bash
# Ensure that the poetry shell is activated
poetry shell 
poetry install
python ./src/uns_kafka/uns_kafka_listener.py
```
## Running tests
The set of test for this module is executed by
```bash
# Ensure that the poetry shell is activated
poetry shell 
#run all tests excluding integration tests 
pytest -m "not integrationtest" test/
# runs all tests
pytest test/
```
# Deploying the docker container image created for this module 
The docker container image for this module are built and store in the Dockerize module published to <a href="https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%2Fkafka_mapper">Github Container Registry</a>

The way to run the container  is
```bash
# docker pull ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:<tag>
# e.g.
docker pull ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:latest
# docker run --name <container name> -d s-v <full path to conf>/:/app/conf uns/kafka_mapper:<tag>
docker run --name uns_mqtt_2_kafka -d -v $PWD/conf:/app/conf ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:latest
```
**Note**: Remember to update the following before executing 
*  **\<container name\>** (optional): Identifier for the container so you can work with the same container instance using 
   ```bash
   docker start <container name>
   docker stop <container name>
   ```
* **\<full path to conf\>** (Mandatory): Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). *Give the complete path and not relative path*
