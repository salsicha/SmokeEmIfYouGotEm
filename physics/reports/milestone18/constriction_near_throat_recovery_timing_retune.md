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
| `finite_volume_roe` | `near_throat_recovery_timing` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.23118 | 0.25 | FAIL |
| `slope_linf` | 0.790651 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.84684 | 0.25 | FAIL |
| `cross_section_linf` | 0.197122 | 0.25 | PASS |
| `mass_drift_delta` | 0.0322516 | 0.05 | PASS |
| `energy_change_delta` | 0.0866112 | 0.25 | PASS |
| `froude_delta` | 0.460041 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.670548 | 10 | PASS |

## Notes

- Feature forcing remains off while the near-throat support now uses a mass-bounded shelf/interior profile with duration-normalized shelf and interior velocity timing.
- The recovery-centerline pass adds late-only, mass-conservative depth transfer from the upper recovery shelf plus bounded velocity relaxation; cross-section Linf now passes at 0.197122 while conservation, energy, and Froude stay green.
- Promotion remains blocked by final-frame field/slope/wet-mask and point-probe errors, with the next queue target shifted to upstream-center hu/u/v timing.

