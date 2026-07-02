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
| `finite_volume_roe` | `upstream_centerline_balance` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.20012 | 0.25 | FAIL |
| `slope_linf` | 0.71908 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.461007 | 0.25 | FAIL |
| `cross_section_linf` | 0.197127 | 0.25 | PASS |
| `mass_drift_delta` | 0.047266 | 0.05 | PASS |
| `energy_change_delta` | 0.171134 | 0.25 | PASS |
| `froude_delta` | 0.431289 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.626267 | 10 | PASS |

## Notes

- Feature forcing remains off while the upstream shelf balance transfers mass conservatively from the over-deep upper edge row into lower-edge receivers, then a duration-normalized late upstream-centerline pass transfers remaining upper-edge depth into centerline rows and shapes edge cross-stream velocity without adding gameplay forcing.
- The attempt improves field Linf to 3.20012, slope Linf to 0.71908, probe Linf to 0.461007, energy delta to 0.171134, Froude delta to 0.431289, and feature-strength delta to 0.626267 while keeping cross-section Linf passing at 0.197127 and mass drift passing at 0.047266.
- Promotion remains blocked by field, slope, wet-mask, and probe thresholds; the next lever should address remaining upstream edge velocity/depth field errors and downstream/probe hu without breaking the conservation margin.

