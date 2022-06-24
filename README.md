[![UNS Project](https://github.com/mkashwin/unifiednamespace/actions/workflows/python-app.yml/badge.svg)](https://github.com/mkashwin/unifiednamespace/actions/workflows/python-app.yml)

# Unified Name Space (UNS)
This project aims to create an open sourced option for setting up a unified name space for IIOT transformation.

My objective is to build an open source, free to use UNS solution for the community which can be enhanced and adapted by other enthusiasts. 

All components used in this solution are community versions and I do not own any rights on them. Most of them also provide a commercial / enterprise version which may also be considered to have better tool support.
I also used this, as an opportunity to learn Python.

## What is the Unified Name Space?
A unified namespace is a ***software solution*** that acts as a ***centralized repository*** of data, information, and context where any application or device can consume or publish data needed for a specific action via an ***event driven*** and ***loosely coupled architecture***. ​

This is a critical concept to allow scalability by preventing point to point connectivity.
![Credit Walter Reynolds -- IIOT University](./images/UNS.png)

**References / Further Reading**
1. [Video explaining UNS](https://youtu.be/PB_9HIgSCWc)
1. [UNS Q&A by Walter Reynolds](https://youtu.be/IiUZTSGjCQI)
1. [Event driven architecture on Wikipedia](https://en.wikipedia.org/wiki/Event-driven_architecture)​
1. [Advantages of Event Driven Architecture](https://developer.ibm.com/articles/advantages-of-an-event-driven-architecture/)

---
## **Architecture**
The overall architecture and the deployment setup is as follows
1. K8s Cluster on the edge - Factory1
    * K8s Cluster on the edge
    * MQTT edge installed on K8s
    * Bridge between Factory1 and the Enterprise MQTT clusters
    * Graph DB installed and running on docker

1. K8s Cluster on the edge - Factory2
    * K8s Cluster on the edge
    * MQTT edge installed on K8s
    * Bridge between Factory1 and the Enterprise MQTT clusters
    * Graph DB installed and running on docker

1. K8s Cluster on the cloud / enterprise  - Enterprise 
    * K8s Cluster of the enterprise 
    * MQTT Broker installed on K8s
    * TimescaleDB installed and running on docker
    * Graph DB installed and running on docker

![Logical Architecture for implementing UNS](./images/UNS-Architecture.png)

---
## **Technology Choices**
The following section lists the various options and technology choices that I evaluated and the reasoning for choosing them.
This should hopefully also give you possible alternatives to consider if you choose to implement and extend this for your needs.
The opinions below are my personal ones with no influence from the companies that built them

### **Clustering at the Edge with Kubernetes**
To run the MQTT broker on the Edge, a cluster is ***not*** a prerequisite.  If you do not have a business need for a high availability MQTT cluster, running just a single instance ( probably within a docker) would be a lot more easier.

Even for a clustered setup most of the MQTT brokers do provide an option for clustering however running this cluster on K8s provides significant benefits for scaling, auto healing etc. 

I evaluated the following K8s options because it needs to be a extremely light weight and high performant distribution to be able to run on the edge (constrained environments). Any of these is a perfectly good choice depending on your context.
1. [MicroK8s](https://microk8s.io/)
1. [K3s](https://k3s.io/)

There are quite some comparisons between the the k8s distributions on the net so I am not going to list detailed comparison here.

I finally choose to go ahead with ***MicroK8s*** because 
* Most of my environment was on Ubuntu hence enabling a snap for microk8s was very easy
* The inbuilt addons and the ease of enabling them without wading through YAML files
* The default CNI provided for the cluster is Calico which [claimed](https://www.suse.com/c/rancher_blog/comparing-kubernetes-cni-providers-flannel-calico-canal-and-weave/) to be more performant
* Setting up a High Availability cluster is extremely easy by adding multiple master nodes

   > **Note:** Avoid setting up high availability and multiple masters for your edge cluster as this increases the resource consumption & load on the edge devices. A single master node should suffice majority of your availability requirements if you actually even need a k8s cluster on the edge in the first place.

* Having a bit more experience with Ubuntu I found the documentation and guides a lot more easy to find and follow, including the community support, especially troubleshooting. As a K8s noob this really helped.

However microk8s did show up some limitations as well as bugs. Details of these are in **[01_k8scluster](./01_k8scluster/Readme.md)**. The link will provide details of all the addons, workarounds etc. that I did for bringing up my cluster. If you choose to setup your k8s with a different distribution, each of those addons could be setup / configured albeit in a different manner.


Some key limitations to bear in mind
* I faced some stability issues while trying to run this lower raspberry pi (pi3)
* microk8s is not available for every linux distribution. 
---
### **MQTT Broker**
The backbone of the ***Unified Name Space*** is the MQTT broker. 
#### **Why MQTT**
The overall structure of the UNS is based on the hierarchical structure as defined in ISA-95 part 2.
> \<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>

The level at which the message is published has a direct implication on it's time sensitivity as well as guidance on being processed  at the edge or on the cloud.<br/>
![ISA-95 Part 2](./images/ISA-95-part2.png)

I evaluated and read the user guides of the following brokers (open source versions only). All three also provide commercial / enterprise versions which is recommended for more robust setup and professional support
1. [EMQX](https://www.emqx.io/)
2. [VERNEMQ](https://vernemq.com/)
3. [HIVEMQ](https://www.hivemq.com)

While HIVEMQ has the best documentation and community support I decided try out EMQX for the following reasons
* EMQX is written in erlang which has a lower footprint than java (HIVEMQ). They also provide 2 versions of the broker, one specifically lightweight for edge deployment and the standard for enterprise or cloud deployment.
The details of setting up the MQTT cluster are provided in **[02_mqtt-cluster](./02_mqtt-cluster/Readme.md)**. The link provides the guidance to install EMQX on a K8s cluster using helm.

***Having said that, any of the above three would be perfectly good selections because***
* All the three have extension capabilities via standard as well as custom plugins. However I liked the rules plugin from EMQX which comes by default allowing for lot of flexibility for pre and post processing messages. Also EMQX seems to be supporting the ability to create plugins in multiple languages
* All three deploy very easily on K8s and all three have community (free) as well as commercial offering 
* All three support **MQTT 5** which is critical for manufacturers and **Sparkplug B** support
* All three support MQTT bridging allowing copying data between edge to cloud instances
* Both [HiveMQ](hivemq.com/mqtt-cloud-broker/) and [EMQX](https://www.emqx.com/en/cloud) provide fully managed cloud services which might be interesting offer to explore for your cloud / enterprise MQTT Cluster

#### <a id="broker_plugin"> </a>
>**Important Note:** The community edition of these brokers do not provide all functionalities. e.g. EMQX community doesn't allow plugins to be triggered on message delivery (this is an enterprise feature). As I wanted this solution to be completely open source and free, I decided to write an MQTT client subscribing to `"#"`. This works but is less efficient than creating a plugin within the broker and natively persisting the messages to a database. You can further optimize this by subscribing to a subset e.g. `"<enterprise>/#"`
However if you go for the enterprise version, I would recommend creating a plugin instead of the [MQTT Listeners](#plugin--mqtt-client-to-subscribe-and-write-to-the-above-data-bases) provided here for better performance. But for most scenarios, an MQTT client should suffice and be broker independent.

Hence I decided to write [my own plugin](#plugin--mqtt-client-to-subscribe-and-write-to-the-above-data-bases)  as an MQTT client which listens to the broker and on message persists the message ( either the GraphDB or the Historian)

### **GraphDB**
Normally I configured the MQTT publishers  to publish messages with retain flag so that consumers are able to get the latest message even if they weren't connected with broker at the time of publishing.

However I realized that,  in order to merge messages, or provide the capability to add relationships across multiple messages, MQTT alone will not be able to support that. Hence after some deliberation decided to use a Graph Database.

This provide the flexibility of defining relationships , simple way representing your object hierarchy as well as support merging of attributes

I choose to go with **[Neo4J](https://neo4j.com/)** simply because it was the only graphDB I was aware of as well as the fact that it runs seamlessly on Kubernetes.
The GraphDB also allows for extremely fine grained access control across the nodes, specific sections of the tree as well as limit access to specific properties. Refer [Neo4j - Access Control](https://neo4j.com/docs/operations-manual/current/authentication-authorization/access-control/)

> **Important Note:** The clustering feature of neo4j on K8s is an enterprise feature and [not available in the community version](https://community.neo4j.com/t/neo4j-community-edition-on-kubernetes/4955)

### **Historian**
The other critical component of the ***Unified Name Space*** is the historian. This allows to keep a full history of all messages, entities and artifacts generated. 
Since the graph databases are not suited for historian data (there were a couple of projects enhancing Neo4j but all were archived), it makes sense to delegate that to specialist. 

I evaluated and read the user guides of the following historians
1. [InfluxDb](https://www.influxdata.com/) combined with Timescale
1. [TimescaleDB](https://www.timescale.com/) combined with [MQTT Listeners](#plugin--mqtt-client-to-subscribe-and-write-to-the-above-data-bases)

Both of these are excellent options and have significant user adoption. InfluxDb combined with Telegraph provide a strong low code approach to the integration. Telegraf however did not have a plugin for Neo4j and InfluxDb does not support K8s. Given the stronger stability of postgres (on which TimescaleDB is built) as well as support for [JSON](https://docs.timescale.com/timescaledb/latest/how-to-guides/schema-management/json/) I decided to go ahead with **[TimescaleDB](https://www.timescale.com/)**

For production systems you might want to consider the cloud versions of the historians ([InfluxDB Cloud](https://www.influxdata.com/products/influxdb-cloud/) or [TimescaleDB](https://www.timescale.com/products#timescale-cloud)) for lower maintenance and higher scalability


### **Plugin / MQTT Client to subscribe and write to the above databases**
Since I did not have the enterprise version of the MQTT brokers, I decided to develop a broker agnostic solution. Hence the MQTT client seems to be a the best option ( even if it is not as performant as the Broker plugin/module).

I choose to wite the client in Python even thought Python is not as performance as Go, C or Rust primarily because
* In the OT space most professionals  ( in my experience) were more familiar coding with Python than Go, C or Rust. Hence I hope this increases the adoptions and contributions from the community in further developing this tool
* Should a team want to further optimize the code, given the readability and the inline comments in the code, they are hopefully able to rewrite the application in their choice of language
* I wanted to learn Python
