#!/bin/bash
# This script is to be executed on each node of the kubernetes cluster
# ensure that both the config.conf must  be correctly updated and uploaded to each of the nodes

#
# Setting the default values before loading the conf file.
COUNT_WORKERS=0
DEFAULT_NETWORK_LINK="enp0s3"
IS_THIS_MASTER=false
MASTER_COUNT=0

source ./config.conf
# Obtain the current IP of this node
LOCAL_IP=$(ip address show dev ${DEFAULT_NETWORK_LINK} | grep 'inet ' | awk -F ' ' '{print $2}' | sed 's/[/][2][4]//g') 


## Loop through the configurations of nodes
for ((i=0; i<$COUNT_NODES; i++ ));
do
    declare NODE_IP="NODE_${i}_IP"
    declare NODE_NAME="NODE_${i}_NAME"
    declare NODE_ISMASTER="NODE_${i}_ISMASTER"
    declare NODE_USER="NODE_${i}_USERNAME"

    ## Need to update /etc/hosts with internal IP of the other nodes
    if [ "$LOCAL_IP" = "${!NODE_IP}" ]
    then
        # Skip putting this entry in /etc/hosts 
        # check is this node is to be a master
        IS_THIS_MASTER=${!NODE_ISMASTER}
    else
        echo ${!NODE_IP} ${!NODE_NAME} | sudo tee -a /etc/hosts
    fi
## Count the number of master nodes
    if [ "${!NODE_ISMASTER}" = true ] ; then 
        let MASTER_COUNT++ 
    fi
done
## grant the user sudo priviledges
if [ ! -f /etc/sudoers.d/$USER ]; then
    echo "${USER} does not have adequate sudo rights. Adding him to sudo list to prevent always asking for passwords"
    sudo echo "$USER ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER
    sudo chown root:root /etc/sudoers.d/$USER
    sudo chmod o-r,a-w /etc/sudoers.d/$USER
    # su - $USER
    echo "User did not have adequate right to continue. Rights have been granted."
    echo "Please re-execute the script after logging off and loggin again. alternatively execute 'su - $USER'"
    exit  -1 
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

# Mayastor specific configurations / packagess
sudo sysctl vm.nr_hugepages=1024
echo 'vm.nr_hugepages=1024' | sudo tee -a /etc/sysctl.conf
sudo apt install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_tcp
echo 'nvme-tcp' | sudo tee -a /etc/modules-load.d/microk8s-mayastor.conf

#Install microk8s
sudo snap install microk8s --classic --channel=latest/stable
# Adding the current user to Microk8s group
sudo usermod -a -G microk8s $USER

mkdir ~/.kube
sudo microk8s.config > ~/.kube/config
sudo chown -f -R $USER ~/.kube

sudo chown root:$USER /var/snap/microk8s/current/credentials/
sudo chown root:$USER /var/snap/microk8s/current/credentials/client.config

sudo chown root:$USER /var/snap/microk8s/current/args/
sudo chown root:$USER /var/snap/microk8s/current/args/kubectl

if [ "$IS_THIS_MASTER" = true ] ; then
## Configurations specific to the masters
    echo "configuring the master node " $(hostname)
fi
touch ~/.bash_aliases
# drop the microk8s prefix and just use *kubectl to issue commands to Kubernetes, create an alias by running the command: 
echo "alias kubectl='microk8s kubectl'" >> ~/.bash_aliases
# drop the microk8s prefix and just use *helm to issue commands to Kubernetes, create an alias by running the command: 
echo "alias helm='microk8s helm3'" >> ~/.bash_aliases

sudo microk8s.stop
sudo microk8s.start
sudo microk8s status --wait-ready

# Re-entering user session for group update to take effect
#su - $USER
# Reload the mircok8s group users
newgrp microk8s

echo "Session needs to be reloaded for changes to take effect"
echo "Please Log off and Login again. Alternatively execute 'su - $USER'"
echo "Check status of microK8s with the command 'microk8s status' and if it is running you may proceed with executing  setup_k8s_cluster.sh on any one master node"