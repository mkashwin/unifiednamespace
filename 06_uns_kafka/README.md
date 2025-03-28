# MQTT to Kafka Bridge

[![Kafka bridge](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_kafka-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_kafka-app.yml)

This module provides a bridge between an MQTT (Message Queuing Telemetry Transport) server and a Kafka broker, allowing messages received on the MQTT server to be published to the Kafka broker.

## Mapping logic for MQTT Topic to Kafka Topic

Valid characters for Kafka topics are the ASCII alphanumerics, **`.`**, **`_`**, and **`-`** and it is better not to mix `.` and `_` to avoid metric namespace collisions

Valid characters for MQTT topics are similar to above with the exception that **`/`** character is user to denote hierarchy.

Since **`/`** is not allowed for Kafka topics, we replace all occurrences of **`/`** in the MQTT topic name with **`_`**
see [kafka_handler.py.convert_MQTT_KAFKA_topic()](./src/uns_kafka/kafka_handler.py#convert_MQTT_KAFKA_topic)

**IMPORTANT NOTE:** The Kafka broker must be configured to allow producer clients to create topics in order to ease the operation of converting new MQTT topics to Kafka

## Architectural options and choices

1. **Integration Options to KAFKA**
   There are two possibles ways to integrate the current setup

   - _Bridge MQTT to KAFKA_:
     Which is the approach I have chosen primarily because it provides flexibility and decoupling between all the service. Also most enterprise Kafka brokers have an inbuilt KAFKA plugin to ease the integration of MQTT to KAFKA

   - _Change Detect Capture via Debezium from the Graph database_:
     This approach showed a lot of promise **([Refer this article](https://medium.com/neo4j/a-new-neo4j-integration-with-apache-kafka-6099c14851d2))**. I chose against this primarily because this was coupling the graph database with Kafka as well as adding additional complexity to the graph database

1. **Deployment of KAFKA Broker**
   The primary location for deploying the KAFKA broker would be in the Enterprise hosting or the Cloud next to the Enterprise/Cloud based MQTT broker as opposed to deploying KAFKA on the manufacturing floor
   @Kai Waehner has a brilliant [5 part Blog series](https://www.kai-waehner.de/blog/2021/03/15/apache-kafka-mqtt-sparkplug-iot-blog-series-part-1-of-5-overview-comparison/) on extracting the best by integrating MQTT and KAFKA
   Just like the hosted enterprise versions of MQTT provided by various vendors, going with a hosted solution for KAFKA like [Confluent Cloud](https://www.confluent.io/), [AWS MSK](https://aws.amazon.com/msk/what-is-kafka/), [Aiven](https://aiven.io/), [cloudkarafka](https://www.cloudkarafka.com/) etc.
   If you want to deploy and manage Kafka, I recommend also checking out [Strimzi](https://strimzi.io/) as a way to deploy and manage Kafka on Kubernetes.
   I would recommend using Kafka in [Kraft mode](https://developer.confluent.io/learn/kraft/) which significantly improved the experience of deploying and managing Kafka

1. **Choice of KAFKA Client library**
   Of the many Kafka client libraries for python, I selected [confluent-kafka](https://docs.confluent.io/kafka-clients/python/current/overview.html) primarily for its slightly better performance and similarity to other libraries (owing to being a wrapper over the C library librdkafka)

## Key Configurations to provide

This application has two configuration file.

1. [settings.yaml](./conf/settings.yaml): Contain the key configurations need to connect with MQTT brokers as well as the Kafka brokers

   | **key**              | **sub key**           | **description**                                                                                                                                                                                                                                                                                              | **_default value_** |
   | -------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
   | **mqtt**             | **host**\*            | Hostname of the mqtt broker instant. Mandatory configuration                                                                                                                                                                                                                                                 | _None_              |
   | mqtt                 | port                  | Port of the mqtt broker (int)                                                                                                                                                                                                                                                                                | _1883_              |
   | mqtt                 | topics                | Array of topics to be subscribed to. Must be in the names space of SpB i.e. **spBv1.0/#**                                                                                                                                                                                                                    | _["spBv1.0/#"]_     |
   | mqtt                 | qos                   | QOS for the subscription. Valid values are 0,1,2                                                                                                                                                                                                                                                             | _1_                 |
   | mqtt                 | keep\*alive           | Maximum time interval in seconds between two control packet published by the client (int)                                                                                                                                                                                                                    | \_60\*              |
   | mqtt                 | reconnect\*on_failure | Makes the client handle reconnection(s). Recommend keeping this True (True,False)                                                                                                                                                                                                                            | \_True\*            |
   | mqtt                 | version               | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31)                                                                                                                                                                               | _5_                 |
   | mqtt                 | clean\*session        | Boolean value to be specified only if MQTT Version is not 5                                                                                                                                                                                                                                                  | \_None\*            |
   | mqtt                 | transport             | Valid values are "websockets", "tcp"                                                                                                                                                                                                                                                                         | _"tcp"_             |
   | mqtt                 | ignored\*attributes   | Map of topic & list of attributes which are to be ignored from persistence. supports wild cards for topics and nested via . notation for the attributes <br /> e.g.<br /> {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } | None                |
   | mqtt                 | timestamp_attribute   | the attribute name which should contain the timestamp of the message's publishing                                                                                                                                                                                                                            | \*"timestamp"\_     |
   | **kafka**            | **config**\*          | Mandatory Dict. see [Kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). All non security configurations                                                                                                                                                   | \_None\_            |
   | **dynaconf_merge**\* |                       | Mandatory param. Always keep value as true                                                                                                                                                                                                                                                                   |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect
   This file is not checked into the repository for security purposes. However there is a template file provided [**`.secrets_template.yaml`**](./conf/.secrets_template.yaml) which should be edited and renamed to **`.secrets.yaml`**

   | **key** | **sub key** | **sub key**       | **description**                                                                                                                                     | **_default value_** |
   | :------ | :---------- | :---------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ |
   | mqtt    | username    |                   | The user id needed to authenticate with the MQTT broker                                                                                             | _None_              |
   | mqtt    | password    |                   | The password needed to authenticate with the MQTT broker                                                                                            | _None_              |
   | mqtt    | tls         |                   | Provide a map of attributes needed for a TLS connection to the MQTT broker. See below attributes                                                    | _None_              |
   | mqtt    | tls         | ca\*certs         | fully qualified path to the ca cert file. Mandatory for an SSL connection                                                                           | \_None\*            |
   | mqtt    | tls         | certfile          | fully qualified path to the cert file                                                                                                               | _None_              |
   | mqtt    | tls         | keyfile           | fully qualified path to the keyfile for the cert                                                                                                    | _None_              |
   | mqtt    | tls         | cert\*reqs        | Boolean. If note provided then ssl.CERT_NONE is used. if True the ssl.CERT_REQUIRED is used. else ssl.CERT_OPTIONAL is used                         | \_None\*            |
   | mqtt    | tls         | ciphers           | Specify which encryption ciphers are allowed for this connection                                                                                    | _None_              |
   | mqtt    | tls         | keyfile\*password | Password used to encrypt your certfile and keyfile                                                                                                  | \_None\*            |
   | mqtt    | tls         | insecure\*cert    | Boolean. Skips hostname checking required for self signed certificates.                                                                             | \_True\*            |
   | kafka   | config      |                   | Dict. see [kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). Only the security related settings | _None_              |

   **dynaconf_merge**\* | | | Mandatory param. Always keep value as true |

## Setting up the development environment for this module

This sub module can be independently setup as a dev environment in the folder [`06_uns_kafka`](.)
The following command creates a dev instance of a Kafka broker. **To be used only for development purposes**.

```bash

docker run \
    --name uns_kafka \
    --env KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://localhost:9092" \
    --env ALLOW_PLAINTEXT_LISTENER="yes" \
    --env KAFKA_CFG_NODE_ID="0" \
    --env KAFKA_CFG_PROCESS_ROLES="controller,broker" \
    --env KAFKA_CFG_LISTENERS="PLAINTEXT://:9092,CONTROLLER://:9093" \
    --env KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP="CONTROLLER:PLAINTEXT, PLAINTEXT:PLAINTEXT" \
    --env KAFKA_CFG_CONTROLLER_QUORUM_VOTERS="0@localhost:9093" \
    --env KAFKA_CFG_CONTROLLER_LISTENER_NAMES="CONTROLLER" \
    -p 9092:9092 \
    -d \
    bitnami/kafka:latest
```

Setting up a production grade Kafka cluster is detailed on the confluent site **[Running Kafka in Production](https://docs.confluent.io/platform/current/kafka/deployment.html)**

This has been tested on **Unix(bash)**, **Windows(powershell)** and **Mac(zsh)**

```bash
python -m pip install --upgrade pip uv
# Ensure that the uv shell is activated
uv venv
uv sync
```

> **Setting up VSCode**
>
> While importing the folder into VSCode remember to do the following steps the first time
>
> 1. Open a terminal in VSCode
> 1. Activate the venv
>
>    ```bash
>    python -m pip install --upgrade pip uv
>    uv venv
>    ```
>
> 1. Select the correct python interpreter in VSCode (should automatically detect the .venv virtual environment)

## Running the python script

This function is executed by the following command with the current folder as [`06_uns_kafka`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance

```bash
# Ensure that the uv shell is activated
uv venv
uv run uns_kafka_mapper
```

### Running tests

The set of test for this module is executed by

```bash
#run all tests excluding integration tests
uv run pytest -m "not integrationtest" test/
# runs all tests
uv run pytest test/
```

## Deploying the docker container image created for this module

The docker container image for this module are built and store in the Dockerize module published to [Github Container Registry](https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%2Fkafka_mapper)

The way to run the container is

```bash
# docker pull ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:<tag>
# e.g.
docker pull ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:latest
# docker run --name <container name> -d s-v <full path to conf>/:/app/conf uns/kafka_mapper:<tag>
docker run --name uns_mqtt_2_kafka -d -v $PWD/conf:/app/conf ghcr.io/mkashwin/unifiednamespace/uns/kafka_mapper:latest
```

**Note**: Remember to update the following before executing

- **\<container name\>** (optional): Identifier for the container so you can work with the same container instance using

  ```bash
  docker start <container name>
  docker stop <container name>
  ```

- **\<full path to conf\>** (Mandatory): Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). _Give the complete path and not relative path_
