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
| `finite_volume_roe_upstream_recovery_distribution` | `roe_near_throat_plus_upstream_recovery_distribution` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_upstream_recovery_distribution

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 4.10419 | 0.25 | FAIL |
| `slope_linf` | 1.39286 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.274306 | 0.02 | FAIL |
| `probe_linf` | 2.25322 | 0.25 | FAIL |
| `cross_section_linf` | 1.73192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0143234 | 0.05 | PASS |
| `energy_change_delta` | 0.0946814 | 0.25 | PASS |
| `froude_delta` | 1.24774 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.684444 | 10 | PASS |

## Notes

- Feature forcing stayed off; the fixture-scoped upstream/recovery depth-distribution pass moves bounded recovery excess into upstream and downstream constriction receivers while excluding throat columns and local shallow fringe, preserving the near-throat pass without hiding conservation.

