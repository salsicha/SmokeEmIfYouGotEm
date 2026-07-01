# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_volume_response/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_volume_response/finite_volume_roe/scenario/constriction_seed_16`
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
| `upstream_approach` | -5.61017 | 0.0736945 | -0.521054 | -112.618 | -5.31659 | -1.5 | -52.5216 | -3 | -2.43527 |
| `constriction_throat` | -0.789674 | 0.0296412 | -0.143203 | 25.7822 | 0.473835 | -5.25 | 30.3151 | -2.25 | -0.379965 |
| `downstream_constriction` | -2.77153 | -0.231233 | -0.124354 | 24.0622 | 0 | 0 | 24.0622 | 0 | 0.521433 |
| `recovery` | 11.0189 | 0.167842 | -0.153161 | 41.2217 | 6.27921 | 6 | 79.1546 | -3 | -0.0977645 |

## Blocked Reasons

- C++ final constriction-zone mass differs from GeoClaw beyond the diagnostic budget.
- C++ peak-energy timing differs from GeoClaw beyond the diagnostic budget.
- C++ peak-energy magnitude differs from GeoClaw beyond the diagnostic budget.
- C++ final zone Froude envelope differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Retune constriction water volume and depth response now that wet-mask shape is closer to GeoClaw.
- Compare peak mass and energy timing before adding gameplay feature forcing.
- Add a bounded source/flux response only if it preserves Milestone 17 guardrails and does not hide conservation failures.
