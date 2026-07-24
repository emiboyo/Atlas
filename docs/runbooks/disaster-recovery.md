# Disaster recovery runbook

## Scope

This runbook covers loss or prolonged unavailability of the primary AWS region. The implemented
foundation provides encrypted cross-region RDS recovery points; it does not maintain an active
secondary application stack or zero-data-loss synchronous replication.

## Required business decisions

Before production launch, executive, compliance, and engineering owners must approve:

- Recovery point objective (RPO)
- Recovery time objective (RTO)
- Incident commander and activation authority
- Customer and regulator communication requirements
- Data reconciliation and market-operation resumption criteria

## Readiness checks

Perform at least quarterly:

1. Confirm successful primary backups and cross-region copies.
2. Restore the latest recovery point into an isolated DR network.
3. Validate schema head, row counts, ledger balance invariants, and critical checksums.
4. Deploy the exact production image digest into an isolated DR ECS service.
5. Exercise secret recreation, Clerk/Stripe endpoint configuration, and DNS switching.
6. Record achieved RPO/RTO, discrepancies, evidence, and remediation owners.
7. Destroy the isolated exercise resources through a reviewed Terraform plan.

## Regional recovery sequence

1. Declare the incident and freeze non-essential deployments and financial processing.
2. Determine the latest known-consistent cross-region recovery point.
3. Apply the environment Terraform stack in the DR region with a non-overlapping VPC CIDR.
4. Restore PostgreSQL from the selected recovery point using the DR KMS key.
5. Create a clean Redis cluster; Redis is not a financial source of truth.
6. Recreate runtime secrets through the approved secret-management process.
7. Run database integrity, tenant-isolation, ledger-balance, and reconciliation checks.
8. Deploy the last approved immutable API image.
9. Configure Stripe webhook and Clerk origins for the recovery hostname.
10. Execute synthetic health, authentication, billing, and read-only portfolio checks.
11. Obtain incident-command approval before directing production traffic to DR.
12. Reconcile queued external events before enabling state-changing operations.

## Failback

Failback is a separate controlled migration. Establish the primary region from a verified,
quiesced recovery point; reconcile external events; test it in isolation; then perform a
scheduled traffic transition. Never attempt simultaneous writes in two regions without an
approved multi-region consistency architecture.

## Evidence

Retain backup job IDs, recovery point ARNs, Terraform plan/apply records, database validation
reports, image digests, test output, timestamps, decision logs, and approver identities according
to the incident-retention policy.
