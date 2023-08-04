data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {

  account_id = data.aws_caller_identity.current.account_id
  region = data.aws_region.current.name
  env_service_id = "${var.apigee_environment}-${var.service_id}"
  env_namespaced_name = "${var.apigee_environment}-${var.namespaced_name}"
  short_env_namespaced_name = "${var.apigee_shortenv}-${var.namespaced_name}"

  common_tags = {
    source = "terraform"
    project = var.service_id
    api-service = var.service_id
    api-environment = var.apigee_environment
    api-namespaced-name = var.namespaced_name
    api-is-namespaced = var.namespace == "" ? false : true
  }

  logConfig = {
  for container in local.ecs_service:
  container.name => {
    logDriver = "splunk"
    options = {
      splunk-format = "json"
      splunk-index = "requests_apm_${var.account}"
      splunk-sourcetype = "apm-json-docker"
      splunk-source = "apm:ecs:${var.workspace}:${container.name}"
      splunk-insecureskipverify = "true" # this is ok because we're talking to the internal endpoint ...
    },
    secretOptions= [
      {
        name = "splunk-url"
        valueFrom = "/${var.account}/platform-common/splunk/internal_hec_url"
      },
      {
        name = "splunk-token"
        valueFrom = "/${var.account}/platform-common/splunk/hec_token"
      }
    ]
  }

  }

  ecs_service = [
  {% for container in ecs_service %}
    {{
        (
          container
          | combine(
            {'image': '${local.account_id}.dkr.ecr.eu-west-2.amazonaws.com/' + service_id + '_' + container.name + ':' + build_label }
          )
        ) | to_json
    }},
  {% endfor %}
  ]

  exposed_service = element(matchkeys(local.ecs_service, local.ecs_service.*.expose, list(true)), 0)

  private_alb_arn_suffixes = data.terraform_remote_state.pre-reqs.outputs.private_alb_arn_suffixes
  private_alb_listener_arns = data.terraform_remote_state.pre-reqs.outputs.private_alb_listener_arns
  private_alb_listener_count = data.terraform_remote_state.pre-reqs.outputs.private_alb_listener_count

  autoscaling_resource_labels =  [
    for suffix in data.terraform_remote_state.pre-reqs.outputs.private_alb_arn_suffixes : (
      var.autoscaling_enabled && var.autoscaling_service_metric == "ALBRequestCountPerTarget" ? "${suffix}/${aws_alb_target_group.service.arn_suffix}"
      : "")]
}
