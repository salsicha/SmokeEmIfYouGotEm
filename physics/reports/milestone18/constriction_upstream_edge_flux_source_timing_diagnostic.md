# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_edge_flux_source/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_edge_flux_source/finite_volume_roe/scenario/constriction_seed_16`
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
| `upstream_approach` | 1.97786 | 0.0636011 | 0.143186 | 72.067 | 1.97786 | 0 | 58.981 | 3 | -0.504034 |
| `constriction_throat` | 3.53606 | 0.26996 | 0.0334653 | 16.2123 | 3.53606 | 0 | 16.2123 | 0 | -1.1902 |
| `downstream_constriction` | 2.06694 | 0.252451 | 0.239199 | -11.6426 | 0 | 0 | -11.6426 | 0 | -0.425129 |
| `recovery` | -4.62466 | -0.0805988 | -0.0864033 | -47.1634 | 0 | 0 | -47.1634 | 0 | -0.150539 |

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
