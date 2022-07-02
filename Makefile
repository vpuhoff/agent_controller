check:
	helm install --dry-run agent-controller  -f values.yaml .

install:
	helm install  -f values.yaml agent-controller .

update:
	helm upgrade -f values.yaml agent-controller .

change_param:
	helm upgrade dashboard-demo stable/kubernetes-dashboard --set fullnameOverride="kubernetes-dashboard" --reuse-values

create_secret:
	kubectl create secret generic docker-hub-token \
    --from-file=.dockerconfigjson=docker-config.json \
    --type=kubernetes.io/dockerconfigjson