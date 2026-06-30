# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **PARTIAL_PROMOTION**

Scenario family: `wet_dry_shoreline`
Gate scenario: `wet_dry_shoreline`
Actual scenario: `wet_dry_shoreline_seed_16`
Reference manifest: `outputs/m16g/c_wetdry/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume` | `finite_volume_hll_uniform_retune_defaults` | BLOCKED | field_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta, feature_location_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_wet_neighbor_pressure_gradient` | PROMOTED | none | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.511772 | 0.35 | FAIL |
| `slope_linf` | 0.0582183 | 0.08 | PASS |
| `wet_mismatch_fraction` | 0.333333 | 0.1 | FAIL |
| `probe_linf` | 1 | 0.35 | FAIL |
| `cross_section_linf` | 0.534672 | 0.35 | FAIL |
| `mass_drift_delta` | 1.92752e-05 | 0.04 | PASS |
| `energy_change_delta` | 0.0178962 | 0.15 | PASS |
| `froude_delta` | 0.362275 | 0.1 | FAIL |
| `feature_location_delta` | 3.60555 | 3 | FAIL |
| `feature_strength_delta` | 0.11366 | 0.55 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.0494399 | 0.35 | PASS |
| `slope_linf` | 2.16744e-08 | 0.08 | PASS |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0 | 0.35 | PASS |
| `cross_section_linf` | 0.0494399 | 0.35 | PASS |
| `mass_drift_delta` | 0 | 0.04 | PASS |
| `energy_change_delta` | 0.000858105 | 0.15 | PASS |
| `froude_delta` | 0.0270348 | 0.1 | PASS |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 4.74128e-09 | 0.55 | PASS |

## Notes

- Reduced mode now masks dry neighbors out of pressure-gradient sampling, preserving shoreline wet masks without feature forcing.
- Finite-volume mode remains blocked for this family and still needs hydrostatic wet/dry reconstruction before promotion.

