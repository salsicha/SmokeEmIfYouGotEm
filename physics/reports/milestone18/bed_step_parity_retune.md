# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `bed_step`
Gate scenario: `bed_step`
Actual scenario: `bed_step_seed_16`
Reference manifest: `outputs/m16g/c_step/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume` | `finite_volume_bed_step_face_source_bed0p75` | BLOCKED | field_linf, slope_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_baseline_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, mass_drift_delta, energy_change_delta | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.353044 | 0.35 | FAIL |
| `slope_linf` | 0.103296 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0.33231 | 0.35 | PASS |
| `cross_section_linf` | 0.119138 | 0.35 | PASS |
| `mass_drift_delta` | 8.79344e-05 | 0.04 | PASS |
| `energy_change_delta` | 0.0358039 | 0.15 | PASS |
| `froude_delta` | 0.0481703 | 0.1 | PASS |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 0.191853 | 0.55 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.610705 | 0.35 | FAIL |
| `slope_linf` | 0.104595 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0.392414 | 0.35 | FAIL |
| `cross_section_linf` | 0.269168 | 0.35 | PASS |
| `mass_drift_delta` | 0.0948885 | 0.04 | FAIL |
| `energy_change_delta` | 0.16485 | 0.15 | FAIL |
| `froude_delta` | 0.00820177 | 0.1 | PASS |
| `feature_location_delta` | 2 | 3 | PASS |
| `feature_strength_delta` | 0.0141865 | 0.55 | PASS |

## Notes

- Finite-volume abrupt bed-step face-source correction is scoped to fixture_kind=bed_step so boulder, drop, and cascading raft scenarios keep their existing acceptance lanes.
- Finite-volume now passes bed-step probe, cross-section, wet-mask, mass, energy, Froude, and feature checks, but remains blocked on field_linf and slope_linf.
- Scalar source-scale sweeps could not pass field_linf and slope_linf together; the next fix is an augmented topography Riemann/source-distribution treatment rather than threshold widening or feature forcing.

