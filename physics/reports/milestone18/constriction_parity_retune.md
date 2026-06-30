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
| `finite_volume_hll` | `finite_volume_hll_corrected_boundary_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `finite_volume_roe` | `finite_volume_roe_corrected_boundary_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, froude_delta, feature_strength_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_corrected_boundary_feature0` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_strength_delta | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume_hll

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.63949 | 0.35 | FAIL |
| `slope_linf` | 0.677121 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0.0277778 | 0.1 | PASS |
| `probe_linf` | 1.49213 | 0.35 | FAIL |
| `cross_section_linf` | 2.31086 | 0.35 | FAIL |
| `mass_drift_delta` | 0.117248 | 0.04 | FAIL |
| `energy_change_delta` | 0.201833 | 0.15 | FAIL |
| `froude_delta` | 0.637727 | 0.1 | FAIL |
| `feature_location_delta` | 3.60555 | 3 | FAIL |
| `feature_strength_delta` | 1.30729 | 0.55 | FAIL |

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.65866 | 0.35 | FAIL |
| `slope_linf` | 0.641343 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0.0277778 | 0.1 | PASS |
| `probe_linf` | 0.829959 | 0.35 | FAIL |
| `cross_section_linf` | 2.13506 | 0.35 | FAIL |
| `mass_drift_delta` | 0.0936647 | 0.04 | FAIL |
| `energy_change_delta` | 0.131454 | 0.15 | PASS |
| `froude_delta` | 0.5628 | 0.1 | FAIL |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 1.76149 | 0.55 | FAIL |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.8506 | 0.35 | FAIL |
| `slope_linf` | 0.933834 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0.388889 | 0.1 | FAIL |
| `probe_linf` | 2.26143 | 0.35 | FAIL |
| `cross_section_linf` | 1.11512 | 0.35 | FAIL |
| `mass_drift_delta` | 0.164981 | 0.04 | FAIL |
| `energy_change_delta` | 0.589304 | 0.15 | FAIL |
| `froude_delta` | 2.07151 | 0.1 | FAIL |
| `feature_location_delta` | 3 | 3 | PASS |
| `feature_strength_delta` | 1.44396 | 0.55 | FAIL |

## Notes

- Corrected constriction GeoClaw reference now records west user-boundary inflow via bc2amr.f90 instead of the stale west extrap boundary in the Milestone 16 snapshot.
- No constriction lane is promoted: finite-volume Roe reduces mass and energy error versus HLL, but field, slope, probe, cross-section, mass-drift, Froude, and feature-strength checks still fail with feature forcing off.
- Next retune lever is geometry-aware throat reconstruction/source treatment rather than adding feature forcing, because the remaining errors are core field and conservation failures.

