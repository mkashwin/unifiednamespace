# Application to store messages to Historian 

It makes since to have the historian connect only to the corporate / cloud instance since the factory doesn't necessarily need the history of all messages. The historian should  subscribe to '**#**' or the first level **\<enterprise\>/#**' topic wildcard
If you need to scale and reduce the load on broker multiple instanced of this client can be deployed with separate topic wild cards
> Ensure that each instance is subscribing to it's unique topic and not causing any overlaps

## Deploying and running TimescaleDB
There are a number of ways to deploy and run your TimescaleDB instance locally. 
I chose to run this as a docker instance to ease the setup and portability. 

**[Detail Guide](https://docs.timescale.com/install/latest/installation-docker/#install-self-hosted-timescaledb-from-a-pre-built-container)**

Quick command reference 
```bash
sudo apt install postgresql-client-common postgresql-client-12 postgresql-doc-12
docker run \
    --name uns_timescaledb \ 
    -p 5432:5432 \ # Ports of operation 
    -v $HOME/timescaledb/data:/var/lib/postgresql/data \
    -d \  # Runs the container detached     
    -e POSTGRES_PASSWORD=uns_historian \ #<super user password>. REMEMBER to update the password
    timescale/timescaledb:latest-pg14


# Create the db and enable the timescaledb extension
psql -U postgres -h localhost -f './sql_scripts/01_setup_db.sql'

#create DBA
docker exec -ti uns_timescaledb bash -c "su -u postgres -c 'createuser --createdb --createrole --login -e uns_dba -P'" 
# Manually enter the password for the dba

#create application user (to be used in the configuration by the application)
docker exec -ti uns_timescaledb bash -c "su -u postgres -c 'createuser --login -e uns_dbuser -P'"
#Manually enter the password for application user

# create the hypertable with the application user 
psql -U uns_dbuser  -h localhost -d uns_historian -f './sql_scripts/02_setup_hypertable.sql'

```
**The key parameters you must update for your environment are :**
* \<container_name\> : is a name you give to identify your container
* \<postgres password\> : password for the super user. 
* \<dba password\> : password for the DBA will be needed for db mgmt. activities
* \<application user password\> : is the password needed to connect to the DB. Needs to be updated in [./.secrets.yaml](#key-configurations-to-provide) 

Depending on your context you may need to change the other properties like port, directories etc. 
Once the docker container is deployed you can work on 
```bash
docker start  uns_timescaledb #<container_name>
docker stop  uns_timescaledb #<container_name>
```
## Key Configurations to provide
This application has two configuration file. 
1. [settings.yaml](./settings.yaml):  Contain the key configurations need to connect with MQTT brokers as well as timescale db. 
    The key configurations to update are
    - mqtt.url
    - historian.url
Defaults for the other parameters are in the file with comments.

1. [.secret.yaml](./.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster and the timescaledb
    This file is not checked into the repository for security purposes. However there is a template file provided **`.secrets_template.yaml`** which should be edited and renamed to **`.secrets.yaml`**

## Running the python script
This function is executed by the following command with the current folder as `03_uns_graphdb`
```bash
# install virtual env
python3 -m pip install --user virtualenv
python3 -m venv env_historian
source env_historian/bin/activate
pip3 install -r requirements.txt
python3 ./src/uns_historian/uns_mqtt_historian.py
```

### Running tests
The set of test for this module is executed by
```python
pytest test/
TBD
```


## The Logic for persisting the message into the historian
The historian will be persisting all the MQTT messages in the raw format directly after extracting the timestamp from the message
The message format is expected to be in JSON and should have an attribute `timestamp`
The attribute key name is configurable in [settings.yaml](./settings.yaml)
If this attribute is missing the application will use the current time 
```python
datetime.datetime.now()
```



### Tag extraction from message
TBD.



## Limitations 
1. In the current design and architecture, the connection to the data base is created for every message and then closed. There is no connection pooling. Need to evaluate the performance impact of that as well as consider alternative designs
