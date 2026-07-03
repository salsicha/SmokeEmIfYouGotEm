# Milestone 18 Analytic Retune Guardrail

Schema: `raftsim.milestone18.analytic_retune_guardrail.v0`

Decision: **BLOCKED**

Retune batch: `recovery_upper_interior_to_lower_shelf_depth_pocket_final_support`

Manifest: `physics/data/validation/milestone17/analytic_fixtures/manifest.json`

| Stage | Result | Candidate | Fixtures | Failed | Report |
| --- | --- | --- | ---: | ---: | --- |
| preflight | FAIL | throat_interior_depth_relief_pocket_final_support (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_upper_interior_to_lower_shelf_depth_pocket_final_support/recovery_upper_interior_to_lower_shelf_depth_pocket_final_support/preflight_analytic_validation.json` |
| postflight | FAIL | recovery_upper_interior_to_lower_shelf_depth_pocket_final_support (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_upper_interior_to_lower_shelf_depth_pocket_final_support/recovery_upper_interior_to_lower_shelf_depth_pocket_final_support/postflight_analytic_validation.json` |

## Blocked Reasons

- Preflight analytic fixtures are already failing; retuning cannot start from this baseline.
- Postflight analytic fixtures failed; reject the retune batch.
