# Milestone 18 Constriction Probe/Cross-Section Diagnostic

Schema: `raftsim.milestone18.constriction_probe_cross_section.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/scenario/constriction_seed_16`
Velocity depth floor: `0.15` m

## Summary

- Max probe Linf: `2.15656`
- Max cross-section Linf: `1.6623`

## Worst Raw Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `midstream_center` | `hv` | 3 | n/a | `constriction_throat` | `6,12` | 0.775086 | -1.38147 | -2.15656 | 2.15656 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.10518/0.882025` | 0.25 | 8.62622 |
| `probe` | `upstream_center` | `hv` | 6 | n/a | `upstream_approach` | `6,6` | -0.940908 | 1.08125 | 2.02216 | 2.02216 | `1.83972/0.97954/-0.511441/0.260112` | `1.87409/1.48473/0.576946/0.371497` | 0.25 | 8.08863 |
| `probe` | `downstream_center` | `hu` | 6 | n/a | `recovery` | `6,18` | 3.72586 | 1.7667 | -1.95916 | 1.95916 | `1.2504/2.97973/0.51569/0.863428` | `1.03729/1.70319/0.0108016/0.533932` | 0.25 | 7.83663 |
| `cross_section` | `mid_cross_section` | `v` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.87272 | 1.21041 | -1.6623 | 1.6623 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.21041/0.893219` | 0.25 | 6.64921 |
| `probe` | `midstream_center` | `v` | 3 | n/a | `constriction_throat` | `6,12` | 0.549413 | -1.10518 | -1.65459 | 1.65459 | `1.41075/2.90826/0.549413/0.795586` | `1.25/2.88417/-1.10518/0.882025` | 0.25 | 6.61835 |
| `cross_section` | `mid_cross_section` | `froude` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.42737 | 0.893219 | -1.53415 | 1.53415 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.21041/0.893219` | 0.25 | 6.13659 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `recovery` | `6,18` | 2.97973 | 1.70319 | -1.27654 | 1.27654 | `1.2504/2.97973/0.51569/0.863428` | `1.03729/1.70319/0.0108016/0.533932` | 0.25 | 5.10617 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -2.5 | `constriction_throat` | `3,12` | 1.79052 | 2.88417 | 1.09365 | 1.09365 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.21041/0.893219` | 0.25 | 4.37459 |
| `probe` | `upstream_center` | `v` | 6 | n/a | `upstream_approach` | `6,6` | -0.511441 | 0.576946 | 1.08839 | 1.08839 | `1.83972/0.97954/-0.511441/0.260112` | `1.87409/1.48473/0.576946/0.371497` | 0.25 | 4.35355 |
| `cross_section` | `mid_cross_section` | `h` | 3 | -2.5 | `constriction_throat` | `3,12` | 0.198238 | 1.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.21041/0.893219` | 0.25 | 4.20705 |
| `cross_section` | `mid_cross_section` | `eta` | 3 | -2.5 | `constriction_throat` | `3,12` | 2.19824 | 3.25 | 1.05176 | 1.05176 | `0.198238/1.79052/2.87272/2.42737` | `1.25/2.88417/1.21041/0.893219` | 0.25 | 4.20705 |
| `probe` | `upstream_center` | `hu` | 6 | n/a | `upstream_approach` | `6,6` | 1.80208 | 2.78252 | 0.980444 | 0.980444 | `1.83972/0.97954/-0.511441/0.260112` | `1.87409/1.48473/0.576946/0.371497` | 0.25 | 3.92178 |

## Blocked Reasons

- C++ constriction point-probe raw samples still exceed the GeoClaw/C++ threshold.
- C++ constriction cross-section raw samples still exceed the GeoClaw/C++ threshold.
- Cross-stream velocity or momentum has the wrong magnitude/sign at sampled constriction locations.
- Froude mismatch is still present in the sampled constriction section.

## Next Levers

- Retune from `probe` `midstream_center` field `hv` at t=3s because it is 8.62622x threshold.
- Correct cross-stream circulation sign and magnitude at the sampled constriction centerline before changing more depth volume.
- Preserve the Froude envelope while changing lateral circulation; the previous shape pass regressed Froude just over threshold.
- Use the recorded cross-section distance and cell coordinates to tune section shape, not only whole-field Linf cells.
