# Milestone 18 Constriction Probe/Cross-Section Diagnostic

Schema: `raftsim.milestone18.constriction_probe_cross_section.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/scenario/constriction_seed_16`
Velocity depth floor: `0.15` m

## Summary

- Max probe Linf: `2.20322`
- Max cross-section Linf: `1.69192`

## Worst Raw Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `midstream_center` | `hv` | 3 | n/a | `constriction_throat` | `6,12` | 0.775086 | -1.42814 | -2.20322 | 2.20322 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 8.81289 |
| `probe` | `upstream_center` | `hv` | 6 | n/a | `upstream_approach` | `6,6` | -0.940908 | 1.08126 | 2.02217 | 2.02217 | `1.83972/0.97954/-0.511441/0.260112` | `1.8741/1.48474/0.576948/0.371498` | 0.25 | 8.08868 |
| `probe` | `downstream_center` | `hu` | 6 | n/a | `recovery` | `6,18` | 3.72586 | 1.76616 | -1.9597 | 1.9597 | `1.2504/2.97973/0.51569/0.863428` | `1.03763/1.70212/-0.20141/0.537222` | 0.25 | 7.8388 |
| `probe` | `midstream_center` | `v` | 3 | n/a | `constriction_throat` | `6,12` | 0.549413 | -1.14251 | -1.69192 | 1.69192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `v` | 3 | 0.5 | `constriction_throat` | `6,12` | 0.549413 | -1.14251 | -1.69192 | 1.69192 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.14251/0.885896` | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `froude` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.42737 | 0.894562 | -1.53281 | 1.53281 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 6.13123 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `recovery` | `6,18` | 2.97973 | 1.70212 | -1.27761 | 1.27761 | `1.2504/2.97973/0.51569/0.863428` | `1.03763/1.70212/-0.20141/0.537222` | 0.25 | 5.11045 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -2.5 | `constriction_throat` | `3,12` | 1.79052 | 2.88417 | 1.09365 | 1.09365 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 4.37459 |
| `probe` | `upstream_center` | `v` | 6 | n/a | `upstream_approach` | `6,6` | -0.511441 | 0.576948 | 1.08839 | 1.08839 | `1.83972/0.97954/-0.511441/0.260112` | `1.8741/1.48474/0.576948/0.371498` | 0.25 | 4.35356 |
| `cross_section` | `mid_cross_section` | `h` | 3 | -2.5 | `constriction_throat` | `3,12` | 0.198238 | 1.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 4.20705 |
| `cross_section` | `mid_cross_section` | `eta` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.19824 | 3.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.22251/0.894562` | 0.25 | 4.20705 |
| `probe` | `upstream_center` | `hu` | 6 | n/a | `upstream_approach` | `6,6` | 1.80208 | 2.78256 | 0.980478 | 0.980478 | `1.83972/0.97954/-0.511441/0.260112` | `1.8741/1.48474/0.576948/0.371498` | 0.25 | 3.92191 |

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
