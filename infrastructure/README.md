# Atlas infrastructure

Atlas deploys the public Next.js application to Vercel and the API/data platform to AWS.
Terraform under `aws/` owns the AWS environment as one versioned stack.

## Provisioned architecture

```text
Internet
   │
 AWS WAF
   │
 HTTPS ALB ───── encrypted access logs
   │
 ECS Fargate tasks in three private subnets
   ├── RDS PostgreSQL Multi-AZ
   ├── ElastiCache Redis replication group
   ├── Secrets Manager
   └── CloudWatch logs, metrics, alarms and dashboard

AWS Backup ── encrypted primary vault ── cross-region DR vault
```

The stack also provisions immutable ECR storage, KMS keys, task-specific security groups,
least-privilege ECS roles, GitHub OIDC deployment permissions, VPC flow logs, autoscaling,
deployment rollback, encrypted backups, and optional alarm email routing.

## Prerequisites

- Terraform 1.9 or later
- Existing encrypted S3 state bucket and DynamoDB lock table
- Existing ACM certificate in the workload region
- Existing GitHub Actions OIDC provider if repository deployment is enabled
- A protected mechanism for setting Secrets Manager values and `TF_VAR_redis_auth_token`
- Account-level CloudTrail, GuardDuty, Security Hub, AWS Config, IAM Access Analyzer, and
  organization security policies managed by the platform/security account baseline

## Two-phase bootstrap

Runtime secret values never enter Terraform state. Bootstrap the durable prerequisites first:

```sh
terraform init -backend-config=backend.hcl
terraform apply \
  -target=aws_db_instance.postgres \
  -target=aws_elasticache_replication_group.redis \
  -target=aws_secretsmanager_secret.api \
  -target=aws_ecr_repository.api
```

Terraform will include the required network, security, and encryption dependencies. Use the
resulting private data endpoints and RDS-managed credential to populate the API secret as one
JSON object:

```json
{
  "database_url": "postgresql+asyncpg://...",
  "redis_url": "rediss://:token@...",
  "clerk_issuer_url": "https://...",
  "clerk_jwks_url": "https://.../.well-known/jwks.json",
  "stripe_secret_key": "REPLACE_WITH_PRODUCTION_STRIPE_SECRET",
  "stripe_webhook_secret": "whsec_..."
}
```

Push the immutable bootstrap API image to ECR, then run a normal reviewed plan and apply.
Production changes must be applied only from a protected CI environment using OIDC.

## Commands

```sh
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -out=atlas.tfplan
terraform show atlas.tfplan
terraform apply atlas.tfplan
```

Copy `terraform.tfvars.example` to an uncommitted environment-specific `.tfvars` file.
Provide the Redis token through `TF_VAR_redis_auth_token`.

## Production defaults

- Three NAT gateways and at least three API tasks across availability zones
- RDS Multi-AZ, deletion protection, PITR, enhanced monitoring, and Performance Insights
- Redis automatic failover, Multi-AZ, TLS, at-rest encryption, authentication, and replicas
- WAF managed protections and a global IP rate limit
- Immutable ECR tags and KMS encryption
- 365-day application, flow, and access-log retention
- Locked backup vaults and 90-day cross-region copies

Sizing defaults are starting guardrails, not capacity claims. Load tests and measured SLOs must
drive task, database, cache, connection pool, and autoscaling configuration.

## Deployment

`deploy-api.yml` builds an image tagged with the Git commit SHA, pushes it to ECR, registers a
new task definition, runs Alembic as a one-off Fargate task, verifies the migration exit code,
then deploys the exact task definition and waits for service stability.

Required protected GitHub environment values:

- Secret `AWS_DEPLOY_ROLE_ARN`
- Variable `AWS_REGION`
- Variable `API_ECR_REPOSITORY_URL`
- Variable `ECS_CLUSTER`
- Variable `ECS_SERVICE`

## Disaster recovery

See [the disaster-recovery runbook](../docs/runbooks/disaster-recovery.md). Backups are not
considered operational until scheduled restore tests demonstrate the approved RPO and RTO.
