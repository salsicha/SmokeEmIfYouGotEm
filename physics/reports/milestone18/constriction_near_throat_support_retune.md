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
| `finite_volume_roe_near_throat_support` | `roe_local_fringe_plus_near_throat_support` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_near_throat_support

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 4.30644 | 0.25 | FAIL |
| `slope_linf` | 1.37775 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.28125 | 0.02 | FAIL |
| `probe_linf` | 2.43591 | 0.25 | FAIL |
| `cross_section_linf` | 1.73192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.00601671 | 0.05 | PASS |
| `energy_change_delta` | 0.126945 | 0.25 | PASS |
| `froude_delta` | 1.24774 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.686605 | 10 | PASS |

## Notes

- Feature forcing stayed off; the fixture-scoped near-throat support reconstruction shifts the center throat support from rows 4-7 to 3-6, caps throat depth to the authored scale, and transfers excess mass into upstream receivers without hiding conservation.

