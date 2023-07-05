# Preparing the nodes for setting up a kubernetes cluster
This module has two scripts in `bash` and configuration file.
>* ./pre_setup_nodes.sh
>* ./setup_microk8s_cluster.sh
>* ./config.conf


## ***Following are the steps to setup the cluster*** 
1. Update the configuration file `config.conf` with the details of the nodes/virtual machines. 

   **IMPORTANT:** Ensure that that configurations are updated to your context   
   The key configurations are
    ```bash
    # number of nodes.  This should be a positive integer as it will be used in a for loop 
    COUNT_NODES=2
    # Default network link name used by all the nodes to get the IP address required by the K8s cluster
    DEFAULT_NETWORK_LINK="enp0s3"
    ## This is the value needed to configure network traffic to your metallb loadbalancer
    METALLB_IPRANGE="198.168.220.1-198.168.220.126"
    ```
    Update the details for each node in the configuration file. The template of for the configuration for each node is 
    ```bash
    #Counter here is a placeholder for the node count (0,1,2,3,4 etc.)
    NODE_${COUNTER}_NAME = ## Hostname of the node 
    NODE_${COUNTER}_IP = ## Host ip addressed to be used by k8s control plane to communicate
    NODE_${COUNTER}_USERNAME = ## Unix user name used to log into the machine over ssh
    NODE_${COUNTER}_ISMASTER = ## (true/false) boolean to indicate this node is a master node. IMPORTANT to pay attention this is is specified in lower case. If more than one node is marked as master then the k8s will be setup as high availability
    ```
1. Configure network traffic based on the Metal Load Balancer Range configured in the configuration file. For more details also refer the links in the [Further Reading](#further-reading) section

    ### <a id="windows"></a>
    * On windows if you are working with virtual machines. Add route to the range covering the METALLB range and ensure that it points to the DHCP server for your virtual machine farm. 
        ```powershell
        route -p ADD 198.168.220.0 MASK 255.255.255.128 198.168.200.1
        ```
        where 
        - `198.168.220.0 MASK 255.255.255.128` is the IP range allocated to MetalLB
        - `198.168.200.1` is the DHCP server for your virtual box network 

    ### <a id="unix"></a>
    * On Unix if you are working with virtual machines. Add route to the range covering the METALLB range and ensure that it points to the DHCP server for your virtual machine farm. 
        ```powershell
        sudo ip route add 198.168.220.0/24 via 198.168.200.1 dev vboxnet0
        ```
        where
        - `198.168.220.0/24` is the IP range allocated to MetalLB
        - `198.168.200.1` is the DHCP server for your virtual box network
        - `vboxnet0` is the virtual box network adaptor setup 


1. Copy the configuration file and configuration scripts to all the nodes
    ```bash
    scp pre_setup_nodes.sh setup_microk8s_cluster.sh config.conf <remoteuser>@<nodeip>:.
    ```
    replace the `<remoteuser>` and `<nodeip>` accordingly


1. It is highly advised that you also ensure that the unix user has sudo rights. You can do this by running the following commands on each of the node
    ```bash
    sudo echo "$USER ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER
    sudo chown root:root /etc/sudoers.d/$USER
    sudo chmod o-r,a-w /etc/sudoers.d/$USER
    su - $USER
    ```
1. Run the pre-configuration script **on each node** ensuring that the configuration file is in the same directory as the script and readable. **Run the script as the normal unix user and not as ***root***.**
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
    * metallb   : ***Not required if your cluster is deployed on the cloud. Only needed for edge clusters and enterprise clusters***
    * dashboard : ***This is not mandatory. This is just for your convenience should you need it***
---
## **Further Reading**
### MetalLB
There are quite some options and considerations while setting up MetalLB. This section provides some resources & references to better understand.

**Additional References**
- [Layer 2 mode](https://metallb.universe.tf/concepts/layer2/): The current setup for the virtual machines is done using Layer 2 mode
- [BGP mode](https://metallb.universe.tf/concepts/bgp/): Ensure that you refer to the limitations of MetalLB specially with [Calico](https://metallb.universe.tf/configuration/calico/)
- [Fine Tune L2](https://blog.emptyq.net/a?ID=00004-8833cb83-c0cd-48db-a2d4-1367c7637876) provides further guidance on setting up routing rules to MetalLB using L2 routing
- [Kubernetes Under The Hood](https://mvallim.github.io/kubernetes-under-the-hood/documentation/kube-metallb.html): MetalLB setup

### VirtualBox Networking
- [VirtualBox Network setting guides](https://www.nakivo.com/blog/virtualbox-network-setting-guide/)

---

## **Limitations / Enhancements being considered for a later release / contributions**
* [ ] Consider converting this from shell script to Ansible 
* [ ] Unit testing of the code
* [x] There were some CoreDNS [issues](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/#known-issues) in the worker node. I fixed the issue in the script by manual entries in `/var/snap/microk8s/current/args/kubelet` file of all nodes. See [`setup_microk8s_cluster.sh`](./setup_microk8s_cluster.sh#L67)
* [x] MetalLB: How to configure network routing. See [References](#metallb)
