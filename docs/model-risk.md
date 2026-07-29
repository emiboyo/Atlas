# Milestone 5 Model Risk

The implemented calculation model is deterministic and rule-based. Principal risks are specification error, look-ahead bias, survivorship bias in the source universe, incomplete observations, unrealistic fees or execution assumptions, overfitting, and users mistaking historical simulation for advice or prediction.

Controls include typed bounded rules, explicit execution/fee/slippage/sizing/missing-data assumptions, immutable versions, input and result checksums, engine versioning, data-quality labels, neutral comparison, prominent disclaimers, and no financial execution path.

The local explanation template cannot change calculations. It describes stored evidence and states limitations. No external model, prompt service, training pipeline, personalised advice, autonomous action, or live recommendation is authorised.

Independent security and model-risk review remains required before production. Governance expires on 2026-10-27 and is reviewed on 2026-08-27 by risk owner Adebayo Olaegbe.
