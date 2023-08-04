data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id     = data.aws_caller_identity.current.account_id
  region         = data.aws_region.current.name
  aws_ecr_bucket = "prod-eu-west-2-starport-layer-bucket"

  env_service_id       = "${var.apigee_environment}-${var.service_id}"
  service_namespaces     = contains(["internal-dev", "internal-dev-sandbox"], var.apigee_environment) ? [var.service_id, "${var.service_id}-*"] : [var.service_id]
  env_service_namespaces = [for ns in local.service_namespaces : "${var.apigee_environment}-${ns}"]
  short_env_service_namespaces = [for ns in local.service_namespaces : "${var.apigee_shortenv}-${ns}"]
  workspaces             = contains(["internal-dev", "internal-dev-sandbox"], var.apigee_environment) ? [var.workspace, "${var.workspace}:*"] : [var.workspace]

  private_alb_listeners = data.terraform_remote_state.account.outputs.apis.alb-listener.private[var.apigee_environment]
  private_albs          = data.terraform_remote_state.account.outputs.apis.alb.private[var.apigee_environment]
  ecs_cluster         = data.terraform_remote_state.account.outputs.apis.ecs_clusters[var.apigee_environment]
  apis_subdomain      = data.terraform_remote_state.account.outputs.apis.apis_subdomain


}
