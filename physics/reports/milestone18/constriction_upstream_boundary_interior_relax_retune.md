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
| `finite_volume_roe` | `roe_upstream_boundary_interior_relax` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.23058 | 0.25 | FAIL |
| `slope_linf` | 0.787354 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.263889 | 0.02 | FAIL |
| `probe_linf` | 2.15656 | 0.25 | FAIL |
| `cross_section_linf` | 1.6623 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0241993 | 0.05 | PASS |
| `energy_change_delta` | 0.105115 | 0.25 | PASS |
| `froude_delta` | 0.459515 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.812922 | 10 | PASS |

## Notes

- Record bounded upstream inflow-column support plus stronger upstream interior velocity relaxation; feature forcing remains off.
- Do not promote: field/mass/energy improve and Froude remains passing, but wet-mask, probe, cross-section, and upper-edge lateral velocity remain blocked.

