# South Fork raft-centred spray: source-ownership diagnosis

## Follow-up: normal standalone v28 correction verified

September29UTC. The historical diagnosis below is retained; its pending repair
status is superseded by these results. Normal South Fork now gates ambient
raft aeration by raft-relative impact/contact when the existing river-owned
Niagara breaking path is ready. Other rivers retain the existing classifier.
River-site emitters, physical forces and full-contact response are unchanged.
The experimental certified shoreline remains OFF.

Four native VFX tests passed, including co-moving supercritical/no-contact,
increasing relative slip, full contact, dry and underwater cases. The standalone
v28 executable was rebuilt successfully and its existing immutable cooked
assets were verified against v27; no cook ran into a hard-linked stage.
Executable SHA256:
`48c93073f02dd3131d57e3a7e9de8c9778a2af66bb73ad90fbc074970f6bd762`.
All frozen source inputs and the previous executable remained unchanged.

`tmp/raft-spray-v28-motion-20260929.json` verifies actual Boot -> main menu ->
FullReach launch, then80 motion samples from8313.432 to8487.418m (173.986m).
The normal-config motion recording decoded2483 frames at1280x720 over82.733s.
Encoded frame rate is not game FPS. Reviewed10/20/21/40/60/78s frames show no
recurring interior plume; river-site spray remains visible. The raft advances
past bank landmarks and foam changes position. These are sampled observations,
not full-traversal shoreline/animation acceptance or a pixel-controlled A/B.

The same-frame diagnostic at world10.118513s measured contact0, relative speed
0.642931m/s, old/new spray0.106605/0.047979, mist0.083418/0.017235 and
droplets0.100727/0.057344. Six each river aerosol/roller/crest emitters remained
active with zero measured source-centre clearance error. This paired classifier
comparison establishes the mechanism without attributing every historical
plume to this source. Hull-placement of genuine impact spray is not solved.

Independent submitted-triangle support audit:1867 wet probes,899 affected by
paired detail,zero unavailable or ground-occluded wet points. This is sampled
support evidence, not a full collision traversal; no paired GPU parity capture
was requested in this run. No runtime errors were observed.

Recording SHA256:
`01776dce242bde1edc99c43bb2e1c3f05886c10668f10265bd32e349ee3eb2e7`.
Frames/report are in the thread visualization folder
`south-fork-v28-motion-20260929`.

Visible remaining failures: broad flat white foam ribbons, weak breaking-wave
relief, angular bank/rock shapes and mostly resting crew poses. This is a bounded normal-play spray
improvement, not river completion or whole-scene visual acceptance.

### Isolated standalone performance

All three normal-configuration runs completed1200 frames;1140 rows30..1169
were audited. Zero runtime errors, no competing workloads across19/29/35
isolation polls, frozen source/executable hashes unchanged. The strict CSV
scope/clock parser passed; parsing success does not mean performance acceptance.

| Start | Mean ms | p95 ms | Max ms | Frames >100ms | 20FPS gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu | 33.2413 | 47.8360 | 59.3657 | 0 | Pass |
| 8310m | 60.5919 | 98.2354 | 268.2680 | 55 | Fail |
| 11520m | 71.4376 | 91.9015 | 172.1190 | 14 | Fail |

The two heavy runs are worse than historical v27 samples; these separate runs
have different trajectories and are not a controlled source-change A/B. Do not
attribute the difference to the spray correction without paired evidence.
There is no performance-win claim. At8310m the measured inclusive surface Tick
mean was34.67ms, SetMesh16.73ms, crest Update12.62ms and solver StepWater13.76ms.
These scopes are nested/overlapping and must not be summed.

Bridge debt: menu0.003332->0.015512s(max0.01663);8310m0.9426->0.012205s
(max3.9051);11520m1.1397->6.5558s(max10.6779). All1140 audited11520m frames
consumed the four-tick limit. Simulation-capacity acceptance remains false;
do not discard elapsed time or change the timestep to conceal this debt.

