# Same-coordinate source comparison and repaired bank-view launch

September 17, 2026. Previous goal turn made progress: committed the exact-output
crest-boundary optimization. This turn verifies its installed appearance and
locates remaining shape differences in source-matched terrain/flow evidence.
No hydraulic candidate is promoted and no visual or performance gate is closed.

## Installed gameplay, not an override

`south-fork-crest-boundaries-installed-startup-v1-20260917` exits0 with24 actual
1280x720 PNGs. The wrapper verifies exact cook17516 pause/resume0. No candidate
module, material, terrain or flow argument is used. Installed optimization and
integer optical-normal correction remain active.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260917-071212.mp4`, SHA256
`e433c78488b44cc9bc2b5ac1aa34b5fe258863525fa5d7c0e97575a16422d50a`:
234 engine source frames/15.839s; independent decoder reads all475 encoded
frames, last PTS15.8s. Inspected decoded1/6/11s frames. The obvious rectangular
normal patches remain absent; broad sheet-like white water and the sharp
foreground face remain. Complete decoding is not continuous calibrated motion
review. The encoded30Hz timeline repeats frames and is NOT game FPS.
Decoder report: `tmp/crest-boundaries-installed-motion-v1-20260917/`.

Existing ordinary timing audit remains30.936070FPS/p9539.5813ms for indexed
boundaries versus30.263432/p9540.0262ms for legacy control. BOTH miss the
33.333333ms p95 budget; no sustained/repeatable whole-frame improvement claimed.
See [boundary qualification](crest-boundaries-installed.md).

## References actually accessed

Used the computer-use skill and the in-app browser, without login, download,
upload or security changes. The ordinary Skip-ad control exposed Qweniden's
[bank-side reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ); inspected
paused0:55 and1:00. Exposed angular shelves constrain several narrow overfalls,
with irregular white tongues and darker intervening water; the camera pans.
John Elkins' [raft-view reference](https://www.youtube.com/watch?v=ZEG1kvjNI30)
also played; inspected paused0:40 at the drop, with passengers obscuring part
of the view. These are sparse actual frames, not measured bed, discharge,
dimensions, velocities or fixed-camera photogrammetry. No reference media was
imported into shipping assets. The game still lacks convincing localized
breaking and foam compared qualitatively with these views.

## Same XY, not the same pixel in different raft trajectories

`south-fork-control-ablation-shape-v1-20260917` uses the existing verified3350s
joint descriptor and the installed modules/material. It exits0 with24 PNGs and
exact cook resume0. Native preflight confirms803,842 exact replacement terrain
triangles before BeginPlay. Frame022 SHA256:
`3d96a727a71214ed17b3126f40982263f3e5fd9a4c25a43cbfe9bdb2f804d5be`.
The inspected image is flatter at the foreground face but still has broad
smooth aeration and detached-looking spray. Flatter alone is not success.

The two raft paths/cameras differ. New `compare_carrier_source_fields.py`
reconstructs the original camera rays from the original source files, finds
their CPU triangles, and samples BOTH cached source stages at those exact world
XY vertices. It preserves the shoreline A-C-D/A-D-B diagonal, checks complete
finite ordered lattices and reference epochs, and leaves dry/outside/missing
comparisons unavailable. It never compares different camera pixels as if they
were the same water. All input hashes are retained.

Reference: `south-fork-integer-hash-angular-boundary-v1-20260917_022.png.carrier.json`,
game155/world11.276242s/detail152. Candidate: new capture022,
game156/world11.246666s/detail153. Both names are under
`unreal/Saved/Screenshots/`. All seven original probes are comparable and kept.

| Original image probe | Reference cached-stage slope | Candidate cached-stage slope at identical XY |
| --- | ---: | ---: |
| (640,650) | 42.505185deg | 7.354862deg |
| (960,690) | 42.939334deg | 2.799337deg |

At the first footprint, candidate-minus-reference stage at the three original
vertices is+1.280675/+1.167953/+0.924770m; at the second it is
+1.121541/+1.412325/+0.952706m. The strong mean-stage face is absent there in the
candidate source. This directs work toward source-consistent terrain/flow and
local breaking, not flattening fine crests to conceal the installed base face.
However, the different bed hypothesis, cook age and runtime evolution are
confounded: this is NOT an isolated causal bed experiment or a calibrated
physical correction. Source stages are not candidate rendered triangles/GPU
visibility; the candidate is still unsettled and its submerged bed is inferred.

Report `tmp/south-fork-same-xy-source-comparison-v1-20260917.json`, SHA256
`b1608e9883382775d5fb15432762854eabd20f73883cbbeed52633e2f8327689`.

## Preview launcher repaired and exercised

The native loader accepts joint descriptorv1 and registered-terrainv2, but
`run_south_fork_joint_preview.ps1` rejected allv2 descriptors before launch.
Its guard now accepts both exact schema strings and requires explicit boolean
candidate=true/production_promoted=false. Missing, coerced, promoted and unknown
formats remain rejected. Native dependency, collision, field, terrain and
pre-BeginPlay checks are unchanged. Added a production-function PowerShell test
for both supported versions and11 rejection cases.

Actual `south-fork-source-matched-bank-v1-20260917` completes through this wrapper:
exit0, exactly one preflight installation, singleSurface=1, three PNGs, finalized
recording; runtime report SHA256
`e258fa4c749da34f776309c6b2f1c64852630fb84896182ec2feb2d88eb8a31a`.
The exact source camera remains at(-545095,-362309,1800)cm,
pitch-27.8/yaw18.075deg over captures at world12.466/13.118/14.128s.
This is a registered game camera, NOT a calibrated YouTube camera.

Recording `RaftSim_20260917-072345.mp4`:78 engine frames/6.198s, all186 encoded
frames decoded, last PTS6.166667s. SHA256
`499649ed7e51eae891b3e6839f40bc608e3e3f949d645a788deaf8e7af8185c6`.
Inspected decoded1/6s frames. Requested11s extraction is unavailable because the
clip is shorter; it is not fabricated. Decoder output:
`tmp/source-matched-bank-motion-v1-20260917/`. Broad white sheeting persists
beside the exposed rock control. This run shares the machine with the verified
live cook and is NOT a performance capture. Ordinary saved assets are unchanged.

Focused source-comparison, carrier-ray/shape/epoch, boundary-pair and frame-CSV
Python tests:61 PASS. Includes shifted/rescaled source grids, both Y conventions,
nonplanar diagonal, unavailable data, invalid metadata and differing epochs.
Existing joint-preview, verified playback, terrain replacement, retention-rebind
and mesh-staging suites:112 PASS. Both PowerShell launcher/identity suites PASS.
Installed gameplay, water-detail, project DLL and material hashes still match
the preceding installed record. No engine binary/source changed
this turn; no new native test count or release build is claimed.

## Hydraulic continuation and remaining work

Exact same cook PID17516/start2026-09-17T12:52:03.0749210Z remains directly live.
Completed3850/local5000 passes state/conservation AND all86,720 exactly dry bank
cells. h SHA256`60fba1650bb7fb638ae009e85f394efe39d498dde9bbe75a4ec0e33be5b34300`.
Maximum depth4.010614m, speed5.390118m/s, volume2,901,932.220352m3 and maximum
step residual1.521822e-8m3. Outflow89.657875 versus inflow45.306955m3/s:
NOT settled or promoted. Both reports are
`tmp/control-ablation-3850s-{state,banks}-v1-20260917.json`.
The subsequent3900/local6000 completion also passes BOTH audits: maximum
depth3.996081m, speed5.375223m/s, volume2,899,690.788988m3, maximum step
residual1.521822e-8m3. Outflow89.927435 versus inflow45.306955m3/s remains
unsettled. Reports `tmp/control-ablation-3900s-{state,banks}-v1-20260917.json`;
h SHA256`44eb6fa0506f450f2c5780df8e7feb5a390783f01c46bd6c23db11ccfd370b6f`.
Next3950/local7000 needs its completion marker and both independent audits.

Next physical work must retain exposed source landmarks and distinguish bed
inference, qualify the evolving source/terrain together, then resolve localized
breaking and transported froth on the shared playable/contact surface. Neither
a flatter candidate nor a diagnostic pass closes this work. Sustained30FPS,
Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi, crew fit/animation/realism,
normalization, regressions and release remain open. Troublemaker is only a rapid
inside South Fork, never a separate scenario/menu entry.
