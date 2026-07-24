variable "project_name" {
  description = "Name used to namespace Atlas resources."
  type        = string
  default     = "atlas-ai"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for regional resources."
  type        = string
  default     = "eu-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block allocated to the environment."
  type        = string
  default     = "10.20.0.0/16"
}

variable "dr_region" {
  description = "Secondary AWS region used for encrypted backup copies."
  type        = string
  default     = "eu-west-1"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the public API hostname."
  type        = string
}

variable "api_image_tag" {
  description = "Immutable API image tag or digest promoted into this environment."
  type        = string
  validation {
    condition     = var.api_image_tag != "latest" && length(var.api_image_tag) > 0
    error_message = "Use an immutable image tag or digest; latest is prohibited."
  }
}

variable "api_desired_count" {
  description = "Steady-state API task count. Production should use at least three."
  type        = number
  default     = 1
  validation {
    condition = (
      var.api_desired_count >= 1 &&
      (var.environment != "production" || var.api_desired_count >= 3)
    )
    error_message = "At least one API task is required; production requires at least three."
  }
}

variable "api_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 1024
}

variable "api_min_capacity" {
  description = "Minimum API task count for autoscaling."
  type        = number
  default     = 1
}

variable "api_max_capacity" {
  description = "Maximum API task count for autoscaling."
  type        = number
  default     = 10
}

variable "api_cors_origins" {
  description = "JSON array of allowed web origins."
  type        = string
  default     = "[\"https://atlas.example\"]"
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.t4g.medium"
}

variable "db_engine_version" {
  description = "Approved PostgreSQL engine version."
  type        = string
  default     = "16.4"
}

variable "db_allocated_storage_gib" {
  description = "Initial gp3 database storage."
  type        = number
  default     = 100
}

variable "db_max_allocated_storage_gib" {
  description = "Maximum autoscaled database storage."
  type        = number
  default     = 1000
}

variable "redis_node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.t4g.small"
}

variable "redis_auth_token" {
  description = "ElastiCache auth token, supplied by a protected CI secret."
  type        = string
  sensitive   = true
  validation {
    condition = (
      length(var.redis_auth_token) >= 16 &&
      length(var.redis_auth_token) <= 128 &&
      length(regexall("[\"/@]", var.redis_auth_token)) == 0
    )
    error_message = "Redis auth tokens must be 16-128 characters and cannot contain /, @, or quotes."
  }
}

variable "alarm_email" {
  description = "Optional operational alarm subscription email."
  type        = string
  default     = ""
}

variable "backup_retention_days" {
  description = "Warm retention for primary-region recovery points."
  type        = number
  default     = 35
}

variable "dr_backup_retention_days" {
  description = "Retention for cross-region backup copies."
  type        = number
  default     = 90
}

variable "github_repository" {
  description = "GitHub owner/repository allowed to deploy, for example atlas-ai/platform."
  type        = string
  default     = ""
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub Actions IAM OIDC provider ARN for this AWS account."
  type        = string
  default     = ""
}
