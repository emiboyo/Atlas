output "vpc_id" {
  description = "VPC identifier for workload modules."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet identifiers for internet-facing load balancers."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet identifiers for application and data workloads."
  value       = aws_subnet.private[*].id
}

output "api_ecr_repository_url" {
  description = "Repository receiving immutable API images."
  value       = aws_ecr_repository.api.repository_url
}

output "api_load_balancer_dns_name" {
  description = "DNS target for the public API hostname."
  value       = aws_lb.api.dns_name
}

output "api_runtime_secret_arn" {
  description = "Secret to populate with API runtime JSON keys."
  value       = aws_secretsmanager_secret.api.arn
}

output "postgres_endpoint" {
  description = "Private PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "postgres_master_secret_arn" {
  description = "AWS-managed RDS master credential secret."
  value       = aws_db_instance.postgres.master_user_secret[0].secret_arn
  sensitive   = true
}

output "redis_configuration_endpoint" {
  description = "Private TLS Redis configuration endpoint."
  value       = aws_elasticache_replication_group.redis.configuration_endpoint_address
}

output "alarm_topic_arn" {
  description = "SNS topic for operational alarm routing."
  value       = aws_sns_topic.alarms.arn
}

output "dr_backup_vault_arn" {
  description = "Cross-region disaster recovery backup vault."
  value       = aws_backup_vault.dr.arn
}

output "ecs_cluster_name" {
  description = "Cluster name used by the application deployment workflow."
  value       = aws_ecs_cluster.main.name
}

output "ecs_api_service_name" {
  description = "API service name used by the application deployment workflow."
  value       = aws_ecs_service.api.name
}

output "github_deploy_role_arn" {
  description = "OIDC deployment role ARN when GitHub integration is configured."
  value       = try(aws_iam_role.github_deploy[0].arn, null)
}
