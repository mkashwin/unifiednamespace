[![SparkplugB Decoder](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml)

# Decoder Application to process SparkPlugB 
This SparkplugB decoder is an MQTT Application Node  deployed on the edge with the following functionality
- subscribes to the  Topic *`spBv1.0/#`* 
- decodes the payload received and extract the metrics received 
- enhance the decoded message to add 
    - *\<group_id\>
    - *\<edge_node_id\>
    - *\<device_id\> *if provided*
- extract metric name to get ISA-95 UNS namespace
- if metric alias is used, map the metric alias to previously provided metric name
- collate all metrics specific to one metric name and create a consolidated message payload
- publish consolidate message payload to the UNS namespace

This is  **not** a SCADA/IIOT host and will not be publishing any control messages to the broker 

## Mapping logic for SparkplugB to ISA-95 
With reference to the article [Using Sparkplug to Map ISA 95](https://www.hivemq.com/solutions/manufacturing/smart-manufacturing-using-isa95-mqtt-sparkplug-and-uns/), each SparkPlugB message contains an attribute **name** which contains the ISA namespace for the message in addition to the tag. 
e.g.
```json
{
"timestamp": 1486144502122,
"metrics": [{
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
When we parse the metric name we get 
    - The topic name in the UNS i.e. `Enterprise/Site/Area/Line/Cell`
    - The name of the tag i.e. `Tag1` and `Tag2` which will now be added as an attribute to the JSON object being published to the UNS

The spB payload may contain multiple metrics which belong to different topics hence we merge all tags belonging to the name UNS topic. The logic for merging is as following
    - the name of the metric will be split into the topic and tag
    - tags for the same topic are merged in to one JSON object
    - if a metric is historical, we create an array of tag values with the latest version being at 0 position
    - if a metric name is duplicated and not historical, the newer tag value will override the older tag value in the JSON object
    - the overall timestamp for the JSON object is the max of timestamps of all the tags  



This mapping is to be done only for the message types 
   - NDATA
   - DDATA
   - NCMD
   - DCMD 
***IMPORTANT: The birth and death messages are not mapped to the UNS currently***

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
1. [settings.yaml](./conf/settings.yaml):  Contain the key configurations need to connect with MQTT brokers as well as timescale db
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
    sparkplugb |   | *currently empty*|
    **dynaconf_merge**\*  |  | Mandatory param. Always keep value as true  |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster and the timescaledb
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
   **dynaconf_merge**\*  |  | | Mandatory param. Always keep value as true  |

   
## Running the python script
This function is executed by the following command with the current folder as [`05_sparkplugb`](.)
```bash
# install virtual env
python -m pip install --user virtualenv
python -m venv env_sparkplugb
source env_sparkplugb/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
python ./src/uns_sparkplugb/uns_sparkplugb.py
```

### Running tests
The set of test for this module is executed by
```bash
source env_sparkplugb/bin/activate
python -m pip install  -r requirements_dev.txt
#run all tests excluding integration tests 
pytest -m "not integrationtest" test/
# runs all tests
pytest test/
```
# Reference
* [Eclipse Sparkplug B Specification](https://www.eclipse.org/tahu/spec/Sparkplug%20Topic%20Namespace%20and%20State%20ManagementV2.2-with%20appendix%20B%20format%20-%20Eclipse.pdf)
* [Cirrus Link Sparkplug B MQTT Tutorials](https://docs.chariot.io/display/CLD79/B%3A+Example+Python+Client)
* [Github Eclipse Tahu project](https://github.com/eclipse/tahu)
* [Google Protocol Buffers Project](https://github.com/protocolbuffers/protobuf)


## Limitations 
1. The application assumes the the MQTT broker for SparkPlugB and the UNS are one and the same as it does not sense to have separate brokers for the same. This can be enhanced easily if there is a requirement for the same. Please create issue on the Github project
1. Need to understand how to handle NBIRTH, NDEATH, DBIRTH, DDEATH, STATE message types
1. Need to understand how to handle metric types DataSet, Template 
1. Need to understand how to handle metadata, properties, is_multi_part etc.