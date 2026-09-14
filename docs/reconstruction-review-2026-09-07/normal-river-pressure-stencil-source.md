# Actual wider boundary-source stencil — September 14, 2026

SOURCE CAPTURE VERIFIED, boundary closure still OPEN: build21221 TERMINAL exit0,118.14s. First native92023 passed the
new test only; two requested names were incorrect, not silently counted as
passes. Corrected native96665 TERMINAL exit0: all3tests PASS0.400519s:
PressureStencilSource, DetailSampleGrid, LiveTotalDepthSourceGPU.
Five independent source-audit tests PASS0.75s. Actual normal-game source
capture26326 TERMINAL exit0; no boundary operator or playable solver promotion.

Fresh actual source audit PASS for revisions2/3 at native times0.0666666701
and0.1333333403s, origin[-5450,3566]. Both retain1572 halo samples; all512
original exterior entries agree exactly and the full sampled bed is unchanged.
Input SHA256:129a7a9de42d2f5559f8b0e777cfe38d36b4e7f6c43aa933d0292888ccb4d7de.
Report: `tmp/south-fork-pressure-stencil-source-audit-v1-20260914.json`.
Actual GPU temporal audit PASS: maximum normalized error5.957916e-8, exact bed,
zero time/state/bed/face errors. This checks uploads/interpolation, not evolution.

Completed recording `RaftSim_20260914-045531.mp4`:45 source frames over6.436s,
all193 encoded frames decoded. Inspected decoded1s image still has broad smeared
foam and sheetlike crests; visual acceptance remains FAIL. Encoder30FPS is not
gameplay30FPS. No CSV or performance improvement is claimed for this capture.
Final source/frame-budget regression suite:15PASS1.09s. Desktop target verified
at30FPS/p9533.333ms, physics120Hz unchanged; no frame cap imposed.

## What data was missing

The previous turn exposed a non-refining50% endpoint gradient error in the
constant-null scalar candidate. Existing observations retain only one fine-cell
ghost ring (without corners) and independent face-normal velocity/time-rate.
They do not supply general scalar derivatives or pressure boundary conditions.
Recovering a wider spatial stencil from those records by clamping or padding
would invent source data. The existing frozen histories remain intact.

## Opt-in live acquisition, same authoritative inputs

`-RaftSimCapturePressureStencil` expands ONLY the diagnostic moving-window
source query lattice from67x67 to69x69 actual1m nodes. The fixed world-aligned
coarse origin is unchanged; the halo grows from1m to2m. This adds272 hydraulic
queries per refresh when explicitly enabled. Ordinary gameplay remains67x67;
the legacy65x65 mean/entrainment/timestep inputs keep their existing nodes.

The new interpolation range covers three half-metre rings at indices-3..130,
including corners, for both half-cell phases. Each immutable packet optionally
retains1572 h/hu/hv/zero-foam and bed samples,31,440 represented CPU bytes.
There are1060 additional samples beyond the existing512 exterior centers.
Packing is row-major over the134x134 bounding box, excluding128x128 interior.
All samples retain the same native time, source revision and field axes.

The existing state/bed/reference/exterior/face arrays and GPU upload layout are
unchanged. No evolving state reset, source masking, pressure assignment, new
foam source or visual displacement is introduced. This is point interpolation
of actual hydraulic data, not surveyed subgrid terrain or a conservative remap.

The temporal and nonlinear-owner audit exports include the optional explicit
width marker and full stencil arrays. Older captures lack these fields and the
new independent reader rejects them; they are NOT retroactively extended.

## Verification

Native test checks all four half-cell phases with tiny positive depths and
rounded surface==bed. Existing67584 interior/first-ring cells across those
phases remain exact.6288 wider-ring samples are checked against independent
four-corner interpolation (1e-6 float tolerance, exact bed); all outer cells
appear once and partial halos are rejected. Total73872 source/ghost comparisons.
The existing fixed-world grid and actual GPU source/temporal upload tests pass.

`physics/scripts/audit_pressure_stencil_source.py` reconstructs the full sampled
rectangle independently, requires all1572 ring samples and exact agreement
with every original exterior entry, checks conserved-state validity, fixed bed,
registration and increasing native time/revision. It explicitly reports pressure
boundary, gameplay and performance qualification as FALSE.

Next inspect the actual temporal pair and derive a finite-window scalar closure
using retained exterior data and the current evolving interior. Pressure work,
wet/dry consistency and complete histories still require qualification; the
boundary defect itself is NOT fixed by capturing its missing input support.
All original full-project terrain/waves/froth/contact/30FPS/crew/later-river/
release/final-commit requirements remain open.
