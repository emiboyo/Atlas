# ADR 0005: AWS regional platform with cross-region backup recovery

- Status: Accepted
- Date: 2026-07-24

## Context

Atlas needs an isolated, observable workload platform with a credible recovery path before
financial features launch. An active-active database design would add consistency risk before
RPO, RTO, and geographic requirements are measured.

## Decision

Run FastAPI on ECS Fargate in private subnets behind WAF and an HTTPS ALB. Use RDS PostgreSQL
Multi-AZ as the durable source, ElastiCache Redis as reconstructable state, Secrets Manager for
runtime credentials, and CloudWatch for initial operations. Use immutable ECR images and a
GitHub OIDC deployment role. Copy encrypted RDS recovery points to a second region through AWS
Backup and restore through a tested warm-recovery runbook.

## Consequences

The platform tolerates task, node, and availability-zone failures. Regional recovery is
asynchronous and operator-driven. Backup restore exercises, external endpoint reconfiguration,
DNS failover, and event reconciliation are mandatory. Active-active or global-database designs
remain deferred until business RPO/RTO and consistency requirements justify them.
