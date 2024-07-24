SHELL := /bin/bash

########################################################################################################################
##
## Makefile for managing ansible commands
##
########################################################################################################################

list:
	@grep '^[^#[:space:]].*:' Makefile

guard-%:
	@ if [ "${${*}}" = "" ]; then \
	    echo "Environment variable $* not set"; \
	    exit 1; \
	fi

CHECK := $(if $(filter 1,${CHECK}),--check,)
VERBOSE := $(if $(filter 1,${VERBOSE}),-vvv,)

template-manifest: guard-DIST_DIR
	@poetry run ansible-playbook $(VERBOSE) -i local template-manifest.yml

add-jwks-resource-url-to-app: guard-APIGEE_ENVIRONMENT guard-APIGEE_ACCESS_TOKEN guard-APP_ID
	@poetry run ansible-playbook $(VERBOSE) --diff $(CHECK) -i local add-jwks-resource-url-to-app.yml

add-apim-guids-policy:
	@poetry run ansible-playbook $(VERBOSE) --diff $(CHECK) -i local add-apim-guids-policy.yml

validate-manifest: guard-DIST_DIR
	@poetry run ansible-playbook $(VERBOSE) -i local validate-manifest.yml

deploy-manifest: guard-APIGEE_ENVIRONMENT guard-APIGEE_ORGANIZATION guard-APIGEE_ACCESS_TOKEN
	@poetry run ansible-playbook -vvv --diff $(CHECK) -i local deploy-manifest.yml

build-ecs-proxies: guard-build_label guard-service_id guard-CONTAINER_VARS_FILE
	@poetry run ansible-playbook -i local build-ecs-proxies.yml

remove-ecs-proxy-deployment: guard-service_id guard-APIGEE_ENVIRONMENT
	@poetry run ansible-playbook -i local remove-ecs-proxy-deployment.yml

create-build-env-vars: guard-build_label guard-out_dir
	@poetry run ansible-playbook -i local create-build-env-vars.yml

deploy-ecs-proxies: guard-account guard-build_label guard-service_id guard-APIGEE_ENVIRONMENT guard-PROXY_VARS_FILE
	@poetry run ansible-playbook -i local deploy-ecs-proxies.yml

deploy-apigee-proxy: guard-FULLY_QUALIFIED_SERVICE_NAME guard-SERVICE_BASE_PATH guard-APIGEE_ENVIRONMENT guard-APIGEE_ORGANIZATION guard-APIGEE_ACCESS_TOKEN guard-PROXY_DIR guard-PING
	@poetry run ansible-playbook -i local deploy-apigee-proxy.yml

deploy-apigee-product-and-spec: guard-SERVICE_NAME guard-FULLY_QUALIFIED_SERVICE_NAME guard-APIGEE_ENVIRONMENT guard-APIGEE_ORGANIZATION guard-APIGEE_ACCESS_TOKEN guard-FRIENDLY_NAME guard-PRODUCT_DISPLAY_NAME guard-PRODUCT_DESCRIPTION guard-VISIBLE guard-REQUIRE_CALLBACK_URL
	@poetry run ansible-playbook -i local deploy-apigee-product-and-spec.yml

template-proxies: guard-PROXIES_DIR guard-SERVICE_BASE_PATH guard-APIGEE_ENVIRONMENT
	@poetry run ansible-playbook -i local template-proxies.yml

remove-ecs-proxy-pre-reqs: guard-account guard-service_id guard-APIGEE_ENVIRONMENT
	@poetry run ansible-playbook -i local remove-ecs-proxy-pre-reqs.yml

create-ecr-build-role: guard-account guard-service_id
	@poetry run ansible-playbook -i local create-ecr-build-role.yml

remove-ecr-build-role: guard-account guard-service_id
	@poetry run ansible-playbook -i local remove-ecr-build-role.yml

create-api-deployment-pre-reqs: guard-service_id guard-APIGEE_ENVIRONMENT guard-account
	@poetry run ansible-playbook -i local create-api-deployment-pre-reqs.yml

remove-old-ecs-pr-deploys:
	@poetry run ansible-playbook -i local remove-old-ecs-pr-deploys.yml

remove-old-pr-portal-apis:
	@poetry run ansible-playbook -i local remove-old-pr-portal-apis.yml

remove-old-auto-apps:
	@poetry run ansible-playbook -i local remove-old-auto-apps.yml

remove-old-auto-products:
	@poetry run ansible-playbook -i local remove-old-auto-products.yml

remove-old-pr-specs:
	@poetry run ansible-playbook -i local remove-old-pr-specs.yml

remove-old-pr-products:
	@poetry run ansible-playbook -i local remove-old-pr-products.yml

remove-old-pr-proxies:
	@poetry run ansible-playbook -i local remove-old-pr-proxies.yml

remove-target-proxy:
	@poetry run ansible-playbook -i local remove-target-proxy.yml

deploy-api-pipelines: guard-PREFIX guard-REPO guard-SERVICE_CONNECTION_ID
	PREFIX="$(PREFIX)" ORG="NHSD-APIM" PROJECT="API Platform" REPO="https://github.com/NHSDigital/$(REPO)" SERVICE_CONNECTION="$(SERVICE_CONNECTION_ID)" poetry run ansible-playbook ansible/deploy-api-pipelines.yml

get-developer-emails:
	@poetry run ansible-playbook -i local get-developer-emails.yml
