# Preparing the nodes for setting up a kubernetes cluster
This module has two scripts and configuration file

>* ./pre_setup_nodes.sh
>* ./setup_microk8s_cluster.sh
>* ./config.conf
*** Followig are the steps to setup the cluster *** 
1. Update the configuration file with the details of the nodes/virtual machines. The key configurations are
    ```bash
    # number of nodes.  This should be a positive integer as it will be used in a for loop 
    COUNT_NODES=2
    # Default network link name used by all the nodes to get the IP address required by the K8s cluster
    DEFAULT_NETWORK_LINK="enp0s3"¨
    ## This is the value needed to configure network traffic to your metallb loadbalancer
    METALLB_IPRANGE="198.168.220.1-198.168.220.126"
    ```
    Update the details for each node in the configuration file. The template of for the configuration for each node is 
    ```bash
    #Counter here is a placeholder for the node count (0,1,2,3,4 etc.)
    NODE_${COUNTER}_NAME = ## Hostname of the node 
    NODE_${COUNTER}_IP = ## Host ip addresed to be used by k8s control plane to communicate
    NODE_${COUNTER}_USERNAME = ## Unix user name used to log into the machine over ssh
    NODE_${COUNTER}_ISMASTER = ## (true/false) boolean to indicate this node is a master node. IMPORTANT to pay attention this is is specified in lower case. If more than one node is marked as master then the k8s will be setup as high availability
    ```
1. Configure network traffic based on the Metal Load Balancer Range configured in the configuration file. 
    * On windows if you are working with virtual machines. Add route to the range convering the METALLB range and ensure that it points to the DHCP server for your virtual machine farm. 
    ```powershell
    route -p ADD 198.168.220.0 MASK 255.255.255.128 198.168.200.1
    ```
    * On Unix if you are working with virtual machines. Add route to the range convering the METALLB range and ensure that it points to the DHCP server for your virtual machine farm. 
    ```bash
    # TBD
    ```
    * If you have raspberry pi or other physical machines, you might need to configure your router to allow this mapping
    > **TBD** 
1. Copy the configuration file and configuration scripts to all the nodes
    ```bash
    scp pre_setup_nodes.sh setup_microk8s_cluster.sh config.conf <remoteuser>@<nodeip>
    ```
scp myfile.txt myfile2.txt remoteuser@remoteserver:/remote/folder/

1. It is highly advised that you also ensure that the unix user has sudo rights. You can do this by running the following commands on each of the node
    ```bash
    sudo echo "$USER ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER
    sudo chown root:root /etc/sudoers.d/$USER
    sudo chmod o-r,a-w /etc/sudoers.d/$USER
    su - $USER
    ```
1. Run the preconfiguration script **on each node** ensuring that the configuration file is in the same directory as the script and readable. **Run the script as the normal unix user and not as ***root***.**
    ```bash
    ./pre_setup_nodes.sh
    ```
1. Log on to one of the master nodes and execute the second script. Ensure that the configuration file uploaded in the previous step is still available in the same directory
    ```bash
    ./setup_microk8s_cluster.sh
    ```

1. The key ***MicroK8s*** add-ons being used are 
    * helm3
    * ingress
    * openebs 
    * metallb
    * dashboard : ***This is not mandatory. This is just for your convinience should you need it***