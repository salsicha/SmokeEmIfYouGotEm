# Normal installed-module South Fork review

The revised paired terrain/water now has actual rapid-view evidence using the
normal installed Raft, WaterDetail and project DLLs, with no temporary module
override. This is still an explicit reconstruction preview, not a saved-map or
menu-default promotion. Broad white water, bank-side shape, physical breaking,
convincing froth and 30 FPS remain unaccepted.

The preceding commit-only turn verified a clean tree but did not advance the
reconstruction. This turn revalidated the existing processes, completed actual
normal-module captures, found a full-replay timeout, audited the next hydraulic
checkpoint and corrected one current generated-inventory regression. No shader,
solver, gameplay binary or saved scene was changed during the live SM5 suite.

## Installed-module integration and the long replay

The module witnesses inspect the live process's loaded module paths and hash
the corresponding files. Both the long replay and rapid capture load:

| Normal module | SHA256 |
| --- | --- |
| RaftSimRaft | `14e578ba824b73ce9cb90c733eb4cfba2a30b8fdd04261034bbe15448f54d591` |
| RaftSimWaterDetail | `650f80cad069a08f4cba6ec18542c67b3d87f823c13aa68f86975645674bbb37` |
| SmokeEmIfYouGotEm | `4daae5dabefdc6107818c2cc4359b57366799e752d71116eedac20ef54e65af9` |

The first long invocation, session6288, fails before BeginPlay because a bare
PowerShell argument split the descriptor filename before `.json`. Its evidence
is retained in `tmp/normal-installed-detail-play-v1-20260916`. The subsequent
argument-array invocation uses the intact descriptor; this is not a solver fix.

Session78384/PID36592 is now terminal. Its result is **false**, reason
`Actual-play observation timeout`: 4,965 observed ticks, 4,962 fresh presented
frames, seven post-ready handoffs and 331.000017263 detail seconds. The last
sample is world835.763s, total handoffs9 versus first-ready handoffs2. The
formerly failing fifth handoff is crossed with detail still active, but the
required eight post-ready handoffs are not reached within the original900s
wall limit. Do not count this as a completed full regression or lower its gates.
The simultaneous shader/whole-river workloads preclude a frame-rate claim.

The probe's `normal_project_binary_deployed:false` is a hardcoded scope field,
not an inspection of the loaded module. The separate live-module witnesses
above establish installed paths; do not reinterpret the probe field as a pass.

Evidence under `tmp/normal-installed-detail-play-v2-20260916`:

- `result.json`: `13541da6136fc86b445ebc4c503b53315b0b622433cb3d31ed39bcdaa66ad90d`.
- `module-identity.json`: `52f34307a64507dadf539f51e40f275586ddc3d88eae86e517e60d8108a94b43`.

## Actual rapid camera and motion

Queued session56238/PID28860 starts only after the prior gameplay process exits
and finishes engine0. It uses the same350s descriptor
`tmp/control-ablation-350s-joint-preview-v1-20260916.json`, SHA256
`4de7202df61db16d18bd42e87086fc2620681053e5210c50757db35ab68ec3c4`.
The original ground actor is verified resident/replaced before paired-water
BeginPlay. Source water is still transient, not a final calibrated field.

The existing command is `RaftSim.CaptureSeries 12 3 10
normal-installed-rapid-v1-20260916 -545900 -362700 2000 -35.27 46.85 record`.
Actual three captures are1280x720, fixed camera(-545900,-362700,2000)cm,
pitch-35.27/yaw46.85/FOV90. They occur at world12.408/22.062/32.177s, raft
stations8338.619/8347.117/8356.632m. Camera, source age and descriptor match
the prior350s review; trajectories and source/detail clocks are not identical.

Complete local recording decode succeeds:111 engine source frames over25.221s,
757 decoded frames through25.2s. Unmodified5s/15s frames and the final still
were inspected. The raft advances and the water appearance changes, but broad
white coverage, sharp bank-side streaks and visibly faceted boulders persist.
The central unsupported bowl remains absent in this camera. Thirty-Hz encoding
and image-difference statistics do not prove30FPS or correct fluid motion.

The real [Troublemaker reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ&t=30s)
plays successfully again around0:30. Observed irregular foamy crests and gray/
green faces retain darker water gaps as the raft crosses the rock-controlled
rapid. The game comparison still looks too broadly white and smooth in places.
This is qualitative visual rejection, not a calibrated camera, discharge,
stage or submerged-geometry measurement. No remote video was downloaded.

Sampled contact checks cover1,934 wet points,870 affected by paired detail;
maximum support/carrier error4.76780447e-5cm, zero unavailable points. All82
ground-occluded points have dry support. Shared hull/render logs show zero
error at revisions9/1209. This does not prove full traversal, independent
ground truth, GPU upload parity or render latency; GPU audit was not requested.

The log retains experimental engine-plugin Python startup errors for missing
`unreal.AgentSkill` and `unreal.PythonTestRunner`. Engine exit0 does not make
the run an error-free release check. They were not hidden or patched away.

