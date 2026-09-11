# Native vector inflow and pressure convergence

September 8 continuation. Progress on the full active goal, not scene acceptance.
No production promotion or saved scene/system changes.

## Full-vector inflow

The previous virtual boundary imposed normal velocity only, discarding native
tangential velocity retained by emitted particles. A separate `vector-boundary`
candidate now follows centered transfer and consumes local XYZ inflow vectors.
Outgoing stage pressure remains unchanged; vectors are imposed only at inflow.

`build_south_fork_liquid_grid_boundary.py --with-tangent` produces
`grid_vector_boundary_profile.json` (schema v2, 516 float3 rows). Its first 260
rows are checked identical to the previous bed/stage/normal profile. The appended
vectors retain conservative discrete normal speed and native interpolated
momentum/depth tangent, with zero vertical source speed. This does not claim an
exact tangential momentum-flux solve. The captured mesh and hydraulic array
identities are verified by the builder.

Profile SHA256: `02DFEB80F5E21C17D8BBB2597B911C6F283B06EE1F121B04FDDBE731E44DC495`.
The original v1 profile is preserved. The loader checks schema, dimensions,
orthogonal axes, normal-vector agreement and finite data before installing it.

The 60s GPU run `liquid-vector-boundary-60s` verifies all 960 prescribed inflow
cells and all 2,880 velocity components. The actual stored values match exact
float32-to-half truncation toward zero. The maximum raw difference from the
double-precision profile is 0.118428 cm/s. The first audit incorrectly assumed
nearest rounding and is retained as `vector_boundary_audit_60s.json`; the
corrected `vector_boundary_audit_60s_v2.json` checks exact representable nearest
or toward-zero conversion, not a relaxed physical-speed tolerance. All 2,880
components match toward-zero conversion; 1,972 also match nearest conversion.
Tests still reject missing tangential flow.

Actual final boundary and velocity grids agree. Mean prescribed/actual local XY
velocity by wet ghost-cell count (not flux-weighted source means): west
(123.065,20.974)/(123.017,20.966), south (90.213,40.300)/(90.177,40.289), north
(101.454,-23.115)/(101.425,-23.108), all cm/s. East has no prescribed inflow cells.

## Physical results and convergence A/B

Both runs use actual captured blend 0.75 and identical vector-boundary/terrain
data. More iterations are a diagnostic, not a production performance setting.

| Measurement at 60s | 40 iterations | 160 iterations |
|---|---:|---:|
| Particle count (not fluid mass) | 80,508 | 79,846 |
| Mean local velocity XYZ, cm/s | 75.476,16.312,-3.101 | 78.817,14.585,-3.338 |
| Speed p95, cm/s | 206.821 | 208.523 |
| Exact bed probes | 80,434 | 79,767 |
| Missing/penetrating probes | 0/0 | 0/0 |
| Nonfinite velocities | 0 | 0 |
| Final divergence RMS, /s | 0.020224 | 0.000606 |
| Pressure-residual prediction RMS, /s | 0.020217 | 0.000000863 |
| Stage classification mismatches | 0 | 0 |

Both retain 4,142 native stage cells and max stage-pressure error 0.071871 cm²/s².
The 160-iteration result is limited primarily by half-precision velocity storage,
not the remaining pressure residual. No gameplay FPS claim: wall times of
89.020s and 97.427s include blocking readbacks and optical captures. The actual
chosen D3D12 adapter is the RTX 3060 Laptop GPU, not the AMD adapter named in the
generic automation-device metadata.

`liquid_compatible_projection.py --input-velocity StartVelocity` now permits a
reference solve of the same actual pre-projection transfer. The 40-iteration
snapshot converges in 72 CPU PCG iterations to relative residual 8.988e-8 and
divergence 2.044e-8/s. Its velocity differs from the actual GPU result by only
0.321 cm/s RMS. This is a reference, not a production CPU-solver substitution.

The actual SDF aperture one grid cell inside the physical faces gives:

| Face | 40-iteration inward flow, m³/s | 160-iteration inward flow, m³/s |
|---|---:|---:|
| West | 37.354 | 37.212 |
| East | -15.040 | -16.434 |
| South | 1.546 | 1.634 |
| North | -21.549 | -20.298 |

The lateral mismatch is **not fixed** by full-vector inflow or pressure
convergence. These estimates retain the original boundary bed/stage reference at
the inset and do not form a calibrated temporal mass budget. The storage and
native/3D exchange acceptance requirements remain open.

## Rendering evidence and next work

Both fresh oblique `optics_01.png` images were inspected. They remain glossy cyan
blobs with exposed rectangular domain edges, not whitewater. No visual or
single-surface scene-integration acceptance.

Compiled `28_GPUComputeScript_3_1_gpu.hlsl` in the vector-boundary capture proves
the active stage 17 `Grid3D_SetRTValues` writes smoothed SDF to red and constant
zero to green, blue and alpha. The optical material's foam input therefore has
no simulated foam source. Do not interpret tuning that multiplier as foam
simulation. Next rendering work should supply explicit advected aeration/foam
and coherent surface reconstruction, with physical flow acceptance still open.
Do not spend another iteration blindly raising pressure or velocity to fix the
remaining lateral mismatch.

Build 79333 passed in 16.15s. Engine suite 46280 has 10 clean passes, zero
warnings/failures, 21.24s; 38 focused numerical liquid tests pass. Saved contact
system, review map and uproject hashes are unchanged from the prior checkpoint.
