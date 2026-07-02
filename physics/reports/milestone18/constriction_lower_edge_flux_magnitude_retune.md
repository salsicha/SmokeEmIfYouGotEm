# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction_seed_16`
Actual scenario: `constriction_seed_16`
Reference manifest: `physics/outputs/m18g/c_constrict_corrected/constriction_seed_16/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe` | `lower_edge_flux_magnitude_firstwet` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.15001 | 0.25 | FAIL |
| `slope_linf` | 0.718485 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.46647 | 0.25 | FAIL |
| `cross_section_linf` | 0.197107 | 0.25 | PASS |
| `mass_drift_delta` | 0.0472882 | 0.05 | PASS |
| `energy_change_delta` | 0.17333 | 0.25 | PASS |
| `froude_delta` | 0.44574 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.633438 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off and adds a manifest-recorded, bounded, velocity-only lower-edge flux-magnitude balance over relaxed upstream lower shelf and first-wet rows after upstream centerline timing.
- The candidate improves field Linf from 3.15070 to 3.15001, slope from 0.719087 to 0.718485, hv Linf from 1.85185 to 1.82088, and cross-section from 0.197127 to 0.197107 while keeping mass, energy, Froude, and feature checks passing; probe slightly worsens from 0.463334 to 0.466470, so promotion remains blocked.

