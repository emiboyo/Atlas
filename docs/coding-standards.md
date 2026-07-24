# Coding standards

- TypeScript is strict; avoid `any`, unchecked casts, and environment reads outside config.
- Python is fully typed and must pass Ruff and strict mypy.
- Public contracts require tests and backward-compatible evolution.
- Dependencies are injected at boundaries; domain code must not instantiate infrastructure.
- Logs are structured events, contain request correlation, and never include secrets or PII.
- Errors use stable machine-readable codes and safe user-facing messages.
- Database changes use reviewed, reversible Alembic migrations.
- UI must be keyboard-accessible, responsive, and support light and dark themes.
- Security, privacy, and financial correctness take priority over delivery speed.
