data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_kms_key" "platform" {
  description             = "Atlas ${var.environment} platform encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableRootAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudWatchLogs"
        Effect    = "Allow"
        Principal = { Service = "logs.${data.aws_region.current.name}.amazonaws.com" }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = [
              "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/atlas/${var.environment}/*",
              "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:aws-waf-logs-${local.name}-*"
            ]
          }
        }
      },
      {
        Sid       = "AllowSns"
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action    = ["kms:Decrypt", "kms:GenerateDataKey*"]
        Resource  = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "platform" {
  name          = "alias/${local.name}-platform"
  target_key_id = aws_kms_key.platform.key_id
}

resource "aws_secretsmanager_secret" "api" {
  name                    = "${local.name}/api/runtime"
  description             = "Runtime secrets populated by the protected deployment pipeline"
  kms_key_id              = aws_kms_key.platform.arn
  recovery_window_in_days = 30
}

resource "aws_security_group" "alb" {
  name_prefix = "${local.name}-alb-"
  description = "Public HTTPS ingress to Atlas API load balancer"
  vpc_id      = aws_vpc.main.id

  lifecycle { create_before_destroy = true }
}

resource "aws_security_group" "api" {
  name_prefix = "${local.name}-api-"
  description = "Atlas API Fargate tasks"
  vpc_id      = aws_vpc.main.id

  lifecycle { create_before_destroy = true }
}

resource "aws_security_group" "database" {
  name_prefix = "${local.name}-postgres-"
  description = "PostgreSQL access from Atlas API only"
  vpc_id      = aws_vpc.main.id

  lifecycle { create_before_destroy = true }
}

resource "aws_security_group" "redis" {
  name_prefix = "${local.name}-redis-"
  description = "Redis access from Atlas API only"
  vpc_id      = aws_vpc.main.id

  lifecycle { create_before_destroy = true }
}

resource "aws_security_group_rule" "alb_http_ingress" {
  type              = "ingress"
  description       = "HTTP redirect"
  security_group_id = aws_security_group.alb.id
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "alb_https_ingress" {
  type              = "ingress"
  description       = "HTTPS"
  security_group_id = aws_security_group.alb.id
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "alb_api_egress" {
  type                     = "egress"
  description              = "API targets"
  security_group_id        = aws_security_group.alb.id
  source_security_group_id = aws_security_group.api.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "api_alb_ingress" {
  type                     = "ingress"
  description              = "Traffic from ALB"
  security_group_id        = aws_security_group.api.id
  source_security_group_id = aws_security_group.alb.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "api_https_egress" {
  type              = "egress"
  description       = "Outbound HTTPS"
  security_group_id = aws_security_group.api.id
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "api_postgres_egress" {
  type                     = "egress"
  description              = "PostgreSQL"
  security_group_id        = aws_security_group.api.id
  source_security_group_id = aws_security_group.database.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "postgres_api_ingress" {
  type                     = "ingress"
  description              = "PostgreSQL from API"
  security_group_id        = aws_security_group.database.id
  source_security_group_id = aws_security_group.api.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "api_redis_egress" {
  type                     = "egress"
  description              = "Redis TLS"
  security_group_id        = aws_security_group.api.id
  source_security_group_id = aws_security_group.redis.id
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "redis_api_ingress" {
  type                     = "ingress"
  description              = "Redis TLS from API"
  security_group_id        = aws_security_group.redis.id
  source_security_group_id = aws_security_group.api.id
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "redis_self_ingress" {
  type                     = "ingress"
  description              = "Redis replication group traffic"
  security_group_id        = aws_security_group.redis.id
  source_security_group_id = aws_security_group.redis.id
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
}
