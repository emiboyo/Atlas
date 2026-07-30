# Research observability

Atlas exposes Prometheus metrics at `/metrics`. Research labels are fixed enums; IDs,
names, dates, amounts, request data, exception text, and explanation content are
prohibited as labels.

| Metric                                     | Type      | Labels                 | Meaning                                                                              |
| ------------------------------------------ | --------- | ---------------------- | ------------------------------------------------------------------------------------ |
| `atlas_research_strategy_operations_total` | Counter   | `operation`, `outcome` | Create, update, archive, and version-create outcomes                                 |
| `atlas_research_backtests_total`           | Counter   | `outcome`              | Requested, completed, failed, replay, conflict, invariant, and data-quality outcomes |
| `atlas_research_backtest_duration_seconds` | Histogram | none                   | End-to-end request duration with fixed buckets from 10 ms to 30 s                    |
| `atlas_research_explanations_total`        | Counter   | `outcome`              | Requested, generated, disabled, denied, replay, conflict, and failed outcomes        |
| `atlas_research_data_quality_total`        | Counter   | `outcome`              | Complete, stale, unavailable, and insufficient data outcomes                         |
| `atlas_research_conflicts_total`           | Counter   | `operation`            | Version, backtest, explanation, and transaction-commit conflicts                     |

The metrics are operational evidence only. They do not authorise production use and
must not be used to infer investment suitability or performance.
