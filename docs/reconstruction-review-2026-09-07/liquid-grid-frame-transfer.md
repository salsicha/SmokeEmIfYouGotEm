# Rotated particle-to-grid transfer — September 8

South Fork remains incomplete. These are isolated transient candidates, not
production water or photographic acceptance. No saved scene, liquid asset, or
project descriptor changed; no commit was made.

## Confirmed defect and correction

The compiled stock NQ particle-to-grid shader averages particle velocities in
world/simulation space and writes them directly to the velocity grid. Its
particle-update consumer interprets that grid as grid-local and transforms it
through LocalToWorld. In this window the grid yaw is 158.4348 degrees: an extra
rotation substantially changes the direction of downstream momentum.

`CorrectRotatedParticleTransfer` in RaftSimEditorLiquidTerrainContact.cpp copies
the rasterization function into the transient system. Both stock gather branches
now project the averaged world velocity onto the normalized UnitToWorld row axes
before writing the grid. Normalization prevents the 2100/2100/800cm grid extents
from scaling velocity. This adds no force or speed clamp. The currently selected
simple-weight branch is corrected; rotated tent-kernel weighting is not claimed.
Owned graph checks, expected-node-count guards, compile checks and capture asset
identity assertions prevent silently testing an unchanged baseline.

The separate complete-gather variant removes the consumer's initial-density
neighbor truncation. Important distinction: NeighborQuery storage itself is not
a fixed-size particle bucket, but its stock rasterizer DOES cap the number of
neighbors consumed at `MaxParticlesPerCell`, bound to OVERRIDE.ParticlesPerCell.
Removing that cap includes all valid allocated neighbors, but it does not solve
source crowding or calibrate particle volume.

## Actual GPU evidence

All following successful captures advanced 720 steps at 1/60s, with the same
saved source/terrain/contact baseline and fixed overhead camera. Particle
readbacks are blocking correctness measurements, **not performance timings**.

|12-second result|Uncorrected settings audit|Grid-frame correction|Correction + complete gather|
|---|---:|---:|---:|
|Live particles|54273|50366|59250|
|Median downstream coordinate cm|-985.7|-574.9|-646.2|
|Centre-quarter particles|956|12484|7983|
|Maximum occupied-bin count*|3811|840|5222|
|Maximum proposed step cm|4308.92|60.08|71.30|
|Particles >32.8125cm below exact bed|430|21|14|
|Worst exact-bed penetration cm|554.64|538.88|253.73|
|Outside domain|52|35|8|

*Analysis bins are floor(local position / 32.8125cm), not a GPU NQ occupancy
readback. Independent GPU runs are not asserted deterministic.

The corrected water spreads into the window rather than remaining only an inlet
strip. Both opacity-one diagnostic images were inspected. They remain pale,
patchy, smooth and incomplete, with invalid-looking presentation near edges.
The full gather has more crowding and less centre coverage than the frame-only
run; do not describe it as an across-the-board improvement. Neither candidate
meets exact-bed, visual, mass-exchange, raft-coupling or performance acceptance.

Artifacts and owned process outcomes:

- Settings audit26014 exit0: `liquid-terrain-fluid-settings-audit` and
  CaptureLiquidTerrainFluidSettings.log. Runtime dt1/60 and grid transforms
  confirmed. Pressure iterations40; compiled PIC/FLIP ratio0.75. The ratio was
  not retained in captured_system_state, so this is a compiled-value observation.
- First frame attempt9241 exit0 failed its identity assertion because the guard
  expected one custom gather node, but the stock graph has two branches.
  `liquid-terrain-grid-frame-review` is **invalid physical evidence**.
- Build59403 exit0 after correcting the two-branch guard; capture56650 exit0:
  `liquid-terrain-grid-frame-readback`, CaptureLiquidTerrainGridFrameReadback.log.
- Build8072 exit0; capture37374 exit0:
  `liquid-terrain-complete-gather-readback`, CaptureLiquidTerrainCompleteGather.log.
  `active_compiled_shaders/28_GPUComputeScript_3_1_gpu.hlsl` lines2995 onward
  contains the actual compiled basis projection and no neighbor-count clamp.
- Build70857 exit0; regression23502 exit0:
  `engine-liquid-grid-frame/index.json`: eight clean passes, zero warnings or
  failures, 9.47s. New LiquidFixtureTerrainGridFrameTransfer constructs both
  transient variants, checks their compiled GPU program, unchanged source
  vectors and saved-package cleanliness. It is not a physical acceptance test.

Saved-byte hashes after the runs:

- Contact asset: eefde2513997e3cfa1206acc1bc053b6a3729280cfa7c5eae9df6230dc714122
- Registered map: 81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7
- Project: 01b95fffdec2649864c397a9a7c786d083371e469efbace3505e0e0ae2ac3b44

## Next implementation

Retain the confirmed basis correction. Replace empty-tank startup with the
registered hydraulic field's wet volume and velocities. Implement/verify actual
normal inflow and outgoing exchange, not just a particle emission rate. Correct
the inherited face-name mapping. Correction: the preceding interpretation
mistook custom-HLSL argument names for exposed controls. Full module binding
tracing establishes Left/Right=X, Back/Front=Y and Down/Up=Z; the original
factory's four horizontal open controls were correct. Restore Down=false and
Back=true in the later transient variants and source factory. Keep all
changes isolated until the unchanged terrain, water-motion and performance
gates pass. The remainder of the all-scene queue is still pending.
