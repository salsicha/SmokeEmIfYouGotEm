# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/scenario/constriction_seed_16`
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
| `upstream_approach` | 1.96197 | 0.0634425 | 0.14299 | 72.0309 | 1.96197 | 0 | 58.9449 | 3 | -0.504034 |
| `constriction_throat` | 3.53136 | 0.269699 | 0.0332915 | 16.1015 | 3.53136 | 0 | 16.1015 | 0 | -1.1892 |
| `downstream_constriction` | 2.06093 | 0.251852 | 0.238549 | -11.592 | 0 | 0 | -11.592 | 0 | -0.424758 |
| `recovery` | -4.63722 | -0.0807836 | -0.0874158 | -53.6662 | 0 | 0 | -53.6662 | 0 | -0.229271 |

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
