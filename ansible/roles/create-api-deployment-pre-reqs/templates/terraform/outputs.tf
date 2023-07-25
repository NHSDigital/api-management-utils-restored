
output "vpc_id" {
  value = data.terraform_remote_state.account.outputs.account_vpc.id
}

output "private_alb_listener_arns" {
  value = [for listener in local.private_alb_listeners : listener.arn]
}

output "private_alb_listener_count" {
  value = data.terraform_remote_state.account.outputs.apis.alb-listener-count
}

output "private_alb_arn_suffixes" {
  value = [for alb in local.private_albs : alb.arn_suffix]
}

output "subnet_ids" {
  value = data.terraform_remote_state.account.outputs.apis.subnet_ids
}

output "ecs_cluster_id" {
  value = local.ecs_cluster.id
}

output "ecs_sg_id" {
  value = data.terraform_remote_state.account.outputs.apis.sg.apis-ecs-cluster[var.apigee_environment].id
}

output "security_groups" {
  value = [
    data.terraform_remote_state.account.outputs.apis.sg.apis-ecs-cluster[var.apigee_environment].id,
    aws_security_group.api-deployment.id
  ]
}
