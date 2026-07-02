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
| `finite_volume_roe` | `upper_edge_boundary_window_shape` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.24718 | 0.25 | FAIL |
| `slope_linf` | 0.725522 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.430327 | 0.25 | FAIL |
| `cross_section_linf` | 0.197986 | 0.25 | PASS |
| `mass_drift_delta` | 0.00190586 | 0.05 | PASS |
| `energy_change_delta` | 0.0714078 | 0.25 | PASS |
| `froude_delta` | 0.455441 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.780811 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off and adds a bounded, velocity-only, mass-preserving late upper-edge shape over the first three upstream boundary columns after upstream centerline timing; broader upper-edge flux-magnitude trials and higher speed targets were rejected because they spent too much probe margin.
- The candidate is not promoted: it improves mass from 0.0090901 to 0.00190586, energy from 0.0922814 to 0.0714078, Froude from 0.466646 to 0.455441, upper-edge column 1 q delta from 1.13760 to 0.869693, and upper-edge column 2 q delta from 0.683985 to 0.381482, but field/probe/slope regress to 3.24718/0.430327/0.725522 and the queue moves to lower-edge column 5 rows 1-2.

