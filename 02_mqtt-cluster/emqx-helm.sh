# Need to have helm 3 
microk8s helm3 repo add emqx https://repos.emqx.io/charts
microk8s helm3 repo update
microk8s helm3 search repo emqx

# create a persitent volume claim
# kubectl apply -f ./01_emx-jivavolumepolicy.yaml
# kubectl apply -f ./02_emqx-storageclass.yaml
# kubectl apply -f ./03_emqx-emx-pvc.yaml

kubectl patch storageclass openebs-jiva-csi-default -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
# kubectl apply -f ./emqx-pvc.yaml

##EMQX
#microk8s helm3 install my-emqx emqx/emqx --set persistence.enabled=true --set persistence.existingClaim=emx-pvc
#microk8s helm3 upgrade --set replicaCount=5 my-emqx emqx/emqx
#helm install my-emqx-edge emqx/emqx --set image.repository=emqx/emqx-edge


##EMQXEdge
# microk8s helm3 install uns-emqx-edge emqx/emqx -f ./emqx-values.yaml  --namespace factory1
microk8s helm3 install uns-emqx-edge emqx/emqx  --namespace factory1   --set image.repository=emqx/emqx-edge --set service.type=LoadBalancer --create-namespace --wait
microk8s helm3 install uns-emqx-edge2 emqx/emqx --namespace factory2   --set image.repository=emqx/emqx-edge --set persistence.enabled=true --set persistence.size=100M --set persistence.storageClass=openebs-jiva-csi-default --set service.type=LoadBalancer --create-namespace --wait
microk8s helm3 install uns-emqx-corp emqx/emqx  --namespace enterprise --set persistence.enabled=true --set persistence.size=100M --set persistence.storageClass=openebs-jiva-csi-default --set service.type=LoadBalancer --create-namespace --wait

microk8s kubectl get pods
# kubectl -n <namespace> exec -it <pod name> -- bash

##Delete the MQTT Cluster
#microk8s helm3 uninstall uns-emqx-edge --namespace factory1
#microk8s kubectl get pvc
#kubectl delete pvc <> #put names retrieved from above