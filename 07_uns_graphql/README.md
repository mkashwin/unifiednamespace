# GraphQL API for the Unified Namespace

[![UNS GraphQL Client](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_graphql-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_graphql-app.yml)

TBD
_TBD_

## Deploying and running GraphQL Server

## Queries supported

## Key Configurations to provide

This application has two configuration file.
All of these configurations are a combination of the configurations of the other modules with the exception of

- Not having the `mqtt.ignored_attributes` , `mqtt.topics`, `mqtt.reconnect_on_failure` as these are not relevant for the GraphQL services or the aiomqtt.Client being used.
- Additional mqtt configuration for `retry_interval` in case of MQTT errors
- Kafka configuration map should be specific to the the consumer configurations and not producer
- Additional Kafka configuration for controlling consumer poll timeout

1. [settings.yaml](./conf/settings.yaml): Contain the key configurations need to connect with MQTT brokers

   | **key**              | **sub key**                | **description**                                                                                                                                                         | **_default value_**                                         |
   | -------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
   | **mqtt**             | **host**\*                 | Hostname of the mqtt broker instant. Mandatory configuration                                                                                                            | _None_                                                      |
   | mqtt                 | port                       | Port of the mqtt broker (int)                                                                                                                                           | _1883_                                                      |
   | mqtt                 | qos                        | QOS for the subscription. Valid values are 0,1,2                                                                                                                        | _1_                                                         |
   | mqtt                 | keep\*alive                | Maximum time interval in seconds between two control packet published by the client (int)                                                                               | \_60\*                                                      |
   | mqtt                 | version                    | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31)                                          | _5_                                                         |
   | mqtt                 | clean\*session             | Boolean value to be specified only if MQTT Version is not 5                                                                                                             | \_None\*                                                    |
   | mqtt                 | transport                  | Valid values are "websockets", "tcp"                                                                                                                                    | _"tcp"_                                                     |
   | mqtt                 | timestamp\*attribute       | the attribute name which should contain the timestamp of the message's publishing                                                                                       | \*"timestamp"\_                                             |
   | mqtt                 | retry_interval             | Seconds to wait before trying to reconnect when there is an MQTT communication error                                                                                    | \_10\_                                                      |
   | **graphdb**          | **url**\*                  | Mandatory. The db connection URL string for your Neo4j instance                                                                                                         | _None_                                                      |
   | graphdb              | database                   | the data base name to write to. if not provided default db ('') will be used                                                                                            | _''_                                                        |
   | graphdb              | uns\*node_types            | List based on ISA-95 part 2 the nested depth. Nodes will by tagged with the node type depending on their depth. Can be of variable length. Recommended is 5             | ["ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE"]        |
   | graphdb              | spB_node_types             | List based SparkplugB namespace specifications. Nodes will by tagged with the node type depending on their depth. This must be of length 5                              | ["spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"] |
   | graphdb              | nested_attribute_node_type | Node Type used for nested attributes when they are created as child nodes to one of the topic nodes or another nested attribute node                                    | NESTED_ATTRIBUTE                                            |
   | **historian**        | **hostname**\*             | Mandatory. The db hostname of your TimescaleDB instance                                                                                                                 | \_None\*                                                    |
   | historian            | port                       | The port for the instance of your TimescaleDB instance                                                                                                                  | _5432_                                                      |
   | **historian**        | **database**\*             | Mandatory. The database name to write to.                                                                                                                               | _None_                                                      |
   | **historian**        | **table**\*                | Mandatory. The hypertable where the time-series of messages is stored.                                                                                                  | _None_                                                      |
   | **kafka**            | **config**\*               | Mandatory Dict. see [Kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). All non security configurations for consumer | _None_                                                      |
   | kafka                | consumer\*timeout          | Maximum time to block waiting for message in Seconds                                                                                                                    | \_1.0\*                                                     |
   | **dynaconf_merge**\* |                            | Mandatory param. Always keep value as true                                                                                                                              |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect
   This file is not checked into the repository for security purposes. However there is a template file provided [**`.secrets_template.yaml`**](./conf/.secrets_template.yaml) which should be edited and renamed to **`.secrets.yaml`**

   | **key**              | **sub key**    | **sub key**       | **description**                                                                                                                                     | **_default value_** |
   | :------------------- | :------------- | :---------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ |
   | mqtt                 | username       |                   | The user id needed to authenticate with the MQTT broker                                                                                             | _None_              |
   | mqtt                 | password       |                   | The password needed to authenticate with the MQTT broker                                                                                            | _None_              |
   | mqtt                 | tls            |                   | Provide a map of attributes needed for a TLS connection to the MQTT broker. See below attributes                                                    | _None_              |
   | mqtt                 | tls            | ca\*certs         | fully qualified path to the ca cert file. Mandatory for an SSL connection                                                                           | \_None\*            |
   | mqtt                 | tls            | certfile          | fully qualified path to the cert file                                                                                                               | _None_              |
   | mqtt                 | tls            | keyfile           | fully qualified path to the keyfile for the cert                                                                                                    | _None_              |
   | mqtt                 | tls            | cert\*reqs        | Boolean. If note provided then ssl.CERT_NONE is used. if True the ssl.CERT_REQUIRED is used. else ssl.CERT_OPTIONAL is used                         | \_None\*            |
   | mqtt                 | tls            | ciphers           | Specify which encryption ciphers are allowed for this connection                                                                                    | _None_              |
   | mqtt                 | tls            | keyfile\*password | Password used to encrypt your certfile and keyfile                                                                                                  | \_None\*            |
   | mqtt                 | tls            | insecure\*cert    | Boolean. Skips hostname checking required for self signed certificates.                                                                             | \_True\*            |
   | **graphdb**          | **username**\* |                   | The user id needed to authenticate with GraphDB                                                                                                     | _None_              |
   | **graphdb**          | **password**\* |                   | The password needed to authenticate with GraphDB                                                                                                    | _None_              |
   | **historian**        | **username**\* |                   | The user id needed to authenticate with TimescaleDB                                                                                                 | _None_              |
   | **historian**        | **password**\* |                   | The password needed to authenticate with TimescaleDB                                                                                                | _None_              |
   | historian            | sslmode        |                   | Enables encrypted connection to TimescaleDB. valid values are disable, allow, prefer, require, verify-ca, verify-full                               | _None_              |
   | historian            | sslcert        |                   | Specifies the file name of the client SSL certificate                                                                                               | _None_              |
   | historian            | sslkey         |                   | Specifies the location for the secret key used for the client certificate                                                                           | _None_              |
   | historian            | sslrootcert    |                   | Specifies the name of a file containing SSL certificate authority (CA) certificate(s)                                                               | _None_              |
   | historian            | sslcrl         |                   | Specifies the file name of the SSL certificate revocation list (CRL)                                                                                | _None_              |
   | kafka                | config         |                   | Dict. see [kafka client configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). Only the security related settings | _None_              |
   | **dynaconf_merge**\* |                |                   | Mandatory param. Always keep value as true                                                                                                          |

