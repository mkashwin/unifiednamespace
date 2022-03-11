# Application to store messages to graphDB 

We will be publishing messages as per the ISA-95 part 2 specifications
> \<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>

We choose a graph database in this case because it allows us to define and maintain relationships and connections across our enterprise as well as merge messages to the same topic.
e.g. the ERP system which is publishing to the Enterprise node can have a relationship with a device allowing us to easily correlate identifiers across the various systems.

The Graph DB is not a store for historical data, this decision is done for performance purposes. For that refer to the [historian](./../04_uns_historian/Readme.md)

The GraphDB is also deployed both at the factory level and enterprise level. 
Devices can query the GraphDB if they need merged data. If they just need the latest message published it would be more efficient to subscribe to the topic ( assuming that MQTT messages are published with retain flag as true)

We need setup 2 instances of this connector
1. ***(Mandatory)*** Setup the application to point to the enterprise instance / cloud instance . This instance will be used by the to link data across all factories and enterprise application. It is important to have the connector listen to Topic '#" while connecting to the enterprise/cloud  MQTT cluster instance.
1. ***(Optional)*** Setup the application to point to the factory instance. This instance will be used by the application to provide a snapshot of the merged data to the factory devices. For the factory cluster it would make sense to listen to the  level 4 topic i.e. `+/+/+/#`

## Deploying and running Neo4j
There are a number of ways to deploy and run your Neo4j instance. 
I chose to run this as a docker instance to ease the setup and portability. 

**[Detail Guide](https://neo4j.com/developer/docker-run-neo4j/)**
Quick command reference 
```bash
docker run \
    --name  uns_graphdb \           # <container_name> . Needed 
    -p7474:7474 -p7687:7687 \       # Ports of operation 
    -d \                            # Runs the container detached 
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH= neo4j/uns_neo4j_password \ #**<username/**<password>** 
    neo4j:latest
```
**The key parameters you must update for your environment are :**
* \<container_name\> : is a name you give to identify your container
* \<username\> : is the username needed to connect to the DB. Needs to be updated in [./.secrets.yaml](#key-configurations-to-provide)
* \<password\> : is the password needed to connect to the DB. Needs to be updated in [./.secrets.yaml](#key-configurations-to-provide) 

Depending on your context you may need to change the other properties like port, directories etc. 
Once the docker container is deployed you can work on 
```bash
docker start  uns_graphdb #<container_name>
docker stop  uns_graphdb #<container_name>
```

## Key Configurations to provide
This application has two configuration file 
1. [settings.yaml](./settings.yaml):  Contain the key configurations need to connect with MQTT brokers as well as Neo4j db.
    The key configurations to update are
    - mqtt.url
    - graphdb.url
    
1. [.secret.yaml](./.secrets_template.yaml) : Contains the username and passwords to connect to the MQTT cluster and the GraphDB
    This file is not checked into the repository for security purposes. However there is a template file provided **`.secrets_template.yaml`** which should be edited and renamed to **`.secrets.yaml`**

## Running the python script

## Logic for persisting MQTT messages to the Graph DB
The GraphDB will always store the latest value of all attributes but allows merging of MQTT messages also.

**It is important to model the the data structure correctly specially to ensure that different messages on the same topic are correctly merged.**

All messages which are published to the same topic name will be merged to the same node. If two messages publish the same attribute in their message the the newer message attribute will override the existing value
 
The node type will be determined the topic depth on which it is publish

**MQTT Topic** | **Node Type**
------ | ------
\+ | enterprise
\+/\+ | facility
\+/\+/\+ | area
\+/\+/\+/\+ | line
\+/\+/\+/\+/\+ | device


e.g. Any message published to the topic `erp/` will be saved as node of type Enterprise. 
The topic name "*erp*" will be the identifier so if multiple messages are published to the same topic all those attributes will be merged. 

Topic : **erp/** 

*message 1:* 
```json 
    {timestamp: 202203011130, id1: "identifier"} 
```
*message 2:* 
```json 
    {timestamp: 202203011145, sensor1: 100} 
```

will result in a node in the GraphDB
```json
(erp:enterprise : { id1: "identifier", sensor1: 100, timestamp: 202203011145})
```
## Tag extraction from message
TBD.
[ ] Need to discuss and update the logic of tag extraction especially for PLC other IIoT devices

## Limitations / workarounds 
1. Neo4j does not support nested attributes. If your message contains nested data the current logic will flatten the JSON object. 
   See the function [_flatten_json_for_Neo4J()](./graphdb_handler.py#_flatten_json_for_Neo4J)
1. If your MQTT message contains the key ***"node_name"***, The key will be changed to uppercase before storing. This is because our application uses the key ***"node_name"*** to uniquely identify the node. This is the stripped topic name
1. Current code & configurations have not considered securing the database and encrypted connections
1. Current code & configurations have not considered securing the MQTT broker authentication and encrypted connections
1. Need to check how to containerize and perhaps deploy this on the same cluster as the MQTT  brokers
1. Add and improve automated test coverage