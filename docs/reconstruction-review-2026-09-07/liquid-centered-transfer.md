# Centered liquid momentum transfer — isolated candidate

September 8 continuation. Full scene/release acceptance remains open. These
experiments never save the transient system or promote it into a shipping scene.

## Finding and implementation

Actual initial-state mean local XY velocity is 138.025, -26.959 cm/s. In the
previous outlet-stage candidate it falls to 35.585, 6.453 cm/s after one second.

The compiled P2G shader gathers bins `Index-1` and `Index` with equal weights.
Actual NQ insertion is `floor(Unit*NumCells)`; velocity texels are centered at
`(Index+.5)/NumCells`. On uniform quadrature the old gather samples half a cell
off center in every axis. Its optional geometric weights also use world-axis
displacements divided by a single scalar cell size, unsuitable for this rotated,
anisotropic grid.

The new `centered-transfer` variant gathers all 27 bins intersecting the centered
tent support. It reads actual particle positions and projects displacements onto
the normalized UnitToWorld rows, dividing by each axis's actual cell spacing.
P2G velocity remains correctly rotated into the grid basis. All allocated valid
neighbors are retained. NQ insertion, source volume, contact geometry, pressure,
default blend, and renderer are not changed by this correction.

Independent numerical regressions reproduce the old bias and verify centered
support, uniform/affine velocity preservation on uniform quadrature, and rotated
anisotropic equivalence. Engine regressions verify the actual compiled shader.

## Retained A/B results

All mean velocities below are particle means, **not** mass-weighted discharge.

| Run | Actual FLIP blend | Mean downstream velocity at 1s (cm/s) | At 12s (cm/s) | Particle speed p95 at 12s (cm/s) |
|---|---:|---:|---:|---:|
| Previous outlet-stage V5 | 0.75 | 35.585 | 39.599 | 162.88 |
| Old transfer, pure FLIP | 1 | 106.975 | 170.695 | 4395.36 |
| Centered transfer | 0.75 | 82.710 | 89.552 | 216.50 |

`liquid-transfer-flip-one` is **rejected**: it preserves early momentum but becomes
unstable, reaching approximately 44 m/s p95 by 12s. Raising the blend is not the
fix. The saved default remains 0.75.

`liquid-centered-transfer` accidentally ran with actual blend **0**, not 0.75:
PowerShell split the unquoted decimal argument into `=0 .75`. Its capture records
0 correctly. Retain it as a pure-PIC experiment; do not cite it as a matched A/B.
Quote decimal-valued native command arguments. The corrected run is
`liquid-centered-transfer-075`; actual captured blend is 0.75 at every sample.

The 12s matched run has zero detected penetration. Its measured divergence is
0.021024/s and agrees with the independently predicted pressure residual within
0.000595/s. The 4,142 stage cells match classification; pressure-support fixed
velocity error is 0.015625 cm/s.

## Longer run and visual review

`liquid-centered-transfer-075-60s` completes at 60 simulated seconds. Actual final
mean local velocity is (75.391, 14.976, -3.163) cm/s and speed p95 is 205.447 cm/s.
There are 80,276 particles, 80,188 exact bed probes, zero missing bed probes,
zero detected penetration over 1 mm, and zero nonfinite velocities. Eighty-eight
particles are outside the physical box at the final sample, pending retirement.
Particle count is not calibrated fluid storage.

Final divergence is 0.019786/s; residual prediction differs by 0.000585/s. All
4,142 stage cells still match; stage pressure maximum error is 0.071871 cm²/s².
See retained `projection_60s.json` and actual GPU readbacks.

The SDF wet-aperture estimate one grid cell inside the physical faces remains
inconsistent with the native exchange: west +37.418, east -15.577, south +1.736,
north -21.274 m³/s (positive inward). This is not a calibrated mass budget;
inset planes use original boundary bed/stage references. See
`sdf_exchange_60s_inset.json` and [aperture limitations](liquid-surface-aperture.md).

The actual oblique `optics_01.png` was inspected. It is a glossy cyan, blobby
liquid patch with rectangular exposed edges against diagnostic terrain. It has
depth but is **not realistic whitewater**. There is no accepted foam/breakup,
full-scene single-surface handoff, motion clip, or gameplay FPS result. Diagnostic
wall times (43.972s for the 12s matched capture; 87.770s for the 60s optical capture)
include blocking readbacks/rendering and are not frame-rate measurements.

## Validation and next work

Build 6960 succeeded in 18.76s. `engine-liquid-centered-transfer/index.json` has
10 clean passes, zero warnings/failures, 20.94s. The expanded transfer test covers
the old variants plus centered transfer with default and explicit blend 1.
All 34 focused Python liquid tests pass. Saved system, review map, and uproject
hashes are unchanged from the prior checkpoint.

Next: establish actual temporal exchange/storage and boundary momentum
consistency. The virtual inflow currently supplies only normal velocity, although
source particles retain native tangential velocity. Source flux-weighted local XY
velocities are west (173.457,28.656), south (171.445,97.918), and north
(116.558,-63.753) cm/s. This mismatch needs investigation; restoring tangential
momentum must not be claimed to fix northward exit without an actual test.
Then explicit advected aeration/foam, coherent surface reconstruction, scene
integration and normal-gameplay performance/visual acceptance remain required.
