# Milestone 18 Constriction Recovery Retune Rejection Diagnostic

Schema: `raftsim.milestone18.constriction_recovery_retune_rejection.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`

## Summary

- Baseline shelf-release field/probe Linf: `2.24265` / `0.350027`
- Rejected final recovery-edge shape field/probe Linf: `2.575` / `0.636084`
- Rejected fast-interior recovery edge-balance field/probe Linf: `3.89581` / `0.578405`
- Baseline mass/energy/Froude deltas: `0.00217828` / `0.120452` / `0.0240472`

## Rejected Trials

| Trial | Output | Field Linf | Probe Linf | Rejected reason |
| --- | --- | ---: | ---: | --- |
| `recovery_edge_final_shape_trial` | `physics/outputs/m18cmp/c_constrict_recovery_edge_final_shape_trial/finite_volume_roe` | `2.575` | `0.636084` | Over-damped recovery interior momentum after improving edge/shelf rows. |
| `recovery_edge_balance_fast_interior_trial` | `physics/outputs/m18cmp/c_constrict_recovery_edge_balance_fast_interior_trial/finite_volume_roe` | `3.89581` | `0.578405` | Stronger global recovery edge-balance response created reverse/under-speed centerline errors. |

## Blocked Reasons

- The final recovery-edge velocity-only shape rejected as a promotion lever: it improved edge/shelf rows but worsened field Linf from `2.24265` to `2.575` and probe Linf from `0.350027` to `0.636084`.
- The stronger existing recovery edge-balance retune rejected as a promotion lever: it pushed recovery interior momentum into reverse/under-speed and worsened field Linf to `3.89581`.
- The remaining recovery blocker requires split treatment of edge/shelf overdepth and center/interior streamwise momentum, not a global velocity-rate or speed-fraction increase.

## Next Levers

- Do not promote a velocity-only final recovery-edge shape; it hides edge errors by creating larger recovery-interior momentum failures.
- Do not globally raise the recovery edge-balance rate/max speed or far-interior speed fraction; the existing recovery balance needs profile-split treatment.
- Retune recovery edge/shelf depth relief separately from center/interior streamwise acceleration, then rerun field-profile, face-state, face/source, threshold, and analytic guardrail reports.
- Keep feature forcing off for the next water-field closure pass.
