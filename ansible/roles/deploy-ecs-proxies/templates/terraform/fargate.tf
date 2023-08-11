
data "aws_iam_role" "ecs-execution-role" {
  name = "ecs-x-${local.env_service_id}"
}

resource "aws_ecs_task_definition" "service" {
  family                   = local.env_namespaced_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = {{ service_cpu }}
  memory                   = {{ service_memory }}
  execution_role_arn       = data.aws_iam_role.ecs-execution-role.arn

  container_definitions = jsonencode(
  [
  for container in local.ecs_service:
  {
    cpu              = container.cpu
    essential        = container.essential
    image            = container.image
    name             = container.name
    logConfiguration = local.logConfig[container.name]
    portMappings = [
      {
        containerPort = container.port
        hostPort      = container.port
        protocol      = lower(container.protocol)
      }
    ]
    mountPoints = []
    volumesFrom = []
    environment = container.environment
    secrets     = container.secrets
  }
  ]
  )

  tags = local.common_tags

}



resource "aws_ecs_service" "service" {
  platform_version = "1.4.0"
  name             = var.namespaced_name
  cluster          = data.terraform_remote_state.pre-reqs.outputs.ecs_cluster_id
  task_definition  = aws_ecs_task_definition.service.arn

  desired_count = var.min_desired_capacity
  launch_type   = "FARGATE"

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  force_new_deployment               = true

  network_configuration {
    security_groups = data.terraform_remote_state.pre-reqs.outputs.security_groups
    subnets         = data.terraform_remote_state.pre-reqs.outputs.subnet_ids
  }

  health_check_grace_period_seconds = {{ health_check_grace_period_seconds }}

  load_balancer {
    target_group_arn = aws_alb_target_group.service.arn
    container_name   = local.exposed_service.name
    container_port   = 9000  # SG rules expect this to be on port 9000 as the SGs are clusterwise
  }

  depends_on = [
    aws_lb_listener_rule.service
  ]

  lifecycle {
    ignore_changes = [
      desired_count
    ]
  }

  tags = local.common_tags

}

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = var.min_desired_capacity
  resource_id        = "service/apis-${var.apigee_environment}/${aws_ecs_service.service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}


resource "aws_appautoscaling_policy" "ecs_policy" {

  count = var.autoscaling_enabled ? 1 : 0

  name               = local.short_env_namespaced_name
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = var.autoscaling_service_metric
      resource_label = local.autoscaling_resource_label
    }
    scale_out_cooldown = var.autoscaling_scale_out_cooldown
    scale_in_cooldown = var.autoscaling_scale_in_cooldown
    target_value = var.autoscaling_target_value
  }
}