| Local evidence | SHA256 |
| --- | --- |
| tmp/normal-installed-rapid-review-v1-20260916/module-identity.json | `e50438874b15c17bd5cdf239b56056f42db4c2237c0ec6717b7193766bbccdd5` |
| tmp/normal-installed-rapid-review-v1-20260916/play.log | `2cba73ab3897d197b8a26dee0d9303b9f1ad976792d9cad2f9e5fcb4b835156d` |
| tmp/normal-installed-rapid-review-v1-20260916/contact.json | `d9e2212577afbb66f98cfdef72d45888ced530d7d9ec7094ce9fb6aad2b66eb5` |
| tmp/normal-installed-rapid-motion-v1-20260916/play.json | `05fdd24f7046ec1d1d810c15c2c597259702631c0134c893c09f3aa928a2e472` |
| unreal/Saved/Screenshots/normal-installed-rapid-v1-20260916_002.png | `2c827c60007a80a73f447a92d7d0f0efa200caf618fdc91888015ced9f05a63e` |
| unreal/Saved/VideoCaptures/RaftSim_20260916-140748.mp4 | `b714dc1ded57328e83a5cec7168b256f6391e3320c993387b3a7d94df4b65927` |

## Same hydraulic continuation

Session40601/PID11316 remains live, last observed near868s; no restart or
executable replacement. Both800/local4000 and850/local5000 pass all5,382,400
state cells and86,720 exactly dry artificial-bank faces. At850s depth maximum
4.67419456m, speed9.59760093m/s, maximum step mass residual1.28737396e-8m3.
Outflow59.15712042 versus inflow45.30695455m3/s remains **not settled**.
Next complete900/local6000 needs both audits before using its state.

The zero-step600/700/800s rapid inspection also completes, using the same native
flux operator without advancing state. Four rapid tiles drain from10,123.61 to
9,161.00m3. Their700-800s mean inventory rate is-4.05893646m3/s; instantaneous
800s selected net inflow is-2.80020132m3/s. Within the40m comparison circle,
water outside the historical captured-water mask falls80.34 ->55.03 ->40.50m3.
That historical mask is not a calibrated present-flow shoreline. These results
support continued settling, not lowering banks, tuning roughness or visual
concealment to match a transient field.

| Report under tmp | SHA256 |
| --- | --- |
| control-ablation-800s-state-v1-20260916.json | `88fa8baab74c698d691a7074c3d80c63db559bb68cc537112e06792bbdf0fecc` |
| control-ablation-800s-banks-v1-20260916.json | `b540b9cfe0920de9e04d15341b52515ec8e99bdb8c14c4d470decbe043ff07e3` |
| control-ablation-850s-state-v1-20260916.json | `127846dcadbb8b7f2bb531e09d4627a0097c2a808ba06a9a006668d2da8c47c3` |
| control-ablation-850s-banks-v1-20260916.json | `042d9d6f62d61467bcdb858b927a50d282be522f00eb6b14b013a16b107516e4` |
| control-ablation-inundation-600to800-v1-20260916.json | `6cc116194fe2a6237f81b4fe5c73a24ec24257814604d2f09224a2be16bf5ec6` |

All464 protected identities are retained:462 unchanged plus the two previously
verified CPU-retention-only revisions, zero mismatches. Fresh report
`tmp/normal-installed-rapid-protected-v1-20260916.json` SHA256
`0f55a76e0232f2c61eb38c15f2c038abdd778fe05f4229ac34e10ef9a01eac44`.

## Regressions and next implementation

The current source inventory was stale at90 files. Its existing generator now
records168 implementations/109,235 lines/37 registered commands; no tests or
historical review hashes were changed. Inventory/catalog/layout/release subset:
26 PASS. The same larger focused set improves62 PASS/13 FAIL to63 PASS/12 FAIL.
The12 remaining source-layout/foliage/water/provenance failures are preserved in
`tmp/normal-installed-review-regressions-final-v1-20260916.xml` and remain open.

SM5 suite47178/PID35584 remains LIVE with three independently live shader
workers. New transport8/3 compile-threshold warnings are not terminal failure
or success. Continue the same job; do not modify its shader/DLL inputs or start
a duplicate full cook. See [binding changes](sm5-resource-bindings.md).

Normal `RaftSimStatefulDetailComponent` still sends the nonlinear total-depth
owner to an explicit audit path; these native tests do not by themselves
integrate that model into displayed gameplay. Full coupled physical breaking/
foam, outer-domain return exchange and sustained capacity remain required.
Next: finish the current SM5 result, complete the unchanged normal full replay
under a suitable workload, use settled source-consistent rapid data for the
next physical-water/visual change, then qualify normal-menu/default delivery
and uncontended30FPS/p95<=33.333ms. Last ordinary17.819710FPS/p9581.6343ms fails.
Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi water, crew, normalization and
full release work remain open. Troublemaker is only a rapid within South Fork.
