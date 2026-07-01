# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction`
Actual scenario: `constriction_seed_16`
Reference manifest: `outputs/m18g/c_constrict_corrected/constriction_seed_16/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe_flux_mass_froude_timing` | `roe_flux_mass_froude_timing` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_flux_mass_froude_timing

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.82762 | 0.25 | FAIL |
| `slope_linf` | 1.46966 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.274306 | 0.02 | FAIL |
| `probe_linf` | 2.25322 | 0.25 | FAIL |
| `cross_section_linf` | 1.73192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0397839 | 0.05 | PASS |
| `energy_change_delta` | 0.227565 | 0.25 | PASS |
| `froude_delta` | 0.488792 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.637697 | 10 | PASS |

## Notes

- Feature forcing stayed off; this fixture-scoped pass couples a bounded post-velocity recovery transfer with a shallow-fringe Froude target, preserving mass-conservative recovery movement while moving the constriction Froude summary inside threshold.

