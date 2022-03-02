# Serverless Function to store messages to graphDB as well as historian


## Setup OpenFaas as your serverless platform 
Creating a serverless function base on OpenFaas.
For microk8s the following command on the master node will enable OpenFaas
```
microk8s enable openfaas
```
On running it you will get
```
NAMESPACE: openfaas
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
To verify that openfaas has started, run:

  kubectl -n openfaas get deployments -l "release=openfaas, app=openfaas"
To retrieve the admin password, run:

  echo $(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
OpenFaaS has been installed
```

## Setup the mqtt connector(s) 

Refer the links on how to setup the connector 
```
https://github.com/openfaas/mqtt-connector
https://github.com/openfaas/faas-netes/tree/master/chart/mqtt-connector
```

-f ./graphdb-values.yaml
-f ./historian-values.yaml
```
we will setup 2 instances of this connector
1) Setup the broker details to point to the factory instance. This connector will be used by GraphDB function



2) Setup the broker details to point to the corporate instance. This connector will be used by the Historian


It is important to have the connector listen to Topic '#" if you are on the enterprise cluster. 
The GraphDB may be deployed both at the factory glo
In order to historize the messages correctly each message must have a timestamp field


## The two functions for persisting the messages
We create 2 functions
###Funtion 1: Graph DB
Stores the latest value
It is important to model the the data structure correctly specially to ensure that different messages on the same topic are correctly merged. 


###Function 2: Historian 
Current implementation is with timescaledb but this can 



## Limitations 


