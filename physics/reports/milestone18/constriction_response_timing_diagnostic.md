# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_asymmetric_envelope/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_asymmetric_envelope/finite_volume_roe/scenario/constriction_seed_16`
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
| `upstream_approach` | -25.6979 | -0.140005 | -0.721757 | -102.27 | -25.6979 | 0 | -52.5216 | -3 | -2.40352 |
| `constriction_throat` | -6.47783 | -0.286367 | -0.591863 | -12.4209 | -0.746215 | -5.25 | 4.61672 | -5.25 | -0.3229 |
| `downstream_constriction` | -3.62794 | -0.316874 | -0.160731 | -10.6117 | 0 | 0 | -2.72593 | -4.5 | 0.33339 |
| `recovery` | 0.867122 | 0.0163231 | -0.329206 | 1.14961 | 1.66667 | 1.5 | 47.7367 | -3.75 | -0.458348 |

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
