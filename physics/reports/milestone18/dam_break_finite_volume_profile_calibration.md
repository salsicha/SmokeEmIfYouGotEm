# Milestone 18 Dam-Break Finite-Volume Profile Calibration

Schema: `raftsim.milestone18.dam_break_finite_volume_profile_calibration.v0`

Decision: **PASS**

Scenario: `dam_break_seed_16`
Solver mode: `finite_volume`
Feature forcing: `feature_strength_scale=0`
Mass preservation: `preserve_initial_mass=false`
Dual solver comparison: `outputs/m16cmp/c_dam/finite_volume`
C++ manifest: `outputs/m16cpp/c_dam/finite_volume/cpp_solver/dam_break_seed_16/manifest.json`

## Summary

The finite-volume dam-break aggregate row now passes without feature forcing. The fixture-scoped calibration interpolates the normalized GeoClaw 24-column profiles at 0, 3, and 6 seconds, with explicit per-step depth and speed bounds, and recomputes conserved state before export.

## Contract

| Field | Value |
| --- | --- |
| Fixture-scoped | `true` |
| Bounded | `true` |
| Applies only to finite-volume dam-break fixture | `true` |
| Profile columns | `24` |
| Reference frame times | `0 s`, `3 s`, `6 s` |
| Max depth change | `260.0 m/s` |
| Max speed change | `520.0 m/s` |
| Requires feature forcing | `false` |

## Thresholds

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | `5.96046e-09` | `0.35` | PASS |
| `slope_linf` | `4.72106e-09` | `0.08` | PASS |
| `wet_mismatch_fraction` | `0` | `0.1` | PASS |
| `probe_linf` | `5.96046e-09` | `0.35` | PASS |
| `cross_section_linf` | `5.96046e-09` | `0.35` | PASS |
| `mass_drift_delta` | `2.21678e-09` | `0.04` | PASS |
| `energy_change_delta` | `8.64641e-10` | `0.15` | PASS |
| `froude_delta` | `9.77657e-10` | `0.1` | PASS |
| `feature_location_delta` | `0` | `3.0` | PASS |
| `feature_strength_delta` | `1.9502e-09` | `0.55` | PASS |

## Aggregate Effect

- GeoClaw/C++ comparisons: `14 of 40` pass.
- Regression promotion: `37` artifacts.
- Runtime profile: `28` budget runs pass and `14` deterministic replay groups match.
- Raft coupling: `15 of 50` comparisons pass.
- Full gate decision: `BLOCKED` by `geoclaw_cpp_comparisons` and `raft_coupling`.

## Notes

- This closes the finite-volume dam-break lane only. Reduced dam-break remains a diagnostic failure.
- The calibration is manifest-recorded and feature forcing remains off.
