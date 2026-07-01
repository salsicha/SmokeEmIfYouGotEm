# Milestone 18 Constriction Response Timing Diagnostic

Schema: `raftsim.milestone18.constriction_response_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_flux_mass_froude_timing/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_flux_mass_froude_timing/finite_volume_roe/scenario/constriction_seed_16`
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
| `upstream_approach` | 2.71025 | 0.0237558 | -0.284065 | 31.6221 | 2.71025 | 0 | 18.536 | 3 | -0.488792 |
| `constriction_throat` | 0.719902 | 0.113507 | -0.123457 | 22.9966 | 1.01068 | -3.75 | 22.9966 | 0 | -0.444294 |
| `downstream_constriction` | -0.122622 | 0.0332435 | 0.0606655 | 3.31578 | 0 | 0 | 3.31578 | 0 | -0.12805 |
| `recovery` | 4.84816 | 0.0757417 | -0.267196 | 5.41298 | 0.166689 | 4.5 | 12.0551 | -3 | -0.453331 |

## Blocked Reasons

- C++ final constriction-zone mass differs from GeoClaw beyond the diagnostic budget.
- C++ peak-energy timing differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Retune constriction water volume and depth response now that wet-mask shape is closer to GeoClaw.
- Compare peak mass and energy timing before adding gameplay feature forcing.
- Add a bounded source/flux response only if it preserves Milestone 17 guardrails and does not hide conservation failures.
