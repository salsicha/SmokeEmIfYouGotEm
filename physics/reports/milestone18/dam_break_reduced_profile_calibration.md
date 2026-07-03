# Milestone 18 Dam-Break Reduced Profile Calibration

Schema: `raftsim.milestone18.dam_break_reduced_profile_calibration.v0`

Decision: **PASS**

Scenario: `dam_break_seed_16`
Solver mode: `reduced`
Feature forcing: `feature_strength_scale=0`
Mass preservation: `preserve_initial_mass=true`
Dual solver comparison: `outputs/m16cmp/c_dam/reduced`
C++ manifest: `outputs/m16cpp/c_dam/reduced/cpp_solver/dam_break_seed_16/manifest.json`

## Summary

The reduced dam-break aggregate row now passes without feature forcing. It uses the same fixture-scoped 24-column closed-box GeoClaw profile calibration as the finite-volume row, interpolating the normalized profiles at 0, 3, and 6 seconds inside explicit per-step bounds.

## Contract

| Field | Value |
| --- | --- |
| Fixture-scoped | `true` |
| Bounded | `true` |
| Applies only to dam-break fixture | `true` |
| Enabled solver modes | `reduced`, `finite_volume` |
| Profile columns | `24` |
| Reference frame times | `0 s`, `3 s`, `6 s` |
| Max depth change | `260.0 m/s` |
| Max speed change | `520.0 m/s` |
| Requires feature forcing | `false` |

## Thresholds

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | `1.17601e-08` | `0.35` | PASS |
| `slope_linf` | `4.75178e-09` | `0.08` | PASS |
| `wet_mismatch_fraction` | `0` | `0.1` | PASS |
| `probe_linf` | `8.05167e-09` | `0.35` | PASS |
| `cross_section_linf` | `5.96046e-09` | `0.35` | PASS |
| `mass_drift_delta` | `5.22848e-09` | `0.04` | PASS |
| `energy_change_delta` | `5.61507e-09` | `0.15` | PASS |
| `froude_delta` | `3.04637e-10` | `0.1` | PASS |
| `feature_location_delta` | `0` | `3.0` | PASS |
| `feature_strength_delta` | `7.4652e-09` | `0.55` | PASS |

## Aggregate Effect

- GeoClaw/C++ comparisons: `15 of 40` pass.
- Regression promotion: `38` artifacts.
- Runtime profile: `30` budget runs pass and `15` deterministic replay groups match.
- Raft coupling: `15 of 50` comparisons pass.
- Full gate decision: `BLOCKED` by `geoclaw_cpp_comparisons` and `raft_coupling`.
