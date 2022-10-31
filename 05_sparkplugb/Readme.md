[![SparkplugB Decoder](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_sparkplugb-app.yml)

# Decoder Application to process SparkPlugB 
This SparkplugB decoder is an MQTT Application Node  deployed on the edge with the following functionality
- subscribes to the  Topic *`spBv1.0/#`* 
- decodes the payload received.
- translate the sparkplugB topic name space to the ISA-95 UNS 
This is  **not** a SCADA/IIOT host and will not be publishing any control messages to the broker 

# SparkplugB™ Topic Namespace 
SparkplugB Topic namespace follows the following structure 
>**spBv1.0**/*\<group_id\>*/*\<message_type\>*/*\<edge_node_id\>*/*[\<device_id\>]*

Where in:
* *\<group_id\>*:  provides for a logical grouping of MQTT EoN nodes
* *\<message_type\>*  provides an indication as to how to handle the MQTT payload of the message. The following message_type elements are defined for the SparkplugB™ Topic Namespace:
    - NBIRTH: Birth certificate for MQTT EoN nodes.
    - NDEATH: Death certificate for MQTT EoN nodes.
    - DBIRTH: Birth certificate for Devices.
    - DDEATH: Death certificate for Devices.
    - NDATA: Node data message.
    - DDATA: Device data message.
    - NCMD: Node command message.
    - DCMD: Device command message.
    - STATE: Critical application state message
    Please refer to the detailed specification of these message types in the [SparkplugB Specs](https://www.eclipse.org/tahu/spec/Sparkplug%20Topic%20Namespace%20and%20State%20ManagementV2.2-with%20appendix%20B%20format%20-%20Eclipse.pdf)
* *\<edge_node_id\>*: uniquely identifies the MQTT EoN node within the factory context.
* *[\<device_id\>]*: optional and  identifies a device attached (physically or logically) to the MQTT EoN node

## Mapping logic for SparkplugB to ISA-95 
\<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>
**SparkplugB Namespace** |  **ISA-95 Namespace** | ***Comments*** 
------ | ------ | ------
spBv1.0 | - | Default namespace for sparkplugB. No mapping needed 
\<group_id\> | \<enterprise\>/\<facility\> | Map the group id or the alias to the enterprise and facility
\<message_type\> | - | Provides guidance on handling the payload. Not needed for mapping
\<edge_node_id\> | \<area\>/\<line\> | Map the edge node id or the alias to the area and the line 
\<device_id\> | \<device\> | Map the device id to th end device. If the device id is not provided then <br />extract the device(s) from the payload to appropriately map the messages

# Preparation steps required to setup protocol buffer and SparkplugB dependencies
1. **Step 1**: Download or install protoc. Refer 
    - [Installing on Linux/MacOs](https://grpc.io/docs/protoc-installation/)
    - [Install pre-compiled version](https://github.com/protocolbuffers/protobuf/releases). This project currently is using version  [Protocol Buffers v3.19.4](https://github.com/protocolbuffers/protobuf/releases/tag/v3.19.4) 
    and downloaded the pre-compiled versions for  linux-x86_64 and win64. For other platforms please replace with the appropriate runtime or compile the runtime directly
1. **Step 2**: Copy the [SparkPlugB protocol buffer specification](https://github.com/eclipse/tahu/tree/master/sparkplug_b/sparkplug_b.proto) from [Eclipse Tahu project](https://github.com/eclipse/tahu/tree/master/sparkplug_b) to the folder [./sparkplug_b](./sparkplug_b/)
1. **Step 3**: Compile the SparkplugB protocol buffer into python class by the following command
    > 
    ```bash
    # Execute on Linux
    ./protobuf/bin/protoc -I ./sparkplug_b/  --python_out=./src/uns_sparkplugb/generated ./sparkplug_b/sparkplug_b.proto
    ```
    >
    ```powershell
    # Execute on windows
    .\protobuf\bin\protoc.exe -I .\sparkplug_b\  --python_out=.\src\uns_sparkplugb\generated .\sparkplug_b\sparkplug_b.proto
    ```
## Key Configurations to provide
This application has two configuration file. 
1. [settings.yaml](./conf/settings.yaml):  Contain the key configurations need to connect with MQTT brokers as well as timescale db
    **key** | **sub key** | **description**  | ***default value*** |
    ------ | ------ | ------ | ------
    **mqtt** | **host**\*| Hostname of the mqtt broker instant. Mandatory configuration | *None*
    mqtt | port | Port of the mqtt broker (int) | *1883*
    mqtt | topic | Must be in the names space of SpB  i.e. **spBv1.0/#** | *spBv1.0/#* 
    mqtt | qos | QOS for the subscription. Valid values are 0,1,2 | *1*
    mqtt | keep_alive | Maximum time interval in seconds between two control packet published by the client (int) | *60*
    mqtt | reconnect_on_failure | Makes the client handle reconnection(s). Recommend keeping this True  (True,False)| *True*
    mqtt | version | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31) | *5*
    mqtt | transport | Valid values are "websockets", "tcp" | *"tcp"*
    mqtt | ignored_attributes | Map of topic &  list of attributes which are to be ignored from persistance. supports wild cards for topics  and nested via . notation for the attributes <br /> e.g.<br />  {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } |  None 
    mqtt | timestamp_attribute | the attribute name which should contain the timestamp of the message's publishing| *"timestamp"*
    sparkplugb | | |*None*
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
1. The proto files were not being compiled correctly with [Protobuf Ver 3.20.0 and higher](https://github.com/protocolbuffers/protobuf/releases/tag/v3.20.0) hence I had to downgrade the protobuf version to  [Protobuf v3.19.4](https://github.com/protocolbuffers/protobuf/releases/tag/v3.19.4)

1. The protoc executable for [Linux](./protobuf/bin/protoc) is for x86_64  architecture and will need execute rights to be able to run and compile the [sparkplug_b.proto](./sparkplug_b/sparkplug_b.proto) specification. For other architectures please download the appropriate pre compiled version of [Protobuf release v3.19.4](https://github.com/protocolbuffers/protobuf/releases/tag/v3.19.4) e.g.
    - [protoc-3.19.4-linux-aarch_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-linux-aarch_64.zip)
    - [protoc-3.19.4-linux-ppcle_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-linux-ppcle_64.zip)
    - [protoc-3.19.4-linux-s390_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-linux-s390_64.zip)
    - [protoc-3.19.4-linux-x86_32.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-linux-x86_32.zip)
