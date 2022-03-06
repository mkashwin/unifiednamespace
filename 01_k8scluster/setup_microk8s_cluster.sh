#!/bin/bash
## This script is to be executed on any one master node of the cluster
## Ensure that both the config.conf must  be correctly updated and uploaded to each of the nodes
## This script should be involked only after <code>pre_setup_nodes.sh</code> has been executed on all the nodes

echo "Warning! This script should be involked only after pre_setup_nodes.sh  has been executed on all the nodes"


# Setting the default values before loading the conf file.
COUNT_WORKERS=0
DEFAULT_NETWORK_LINK="enp0s3"
MASTER_COUNT=0


source ./config.conf
# Obtain the current IP of this node
LOCAL_IP=$(ip address show dev ${DEFAULT_NETWORK_LINK} | grep 'inet ' | awk -F ' ' '{print $2}' | sed 's/["/24"]//g') 
## Needed due to a bug in core-dns
CLUSTER_DNS=$(kubectl get svc kube-dns --namespace=kube-system | grep kube-dns | awk -F ' ' '{print $3}') 

## Loop through the configurations of nodes

for ((i=0; i<$COUNT_NODES; i++ )); 
do
    declare NODE_IP="NODE_${i}_IP"
    declare NODE_NAME="NODE_${i}_NAME"
    declare NODE_ISMASTER="NODE_${i}_ISMASTER"
    declare NODE_USER="NODE_${i}_USERNAME"
    declare NODE_${i}_HAS_JOINED_K8S=false
    if [$LOCAL_IP = ${!NODE_IP}] && [ "${!NODE_ISMASTER}" = true ] ; then
        echo "This is the same node as the master" 
    else 
        ADD_NODE_CMD=$(microk8s add-node | grep $LOCAL_IP | awk '(NR>1)' )  

        if [ ${!NODE_ISMASTER} = true ] ; then
        ## FIXME how do I pass the password securely / via certs
            ssh -t ${!NODE_USER}@${!NODE_IP} bash -c"
                ${ADD_NODE_CMD};
                microk8s stop;
                echo --node-ip=${!NODE_IP} >> /var/snap/microk8s/current/args/kubelet;
                microk8s start;
            "
        else
        ## FIXME how do I pass the password securely / via certs
            ssh -t ${!NODE_USER}@${!NODE_IP} bash -c"
                ${ADD_NODE_CMD} --worker ;
                microk8s stop ;
                echo --node-ip=${!NODE_IP} >> /var/snap/microk8s/current/args/kubelet ;
                echo --cluster-domain=cluster.local>> /var/snap/microk8s/current/args/kubelet ;
                echo --cluster-dns=${CLUSTER_DNS}>> /var/snap/microk8s/current/args/kubelet ;
                microk8s start;
            "            
        fi
    fi

done

# Enabling Kubernetes web dashboard
microk8s enable dashboard
microk8s enable helm3
microk8s enable ingress
microk8s enable openebs 
# FIXME wait for them to be deployed and running
microk8s enable metallb:${METALLB_IPRANGE}
# FIXME which IP address range to use? how to add the routing 198.168.200.100-198.168.200.150
# e.g. if you specify 198.168.220.1-198.168.220.126

# you need to define that route on the host computer / LAN router to map to the virtual LAN DHCP server
# e.g. route -p ADD 198.168.220.0 MASK 255.255.255.128 198.168.200.1
# arp 198.168.220.2

