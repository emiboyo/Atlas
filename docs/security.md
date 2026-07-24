# Security baseline

- Identity is delegated to Clerk; API authorization must validate issuer, audience, signature,
  expiry, and subject for every protected route.
- Stripe webhook signatures must be verified before event processing.
- Secrets belong in Vercel environment variables or AWS Secrets Manager, never Git.
- Production data services remain private and encrypted in transit and at rest.
- Least-privilege IAM roles are assigned per workload.
- Dependency, container, SAST, and IaC scanning should be enforced before release.
- Audit-relevant events require immutable retention and explicit data classification.
- Financial features require threat modelling, regulatory review, and abuse controls before launch.
