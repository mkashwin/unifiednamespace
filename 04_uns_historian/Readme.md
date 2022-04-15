# Application to store messages to Historian 
[![MQTT Client for Historian](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_historian-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/uns_historian-app.yml)
It makes sense to have the historian connect only to the corporate / cloud instance since the factory doesn't necessarily need the history of all messages. The historian should  subscribe to '**#**' or the first level **\<enterprise\>/#**' topic wildcard. However if it is needed for your specific scenario you can easily deploy a historian at the factory level.
If you need to scale and reduce the load on broker multiple instanced of this client can be deployed with separate topic wild cards
> Ensure that each instance is subscribing to it's unique topic and not causing any overlaps

## Deploying and running TimescaleDB
There are a number of ways to deploy and run your TimescaleDB instance locally. 
I chose to run this as a docker instance to ease the setup and portability. 

**[Detail Guide](https://docs.timescale.com/install/latest/installation-docker/#install-self-hosted-timescaledb-from-a-pre-built-container)**

>**Important Note:** Remember to update the passwords being passed to the docker run command for the postgres user (i.e. `-e POSTGRES_PASSWORD=<postgres user pwd>`)
Quick command reference 
```bash
sudo apt install postgresql-client-common postgresql-client-12 postgresql-doc-12
docker run \
    --name uns_timescaledb  \
    -p 5432:5432  \
    -v $HOME/timescaledb/data:/var/lib/postgresql/data \
    -d \
    -e POSTGRES_PASSWORD=uns_historian \
    timescale/timescaledb:latest-pg14
# =--name : name given to your container
# -p : provide ports of operation 
# -v : volume to persist data 
#- d : run the container detached
#-e POSTGRES_PASSWORD=uns_historian \ #<super user password>. REMEMBER to update the password

# Create the db and enable the timescaledb extension
psql -U postgres -h localhost -f './sql_scripts/01_setup_db.sql'

#create DBA
docker exec -ti uns_timescaledb bash -c "su postgres -c 'createuser --createdb --createrole --login -e uns_dba -P'" 
# Manually enter the password for the dba

#create application user (to be used in the configuration by the application)
docker exec -ti uns_timescaledb bash -c "su postgres -c 'createuser --login -e uns_dbuser -P'"
#Manually enter the password for application user

# create the hypertable with the application user 
psql -U uns_dbuser  -h localhost -d uns_historian -f './sql_scripts/02_setup_hypertable.sql'

```
**The key parameters you must update for your environment are :**
* \<postgres password\> : password for the super user which is passed to the docker command  `-e POSTGRES_PASSWORD=`
* \<dba password\> : password for the DBA will be needed for db mgmt. activities
* \<application user password\> : is the password needed to connect to the DB. Needs to also be updated in [./.secrets.yaml](#key-configurations-to-provide) 

Depending on your context you may need to change the other properties like container name, port, directories etc. 
Once the docker container is deployed you can start / stop it by the commands
```bash
docker start  uns_timescaledb #<container_name>
docker stop  uns_timescaledb #<container_name>
```
## Key Configurations to provide
This application has two configuration file. 
1. [settings.yaml](./settings.yaml):  Contain the key configurations need to connect with MQTT brokers as well as timescale db
    **key** | **sub key** | **description**  | ***default value*** |
    ------ | ------ | ------ | ------
    **mqtt** | **host**\*| Hostname of the mqtt broker instant. Mandatory configuration | *None*
    mqtt | port | Port of the mqtt broker (int) | *1883*
    mqtt | topic | Topic to be subscribed to. Recommend subscribing to a level + # e.g. "erp/#" | *"#"* 
    mqtt | qos | QOS for the subscription. Valid values are 0,1,2 | *1*
    mqtt | keep_alive | Maximum time interval in seconds between two control packet published by the client (int) | *60*
    mqtt | reconnect_on_failure | Makes the client handle reconnection(s). Recommend keeping this True  (True,False)| *True*
    mqtt | version | The MQTT version to be used for connecting to the broker. Valid values are : 5 (for MQTTv5), 4 (for MQTTv311) , 3(for MQTTv31) | *5*
    mqtt | transp ort | Valid values are "websockets", "tcp" | *"tcp"*
    mqtt | ignored_attributes | Map of topic &  list of attributes which are to be ignored from persistance. supports wild cards for topics  and nested via . notation for the attributes <br /> e.g.<br />  {<br /> 'topic1' : ["attr1", "attr2", "attr2.subAttr1" ],<br /> 'topic2/+' : ["A", "A.B.C"],<br /> 'topic3/#' : ["x", "Y"]<br /> } |  None 
    mqtt | timestamp_attribute | the attribute name which should contain the timestamp of the message's publishing| *"timestamp"*
    **historian** | **hostname**\* | Mandatory. The db hostname of your TimescaleDB  instance| *None*
    historian | port |  The port for the instance of your TimescaleDB  instance| *5432*
    **historian**  | **database**\*  | Mandatory. The database name to write to. See [db script](./sql_scripts/01_setup_db.sql) | *None*
    **historian** | **table**\*| Mandatory. The hypertable where the time-series of messages is stored. See [db script](./sql_scripts/02_setup_hypertable.sql)| *None* 
    **dynaconf_merge**\*  |  | Mandatory param. Always keep value as true  |

1. [.secret.yaml](./.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster and the timescaledb
    This file is not checked into the repository for security purposes. However there is a template file provided **`.secrets_template.yaml`** which should be edited and renamed to **`.secrets.yaml`**
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
   **historian** | **username**\* | | The user id  needed to authenticate with TimescaleDB | *None*
   **historian** | **password**\* | | The password needed to authenticate with TimescaleDB | *None*
   historian | sslmode | | Enables encrypted connection to TimescaleDB. valid values are disable, allow, prefer, require, verify-ca, verify-full | *None*
   **dynaconf_merge**\*  |  | | Mandatory param. Always keep value as true  |
## Running the python script
This function is executed by the following command with the current folder as `03_uns_graphdb`
```bash
# install virtual env
python -m pip install --user virtualenv
python -m venv env_historian
source env_historian/bin/activate
python -m pip install --upgrade pip
python -m pip install  -r requirements.txt
python ./src/uns_historian/uns_mqtt_historian.py
```

### Running tests
The set of test for this module is executed by
```python
source env_historian/bin/activate
python -m pip install  -r requirements_dev.txt
pytest test/
TBD
```


## The Logic for persisting the message into the historian
The historian will be persisting all the MQTT messages in the raw format directly after extracting the timestamp from the message
The message format is expected to be in JSON and should have an attribute `timestamp`
The attribute key name is configurable in [settings.yaml](./settings.yaml)
If this attribute is missing the application will use the current time 
```python
time.time()
```


## Limitations 
1. Need to check how to containerize and perhaps deploy this on the same cluster as the MQTT  brokers
1. Add and improve automated test coverage 
