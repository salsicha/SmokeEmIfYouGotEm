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
| `finite_volume_roe` | `lower_edge_transition_momentum_floor2` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.14841 | 0.25 | FAIL |
| `slope_linf` | 0.712231 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.472432 | 0.25 | FAIL |
| `cross_section_linf` | 0.197102 | 0.25 | PASS |
| `mass_drift_delta` | 0.0475158 | 0.05 | PASS |
| `energy_change_delta` | 0.172816 | 0.25 | PASS |
| `froude_delta` | 0.445683 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.630604 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off and adds a manifest-recorded, bounded lower-edge transition momentum source over the upstream first-wet row within two cells of the upstream throat edge; the retained weight floor is 2.0 after 0.65/1.0/3.0/4.0 trials.
- The candidate improves field Linf from 3.15001 to 3.14841, slope from 0.718485 to 0.712231, hv Linf from 1.82088 to 1.69782, cross-section from 0.197107 to 0.197102, Froude from 0.445740 to 0.445683, and feature-strength from 0.633438 to 0.630604 while keeping feature forcing off and mass/energy passing at 0.047516/0.172816; probe worsens to 0.472432 and promotion remains blocked.

