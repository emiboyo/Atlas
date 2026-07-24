# Deployment

## Vercel

1. Import the repository and set the root directory to `apps/web`.
2. Use the repository's `vercel.json` commands.
3. Configure all variables from `apps/web/.env.example` in Vercel.
4. Protect preview and production environments with separate Clerk and Stripe credentials.
5. Require the `Lint`, `Test`, and `Build` GitHub checks before production promotion.

## AWS

1. Create the remote Terraform S3 state bucket and DynamoDB lock table in a dedicated
   bootstrap stack.
2. Copy `backend.tf.example` to an environment-specific, uncommitted backend file.
3. Run `terraform init`, `terraform plan`, and apply through a protected CI environment.
4. Use the documented two-phase bootstrap to create ECR and the empty runtime secret without
   placing secret values in Terraform state.
5. Publish immutable commit-tagged API images and deploy through the protected GitHub OIDC
   workflow, which runs migrations before ECS service promotion.
6. Operate RDS PostgreSQL Multi-AZ, ElastiCache Redis, Secrets Manager, KMS, WAF, CloudWatch,
   locked backup vaults, and cross-region recovery copies. Never deploy Compose data services
   to production.

Production deployment credentials are deliberately not committed. Add workload modules
with the first approved service release so capacity, recovery objectives, and data
classification are specified from real requirements.
