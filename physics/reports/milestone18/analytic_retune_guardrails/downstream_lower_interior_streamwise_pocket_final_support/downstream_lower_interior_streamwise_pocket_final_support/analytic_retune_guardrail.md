# Milestone 18 Analytic Retune Guardrail

Schema: `raftsim.milestone18.analytic_retune_guardrail.v0`

Decision: **BLOCKED**

Retune batch: `downstream_lower_interior_streamwise_pocket_final_support`

Manifest: `physics/data/validation/milestone17/analytic_fixtures/manifest.json`

| Stage | Result | Candidate | Fixtures | Failed | Report |
| --- | --- | --- | ---: | ---: | --- |
| preflight | FAIL | recovery_upper_edge_near_spillback (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/downstream_lower_interior_streamwise_pocket_final_support/downstream_lower_interior_streamwise_pocket_final_support/preflight_analytic_validation.json` |
| postflight | FAIL | downstream_lower_interior_streamwise (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/downstream_lower_interior_streamwise_pocket_final_support/downstream_lower_interior_streamwise_pocket_final_support/postflight_analytic_validation.json` |

## Blocked Reasons

- Preflight analytic fixtures are already failing; retuning cannot start from this baseline.
- Postflight analytic fixtures failed; reject the retune batch.
