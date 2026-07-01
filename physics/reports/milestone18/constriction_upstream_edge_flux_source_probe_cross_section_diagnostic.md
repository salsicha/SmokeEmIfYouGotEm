# Milestone 18 Constriction Probe/Cross-Section Diagnostic

Schema: `raftsim.milestone18.constriction_probe_cross_section.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_edge_flux_source/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_edge_flux_source/finite_volume_roe/scenario/constriction_seed_16`
Velocity depth floor: `0.15` m

## Summary

- Max probe Linf: `2.20322`
- Max cross-section Linf: `1.69192`

## Worst Raw Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `midstream_center` | `hv` | 3 | n/a | `constriction_throat` | `6,12` | 0.775086 | -1.42814 | -2.20322 | 2.20322 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 8.81289 |
| `probe` | `upstream_center` | `hv` | 6 | n/a | `upstream_approach` | `6,6` | -0.940908 | 1.0814 | 2.02231 | 2.02231 | `1.83972/0.97954/-0.511441/0.260112` | `1.87426/1.48481/0.576975/0.371501` | 0.25 | 8.08924 |
| `probe` | `downstream_center` | `hu` | 6 | n/a | `recovery` | `6,18` | 3.72586 | 1.76373 | -1.96213 | 1.96213 | `1.2504/2.97973/0.51569/0.863428` | `1.03842/1.69848/-0.611179/0.56556` | 0.25 | 7.84851 |
| `probe` | `midstream_center` | `v` | 3 | n/a | `constriction_throat` | `6,12` | 0.549413 | -1.14251 | -1.69192 | 1.69192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `v` | 3 | 0.5 | `constriction_throat` | `6,12` | 0.549413 | -1.14251 | -1.69192 | 1.69192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `froude` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.42737 | 0.894562 | -1.53281 | 1.53281 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 6.13123 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `recovery` | `6,18` | 2.97973 | 1.69848 | -1.28125 | 1.28125 | `1.2504/2.97973/0.51569/0.863428` | `1.03842/1.69848/-0.611179/0.56556` | 0.25 | 5.12501 |
| `probe` | `downstream_center` | `hv` | 6 | n/a | `recovery` | `6,18` | 0.644819 | -0.63466 | -1.27948 | 1.27948 | `1.2504/2.97973/0.51569/0.863428` | `1.03842/1.69848/-0.611179/0.56556` | 0.25 | 5.11792 |
| `probe` | `downstream_center` | `v` | 6 | n/a | `recovery` | `6,18` | 0.51569 | -0.611179 | -1.12687 | 1.12687 | `1.2504/2.97973/0.51569/0.863428` | `1.03842/1.69848/-0.611179/0.56556` | 0.25 | 4.50747 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -2.5 | `constriction_throat` | `3,12` | 1.79052 | 2.88417 | 1.09365 | 1.09365 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 4.37459 |
| `probe` | `upstream_center` | `v` | 6 | n/a | `upstream_approach` | `6,6` | -0.511441 | 0.576975 | 1.08842 | 1.08842 | `1.83972/0.97954/-0.511441/0.260112` | `1.87426/1.48481/0.576975/0.371501` | 0.25 | 4.35367 |
| `cross_section` | `mid_cross_section` | `h` | 3 | -2.5 | `constriction_throat` | `3,12` | 0.198238 | 1.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 4.20705 |

## Blocked Reasons

- C++ constriction point-probe raw samples still exceed the GeoClaw/C++ threshold.
- C++ constriction cross-section raw samples still exceed the GeoClaw/C++ threshold.
- Cross-stream velocity or momentum has the wrong magnitude/sign at sampled constriction locations.
- Froude mismatch is still present in the sampled constriction section.

## Next Levers

- Retune from `probe` `midstream_center` field `hv` at t=3s because it is 8.81289x threshold.
- Correct cross-stream circulation sign and magnitude at the sampled constriction centerline before changing more depth volume.
- Preserve the Froude envelope while changing lateral circulation; the previous shape pass regressed Froude just over threshold.
- Use the recorded cross-section distance and cell coordinates to tune section shape, not only whole-field Linf cells.
