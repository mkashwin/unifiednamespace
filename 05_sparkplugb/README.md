# Decoder Application to process SparkPlugB

[![SparkplugB Decoder](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml)

This SparkplugB decoder is an MQTT Application Node deployed on the edge with the following functionality

- subscribes to the Topic _`spBv1.0/#`_
- decodes the payload received and extract the metrics received
- enhance the decoded message to add

  - \*\<group_id\>
  - \*\<edge_node_id\>
  - *\<device_id\> *if provided\*

- extract metric name to get ISA-95 UNS namespace
- if metric alias is used, map the metric alias to previously provided metric name
- collate all metrics specific to one metric name and create a consolidated message payload
- publish consolidate message payload to the UNS namespace

This is **not** a SCADA/IIOT host and will not be publishing any control messages to the broker

## Mapping logic for SparkplugB to ISA-95

With reference to the article [Using Sparkplug to Map ISA 95](https://www.hivemq.com/solutions/manufacturing/smart-manufacturing-using-isa95-mqtt-sparkplug-and-uns/), each SparkPlugB message contains an attribute **name** which contains the ISA namespace for the message in addition to the tag.
e.g.

```json
{
  "timestamp": 1486144502122,
  "metrics": [
    {
      "name": "Enterprise/Site/Area/Line/Cell/Tag1",
      "alias": 1,
      "timestamp": 1479123452194,
      "dataType": "String",
      "isHistorical": false,
      "value": "Test"
    },
    {
      "name": "Enterprise/Site/Area/Line/Tag2",
      "alias": 2,
      "timestamp": 1479123452196,
      "dataType": "String",
      "isHistorical": false,
      "value": "LineTest"
    }
  ],
  "seq": 2
}
```

When we parse the metric name we get - The topic name in the UNS i.e. `Enterprise/Site/Area/Line/Cell` - The name of the tag i.e. `Tag1` and `Tag2` which will now be added as an attribute to the JSON object being published to the UNS

The spB payload may contain multiple metrics which belong to different topics hence we merge all tags belonging to the name UNS topic. The logic for merging is as following - the name of the metric will be split into the topic and tag - tags for the same topic are merged in to one JSON object - if a metric is historical, we create an array of tag values with the latest version being at 0 position - if a metric name is duplicated and not historical, the newer tag value will override the older tag value in the JSON object - the overall timestamp for the JSON object is the max of timestamps of all the tags

This mapping is to be done only for the message types

- NDATA
- DDATA
- NCMD
- DCMD

**_IMPORTANT: The birth and death messages are not mapped to the UNS currently_**

<!-- \<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>
**SparkplugB Namespace** |  **ISA-95 Namespace** | ***Comments***
------ | ------ | ------
spBv1.0 | - | Default namespace for sparkplugB. No mapping needed
\<group_id\> | \<enterprise\>/\<facility\> | Map the group id or the alias to the enterprise and facility
\<message_type\> | - | Provides guidance on handling the payload. Not needed for mapping
\<edge_node_id\> | \<area\>/\<line\> | Map the edge node id or the alias to the area and the line
\<device_id\> | \<device\> | Map the device id to th end device. If the device id is not provided then <br />extract the device(s) from the payload to appropriately map the messages -->

## Key Configurations to provide

This application has two configuration file.

1. [settings.yaml](./conf/settings.yaml): Contain the key configurations need to connect with MQTT brokers
   **key** | **sub key** | **description** | **_default value_** |
   ------ | ------ | ------ | ------
   **mqtt** | **host**\*| Hostname of the mqtt broker instant. Mandatory configuration | _None_
   mqtt | port | Port of the mqtt broker (int) | _1883_
   mqtt | topics | Array of topics to be subscribed to. Must be in the names space of SpB i.e. **spBv1.0/#** | _["spBv1.0/#"]_
   mqtt | qos | QOS for the subscription. Valid values are 0,1,2 | _1_
   mqtt | keep*alive | Maximum time interval in seconds between two control packet published by the client (int) | \_60*
   mqtt | reconnect*on_failure | Makes the client handle reconnection(s). Recommend keeping this True (True,False)| \_True*
   mqtt | version | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31) | _5_
   mqtt | clean*session | Boolean value to be specified only if MQTT Version is not 5 | \_None*
   mqtt | transport | Valid values are "websockets", "tcp" | _"tcp"_
   mqtt | ignored*attributes | Map of topic & list of attributes which are to be ignored from persistance. supports wild cards for topics and nested via . notation for the attributes <br /> e.g.<br /> {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } | None
   mqtt | timestamp_attribute | the attribute name which should contain the timestamp of the message's publishing| *"timestamp"_
   sparkplugb | | \_currently empty_|
   **dynaconf_merge**\* | | Mandatory param. Always keep value as true |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster
   This file is not checked into the repository for security purposes. However there is a template file provided [**`.secrets_template.yaml`**](./conf/.secrets_template.yaml) which should be edited and renamed to **`.secrets.yaml`**
   **key** | **sub key** | **sub key** | **description** | **_default value_** |
   :------ | :------ | :------ | :------ | :------
   mqtt | username | | The user id needed to authenticate with the MQTT broker | _None_
   mqtt | password | | The password needed to authenticate with the MQTT broker | _None_
   mqtt | tls | |Provide a map of attributes needed for a TLS connection to the MQTT broker. See below attributes | _None_
   mqtt | tls | ca*certs | fully qualified path to the ca cert file. Mandatory for an SSL connection | \_None*
   mqtt | tls | certfile | fully qualified path to the cert file | _None_
   mqtt | tls | keyfile | fully qualified path to the keyfile for the cert| _None_
   mqtt | tls | cert*reqs | Boolean. If note provided then ssl.CERT_NONE is used. if True the ssl.CERT_REQUIRED is used. else ssl.CERT_OPTIONAL is used | \_None*
   mqtt | tls | ciphers | Specify which encryption ciphers are allowed for this connection | _None_
   mqtt | tls | keyfile*password | Password used to encrypt your certfile and keyfile | \_None*
   mqtt | tls | insecure*cert | Boolean. Skips hostname checking required for self signed certificates. | \_True*
   **dynaconf_merge**\* | | | Mandatory param. Always keep value as true |

## Setting up the development environment for this module

This sub module can be independently setup as a dev environment in the folder [`05_sparkplugb`](.)
This has been tested on **Unix(bash)**, **Windows(powershell)** and **Mac(zsh)**

```bash
python -m pip install --upgrade pip
pip install poetry
# Ensure that the poetry shell is activated
poetry shell
python -m pip install --upgrade pip poetry
poetry install
python ./src/uns_spb_mapper/uns_sparkplugb_listener.py
```

> **Setting up VSCode**
>
> While importing the folder into VSCode remember to do the following steps the first time
>
> 1. Open a terminal in VSCode
> 1. Activate the poetry shell
>
>    ```bash
>    poetry shell
>    python -m pip install --upgrade pip poetry
>    poetry install
>    ```
>
> 1. Select the correct python interpreter in VSCode (should automatically detect the poetry virtual environment)

## Running the python script

This function is executed by the following command with the current folder as [`05_sparkplugb`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance

```bash
# Ensure that the poetry shell is activated
poetry shell
poetry install
python ./src/uns_spb_mapper/uns_sparkplugb_listener.py
```

### Running tests

The set of test for this module is executed by

```bash
#run all tests excluding integration tests
poetry run pytest -m "not integrationtest" test/
# runs all tests
poetry run pytest test/
```

## Deploying the docker container image created for this module

The docker container image for this module are built and store in the Dockerize module published to [Github Container Registry](https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%2Fspb_mapper)

The way to run the container is

```bash
# docker pull ghcr.io/mkashwin/unifiednamespace/uns/spb_mapper:<tag>
# e.g.
docker pull ghcr.io/mkashwin/unifiednamespace/uns/spb_mapper:latest
# docker run --name <container name> -d s-v <full path to conf>/:/app/conf uns/spb_mapper:<tag>
docker run --name spb_to_uns_mqtt -d -v $PWD/conf:/app/conf ghcr.io/mkashwin/unifiednamespace/uns/spb_mapper:latest
```

**Note**: Remember to update the following before executing

- **\<container name\>** (optional): Identifier for the container so you can work with the same container instance using

  ```bash
  docker start <container name>
  docker stop <container name>
  ```

- **\<full path to conf\>** (Mandatory): Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). _Give the complete path and not relative path_

- If you are running this image on the host as the MQTT broker pass the flag `--network host` along with docker run to enure `localhost` services on the host are correctly resolved

## Limitations

1. [ ] The application assumes the the MQTT broker for SparkPlugB and the UNS are one and the same as it does not sense to have separate brokers for the same. This can be enhanced easily if there is a requirement for the same. Please create issue on the Github project
1. [ ] Need to understand how to handle NDEATH, DDEATH, ~~STATE~~ message types
   - STATE messages are not Protobuf messages but rather JSON messages. They cannot be mapped to the UNS as they have no metrics
1. [x] ~~Handle non compliant messages~~
   - non compliant messages will be logged as an error and ignored
1. [ ] Need to understand how to handle metric types DataSet, Template
1. [ ] Need to understand how to handle metadata, properties, is_multi_part etc.
