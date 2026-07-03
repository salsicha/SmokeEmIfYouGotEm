# Milestone 18 Analytic Retune Guardrail

Schema: `raftsim.milestone18.analytic_retune_guardrail.v0`

Decision: **BLOCKED**

Retune batch: `recovery_upper_edge_near_spillback_depth_pocket_final_relief`

Manifest: `physics/data/validation/milestone17/analytic_fixtures/manifest.json`

| Stage | Result | Candidate | Fixtures | Failed | Report |
| --- | --- | --- | ---: | ---: | --- |
| preflight | FAIL | downstream_middle_streamwise_relief (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_upper_edge_near_spillback_depth_pocket_final_relief/recovery_upper_edge_near_spillback_depth_pocket_final_relief/preflight_analytic_validation.json` |
| postflight | FAIL | recovery_upper_edge_near_spillback (`cpp`) | 7 | 7 | `physics/reports/milestone18/analytic_retune_guardrails/recovery_upper_edge_near_spillback_depth_pocket_final_relief/recovery_upper_edge_near_spillback_depth_pocket_final_relief/postflight_analytic_validation.json` |

## Blocked Reasons

- Preflight analytic fixtures are already failing; retuning cannot start from this baseline.
- Postflight analytic fixtures failed; reject the retune batch.
