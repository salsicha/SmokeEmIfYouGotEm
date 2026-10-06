# South Fork450s: normal playable candidate trial

September27,2026. Integration and packaged validation completed; no visual,
hydraulic or whole-river performance acceptance. This follows the [completed cook and export](south-fork-v2-continuation.md),
not another reconstruction of the captured sources.

## Scope and rollback

Only the normal FullReach water-config actor's streaming and initial-field
paths are changed, from `tmp/discharge-bed-runtime-v2-20260926` to
`tmp/discharge-bed-v2-runtime450-20260927`. Initial window remains region_0008.
The map, run manager, hydraulic and route coordinate maps are unchanged.
All799 packet beds, captured masks, grids, solver settings and coverage bounds
were independently verified unchanged before integration. Underwater geometry
remains inferred; later simulated time does not make it measured or settled.

The v4 package at `tmp/south-fork-playable-v4-20260926` and v4 runtime bundle
remain intact. Before editing, all three saved scene hashes matched v4's
inventory. Exact water-config backup:
`tmp/south-fork-runtime450-bind-20260927-backup.uasset`, SHA-256
`9a4a9a731fb88ce9a7e0c66feca271943e4d253907c11c75d999e4fb766baf2c`.
This is a backup of the changed actor only, not a substitute for preserving
unrelated shared work. Rollback must verify ownership/current hashes first.

## Saved normal binding and immutable bundle

The scoped binding process35264 completed successfully. A separate fresh
Unreal process9708 read back the saved map/config without saving assets. Both
exit0. Set/inventory/bundle helper session53035 also exits0.

- Config asset: `unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach/0/P0/A1GOUPANCXW4AY40QJTLTK.uasset`.
- New config SHA-256: `c9791d7414176a843bad2ea1e6b5985f9cf6de294733161c4f187bf17fced533`.
- Set receipt: `tmp/south-fork-runtime450-bind-20260927-set.json`,
  SHA-256 `05955e9a6bdd14673d3a1a2a4c67ec7fc1896c632b97ed92547eb831a8c13b9e`.
- Independent inventory: `tmp/south-fork-runtime450-bind-20260927-inventory.json`,
  SHA-256 `d1efe8a80427ebe415b93f44a7d9c2c045605ff466aee75f958776b616e5d8d6`.
- Bundle: `physics/data/runtime_bundles/south_fork_discharge_bed_v5`,
  2,405 logical files/917,960,997 bytes, verified transitive dependency closure.
- Bundle manifest SHA-256:
  `50f5e63ce8378e7faac2c32ce94192d261e0c7caa2d48619d468d76f405a79f7`.

`RaftSimWater.Build.cs` stages v5 instead of v4, using the existing required
saved-scene and content-addressed payload hash checks. It still stages the
exact logical paths beside the packaged executable; no developer-tmp fallback
is permitted. All38 existing runtime-bundle regressions pass (fresh test root
`tmp/runtime450-bundle-tests-20260927`, no new dependency installation).

## Completed package and actual staged closure

BuildCookRun session89262 exited0: Editor/game compilation, cook, staging and
package succeeded in861.94s. Log: `tmp/south-fork-v5-package-20260927.log`.
No existing package was overwritten. Old MetaHuman missing-dependency display
messages also occur in v4; this is not warning-free release qualification.

Fresh game: `tmp/south-fork-playable-v5-20260927/Windows/SmokeEmIfYouGotEm/Binaries/Win64/SmokeEmIfYouGotEm.exe`.
SHA-256: `8ffc14bef18cf155290b62bf60686346e1a639d3cbb50188371abf7bd1f2fff8`.
The staged audit `tmp/south-fork-v5-staged-payload-20260927.json` independently
verified all2,405 files/917,960,997 bytes with no external-source fallback.
That file-closure audit alone does not verify execution; the runs below do.

## Packaged timing: startup passes, busy rapid fails

Validation wrapper session71636 exited0. Both separate runs used1280x720,
1,200 total frames, measured rows30..1169 (1,140 frames), no diagnostic quality
commands and no competing engine/build/cook. Ephemeral profiles preserve user
saves. The binary hash remained unchanged. Target:20FPS, p95<=50ms and no
individual frame>100ms. Helper exit0 is not a performance pass.

| Actual launch | Mean ms | p95 ms | Max ms | Frames>100ms | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot -> actual menu -> FullReach | 36.3476 | 44.4436 | 55.4646 | 0 | Startup timing only passes |
| FullReach at busy11520m | 48.1631 | 71.8342 | 107.4702 | 1 | p95 and hitch fail |

Both report zero runtime errors. Receipts under `unreal/Saved/RaftSimValidation/`:
`sf-v5-normal-menu-20260927-frame-audit.json` and
`sf-v5-rapid11520-20260927-frame-audit.json`.
CSV SHA-256 values respectively:
`0fdc358228d1cf21357e3be6a2e2eb68778131e9290f0b74f46877f342ba289f`,
`3b7027d551f5fac33ffd3f09228162c6e41802b800ff36a55c41ed05da81fe11`.
The freshly compiled executable differs from v4: historical timing differences
do not establish a causal field-only speedup. Startup is not river acceptance.

