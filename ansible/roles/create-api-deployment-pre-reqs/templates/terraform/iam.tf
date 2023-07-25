data "aws_iam_policy_document" "ecs-tasks-assume-role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecs-execution-role" {

  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]

    resources = [
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter/${var.account}/platform-common/*",
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter/${var.account}/api-deployment/${var.service_id}/*"
    ]
  }

  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [
      "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:${var.account}/*"
    ]

    condition {
      test = "ForAnyValue:StringLike"
      values = [
        "${var.service_id}",
        "${var.service_id} *",
        "* ${var.service_id} *",
        "* ${var.service_id}",
        "all"
      ]
      variable = "secretsmanager:ResourceTag/AllowedServices1"
    }

  }

  statement {

    actions = [
      "ecr:GetAuthorizationToken"
    ]

    resources = [
      "*"
    ]

  }

  statement {

    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetRepositoryPolicy",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages",
      "s3:GetObject"
    ]

    resources = [
      "arn:aws:ecr:${local.region}:${local.account_id}:repository/${var.service_id}",
      "arn:aws:ecr:${local.region}:${local.account_id}:repository/${var.service_id}_*",
      "arn:aws:s3:::${local.aws_ecr_bucket}/*",
    ]

  }

}

resource "aws_iam_role" "ecs-execution-role" {
  name               = "ecs-x-${local.env_service_id}"
  assume_role_policy = data.aws_iam_policy_document.ecs-tasks-assume-role.json

  tags = {
    Name   = "ecs-x-${local.env_service_id}"
    source = "terraform"
    api-service = var.service_id
    api-environment = var.apigee_environment
  }
}

resource "aws_iam_role_policy" "ecs-execution-role" {
  name   = aws_iam_role.ecs-execution-role.name
  role   = aws_iam_role.ecs-execution-role.name
  policy = data.aws_iam_policy_document.ecs-execution-role.json
}

resource "aws_iam_role_policy_attachment" "attach_AmazonECSTaskExecutionRolePolicy_to_monitoring-ecs-tasks" {
  role       = aws_iam_role.ecs-execution-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "deploy-user" {
  name   = "deploy-${local.env_service_id}"
  policy = data.aws_iam_policy_document.deploy-user.json
}

data "aws_ssm_parameter" "ptl_account_id" {
  name = "/account-ids/ptl"
}

data "aws_iam_policy_document" "deploy-user-assume-role" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type = "AWS"

      identifiers = [
        "arn:aws:iam::${data.aws_ssm_parameter.ptl_account_id.value}:role/build-agent",
      ]
    }
  }
}

resource "aws_iam_role" "deploy-user" {
  name = "deploy-${local.env_service_id}"
  assume_role_policy = data.aws_iam_policy_document.deploy-user-assume-role.json

  tags = {
    source = "terraform"
    api-service = var.service_id
    api-environment = var.apigee_environment
  }
}

resource "aws_iam_role_policy_attachment" "deploy-user" {
  role       = aws_iam_role.deploy-user.name
  policy_arn = aws_iam_policy.deploy-user.arn
}

data "aws_iam_policy_document" "deploy-user" {

  statement {

    actions = [
      "ecr:GetAuthorizationToken",
      "ecs:DescribeTaskDefinition",
      "ec2:DescribeAccountAttributes",
      "ecs:DeregisterTaskDefinition",
      "elasticloadbalancing:DescribeTargetGroup*",
      "elasticloadbalancing:DescribeTags",
      "elasticloadbalancing:DescribeRules",
      "application-autoscaling:RegisterScalableTarget",
      "application-autoscaling:DescribeScalableTargets",
      "application-autoscaling:DeregisterScalableTarget",
      "application-autoscaling:PutScalingPolicy",
      "application-autoscaling:DeleteScalingPolicy",
      "application-autoscaling:DescribeScalingPolicies"
    ]

    # these actions can't be restricted by resource
    resources = [
      "*"
    ]

  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:ListBucketVersions",
      "s3:GetBucketLocation",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem"
    ]
    resources = [
      "arn:aws:s3:::${var.state_bucket}",
      "arn:aws:dynamodb:${local.region}:${local.account_id}:table/terraform-state-lock"

    ]
  }

  statement {

    actions = [
      "s3:GetObject",
    ]

    resources = concat(
      [
        "arn:aws:s3:::${var.state_bucket}/env:",
      ],
      [for ws in local.workspaces : "arn:aws:s3:::${var.state_bucket}/env:/${ws}/*"]
    )
  }

  statement {

    actions = [
      "s3:PutObject",
      "iam:GetRole",
      "iam:PassRole"
    ]

    resources = concat(
      [
        aws_iam_role.ecs-execution-role.arn,
        "arn:aws:iam::${local.account_id}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService"
      ],
      [for ws in local.workspaces : "arn:aws:s3:::${var.state_bucket}/env:/${ws}/deployment/*"]
    )
  }

  statement {

    actions = [
      "ecs:RegisterTaskDefinition"
    ]

    resources = [
      "*"
    ]

    condition {
      test = "StringEquals"
      values = [var.service_id]
      variable = "aws:RequestTag/api-service"
    }

    condition {
      test = "StringEquals"
      values = [var.apigee_environment]
      variable = "aws:RequestTag/api-environment"
    }

  }

  statement {
    actions = [
      "ecs:TagResource",
      "ecs:UntagResource"
    ]

    resources = concat(
      [local.ecs_cluster.arn],
      [for ns in local.service_namespaces : "arn:aws:ecs:${local.region}:${local.account_id}:service/apis-${var.apigee_environment}/${ns}"]
    )
  }

  statement {

    actions = [
      "elasticloadbalancing:*TargetGroup*",
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:*Rule"
    ]
    resources = concat(
      [
        "arn:aws:elasticloadbalancing:${local.region}:${local.account_id}:listener-rule/app/apis-${var.apigee_environment}/*",
        "arn:aws:elasticloadbalancing:${local.region}:${local.account_id}:listener/app/apis-public-${var.apigee_environment}/*",
        "arn:aws:elasticloadbalancing:${local.region}:${local.account_id}:listener-rule/app/apis-public-${var.apigee_environment}/*",
      ],
      [for listener in local.private_alb_listeners : listener.arn],
      [for ns in local.short_env_service_namespaces : "arn:aws:elasticloadbalancing:${local.region}:${local.account_id}:targetgroup/${ns}/*"],
      [for ns in local.service_namespaces : "arn:aws:ecs:${local.region}:${local.account_id}:service/apis-${var.apigee_environment}/${ns}"]
    )
  }

  statement {

    actions = [
      "ecs:DescribeServices",
      "ecs:UpdateService",
      "ecs:DeleteService"
    ]

    resources = [
      for ns in local.service_namespaces :
      "arn:aws:ecs:${local.region}:${local.account_id}:service/apis-${var.apigee_environment}/${ns}"
    ]

    condition {
      test     = "StringEquals"
      values   = [local.ecs_cluster.arn]
      variable = "ecs:cluster"
    }

  }

  statement {

    actions = [
      "ecs:CreateService"
    ]

    resources = [
      for ns in local.service_namespaces :
      "arn:aws:ecs:${local.region}:${local.account_id}:service/apis-${var.apigee_environment}/${ns}"
    ]

    condition {
      test     = "StringEquals"
      values   = [local.ecs_cluster.arn]
      variable = "ecs:cluster"
    }

    condition {
      test     = "StringLike"
      values   = [for ns in local.env_service_namespaces : "arn:aws:ecs:${local.region}:${local.account_id}:task-definition/${ns}:*"]
      variable = "ecs:task-definition"
    }

  }

}
