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

## Limitations 
1. Currently the application does not support further nested topics 
2. Need to figure out how to define the relationships between the tags other than parent relationship
