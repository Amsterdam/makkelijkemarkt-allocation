.PHONY: manifests deploy

dc = docker-compose

ENVIRONMENT ?= local
HELM_ARGS = manifests/chart \
	-f manifests/values.yaml \
	-f manifests/env/${ENVIRONMENT}.yaml \
	--set image.tag=${VERSION}

REGISTRY ?= 127.0.0.1:5001
REPOSITORY ?= salmagundi/allocation
VERSION ?= latest

build:
	$(dc) build

test:
	echo "No tests available"

push:
	$(dc) push

manifests:
	@helm template allocation $(HELM_ARGS) $(ARGS)

deploy: manifests
	helm upgrade --install allocation $(HELM_ARGS) $(ARGS)

update-chart:
	rm -rf manifests/chart
	git clone --branch 1.5.2 --depth 1 git@github.com:Amsterdam/helm-application.git manifests/chart
	rm -rf manifests/chart/.git

clean:
	$(dc) down -v --remove-orphans

reset:
	kubectl delete deployments --all && helm uninstall allocation

refresh: reset build push deploy

dev:
	nohup kubycat kubycat-config.yaml > /dev/null 2>&1&
