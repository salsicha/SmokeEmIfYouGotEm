# Solid-cell motion experiment — rejected as a fix

September 8 continuation; all original acceptance gates remain open.
The previous contact turn was progress. This turn implements and measures one
specific response variant, not a finished river or a production change.

## Cause inspected and implementation

`liquid-particle-update-inputs.json` exports the installed engine's
Grid3D_FLIP_ParticleUpdate graph. Compiled shader inspection confirms its solid
selector holds position and sets velocity to zero when rounded boundary mask=1.
The outer air/out-of-domain selector uses inertial motion. Both versions of the
copied function graph have the same solid selector.

New runtime-only `RaftSim.LiquidTerrainMomentumReview` copies the saved contact
system into the transient package, owns a copy of the particle update function,
and rewires only the solid selector's true position/velocity to the existing
inertial-motion outputs. The non-solid FLIP/PIC branch and pressure boundaries
remain unchanged. The existing global-distance-field contact then attempts to
project the moved particle and remove inward velocity. It does not save assets.

The capture option `-RaftSimLiquidTerrainMomentum` requires contact mode and
asserts that the transient asset was installed. It was tested with a fixed
overhead camera, exact-triangle bed probes and actual GPU particle readback.

## Measured result

Valid run: `liquid-terrain-momentum-readback`, session37669 exit0, complete=true.

|Time s|Live particles|Below bed >1 mm|Below bed >one cell|Worst penetration cm|Outside domain|
|---|---:|---:|---:|---:|---:|
|0.1|440|0|0|0|0|
|0.5|2554|99|60|104.17|1|
|1|5128|186|141|272.92|5|
|4|20022|278|241|294.54|6|
|8|39773|331|278|276.26|3|
|12|59222|399|356|307.03|8|

At12s the original Custom-radius contact run had63075 live particles,
2466 small penetrations,133 penetrations deeper than a cell and59.03cm worst
penetration. The motion variant reduces shallow penetrations but makes the deep
failure much worse. It is **rejected as a contact fix**.

At12s54651 particles remain in the upstream quarter. Mean local forward velocity
is12.86cm/s upstream, -159.97cm/s in the centre and-85.05cm/s downstream. Thus this
does not restore the intended flow-through either. The stable opacity1 screenshot
was inspected: still predominantly a narrow inlet strip, not a filled rapid.
Do not infer mass conservation from live particle count or gameplay performance
from this blocking readback harness. The eight outside particles are measured
after contact; escape retirement remains enabled but does not guarantee zero
outside particles at every stage boundary.

## Retained harness failure and verification

- Build51671 and graph inspection59603 succeeded.
- First candidate build84133 succeeded. Run77636 installed and compiled the
  candidate but stopped at frame6 because the readback filter requires
  LiquidBodyReview in the path. `liquid-terrain-momentum-runtime` is an incomplete
  run, not useful contact evidence.
- Added the existing review-category name to the transient asset; build4787 and
  valid capture37669 succeeded. No physics settings changed in that correction.
- Regression18326 exits0: `engine-liquid-terrain-momentum/index.json` has7 clean
  passes,0 failures/warnings,7.56s. These cover saved liquid fixtures/configuration,
  not acceptance of the rejected transient physics variant. Scoped diff-check
  passes. No owned process remains live.
- Saved contact SHA remains
  `eefde2513997e3cfa1206acc1bc053b6a3729280cfa7c5eae9df6230dc714122`.
  No package or level was saved, promoted or committed by this experiment.

## Next action

Implement contact against the explicitly tagged terrain mesh distance field,
not the scene-wide global field. The installed rigid-mesh DI exposes GPU-only
GetClosestPointMeshDistanceFieldAccurate with world position, dt, time fraction,
max distance; outputs distance, closest position/normal/velocity, normal validity
and encoded-distance limit. Validate its actual separation against the existing
triangle probes; distance-field settings alone are not proof. Preserve tangential
momentum only together with a successful contact projection. Retain pressure,
inlet identity and escape rules. Captured wet-volume initialization and measured
boundary momentum/mass exchange remain necessary for the full flow-through test.
