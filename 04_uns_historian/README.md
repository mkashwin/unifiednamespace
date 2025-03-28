# Application to store messages to Historian

[![MQTT Client for Historian](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_historian-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_historian-app.yml)

It makes sense to have the historian connect only to the corporate / cloud instance since the factory doesn't necessarily need the history of all messages. The historian should subscribe to '**#**' or the first level **\<enterprise\>/#**' topic wildcard. However if it is needed for your specific scenario you can easily deploy a historian at the factory level.
If you need to scale and reduce the load on broker multiple instanced of this client can be deployed with separate topic wild cards

> Ensure that each instance is subscribing to it's unique topic and not causing any overlaps

## Deploying and running TimescaleDB

There are a number of ways to deploy and run your TimescaleDB instance locally.
I chose to run this as a docker instance to ease the setup and portability.

**[Detail Guide](https://docs.timescale.com/install/latest/installation-docker/#install-self-hosted-timescaledb-from-a-pre-built-container)**

> **Important Note:** Remember to update the passwords being passed to the docker run command for the postgres user (i.e. `-e POSTGRES_PASSWORD=<postgres user pwd>`)
> Quick command reference

```bash
# install docker
sudo snap install docker
# add current user to docker group so that we don't need to sudo for docker executions
sudo groupadd docker
sudo usermod -aG docker $USER
# you might need to reboot here
# install the postgres client
sudo apt install postgresql-client-common postgresql-client-12 postgresql-doc-12

# install & run postgres db
docker run \
    --name uns_timescaledb  \
    -p 5432:5432  \
    -v $HOME/timescaledb/data:/var/lib/postgresql/data \
    -d \
    -e POSTGRES_PASSWORD=uns_historian \
    timescale/timescaledb:latest-pg16
# =--name : name given to your container
# -p : provide ports of operation
# -v : volume to persist data
#- d : run the container detached
#-e POSTGRES_PASSWORD=uns_historian \ #<super user password>. REMEMBER to update the password

#create DBA
docker exec -ti uns_timescaledb bash -c "su postgres -c 'createuser --createdb --createrole --login -e uns_dba -P'"
# Manually enter the password for the dba

#create application user (to be used in the configuration by the application)
docker exec -ti uns_timescaledb bash -c "su postgres -c 'createuser --login -e uns_dbuser -P'"
#Manually enter the password for application user

# Create the db and enable the timescaledb extension
psql -U postgres -h localhost -f './sql_scripts/01_setup_db.sql'

# create the hypertable with the application user
psql -U uns_dbuser  -h localhost -d uns_historian -f './sql_scripts/02_setup_hypertable.sql'

```

**The key parameters you must update for your environment are :**

- \<postgres password\> : password for the super user which is passed to the docker command `-e POSTGRES_PASSWORD=`
- \<dba password\> : password for the DBA will be needed for db management activities
- \<application user password\> : is the password needed to connect to the DB. Needs to also be updated in [./.secrets.yaml](#key-configurations-to-provide)

Depending on your context you may need to change the other properties like container name, port, directories etc.
Once the docker container is deployed you can start / stop it by the commands

```bash
docker start  uns_timescaledb #<container_name>
docker stop  uns_timescaledb #<container_name>
```

## Key Configurations to provide

This application has two configuration file.

1. [settings.yaml](./conf/settings.yaml): Contain the key configurations need to connect with MQTT brokers as well as timescale db

   | **key**              | **sub key**           | **description**                                                                                                                                                                                                                                                                                              | **_default value_** |
   | -------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
   | **mqtt**             | **host**\*            | Hostname of the mqtt broker instant. Mandatory configuration                                                                                                                                                                                                                                                 | _None_              |
   | mqtt                 | port                  | Port of the mqtt broker (int)                                                                                                                                                                                                                                                                                | _1883_              |
   | mqtt                 | topics                | Array of topics to be subscribed to. Recommend subscribing to a level +/# and spBv1.0 e.g. ["erp/#","spBv1.0/#"]                                                                                                                                                                                             | _["#"]_             |
   | mqtt                 | qos                   | QOS for the subscription. Valid values are 0,1,2                                                                                                                                                                                                                                                             | _1_                 |
   | mqtt                 | keep\*alive           | Maximum time interval in seconds between two control packet published by the client (int)                                                                                                                                                                                                                    | \_60\*              |
   | mqtt                 | reconnect\*on_failure | Makes the client handle reconnection(s). Recommend keeping this True (True,False)                                                                                                                                                                                                                            | \_True\*            |
   | mqtt                 | version               | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31)                                                                                                                                                                               | _5_                 |
   | mqtt                 | clean\*session        | Boolean value to be specified only if MQTT Version is not 5                                                                                                                                                                                                                                                  | \_None\*            |
   | mqtt                 | transport             | Valid values are "websockets", "tcp"                                                                                                                                                                                                                                                                         | _"tcp"_             |
   | mqtt                 | ignored\*attributes   | Map of topic & list of attributes which are to be ignored from persistence. supports wild cards for topics and nested via . notation for the attributes <br /> e.g.<br /> {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } | None                |
   | mqtt                 | timestamp_attribute   | the attribute name which should contain the timestamp of the message's publishing                                                                                                                                                                                                                            | \*"timestamp"\_     |
   | **historian**        | **hostname**\*        | Mandatory. The db hostname of your TimescaleDB instance                                                                                                                                                                                                                                                      | \_None\_            |
   | historian            | port                  | The port for the instance of your TimescaleDB instance                                                                                                                                                                                                                                                       | _5432_              |
   | **historian**        | **database**\*        | Mandatory. The database name to write to. See [db script](./sql_scripts/01_setup_db.sql)                                                                                                                                                                                                                     | _None_              |
   | **historian**        | **table**\*           | Mandatory. The hypertable where the time-series of messages is stored. See [db script](./sql_scripts/02_setup_hypertable.sql)                                                                                                                                                                                | _None_              |
   | **dynaconf_merge**\* |                       | Mandatory param. Always keep value as true                                                                                                                                                                                                                                                                   |

1. [.secret.yaml](./conf/.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster and the timescaledb
   This file is not checked into the repository for security purposes. However there is a template file provided **`.secrets_template.yaml`** which should be edited and renamed to **`.secrets.yaml`**

   | **key**              | **sub key**    | **sub key**       | **description**                                                                                                             | **_default value_** |
   | :------------------- | :------------- | :---------------- | :-------------------------------------------------------------------------------------------------------------------------- | :------------------ |
   | mqtt                 | username       |                   | The user id needed to authenticate with the MQTT broker                                                                     | _None_              |
   | mqtt                 | password       |                   | The password needed to authenticate with the MQTT broker                                                                    | _None_              |
   | mqtt                 | tls            |                   | Provide a map of attributes needed for a TLS connection to the MQTT broker. See below attributes                            | _None_              |
   | mqtt                 | tls            | ca\*certs         | fully qualified path to the ca cert file. Mandatory for an SSL connection                                                   | \_None\*            |
   | mqtt                 | tls            | certfile          | fully qualified path to the cert file                                                                                       | _None_              |
   | mqtt                 | tls            | keyfile           | fully qualified path to the keyfile for the cert                                                                            | _None_              |
   | mqtt                 | tls            | cert\*reqs        | Boolean. If note provided then ssl.CERT_NONE is used. if True the ssl.CERT_REQUIRED is used. else ssl.CERT_OPTIONAL is used | \_None\*            |
   | mqtt                 | tls            | ciphers           | Specify which encryption ciphers are allowed for this connection                                                            | _None_              |
   | mqtt                 | tls            | keyfile\*password | Password used to encrypt your certfile and keyfile                                                                          | \_None\*            |
   | mqtt                 | tls            | insecure\*cert    | Boolean. Skips hostname checking required for self signed certificates.                                                     | \_True\*            |
   | **historian**        | **username**\* |                   | The user id needed to authenticate with TimescaleDB                                                                         | _None_              |
   | **historian**        | **password**\* |                   | The password needed to authenticate with TimescaleDB                                                                        | _None_              |
   | historian            | sslmode        |                   | Enables encrypted connection to TimescaleDB. valid values are disable, allow, prefer, require, verify-ca, verify-full       | _None_              |
   | historian            | sslcert        |                   | Specifies the file name of the client SSL certificate                                                                       | _None_              |
   | historian            | sslkey         |                   | Specifies the location for the secret key used for the client certificate                                                   | _None_              |
   | historian            | sslrootcert    |                   | Specifies the name of a file containing SSL certificate authority (CA) certificate(s)                                       | _None_              |
   | historian            | sslcrl         |                   | Specifies the file name of the SSL certificate revocation list (CRL)                                                        | _None_              |
   | **dynaconf_merge**\* |                |                   | Mandatory param. Always keep value as true                                                                                  |

## The Logic for persisting the message into the historian

The historian will be persisting all the MQTT messages in the raw format directly after extracting the timestamp from the message
The message format is expected to be in JSON and should have an attribute `timestamp`
The attribute key name is configurable in [settings.yaml](./conf/settings.yaml)
If this attribute is missing the application will use the current time

```python
time.time()
```

## Setting up the development environment for this module

This sub module can be independently setup as a dev environment in the folder [`04_uns_historian`](.)
This has been tested on **Unix(bash)**, **Windows(powershell)** and **Mac(zsh)**

```bash
python -m pip install --upgrade pip uv
# Ensure that the uv shell is activated
uv venv
uv sync

```

> While importing the folder into VSCode remember to do the following steps the first time
>
> 1. Open a terminal in VSCode
> 1. Activate the virtual environment
>
>    ```bash
>    python -m pip install --upgrade pip uv
>    uv venv
>    uv sync
>    ```
>
> 1. Select the correct python interpreter in VSCode (should automatically detect the .venv virtual environment)

## Running the python script

This function is executed by the following command with the current folder as [`04_uns_historian`](.)
Ensure that the [configuration files](./conf/) are correctly updated to your MQTT broker and database instance

```bash
# Ensure that the uv shell is activated
uv venv
uv sync
uv run uns_historian
```

## Running tests

The set of test for this module is executed by

```bash
#run all tests excluding integration tests
uv run pytest -m "not integrationtest" test/
# runs all tests
uv run pytest test/
```

## Deploying the docker container image created for this module

The docker container image for this module are built and store in the Dockerize module published to [Github Container Registry](https://github.com/mkashwin/unifiednamespace/pkgs/container/unifiednamespace%2Funs%2Fhistorian)

The way to run the container is

```bash
# docker pull ghcr.io/mkashwin/unifiednamespace/uns/historian:<tag>
# e.g.
docker pull ghcr.io/mkashwin/unifiednamespace/uns/historian:latest
# docker run --name <container name> -d s-v <full path to conf>/:/app/conf uns/historian:<tag>
docker run --name uns_mqtt_historian -d -v $PWD/conf:/app/conf ghcr.io/mkashwin/unifiednamespace/uns/historian:latest
```

**Note**: Remember to update the following before executing

- **\<container name\>** (optional): Identifier for the container so you can work with the same container instance using

  ```bash
  docker start <container name>
  docker stop <container name>
  ```

- **\<full path to conf\>** (Mandatory): Volume mounted to the container containing the configurations. See [Key Configurations to provide](#key-configurations-to-provide). _Give the complete path and not relative path_

- If you are running this image on the host as the MQTT broker and/or timescaledb pass the flag `--network host` along with docker run to enure `localhost` services on the host are correctly resolved

## Upgrade from postgres 14 to postgres 16

As part of upgrading to postgres16 there are a few steps needed to performed. The following guides provide information on proceeding with it. **It is strongly recommended to backup your existing database before performing the upgrade.** In case of your dev & test environment you can just delete the mount specified during [Deploying TimescaleDB docker](#deploying-and-running-timescaledb).

- [Upgrade postgres in docker](https://www.cloudytuts.com/tutorials/docker/how-to-upgrade-postgresql-in-docker-and-kubernetes/)
- [TimescaleDB Guide for upgrading Postgres](https://docs.timescale.com/self-hosted/latest/upgrades/upgrade-pg/r)
- [Upgrade TimescaleDB in the docker](https://docs.timescale.com/self-hosted/latest/upgrades/upgrade-docker/). Use the _bind mount_ guide

## Limitations

1. [x] ~~Add and improve automated test coverage~~
1. [ ] Currently all messages are stored in the same table. Should we create separate tables per topic or topic type?
