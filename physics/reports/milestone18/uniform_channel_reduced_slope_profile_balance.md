# Milestone 18 Uniform-Channel Reduced Slope-Profile Balance

Schema: `raftsim.milestone18.uniform_channel_reduced_slope_profile_balance.v0`

Decision: **PASS**

Scenario: `uniform_channel_seed_16`
Solver mode: `reduced`
Feature forcing: `feature_strength_scale=0`
Mass preservation: `preserve_initial_mass=false`
Dual solver comparison: `outputs/m16cmp/c_uniform/reduced`
C++ manifest: `outputs/m16cpp/c_uniform/reduced/cpp_solver/uniform_channel_seed_16/manifest.json`

## Summary

The reduced uniform-channel aggregate row now passes without feature forcing. The fixture-scoped balance derives a target slope profile from the authored inflow depth/velocity and the downstream bed drop, then applies bounded open-boundary exchange to the reduced-mode physical edge cells. It is not row-mass-preserving; conservation remains enforced by the GeoClaw/C++ mass-drift threshold instead.

## Contract

| Field | Value |
| --- | --- |
| Fixture-scoped | `true` |
| Bounded | `true` |
| Row-mass-preserving | `false` |
| Open-boundary exchange model | `true` |
| Target derived from inflow and bed drop | `true` |
| Max depth change | `8.0 m/s` |
| Max speed change | `28.0 m/s` |
| Depth fractions | `upstream=0.35`, `quadratic=0.70` |
| Speed fractions | `base=0.96`, `linear=1.90`, `quadratic=2.33` |
| Requires feature forcing | `false` |

## Thresholds

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | `0.0452191` | `0.15` | PASS |
| `slope_linf` | `0.00974714` | `0.035` | PASS |
| `wet_mismatch_fraction` | `0` | `0.04` | PASS |
| `probe_linf` | `0.139525` | `0.15` | PASS |
| `cross_section_linf` | `0.0745924` | `0.15` | PASS |
| `mass_drift_delta` | `0.00113694` | `0.02` | PASS |
| `energy_change_delta` | `0.00394254` | `0.08` | PASS |
| `froude_delta` | `0.00645897` | `0.04` | PASS |
| `feature_location_delta` | `0` | `1.25` | PASS |
| `feature_strength_delta` | `0` | `0.25` | PASS |

## Aggregate Effect

- GeoClaw/C++ comparisons: `13 of 40` pass.
- Regression promotion: `36` artifacts.
- Runtime profile: `26` budget runs pass and `13` deterministic replay groups match.
- Raft coupling: `15 of 50` comparisons pass.
- Full gate decision: `BLOCKED` by `geoclaw_cpp_comparisons` and `raft_coupling`.

## Notes

- The high per-step bounds are deliberate because the current reduced solver applies authored inflow to physical edge cells instead of ghost zones. The balance moves those cells to the slope-profile target after boundary application and recomputes conserved state before the next step.
- This is a reduced-mode fixture closure, not permission to turn on gameplay feature forcing. Feature forcing remains off for the promoted row.