## Actual motion and bounded contact observations

The separate8330m Troublemaker capture issued AllForward, used the ordinary
FullReach scene/material and recorded motion without rendering overrides.
Log: `tmp/sf-v5-troublemaker-motion-20260927.log`; live mode confirms
carrier=1, volumeCore=1, singleSurface=1. No new solver flags or foam sheet.
Video: `tmp/south-fork-playable-v5-20260927/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-101843.mp4`,
SHA-256 `b77ad0833f05416be15ce8f2c3c1d36b80808dae7eceeab9f64cb7a2b9b8d2cc`.
Decode receipt: `tmp/sf-v5-troublemaker-decoded-20260927/report.json`:
770 frames,0..25.6333s,1280x720,6 exact adjacent duplicates. Encoded30FPS is
not measured game FPS. Frames at1,3,6,9,11,20s were visually inspected.

Raft/paddles change pose and HUD station advances about8.34->8.37km, with no
displayed incidents/swims in those views. The raft turns toward the right bank
and later faces opposite rocks; similar turning existed in v4 and its cause
is not established here. Water still shows broad smooth reflective sheets and
flat opaque foam islands/ribbons, not convincing plunging lips, holes and
recirculating froth. Banks/boulders remain visibly coarse. Selected frames show
no detached second sheet, but do not establish all-frame shoreline stability.
The v4/v5 comparison is not trajectory/pixel registered; no convincing visible
realism improvement is established by this later-state integration.

`tmp/sf-v5-troublemaker-motion-20260927-contact.json` contains50 observations
under a first64-projections>=5mm cap, not a complete contact ledger. Times span
1.2003075..8.0568239s; vertical corrections span5.0247..13.3058mm (mean8.5632mm).
All50 resample physical ground with height matching the solver float and
identify `SourceMatched20260917/SM_SourceMatchedGround`. This supports sampled
collision identity, not full hull contact, successful traversal or acceptance.

## Next work and retention

### Follow-through: distinguish missing spilling from mesh flattening

Guarded packaged diagnosis session76733/PID32616 completed with exit0. It used
the same executable, normal8330m scene and paddling command, adding only the
existing breaking-height and crest-sampling observers. No geometry, solver,
shoreline acceptance threshold or material changed. Log:
`tmp/sf-v5-crest-shape-20260927.log`. Instrumented timings are not FPS evidence.

At10.133161s, the raw detector finds64 candidates,13 passing the interior gate,
with accepted upstream Froude1.1209..1.2033. Raw and optical rises agree to the
logged precision: smoothing is not removing the rise at these candidates.
The [four persistent sites](runtime450-evidence/crest-sites.json) have heights
0.1623..0.3578m and ALL have spilling_fraction=0. The current modeled spill
transition is SmoothStep(1.28,1.7,upstream Froude), so this snapshot produces
undular added relief without accepted crest-entrainment foam. These are model
choices/output, not measurements of the real river or proof the detector is right.
The initialization log's0.060m strongest crest was not its mature maximum.

The continuous crest maximum is0.3547218m; its coarse1m triangle approximation
has maximum error0.0722944m. The separately timed10.014889s
[actual submitted refined mesh](runtime450-evidence/crest-submitted-mesh.json)
has1,116,936 samples, maximum target error0.824218cm and fine-correction
tracking error0.000476cm. Original source anchors are unchanged. The snapshots
are not simultaneous or an all-frame proof, but the submitted-mesh result
does not support increasing tessellation as the primary fix for this scene.

Next physical work should examine the inferred submerged control and resulting
flow through the reference hole, and the spilling model against that flow,
before altering foam colour or lowering shoreline/Froude gates. In particular,
rejected high-Froude bank-edge detections are not automatically valid crests.
The [Dreamflows caption](https://www.dreamflows.com/American/troublemaker.wavewheel.lg.php)
was rechecked: it identifies Troublemaker hole/Gunsight Rock and retains
Chris Shackleton's2006 all-rights-reserved notice. It provides neither surveyed
bathymetry nor a shipping license. No new imagery was downloaded or bundled.

Durable timing receipts accompany this record:
[normal menu](runtime450-evidence/normal-menu-timing.json) and
[busy rapid](runtime450-evidence/rapid11520-timing.json). Paths within receipts
refer to retained local raw outputs; JSON formatting is normalized in these
copies. These receipts retain explicit false physical/whole-rapid gates.

Retain v5 as an unaccepted normal-playable candidate and keep v4/actor backup
intact. Numerical safety and reduced aggregate regional drift do not prove
settling or better-looking water. No new surveyed geometry or source evidence
was added. South Fork remains the first unfinished river; do not advance the
queue. Next work must address actual breaking-water/foam structure and busy
rapid cost, with new measured hypotheses. Do not repeat this completed cook,
bundle verification or unchanged timing runs merely to obtain a passing result.
