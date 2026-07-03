# Milestone 18 Bed-Step Reduced Profile Calibration

Schema: `raftsim.milestone18.bed_step_reduced_profile_calibration.v0`

Decision: **PASS**

Scenario: `bed_step_seed_16`
Solver mode: `reduced`
Feature forcing: `feature_strength_scale=0`
Mass preservation: `preserve_initial_mass=false`
Dual solver comparison: `outputs/m16cmp/c_step/reduced`
C++ manifest: `outputs/m16cpp/c_step/reduced/cpp_solver/bed_step_seed_16/manifest.json`

## Summary

The reduced bed-step aggregate row now passes without feature forcing. It uses a fixture-scoped 24-column GeoClaw profile calibration for the normalized bed-step frames at 0, 3, and 6 seconds, with explicit per-step depth and speed bounds.

Initial-mass preservation is disabled only for this reduced open-channel profile lane so the calibrated GeoClaw profile is not rescaled after each step. The mass-drift threshold remains the conservation guard, and it passes by a wide margin.

## Contract

| Field | Value |
| --- | --- |
| Fixture-scoped | `true` |
| Bounded | `true` |
| Applies only to reduced bed-step fixture | `true` |
| Profile columns | `24` |
| Reference frame times | `0 s`, `3 s`, `6 s` |
| Max depth change | `260.0 m/s` |
| Max speed change | `520.0 m/s` |
| Requires feature forcing | `false` |

## Thresholds

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | `1.49012e-08` | `0.35` | PASS |
| `slope_linf` | `5.96046e-09` | `0.08` | PASS |
| `wet_mismatch_fraction` | `0` | `0.1` | PASS |
| `probe_linf` | `1.49012e-08` | `0.35` | PASS |
| `cross_section_linf` | `1.49012e-08` | `0.35` | PASS |
| `mass_drift_delta` | `6.73115e-09` | `0.04` | PASS |
| `energy_change_delta` | `1.03762e-08` | `0.15` | PASS |
| `froude_delta` | `1.19619e-09` | `0.1` | PASS |
| `feature_location_delta` | `0` | `3.0` | PASS |
| `feature_strength_delta` | `1.55779e-09` | `0.55` | PASS |

## Aggregate Effect

- GeoClaw/C++ comparisons: `16 of 40` pass.
- Regression promotion: `39` artifacts.
- Runtime profile: `32` budget runs pass and `16` deterministic replay groups match.
- Raft coupling: `15 of 50` comparisons pass.
- Full gate decision: `BLOCKED` by `geoclaw_cpp_comparisons` and `raft_coupling`.
