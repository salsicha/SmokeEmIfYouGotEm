# Milestone 18 Analytic Retune Guardrail

Schema: `raftsim.milestone18.analytic_retune_guardrail.v0`

Decision: **BLOCKED**

Retune batch: `recovery_center_interior_streamwise_relief_pocket_final_support`

Manifest: `physics/data/validation/milestone17/analytic_fixtures/manifest.json`

| Stage | Result | Candidate | Fixtures | Failed | Report |
| --- | --- | --- | ---: | ---: | --- |
| preflight | FAIL | upstream_lower_middle_cross_stream (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_center_interior_streamwise_relief_pocket_final_support/recovery_center_interior_streamwise_relief_pocket_final_support/preflight_analytic_validation.json` |
| postflight | FAIL | recovery_center_streamwise_relief (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_center_interior_streamwise_relief_pocket_final_support/recovery_center_interior_streamwise_relief_pocket_final_support/postflight_analytic_validation.json` |

## Blocked Reasons

- Preflight analytic fixtures are already failing; retuning cannot start from this baseline.
- Postflight analytic fixtures failed; reject the retune batch.