Suite receipt:`tmp/raft-spray-v28-profile-20260929.json`.
Individual receipts:`unreal/Saved/RaftSimValidation/sf-v28-isolated-*-20260929-frame-audit.json`.
Strict scope/clock reports:`tmp/sf-v28-isolated-*-20260929-scopes-and-clock.json`.
All owned v28 jobs finished; no duplicate job or future polling is needed for
these receipts. Heavy-section cost/debt and appearance remain the next work.

## Historical diagnosis before repair

September29UTC. Supporting source inspection, not a rendered fix or acceptance.
No native source, package, shader or physics setting was changed by this audit.

Actual v10 frames20/21/60s show wispy plumes over the raft. The source inspected
here is `RaftSimWaterVfxActor.cpp`, SHA256
`981b550c421a8c123dcd36c2a341bb36cade3b6ea13834c8906e2465922585da`.
This establishes a reachable inappropriate source placement, but does NOT yet
attribute every recorded plume to this pool rather than the rapid-site pool.

## Concrete reachable case

`EvaluatePresentation` derives HydraulicAeration from absolute water Froude,
independently of raft-relative impact or contact. Take wet water at0.75m depth,
velocity(6.8,0.4,0)m/s; raft velocity equal to that water; zero contacts and
zero indentation. HydraulicAeration saturates to1 while RelativeImpact and
Contact are both0. The implemented equations then produce:

- Spray0.72, above the Niagara0.08 enable threshold.
- Mist0.8128; normalized visible mist about0.7717, above its0.02 threshold.
- Droplets0.5328, above its0.10 threshold.
- ImpactSheet0.

Thus a co-moving, non-contacting raft can emit substantial spray/mist solely
because the surrounding river is fast. This is not proof that these exact
conditions occurred at a reviewed video frame.

In `RefreshVfx`, with no dominant contact, SurfaceCenter uses RaftLocationCm.XY.
Both upstream and outward contact offsets become0. ParticleSurfaceCenter then
has the same XY as the raft centre. Spray/droplets are launched only8/12cm above
SurfaceCenter; the mist anchor is70cm downstream and52cm higher. It is not a
sampled exterior hull-water impact point. The fallback card path shares the
same centre. Moving this centre without re-sampling water would also be wrong.

Separately, `RefreshRapidAerosol` already emits from persistent river breaking
sites before the raft-dependent refresh. Normal South Fork defaults
raftsim.SouthForkCrestSpray=1, with visible-carrier footprint/anchor checks.
Therefore river aeration has a distinct location-owning path; it should not be
assumed to require a second raft-centred generic plume.

## Required bounded repair and verification

1. Distinguish river-site aeration from raft-relative/contact spray. Preserve
   crest-owned rapid aerosol and actual contact/relative-impact splashes. Do
   not remove all spray or lower global density merely to hide the symptom.
2. Add native cases for co-moving supercritical/no-contact flow, slipping flow,
   D4 contacts, dry water and underwater state. Existing classifier tests cover
   calm co-moving and rapid WITH contact, but omit the problematic combination.
3. Attribute actual emitter anchors/enabled states to the same engine-frame
   water/raft input before choosing a hull-placement correction. If a source
   moves outside the hull, sample visible carrier at that XY; preserve contacts
   and forces. Avoid invented underwater survey geometry.
4. Integrate in normal South Fork, rebuild, compare actual boat-camera motion,
   verify no floating/interior smoke and preserved breaking-site spray; measure
   normal Boot/menu and heavy-section cost. These are outstanding, not passed.

The preceding Lava Canyon validation engine27824 was observed live with
`lava-p4-game-cap.log`; it exited during inspection. No duplicate build/game,
capture, cook or benchmark was started and no other process was stopped.
The existing v10 shoreline failure remains independent of this appearance issue.
