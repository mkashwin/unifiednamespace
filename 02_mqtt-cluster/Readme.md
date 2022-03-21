# The MQTT Cluster 
The MQTT Cluster from EMQX is easily setup on a cluster. *There are other ways like within a docker or directly via the executable, but I choose to use the K8s setup to be able to leverage the benefits of scaling up, failover and other orchestration benefits.*
Before proceeding ensure that you have setup your K8s Cluster as described in [01_k8scluster](./../01_k8scluster/Readme.md)

```bash
microk8s helm3 repo add emqx https://repos.emqx.io/charts
microk8s helm3 repo update
microk8s helm3 search repo emqx

# This command needs to be executed to have persistence available to the MQTT instances
kubectl patch storageclass openebs-jiva-csi-default -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## MQTT Cluster for the edge
Using `helm` install the MQTT Cluster on the edge. I choose to have each cluster in it's own namespace
```bash
# Install the Edge version of EMQX which has a smaller footprint and developed specifically for the edge
#microk8s helm3 install uns-emqx-edge emqx/emqx  --namespace <FACTORY NAME>   --set image.repository=emqx/emqx-edge --set service.type=LoadBalancer --create-namespace --wait
#e.g. 
microk8s helm3 install uns-emqx-edge emqx/emqx  --namespace factory1   --set image.repository=emqx/emqx-edge --set service.type=LoadBalancer --create-namespace --wait
```

## MQTT Cluster for the enterprise / cloud 
Normally you would could to use the cloud service MQTT server. I choose to 

```bash
# Install the central cluster  EMQX brokers at  the Corporate instance/ Cloud
microk8s helm3 install uns-emqx-corp emqx/emqx  \
            --namespace enterprise \
            --set persistence.enabled=true \
            --set persistence.size=100M \
            --set persistence.storageClass=openebs-jiva-csi-default \
            --set service.type=LoadBalancer 
            --create-namespace --wait

```

## Configure MQTT bridge between Edge Cluster and Enterprise/
TBD

## Known Limitations / workarounds
1. MQTTv3.1 appears not to be supported by EMQX. While testing client code using `paho.mqtt.client` against [broker.emqx.io](https://www.emqx.com/en/mqtt/public-mqtt5-broker) observed that the connection was not happening and neither the `on_connect()` nor the `on_connect_fail()` callbacks were invoked.
Since most clients would be either MQTTv3.1.1 or MQTTv5.0 this should not be a problem

2. The plugins to intercept messages from EMQx ( which is probably the more efficient mechanism) in order to persist them are available only in the enterprise version and not in the community edition. As a workaround, I created an MQTT client which subscribes to `#` and allows subsequent processing.