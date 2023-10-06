# Need to have helm 3 
microk8s helm3 repo add emqx https://repos.emqx.io/charts
microk8s helm3 repo update
microk8s helm3 search repo emqx

# create a persitent volume claim
# kubectl apply -f ./01_emx-jivavolumepolicy.yaml
# kubectl apply -f ./02_emqx-storageclass.yaml
# kubectl apply -f ./03_emqx-emx-pvc.yaml

microk8s kubectl apply -f - <<EOF
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: mayastor-2
parameters:
  repl: '2'
  protocol: 'nvmf'
  ioTimeout: '60'
  local: 'true'
provisioner: io.openebs.csi-mayastor
volumeBindingMode: WaitForFirstConsumer
EOF
# kubectl apply -f ./emqx-pvc.yaml

##EMQX
#microk8s helm3 install my-emqx emqx/emqx --set persistence.enabled=true --set persistence.existingClaim=emx-pvc
#microk8s helm3 upgrade --set replicaCount=5 my-emqx emqx/emqx
#helm install my-emqx-edge emqx/emqx --set image.repository=emqx/emqx-edge


##EMQXEdge
# microk8s helm3 install uns-emqx-edge emqx/emqx -f ./emqx-values.yaml  --namespace factory1
microk8s helm3 upgrade --install uns-emqx-edge emqx/emqx  --namespace factory1   --set image.repository=emqx/emqx-edge --set persistence.enabled=true --set persistence.size=100M --set persistence.storageClass=mayastor-2 --set service.type=LoadBalancer --create-namespace --wait
microk8s helm3 upgrade --install uns-emqx-edge2 emqx/emqx --namespace factory2   --set image.repository=emqx/emqx-edge --set persistence.enabled=true --set persistence.size=100M --set persistence.storageClass=mayastor-2 --set service.type=LoadBalancer --create-namespace --wait
microk8s helm3 upgrade --install uns-emqx-corp emqx/emqx  --namespace enterprise --set persistence.enabled=true --set persistence.size=100M --set persistence.storageClass=mayastor-2 --set service.type=LoadBalancer --create-namespace --wait

microk8s kubectl get pods -A
# kubectl -n <namespace> exec -it <pod name> -- bash -c "emqx_ctl plugins reload emqx_bridge_mqtt"

kubectl -n factory1 exec -it uns-emqx-edge-0 -- bash -c "emqx_ctl plugins reload emqx_bridge_mqtt"
kubectl -n factory2 exec -it uns-emqx-edge-0 -- bash -c "emqx_ctl plugins reload emqx_bridge_mqtt"
kubectl -n enterprise exec -it uns-emqx-edge-0 -- bash -c "emqx_ctl plugins reload emqx_bridge_mqtt"

##Delete the MQTT Cluster
#microk8s helm3 uninstall uns-emqx-edge --namespace factory1
#microk8s kubectl get pvc
#kubectl delete pvc <> #put names retrieved from above