#!/bin/bash
# This script is not automated , it is a collection of commands and edits to be done.
# working to fully automate this.
# Create 3 VM
# configure host-only network as well as NAT
# https://prahladyeri.wordpress.com/2012/08/02/how-to-setup-a-virtual-lan-on-your-machine-using-oracle-virtualbox/
# https://beamtic.com/virtualbox-host-only-and-nat
# On each machine login via ssh and run these commands
# spell-checker:disable
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get full-upgrade -y
sudo apt install net-tools libnss-mdns openssh-server -y
sudo apt-get auto-remove -y
sudo apt-get install open-iscsi
sudo systemctl enable iscsid
systemctl status iscsid
sudo systemctl enable --now iscsid
sudo snap refresh
# spell-checker:enable

# Need to update /etc/hosts with internal IP of the other nodes

# consider creating key value cert for login
# https://blog.anurut.com/ssh-with-private-key-in-windows-terminal/
# shortcut command to be ru
# cat ~/.ssh/id_rsa.pub | ssh <user>@<host> "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >>  ~/.ssh/authorized_keys"

#FIXME
# will need to enter host name and ipaddress in each VM because ubuntu / Virtualbox is looking up domain names with .local only
# Example of entries to be made in /etc/hosts
# 198.168.200.3 master
# 198.168.200.4 worker1
# 198.168.200.5 worker2
#
#

# https://microk8s.io/docs/high-availability
# https://adamtheautomator.com/microk8s/
#Install microk8s
sudo snap install microk8s --classic --channel=latest/stable

# Adding the current user to Microk8s group
sudo usermod -a -G microk8s "${USER}"
mkdir ~/.kube

sudo chown root:"${USER}" /var/snap/microk8s/current/credentials/
sudo chown root:"${USER}" /var/snap/microk8s/current/credentials/client.config

sudo chown root:"${USER}" /var/snap/microk8s/current/args/
sudo chown root:"${USER}" /var/snap/microk8s/current/args/kubectl
# Re-entering user session for group update to take effect
su - "${USER}"
# spell-checker:disable
# Reload the mircok8s group users
newgrp microk8s
# spell-checker:enable
# change domain number per node 40, 42, 44 <= dont
# echo "failure-domain=42" > /var/snap/microk8s/current/args/ha-conf
microk8s.stop
microk8s.start

microk8s status --wait-ready

# call this on master for every worker node
microk8s add-node
#<= result of this command to be run on the other machines  with suffix --worker
# dont attempt HA setup for control node. on smaller machines this is significantly impacts the k8s cluster
# on each of the worker nodes update the provider file to delete the NAT entry is deleted
# spell-checker:disable
# nano /var/snap/microk8s/current/args/traefik/provider.yaml

# microk8s.kubectl --kubeconfig ~/.kube/config
# spell-checker:enable
sudo microk8s.config >~/.kube/config
sudo chown -f -R "${USER}" ~/.kube

# On every node (including the master(s)):
#     microk8s stop (Stop all nodes before changing configuration files)
microk8s stop

#  Get the internal IP of the node, e.g. 198.168.200.z. Command ip a show dev enp0s3 will show info for interface enp0s3.
#  Add this to the bottom of /var/snap/microk8s/current/args/kubelet:
# --node-ip=10.x.y.z
# spell-checker:disable
#  Add this to the bottom of /var/snap/microk8s/current/args/kube-apiserver:
# --advertise-address=10.x.y.z
# spell-checker:enable
echo --node-ip=$(ip address show dev enp0s3 | grep 'inet ' | awk -F ' ' '{print $2}' | sed 's/["/24"]//g') >>/var/snap/microk8s/current/args/kubelet
#     Get the cluster dns ip kubectl get svc kube-dns --namespace=kube-system
#     Add this to the bottom of /var/snap/microk8s/current/args/kubelet for each worker node

#--cluster-domain=cluster.local
#--cluster-dns=10.152.183.10
# commands to run on workers ( not the master, since this config should be there on the master )
echo --cluster-domain=cluster.local >>/var/snap/microk8s/current/args/kubelet
echo --cluster-dns=$(kubectl get svc kube-dns --namespace=kube-system | grep kube-dns | awk -F ' ' '{print $3}') >>/var/snap/microk8s/current/args/kubelet

microk8s start

# Enabling Kubernetes web dashboard
microk8s enable dashboard
microk8s enable helm3
microk8s enable ingress
microk8s enable openebs
# FIXME wait for them to be deployed and running
microk8s enable metallb:198.168.220.1-198.168.220.126
# FIXME which IP address range to use? how to add the routing 198.168.200.100-198.168.200.150
# e.g. if you specify 198.168.220.1-198.168.220.126

# you need to define that route on the host computer / LAN router to map to the virtual LAN DHCP server
# e.g. route -p ADD 198.168.220.0 MASK 255.255.255.128 198.168.200.1
# arp 198.168.220.2

# Get the default token name
token=$(microk8s kubectl -n kube-system get secret | grep default-token | cut -d " " -f1)
# Display the token value
microk8s kubectl -n kube-system describe secret "${token}"

# microk8s kubectl port-forward -n kube-system service/kubernetes-dashboard 10443:443 --address 0.0.0.0 &
#create a metal llb load balancer for the dashboard. This step is critical to ensure that the metallb, the routing rules etc. are correctly setup
kubectl apply -f ./k8s-dashboard-lb.yaml

# drop the microk8s prefix and just use *kubectl to issue commands to Kubernetes, create an alias by running the command:
alias kubectl='microk8s kubectl'

# drop the microk8s prefix and just use *helm to issue commands to Kubernetes, create an alias by running the command:
alias helm='microk8s helm3'

# template for clean up  Evicted, CrashLoopBackOff pods
# del_state="< the state you want to clean>"
# kubectl get po -A | grep $del_state | awk '{print $1} {print $2}'| xargs microk8s.kubectl delete pod -n
# example
# del_state="Evicted"
# kubectl get po -A  | grep $del_state | awk '{print $1} {print $2}'| xargs microk8s.kubectl delete pod -n

# Nuclear option delete all non running, non under creation pods
# kubectl get po -A  --no-headers=true | grep -v "Running" | grep -v "Pending" | grep -v "ContainerCreating" | awk '{print $1} {print $2}'| xargs microk8s.kubectl delete pod -n
