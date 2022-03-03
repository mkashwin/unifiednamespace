# Unified Name Space
This projecg aims to create an open sourced option for setting up a unified name space for IIOT transformation.

## What is the Unified Name Space

## Technology Choices
The following section lists the various options and technology choices that I evaluated and the reasoning for choosing them.
This should hopefully also give you possible alternatives to consider if you choose to implement and extend this for your needs


### Clustering at the Edge with Kubernetes
To run the MQTT broker on the Edge, a cluster is *** not *** a prerequisite.  If you do not have a business need for a high availability MQTT cluster, runnning just a single instance ( probably dockerized ) would be a lot more easier.

Even for a clustered setup most of the MQTT brokers do provide an option for clustering however running this cluster on K8s provides significant benefits for scaling, auto healing etc. 

I evaluated the following K8s options because it needs to be a extremely light weight and high performant distribution to be able to run on the edge ( constraint enviornments)
1. [MicroK8s](https://microk8s.io/)
1. [K3s](https://k3s.io/)

There are quite some comparisons between the the k8s distributions on the net so I am not going to list detailed comparison here.

I finally choose to go ahead with ***MicroK8s*** because 
* Most of my enviornment was on Ubuntu hence enabling a snap for microk8s was very easy
* The inbuild addons and the ease of enabling them without wading through YAML files
* The default CNI provided for the cluster is Calico which claimed to be more performant
* Setting up a High Availability cluster is extremely easy by adding multiple master nodes
> **Note:** Avoid seting up high availability and multiple masters for your edge cluster as this increases the resource consumption & load on the edge devices. A single master node should suffice majority of your availability requirements if you actually even need a k8s cluster on the edge in the first place

* Having a bit more experience with Ubuntu I found the documentation and guides a lot more easy to find and follow, including the community support, especially troubleshooting. As a K8s noob this really helped.

However microk8s did show up some limitations as well as bugs. Details of these are in the [k8scluster](./01_k8scluster/Readme.md). The link will provide details of all the addons, workarounds etc. that I did for bringing up my cluster. If you choose to setup your k8s with a different distribution, each of those addons could be setup / configured albiet in a different manner.


Some key limitations to list
* I faced some stability issues while trying to run this lower raspberry pi (pi3)
* microk8s is not available for every linux distribution. 



### MQTT Broker
The backbone of the 


### GraphDB

### Historian

### MQTT Client to subscribe and write to the above data bases

