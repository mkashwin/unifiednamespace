# Application to store messages to graphDB 

We will be publishing messages as per the ISA-95 part 2 specifications
> \<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>

We choose a graph database in this case because it allows us to define and maintain relationships and connections across our enterprise as well as merge messages to the smae topic
The Graph DB is not a store for historical data, this decision is done for performance purposes. For that refer to the [historian](./../04_uns_historian/Readme.md)

All messages which are published to the same topic name will be merged to the same node
The node type will be determined the node type

e.g. Any message published to the \erp\> level topic will be saved as node of type Enterprise. The topic name "*erp*" will be the identifier so if multiple messages are published to the same topic all those attributes will be merged. If two messages publish the same attribute in their message the the newer message

- 
e.g. the ERP system which is publishing to the Enterprise node can have a relationship with a device allowing us to easily correlate identifiers across the various systems. 

The GraphDB is also deployed both at the factory level and enterpise level. 
Devices can query the GraphDB if they need merged data. If they just need the latest message published it would be more 

We need setup 2 instances of this connector
1. ***(Mandatory)*** Setup the application to point to the enterprise instance / cloud instance . This instance will be used by the to link data across all factories and enterprise application. It is important to have the connector listen to Topic '#" while connecting to the enterprise/cloud  MQTT cluster instance.
1. ***(Optional)*** Setup the application to point to the factory instance. This instance will be used by the application to provide a snapshot of the merged data to the factory devices. For the factory cluster it would make sense to listen to the  level 4 topic 



## The function for persisting the message into the graph DB
We create 2 functions
###Funtion 1: Graph DB
Stores the latest value
It is important to model the the data structure correctly specially to ensure that different messages on the same topic are correctly merged. 



## Limitations 


