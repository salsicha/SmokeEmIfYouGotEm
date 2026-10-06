# Terrain contact candidate — incomplete

September 8 continuation. No production promotion, scene acceptance or commit.
This is the same 21 m captured-XY candidate with unverified rapid identity and
inferred submerged bed, not a surveyed reconstruction of all Troublemaker.

## Implemented

`RaftSim.CreateSouthForkLiquidTerrainContact` copies the terrain review into
`NS_SouthForkLiquidTerrainContactReview`. It disables the solid-cell deletion
in the actual fluid simulation stage and appends the stock Niagara Collision
module after the FLIP particle update. Pressure terrain boundaries, conservative
source tables and escape retirement remain. Contact uses global distance fields,
custom 2 cm radius, interpenetration correction, no killing, rest state, bounce
or friction. Global distance fields are not the exact tagged-mesh query: actual
separation must be measured against the captured triangles.

The baseline FLIP update still zeros velocity for solid-classified particles
before the appended response. Retention does not establish tangential momentum
preservation, correct flow-through, or volume conservation.

First saved candidate SHA256:
`66f8fde07d3e097cfc05691b5868cc28283cb6305f8ffcb4453e26df2256319e`.
It specified numeric radius but inherited the radius calculation selector.
Corrected saved candidate explicitly selects Custom:
`eefde2513997e3cfa1206acc1bc053b6a3729280cfa7c5eae9df6230dc714122`.
Original bytes retained at `tmp/liquid-terrain-contact-before-radius-20260908.uasset`.
The wrapper requires the exact known prior hash for guarded replacement.

## Actual GPU results at 12 seconds

|Candidate|Live particles|Below exact bed >1 mm|Below bed >32.8125 cm|Worst penetration cm|
|---|---:|---:|---:|---:|
|Deletion bypass, prior control|63160|49510|350|231.08|
|First stock contact|63048|2517|124|59.0295|
|Explicit Custom radius contact|63075|2466|133|59.0295|

The corrected result is `liquid-terrain-contact-opacity-runtime/terrain_0720_particles.json`.
There are zero particles outside the bounded domain, mean speed 52.32 cm/s.
The new response reduces penetration substantially but still fails contact
acceptance. Particle count is not calibrated water mass. Later independent runs
vary slightly in counts; do not claim deterministic particle identity across runs.

## Renderer investigation

The runtime material now exports actual scalar/vector values and component bounds
alongside particle readback. The live transform has yaw158.4348, grid21x21x8 m,
centre(0,0,750)cm, material extents(2100,2100,800)cm and voxel16.40625cm.
These agree in scale but are not proof of every material coordinate operation.
MID opacity is0; absorption alpha.056, scattering alpha.0001.

Runtime-only `RaftSim.LiquidTerrainOpacityReview` changes the current MID, not
the saved asset. The initial high-view opacity0/1/hidden comparison remained
visually terrain-dominated. Later camera movement after freezing does not update
the camera-facing carrier: those multi-angle comparisons cannot establish that
the renderer is empty. Fixed-overhead mode now sets the view before activation
and keeps it fixed throughout all simulation and visibility comparisons.

`liquid-terrain-contact-fixed-overhead` completed. Actual images were inspected:
with terrain visible there are large black regions; terrain-hidden water-only
is almost black with faint edge features. This is not realistic water or visual
acceptance. Need discriminate material lighting/extinction from SDF shape before
adding foam or changing production lighting.

The following **fixed-camera** opacity comparison73596 completed in
`liquid-terrain-contact-fixed-opacity`. Readback confirms MID Opacity1.
Inspected terrain-visible and water-only images now show a narrow blue/white
liquid strip at the inlet, not an empty renderer and not a filled river. The
opacity0 appearance hid much of that strip. Do not infer that the large black
terrain regions are water. Particle readback independently shows most particles
accumulating in the upstream quarter (56250 of63074 in the camera-isolation run),
with centre mean forward velocity10.19cm/s and downstream mean-11.90cm/s.
This identifies flow-through/contact initialization as a priority; changing
opacity alone cannot repair the physics or produce realistic whitewater.
No material parameter was saved by these controls.

## Failures retained, not accepted evidence

- `CreateLiquidTerrainContactRadius.log`: saved0; wrapper detected unchanged
  bytes. The intervening `liquid-terrain-contact-radius-runtime` uses the first
  asset, not corrected radius. Fully loading the package fixed the save;
  `CreateLiquidTerrainContactRadiusLoaded.log` records saved1.
- `liquid-terrain-contact-overhead-runtime` stops at756: HiddenActors property
  cannot be set through that editor API. Replaced it with HideActorComponents,
  which hides drawing only in the capture and leaves scene collision registered.
- `liquid-terrain-contact-camera-isolation` completed but changed camera after
  freezing; retained as an insufficient renderer isolation, not acceptance.
- Build83460 failed linking unexported GetModuleIsEnabled. Using the public
  inline node enable-state accessor fixed build77342 (exit0).

## Verification and remaining work

Regression63508 exits0: `engine-liquid-terrain-contact/index.json` has7 clean
passes,0 failures/warnings,7.74 s. New regression reloads the saved asset and
checks one enabled contact node, disabled solid reject, enabled escape retirement,
distance-field/custom-radius selectors, no bounce/kill/friction, unchanged source
tables and one renderer. Configuration tests do not assert GPU physics accuracy.
Scoped diff-check passes. Baseline terrain system, registered level and project
descriptor hashes remain unchanged from the preceding report.

Continue actual surface rendering, private/exact-bed contact and tangential
momentum, captured wet-volume initialization and inlet/outlet mass calibration.
Then validate raft coupling, stable animation, photographic appearance and normal
gameplay performance. Blocking readback/editor stepping is not a performance test.
All original South Fork and full-queue gates remain open.
