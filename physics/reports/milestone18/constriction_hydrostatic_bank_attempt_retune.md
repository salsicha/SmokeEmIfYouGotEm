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
| `finite_volume_roe_bank_source` | `rejected_abrupt_bank_source_reconstruction` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=1.5, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `finite_volume_roe_full_hydrostatic_flux` | `rejected_full_hydrostatic_flux_reconstruction` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=1.5, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_bank_source

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 6.02796 | 0.25 | FAIL |
| `slope_linf` | 1.10748 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.0277778 | 0.02 | FAIL |
| `probe_linf` | 1.24818 | 0.25 | FAIL |
| `cross_section_linf` | 4.58965 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0019445 | 0.05 | PASS |
| `energy_change_delta` | 0.0841479 | 0.25 | PASS |
| `froude_delta` | 1.08936 | 0.5 | FAIL |
| `feature_location_delta` | 3 | 5 | PASS |
| `feature_strength_delta` | 0.424191 | 10 | PASS |

### finite_volume_roe_full_hydrostatic_flux

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 5.86075 | 0.25 | FAIL |
| `slope_linf` | 1.10745 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.0555556 | 0.02 | FAIL |
| `probe_linf` | 1.21352 | 0.25 | FAIL |
| `cross_section_linf` | 4.37575 | 0.25 | FAIL |
| `mass_drift_delta` | 2.83592e-05 | 0.05 | PASS |
| `energy_change_delta` | 0.0582013 | 0.25 | PASS |
| `froude_delta` | 1.08936 | 0.5 | FAIL |
| `feature_location_delta` | 3 | 5 | PASS |
| `feature_strength_delta` | 0.623595 | 10 | PASS |

## Notes

- Both constriction hydrostatic-bank candidates keep feature forcing disabled and compare against the corrected GeoClaw user-boundary reference.
- Full hydrostatic interface reconstruction brings mass drift nearly to zero and feature strength inside default bounds, but worsens wet-mask, cross-section, Froude, and field-shape errors.
- Abrupt-bank source reconstruction keeps mass, energy, and feature-strength checks inside threshold but still fails field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, and froude_delta; the solver change is not retained as the runtime candidate.
- The next constriction lever is true throat/water-shape reconstruction or scenario width/depth mapping, not more scalar source scaling or bank-face hydrostatic source terms.

