#!/bin/bash
# This script is to be executed on each node of the kubernetes cluster
# ensure that both the config.conf must  be correctly updated and uploaded to each of the nodes

#
# Setting the default values before loading the conf file.
COUNT_WORKERS=0
DEFAULT_NETWORK_LINK="enp0s3"
IS_THIS_MASTER=false
MASTER_COUNT=0
FAILUREDOMAIN=40

source ./config.conf
# Obtain the current IP of this node
LOCAL_IP=$(ip address show dev ${DEFAULT_NETWORK_LINK} | grep 'inet ' | awk -F ' ' '{print $2}' | sed 's/["/24"]//g') 

## Figure out how to add current user to sudo group so that password is not required every time
# sudo usermod -aG sudo $USER
## Re-entering user session for group update to take effect
# su - $USER

## Loop through the configurations of nodes
for ((i=0; i<$COUNT_NODES; i++ ));
do
    declare NODE_IP="NODE_${i}_IP"
    declare NODE_NAME="NODE_${i}_NAME"
    declare NODE_ISMASTER="NODE_${i}_ISMASTER"
    declare NODE_USER="NODE_${i}_USERNAME"

    ## Need to update /etc/hosts with internal IP of the other nodes
    if [$LOCAL_IP = ${!NODE_IP}]
    then
        # Skip putting this entry in /etc/hosts 
        # check is this node is to be a master
        IS_THIS_MASTER=${!NODE_ISMASTER}
        FAILUREDOMAIN=$((${FAILUREDOMAIN} + 2))
    else
        sudo cat $(echo ${!NODE_IP} ${!NODE_NAME}) >> /etc/hosts
    fi
## Count the number of master nodes
    if [ "${!NODE_ISMASTER}" = true ] ; then 
        MASTER_COUNT++ 
    fi
done
## grant the user sudo priviledges
if [ ! -f /tmp/foo.txt ]; then
    sudo echo "$USER ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER
    sudo chown root:root /etc/sudoers.d/$USER
    sudo chmod o-r,a-w /etc/sudoers.d/$USER
    su - $USER
fi

## Basic installations and upgrade of the system
sudo apt-get update -y 
sudo apt-get upgrade -y
sudo apt-get full-upgrade -y
sudo apt install net-tools libnss-mdns openssh-server open-iscsi -y 
sudo apt-get auto-remove -y 

sudo systemctl enable iscsid
systemctl status iscsid 
sudo systemctl enable --now iscsid
sudo snap refresh

#Install microk8s
sudo snap install microk8s --classic --channel=latest/stable
# Adding the current user to Microk8s group
sudo usermod -a -G microk8s $USER
mkdir ~/.kube

sudo chown root:$USER /var/snap/microk8s/current/credentials/
sudo chown root:$USER /var/snap/microk8s/current/credentials/client.config

sudo chown root:$USER /var/snap/microk8s/current/args/
sudo chown root:$USER /var/snap/microk8s/current/args/kubectl
# Re-entering user session for group update to take effect
su - $USER
# Reload the mircok8s group users
newgrp microk8s

if [ "$IS_THIS_MASTER" = true ] ; then
## Configurations specific to the masters 
    if [ MASTER_COUNT > 0 ] ;  then 
        # change domain for HA config only if more than one master are setup and this is a master node
        echo "failure-domain=${FAILUREDOMAIN}" >> /var/snap/microk8s/current/args/ha-conf
    fi
    sudo microk8s.config > ~/.kube/config
    sudo chown -f -R $USER ~/.kube
    touch ~/.bash_aliases
     # drop the microk8s prefix and just use *kubectl to issue commands to Kubernetes, create an alias by running the command: 
    echo "alias kubectl='microk8s kubectl'" >> ~/.bash_aliases
    # drop the microk8s prefix and just use *helm to issue commands to Kubernetes, create an alias by running the command: 
    echo "alias helm='microk8s helm3'" >> ~/.bash_aliases
else
## Configurations specific to the worker nodes
fi
microk8s.stop
microk8s.start