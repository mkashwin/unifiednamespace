# GraphQL API for the Unified Namespace

[![UNS GraphQL Client](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_graphql-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_graphql-app.yml)

TBD
*TBD*

## Deploying and running GraphQL Server

## Queries supported

## Key Configurations to provide

This application has two configuration file.
All of these configurations are a combination of the configurations of the other modules with the exception of

- Not having the `mqtt.ignored_attributes` and`mqtt.topics`  as these are not relevant for the GraphQL services
- Kafka configuration map should be specific to the the consumer configurations and not producer
- Additional Kafka configuration for controlling consumer poll timeout

1. [settings.yaml](./conf/settings.yaml):  Contain the key configurations need to connect with MQTT brokers
    **key** | **sub key** | **description**  | ***default value*** |
    ------ | ------ | ------ | ------
    **mqtt** | **host**\*| Hostname of the mqtt broker instant. Mandatory configuration | *None*
    mqtt | port | Port of the mqtt broker (int) | *1883*
    mqtt | qos | QOS for the subscription. Valid values are 0,1,2 | *1*
    mqtt | keep_alive | Maximum time interval in seconds between two control packet published by the client (int) | *60*
    mqtt | reconnect_on_failure | Makes the client handle reconnection(s). Recommend keeping this True  (True,False)| *True*
    mqtt | version | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31) | *5*
    mqtt | clean_session | Boolean value to be specified only if MQTT Version is not 5 | *None*
    mqtt | transport | Valid values are "websockets", "tcp" | *"tcp"*
    mqtt | timestamp_attribute | the attribute name which should contain the timestamp of the message's publishing| *"timestamp"*
    **graphdb** | **url**\* | Mandatory. The db connection URL string for your Neo4j instance| *None*
    graphdb | database | the data base name to write to. if not provided default db ('') will be used | *''*
    graphdb | uns_node_types | List based on ISA-95 part 2 the nested depth. Nodes will by tagged with the node type depending on their depth. Can be of variable length. Recommended is 5 | ["ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE"]
    graphdb | spB_node_types | List based SparkplugB namespace specifications. Nodes will by tagged with the node type depending on their depth. This must be of length 5 | ["spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"]
    graphdb | nested_attribute_node_type | Node Type used for nested attributes when they are created as child nodes to one of the topic nodes or another nested attribute node | NESTED_ATTRIBUTE
    **historian** | **hostname**\* | Mandatory. The db hostname of your TimescaleDB  instance| *None*
    historian | port |  The port for the instance of your TimescaleDB  instance| *5432*
    **historian**  | **database**\*  | Mandatory. The database name to write to. | *None*
    **historian** | **table**\*| Mandatory. The hypertable where the time-series of messages is stored.| *None*
    **kafka** | **config**\*  | Mandatory Dict. see [Kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). All non security configurations | *None*
    kafka | consumer_timeout |  The port for the instance of your TimescaleDB  instance| *10*
    **dynaconf_merge**\*  |  | Mandatory param. Always keep value as true  |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect
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
   **graphdb** | **username**\* | | The user id  needed to authenticate with GraphDB | *None*
   **graphdb** | **password**\* | | The password needed to authenticate with GraphDB | *None*
   **historian** | **username**\* | | The user id  needed to authenticate with TimescaleDB | *None*
   **historian** | **password**\* | | The password needed to authenticate with TimescaleDB | *None*
   historian | sslmode | | Enables encrypted connection to TimescaleDB. valid values are disable, allow, prefer, require, verify-ca, verify-full | *None*
   kafka | config | | Dict. see [kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). Only the security related settings   |  *None*
   **dynaconf_merge**\*  |  | | Mandatory param. Always keep value as true  |

## Setting up the development environment for this module

This sub module can be independently setup as a dev environment in the folder [`07_uns_graphql`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance
This has been tested on **Unix(bash)**, **Windows(powershell)** and **Mac(zsh)**

```bash
python -m pip install --upgrade pip
pip install poetry
# Ensure that the poetry shell is activated
poetry shell
python -m pip install --upgrade pip poetry
poetry install
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

## Exporting schema definition

The graphQL schema for this module can be found at **[uns_schema](./schema/uns_schema.graphql)**
This can be generated by the following command

```bash
strawberry export-schema uns_graphql.uns_graphql_app:UNSGraphql.schema  --output ./schema/uns_schema.graphql
```

### Running the GraphQL API Server

This function is executed by the following command with the current folder as [`07_uns_graphql`](.)

```bash
# Ensure that the poetry shell is activated
poetry shell
@FIXME
```

#### Running the GraphQL API Server in development mode

```bash
strawberry server uns_graphql.uns_graphql_app:UNSGraphql.schema
```bash

### Running tests

The set of test for this module is executed by

```bash
#run all tests excluding integration tests
poetry run pytest  -m "not integrationtest" test/
# runs all tests
poetry run pytest test/
```

## Deploying the docker container image created for this module

The docker container image for this module are built and store in the Dockerize module published to [Github Container Registry](https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%graphql)

The way to run the container  is

```bash
# docker pull ghcr.io/mkashwin/unifiednamespace/uns/graphql:<tag>
# e.g.
docker pull ghcr.io/mkashwin/unifiednamespace/uns/graphql:latest

# docker run --name <container name> -d -v <full path to conf>:/app/conf uns/graphql:<tag>
# e.g.
docker run --name uns_graphql -d -v $PWD/conf:/app/conf uns/graphql:latest

```

**Note**: Remember to update the following before executing

- **\<container name\>** : Identifier for the container so you can work with the same container instance using

   ```bash
   docker start <container name>
   docker stop <container name>
   ```

- **\<full path to conf\>**: Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). *Give the complete path and not relative path*

- If you are running this image on the host as the MQTT broker  and/or neo4j pass the flag  `--network host` along with docker run to enure `localhost` services on the host are correctly resolved

## Limitations / workarounds

## References

1. [Official GraphQL Documentation](https://graphql.org/): Official website with comprehensive guides, tutorials, and specifications.
    - [GraphQL Python Support](https://graphql.org/code/#python): list of Python based libraries for GraphQL
    - [Why Strawberry](https://mobilelive.medium.com/graphql-in-python-a-comprehensive-guide-to-building-apis-59cb0d638c03):
1. [Code vs Schema Development of GraphQL](https://blog.logrocket.com/code-first-vs-schema-first-development-graphql/): Blog comparing the approaches used for developing GraphQL services
1. [FastAPI vs Flask](https://www.turing.com/kb/fastapi-vs-flask-a-detailed-comparison)
