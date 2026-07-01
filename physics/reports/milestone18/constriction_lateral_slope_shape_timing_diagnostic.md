# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Zones

| Zone | Columns |
| --- | --- |
| `upstream_approach` | `0-9` |
| `constriction_throat` | `10-13` |
| `downstream_constriction` | `14-15` |
| `recovery` | `16-23` |

## Final And Peak Deltas

| Zone | Final mass m3 | Final mean depth m | Final max depth m | Final energy | Peak mass m3 | Peak mass time s | Peak energy | Peak energy time s | Final max Froude |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `upstream_approach` | -2.26266 | 0.0208959 | -0.0761725 | -36.279 | -2.26266 | 0 | -49.365 | 3 | -0.504034 |
| `constriction_throat` | 2.25487 | 0.198782 | -0.220133 | 11.6411 | 2.26805 | -0.75 | 11.6411 | 0 | -1.18676 |
| `downstream_constriction` | 2.04593 | 0.250399 | 0.237317 | -11.6282 | 0 | 0 | -11.6282 | 0 | -0.423756 |
| `recovery` | -4.66018 | -0.0811213 | -0.0872417 | -47.2691 | 0 | 0 | -47.2691 | 0 | -0.151093 |

## Blocked Reasons

- C++ final constriction-zone mass differs from GeoClaw beyond the diagnostic budget.
- C++ final mean wet depth differs from GeoClaw beyond the diagnostic budget.
- C++ peak-energy timing differs from GeoClaw beyond the diagnostic budget.
- C++ peak-energy magnitude differs from GeoClaw beyond the diagnostic budget.
- C++ final zone Froude envelope differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Retune constriction water volume and depth response now that wet-mask shape is closer to GeoClaw.
- Compare peak mass and energy timing before adding gameplay feature forcing.
- Add a bounded source/flux response only if it preserves Milestone 17 guardrails and does not hide conservation failures.
