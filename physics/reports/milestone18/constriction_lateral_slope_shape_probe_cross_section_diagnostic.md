# Milestone 18 Constriction Probe/Cross-Section Diagnostic

Schema: `raftsim.milestone18.constriction_probe_cross_section.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/scenario/constriction_seed_16`
Velocity depth floor: `0.15` m

## Summary

- Max probe Linf: `2.25322`
- Max cross-section Linf: `1.73192`

## Worst Raw Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `midstream_center` | `hv` | 3 | n/a | `constriction_throat` | `6,12` | 0.775086 | -1.47814 | -2.25322 | 2.25322 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.18251/0.890166` | 0.25 | 9.01289 |
| `probe` | `upstream_center` | `hv` | 6 | n/a | `upstream_approach` | `6,6` | -0.940908 | 1.06993 | 2.01084 | 2.01084 | `1.83972/0.97954/-0.511441/0.260112` | `1.67972/1.07991/0.636971/0.308862` | 0.25 | 8.04336 |
| `probe` | `downstream_center` | `hu` | 6 | n/a | `recovery` | `6,18` | 3.72586 | 1.76204 | -1.96382 | 1.96382 | `1.2504/2.97973/0.51569/0.863428` | `1.03777/1.69791/-0.611401/0.565592` | 0.25 | 7.85526 |
| `probe` | `midstream_center` | `v` | 3 | n/a | `constriction_throat` | `6,12` | 0.549413 | -1.18251 | -1.73192 | 1.73192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.18251/0.890166` | 0.25 | 6.92768 |
| `cross_section` | `mid_cross_section` | `v` | 3 | 0.5 | `constriction_throat` | `6,12` | 0.549413 | -1.18251 | -1.73192 | 1.73192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.18251/0.890166` | 0.25 | 6.92768 |
| `cross_section` | `mid_cross_section` | `froude` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.42737 | 0.890166 | -1.5372 | 1.5372 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.18251/0.890166` | 0.25 | 6.14881 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `recovery` | `6,18` | 2.97973 | 1.69791 | -1.28182 | 1.28182 | `1.2504/2.97973/0.51569/0.863428` | `1.03777/1.69791/-0.611401/0.565592` | 0.25 | 5.12729 |
| `probe` | `downstream_center` | `hv` | 6 | n/a | `recovery` | `6,18` | 0.644819 | -0.634496 | -1.27932 | 1.27932 | `1.2504/2.97973/0.51569/0.863428` | `1.03777/1.69791/-0.611401/0.565592` | 0.25 | 5.11726 |
| `probe` | `upstream_center` | `v` | 6 | n/a | `upstream_approach` | `6,6` | -0.511441 | 0.636971 | 1.14841 | 1.14841 | `1.83972/0.97954/-0.511441/0.260112` | `1.67972/1.07991/0.636971/0.308862` | 0.25 | 4.59365 |
| `probe` | `downstream_center` | `v` | 6 | n/a | `recovery` | `6,18` | 0.51569 | -0.611401 | -1.12709 | 1.12709 | `1.2504/2.97973/0.51569/0.863428` | `1.03777/1.69791/-0.611401/0.565592` | 0.25 | 4.50836 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -2.5 | `constriction_throat` | `3,12` | 1.79052 | 2.88417 | 1.09365 | 1.09365 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.18251/0.890166` | 0.25 | 4.37459 |
| `cross_section` | `mid_cross_section` | `h` | 3 | -2.5 | `constriction_throat` | `3,12` | 0.198238 | 1.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.18251/0.890166` | 0.25 | 4.20705 |

## Blocked Reasons

- C++ constriction point-probe raw samples still exceed the GeoClaw/C++ threshold.
- C++ constriction cross-section raw samples still exceed the GeoClaw/C++ threshold.
- Cross-stream velocity or momentum has the wrong magnitude/sign at sampled constriction locations.
- Froude mismatch is still present in the sampled constriction section.

## Next Levers

- Retune from `probe` `midstream_center` field `hv` at t=3s because it is 9.01289x threshold.
- Correct cross-stream circulation sign and magnitude at the sampled constriction centerline before changing more depth volume.
- Preserve the Froude envelope while changing lateral circulation; the previous shape pass regressed Froude just over threshold.
- Use the recorded cross-section distance and cell coordinates to tune section shape, not only whole-field Linf cells.