## Setting up the development environment for this module

This sub module can be independently setup as a dev environment in the folder [`07_uns_graphql`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance
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

## Exporting schema definition

The graphQL schema for this module can be found at **[uns_schema](./schema/uns_schema.graphql)**
This can be generated by the following command

```bash
strawberry export-schema uns_graphql.uns_graphql_app:UNSGraphql.schema  --output ./schema/uns_schema.graphql
```

### Running the GraphQL API Server

This function is executed by the following command with the current folder as [`07_uns_graphql`](.)

```bash
# Ensure that the uv shell is activated
uv venv
uv run uvicorn uns_graphql.uns_graphql_app:UNSGraphql.app --host 0.0.0.0 --port 8000
```

Update the hostname and port appropriately

#### Running the GraphQL API Server in development mode

````bash
strawberry server uns_graphql.uns_graphql_app:UNSGraphql.schema
```bash

### Running tests

The set of test for this module is executed by

```bash
#run all tests excluding integration tests
uv run pytest  -m "not integrationtest" test/
# runs all tests
uv run pytest test/
````

## Deploying the docker container image created for this module

The docker container image for this module are built and store in the Dockerize module published to [Github Container Registry](https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%graphql)

The way to run the container is

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

- **\<full path to conf\>**: Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). _Give the complete path and not relative path_

- If you are running this image on the host as the MQTT broker and/or neo4j pass the flag `--network host` along with docker run to enure `localhost` services on the host are correctly resolved

## Limitations / workarounds / pending

1. [] customize docker image to allow all possible [uvicorn deployment](https://www.uvicorn.org/deployment/) options
1. [] Document Guidelines for securing deployment ( Reverse Proxy | CDN ) etc.
1. [] Implement authorization / RBAC for the API queries & subscriptions
1. [] Implement Caching, Pagination support.
1. [] Explore if using ´gunicorn -k uvicorn.workers.UvicornWorker´ adds any value given [this thread on stack overflow](https://stackoverflow.com/questions/66362199/what-is-the-difference-between-uvicorn-and-gunicornuvicorn)
1. [] Stronger authentication and authorization, passing user principle to backend database to ensure RBAC / consistent fine grained security
1. [] Architecture to secure the GraphQL server (reverse proxy, TLS, caching etc.)

## References

1. [Official GraphQL Documentation](https://graphql.org/): Official website with comprehensive guides, tutorials, and specifications.
   - [GraphQL Python Support](https://graphql.org/code/#python): list of Python based libraries for GraphQL
   - [Why Strawberry](https://mobilelive.medium.com/graphql-in-python-a-comprehensive-guide-to-building-apis-59cb0d638c03):
1. [Code vs Schema Development of GraphQL](https://blog.logrocket.com/code-first-vs-schema-first-development-graphql/): Blog comparing the approaches used for developing GraphQL services
1. [FastAPI vs Flask](https://www.turing.com/kb/fastapi-vs-flask-a-detailed-comparison)
