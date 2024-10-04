#!/bin/bash
## This script is to be executed on any one master node of the cluster
## Ensure that both the config.conf must  be correctly updated and uploaded to each of the nodes
## This script should be invoked only after <code>pre_setup_nodes.sh</code> has been executed on all the nodes

echo "Warning! This script should be invoked only after pre_setup_nodes.sh has been executed on all the nodes"
echo "This script needs to be executed only once on any one of the designated master node of the K8s cluster "

# spell-checker:disable
DEFAULT_NETWORK_LINK="enp0s3"
#This entry is inline wiht microK8s documentation to be done on each master node for high availability
FAILUREDOMAIN=40
# spell-checker:enable
source ./config.conf
# Obtain the current IP of this node
# trunk-ignore(shellcheck/SC2312)
LOCAL_IP=$(ip address show dev "${DEFAULT_NETWORK_LINK}" | grep 'inet ' | awk -F ' ' '{print $2}' | sed 's/["/24"]//g')
## Needed due to a bug in core-dns
# trunk-ignore(shellcheck/SC2312)
CLUSTER_DNS=$(kubectl get svc kube-dns --namespace=kube-system | grep kube-dns | awk -F ' ' '{print $3}') 

IS_THIS_MASTER=false
## Loop through to ensure that this node is actually a master node ( as per config.conf)
# trunk-ignore(shellcheck/SC2004)
for ((i=0; i<${COUNT_NODES}; i++ ));
do
    declare NODE_IP="NODE_${i}_IP"
    declare NODE_ISMASTER="NODE_${i}_ISMASTER"
    if [[ "${LOCAL_IP}" = "${!NODE_IP}" ]]; then
        IS_THIS_MASTER=${!NODE_ISMASTER}
    fi
done

# trunk-ignore(shellcheck/SC2004)
for ((i=0; i<${COUNT_NODES}; i++ ));
do
    declare NODE_IP="NODE_${i}_IP"
    # trunk-ignore(shellcheck/SC2034)
    declare NODE_NAME="NODE_${i}_NAME"
    declare NODE_ISMASTER="NODE_${i}_ISMASTER"
    declare NODE_USER="NODE_${i}_USERNAME"
    declare NODE_"${i}"_HAS_JOINED_K8S=false
    # spell-checker:disable
    if [[ "${LOCAL_IP}" = "${!NODE_IP}" ]] && [[ "${!NODE_ISMASTER}" = true ]] ; then
        echo "This is the same node as the master" 
        echo "failure-domain=${FAILUREDOMAIN}" >> /var/snap/microk8s/current/args/ha-conf
        # trunk-ignore(shellcheck/SC2004)
        FAILUREDOMAIN=$((${FAILUREDOMAIN} + 2))
        IS_THIS_MASTER=true

    elif [[ "${IS_THIS_MASTER}" = true ]] ; then
        # trunk-ignore(shellcheck/SC2312)
        ADD_NODE_CMD=$(microk8s add-node | grep "${LOCAL_IP}" | awk '(NR>1)' )

        if [[ "${!NODE_ISMASTER}" = true ]] ; then
        ## FIXME how do I pass the password securely / via certs
            ssh -t "${!NODE_USER}"@"${!NODE_IP}" bash -c"
                ${ADD_NODE_CMD};
                microk8s stop;
                echo --node-ip=${!NODE_IP} >> /var/snap/microk8s/current/args/kubelet;
                echo 'failure-domain=${FAILUREDOMAIN}' >> /var/snap/microk8s/current/args/ha-conf
                microk8s start;
                sudo microk8s.config > ~/.kube/config
                sudo chown -f -R ${!NODE_USER} ~/.kube
            "
            # trunk-ignore(shellcheck/SC2004)
            FAILUREDOMAIN=$((${FAILUREDOMAIN} + 2))
            eval NODE_"${i}"_HAS_JOINED_K8S=true
        else
        ## FIXME how do I pass the password securely / via certs
            ssh -t "${!NODE_USER}"@"${!NODE_IP}" bash -c"
                ${ADD_NODE_CMD} --worker ;
                microk8s stop ;
                echo --node-ip=${!NODE_IP} >> /var/snap/microk8s/current/args/kubelet ;
                echo --cluster-domain=cluster.local>> /var/snap/microk8s/current/args/kubelet ;
                echo --cluster-dns=${CLUSTER_DNS}>> /var/snap/microk8s/current/args/kubelet ;
                microk8s start;
            "
            eval NODE_"${i}"_HAS_JOINED_K8S=true
        fi
    fi
done

# Enabling Kubernetes web dashboard
microk8s enable dashboard
microk8s enable helm3
microk8s enable ingress
sudo microk8s enable core/mayastor --default-pool-size 20G

microk8s kubectl get pod -n mayastor
microk8s kubectl get diskpool -n mayastor
# spell-checker:enable
# FIXME wait for them to be deployed and running
microk8s enable metallb:"${METALLB_IPRANGE}"
# FIXME which IP address range to use? how to add the routing 198.168.200.100-198.168.200.150
# e.g. if you specify 198.168.220.1-198.168.220.126

# you need to define that route on the host computer / LAN router to map to the virtual LAN DHCP server
# e.g. route -p ADD 198.168.220.0 MASK 255.255.255.128 198.168.200.1
# arp 198.168.220.2