# Terrain particle-loss isolation — September 8

The preceding goal turn made progress (saved source asset, actual GPU terrain
comparison). This turn adds authoritative particle identity/state measurements
and isolates the dominant loss mechanism. It does not establish scene acceptance.

## Measurements

`liquid-terrain-particle-identity` is the unchanged saved terrain-water system.
GPU readback now exports per-particle unique ID, source index, local position and
velocity, plus captured system transforms/timestep. At12s:

-2592 particles survive; IDs223311..227310. Their median approximate age from
  the nominal emission schedule is0.26s and oldest0.76s (one-frame timing
  uncertainty). IDs continue advancing at the requested emission rate.
- Actual simulation delta is0.0166666675s. Actual UnitToWorld has21m horizontal
  axes,8m vertical axis, correct158.4348-degree yaw and bottom at350cm; centre
  is(0,0,750)cm. That grid matrix matches the intended transform and dimensions.
  This does not prove the material transform or every downstream conversion.
- Initial surviving source IDs start at163840, exposing an additional startup
  burst/ID allocation before the continuous source. Do not count those IDs as
  verified real incoming water. The flat tank initializer still needs replacing
  with a state consistent with the captured hydraulic field.

## Controlled solid rejection

The new `RaftSim.LiquidTerrainSolidLossControl` console command makes a
**transient, unsaved** copy. It disables only the active fluid emitter's
simulation-stage `KillParticles` module driven by rounded solid-cell occupancy.
It leaves terrain pressure boundaries, normal flow sources and escape retirement
unchanged. This is a diagnostic, explicitly not a collision fix or promoted asset.

|Time|Baseline live count|Control live count|Control below bed >1mm|Control below bed >one cell|
|---|---:|---:|---:|---:|
|0.1s|439|440|0|0|
|0.5s|2140|2555|373|5|
|1s|2590|5186|2244|21|
|4s|2599|21001|15106|109|
|8s|2613|42079|32338|236|
|12s|2592|63160|49510|350|

Baseline: `liquid-terrain-particle-identity`. Valid control:
`liquid-terrain-solid-loss-active-graph`. Control maximum penetration reaches
231.08cm; zero escaped particles at12s. The control's much higher retained count
identifies solid-cell deletion as a dominant loss mechanism, but it also
demonstrates why removing that deletion alone is unacceptable. A proper surface
contact correction must retain/project water and remove only inward normal
velocity while preserving terrain pressure support and accounting for mass.
Nearest-grid-cell solid classification is not a faithful particle contact test
on this rough captured bed. No calibrated FLIP particle volume is claimed.

## Visual evidence and failures

- Replaced1000x cubemap ambient with1x and set a documented unsaved diagnostic
  sun(-40degree pitch,50000lux). Inspected high-angle baseline and control
  captures show illuminated angular terrain but no convincing river surface.
  Prior low-camera blue sheets must not be interpreted as validated water.
  Material/SDF bounds and camera clearance still need independent verification.
- First control attempt59818 matched two copied nodes, refused installation,
  and inadvertently continued as another baseline. Retain
  `liquid-terrain-solid-loss-control` as **invalid control evidence**. Fixed
  selection to actual fluid-emitter graph(s), and the Python harness now asserts
  that the transient control asset really was installed.
- Build84927 succeeded; baseline41350 succeeded. Build40498 succeeded;
  first control59818 terminal. Build27675 succeeded; valid control25896 succeeded.
  No owned capture/build remains live. All captures are editor-only diagnostic
  stepping/readback; wall time is not gameplay frame performance.
- Final regression29224 exits0: `engine-liquid-terrain-identity/index.json`
  has six clean successes, zero failures/warnings,7.31s. Scoped diff-check passes.
- Saved terrain system SHA remains49be4cc378eca13c1ef2a28742fc82d276d879d7a8af4c43f5c142018209d9e1.
  Registered map and project descriptor retain the hashes in the preceding
  terrain-source report. No asset or level saved by the control; no commit.

## Next implementation

Implement physically appropriate terrain-contact projection/velocity response
in the actual FLIP particle stage, rather than deleting water that touches a
coarsely classified solid cell. Preserve escape retirement and measured sources.
Replace the inherited flat tank startup with the captured field's wet volume
and velocity; quantify born/retired/outgoing mass. Verify the one SDF renderer's
actual runtime material bounds against the captured simulation transform, then
obtain readable multi-angle motion before judging optics. Original South Fork
and full-queue gates remain unchanged and incomplete.
