# Source-matched South Fork gameplay preview

September 15, 2026. This is visible, evolving integration in the existing
playable South Fork scenario, **not production promotion or visual acceptance**.
The prior commit-only turn made progress: `df0312050` built the guarded startup
path. This work supplies the source-matched descriptor and actual game evidence.

## What now runs together

`prepare_south_fork_joint_preview.py` validates 3,255 local dependencies: the
original-return cap and retained terrain, all hydraulic cores, 799 streaming
packets, their bed/mask arrays, the shared atlas, snapshot/bank/coverage audits,
the imported mesh, retained material and its parent, and native collision proof.
It verifies that every packet references the same actual atlas, and that each
audited h/u/v array belongs to that snapshot and flow input. The initial center
must be inside its verified continuous coverage rectangle.

Native preflight independently binds the flow input to the geometry manifest,
all three snapshot arrays to the atlas, and the initial packet's real loader
reference to that exact atlas. It validates hashes before modifying the water
configuration or spawning the transient source solid. This prevents a valid
old packet from passing simply because its loader succeeds.

The existing `L_SouthForkAmerican_FullReach`, scenario `south_fork_full_descent`,
normal raft/controller, and normal carrier/volume-core **single surface** run
together. The source solid uses the unchanged world-projected ground material,
without vertex displacement, a second visual mesh, or moving original returns.
No saved level, production material, default scenario selection, or profile is
changed. Troublemaker remains a rapid within South Fork, not a menu scenario.

The source roof still uses class-1 unclassified LiDAR returns. Their positions
are captured evidence; interpreting them as rock is inference. The closed
solid's sides are inferred. This run does not remove either uncertainty or the
two retained vertical tangent-ray misses from the earlier isolated audit.

## Reproducible local launch

Final descriptor: `tmp/south-fork-joint-preview-50s-v2-20260915.json`, SHA-256
`3ce74403faca8f384920446883322694bd49113020ccf36a1ec8bf26d8ce7c26`.
It binds the 50 s export `tmp/south-fork-rock-union-runtime-50s-v1-20260915`,
geometry `tmp/south-fork-rock-union-geometry-v2-20260915/manifest.json`, cold
input `tmp/south-fork-rock-union-cold-input-v1-20260915/manifest.json`, and
the 50 s snapshot/bank reports. The native collision evidence remains
`unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json`.
Initial packet is `region_0191`, center `[-5437.499999998952, 3646.5]` m.

The source cap SHA is
`4d55ef0243fdef836121b2eb38ab1446a41214927d7d207097fd32d8a4dfe67a`.
The actual atlas SHA is
`4f61bfb4e529d1fda0437fc4ad79c43b7c510450e60423b71b685ed41a687a3e`.
All 406,823 original captured-water probes remain covered with at least 10 m
raft interior margin, exceeding the unchanged 8 m requirement.

After regenerating those local dependencies, use a fresh label:

```powershell
& unreal/Scripts/run_south_fork_joint_preview.ps1 `
  -Manifest tmp/south-fork-joint-preview-50s-v2-20260915.json `
  -Label my-joint-preview -Camera source
```

The launcher always uses an ephemeral editor game, 1280x720 D3D12, a 12 s
warmup, three stills and a recording. `source`, `shore`, and `fixed` are review
cameras only. It refuses to overwrite existing evidence. Generated assets,
simulation files, captures and reports remain covered by the existing ignore
rules; no new `.gitignore` exception or generated-file commit is necessary.

## Actual engine captures and reference inspection

All original `_001` stills were inspected, including the final rebuilt source
view. The fixed-view decoded 5 s frame was also inspected. Full clips were
decoded to the end; this is not a claim of continuously watching every frame.

| Capture label | Camera | Source frames / duration | Decoded frames |
| --- | --- | --- | --- |
| `joint-preview-shore-50s-v1-20260915` | Raft-relative shore-left | 55 / 6.254 s | 188 |
| `joint-preview-fixed-50s-v1-20260915` | Fixed chainage 8350 m, facing upstream | 55 / 6.357 s | 191 |
| `joint-preview-source-50s-v1-20260915` | Source-centered explicit pose | 60 / 6.264 s | 188 |
| `joint-preview-source-50s-v2-20260915` | Same explicit pose, rebuilt preflight | 57 / 6.281 s | 188 |

Logs are `tmp/<label>.log`; original PNGs are in `unreal/Saved/Screenshots`.
Complete decoding reports and unmodified extracted frames are in
`tmp/joint-preview-motion-50s-v{1,2}-20260915`. Inherited ROI names do not label
the same physical regions in these different cameras and must not be used as
registered comparisons. Each capture audit proves three different PNGs and
zero camera displacement/rotation during its own series. Screenshot I/O and
the concurrent cook perturb timing: 30 Hz encoding is **not 30 FPS gameplay**.

Final v2 `_001.png` SHA-256:
`17c799bfb7a237a80dd2d9f20a0f8d3b520279cfead63cf06d8f117310cdf05f`.
Its explicit pose is `[-545095,-362309,1800]` cm, pitch -27.8, yaw 18.075
degrees, FOV 90. This places the candidate source rock clearly in the frame;
the earlier fixed/shore views place much of it near or outside the frame edge.
The pose is a review choice, not calibrated registration to the reference.

The [Qweniden bank-side reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
was accessible again in a read-only browser. Paused 0:10 and 0:15 were inspected
without downloading or uploading media. Real water has local irregular tongues,
exposed angular boundaries and dark gaps between aerated patches. The game
still has broad merged white regions and large smooth faces. Its source rock
has abrupt inferred sides, and adjacent terrain remains too rounded/unresolved.
The raft changes position during the recording, but this does not establish
correct contact forces, full traversal, crew realism, or photographic fidelity.

## Failure reporting and validation

A deliberately wrong initial packet from the prior one-second export was
hashed correctly but referred to a different atlas. Native preflight rejected
it before BeginPlay: no candidate install, water startup or screenshot.
The first shell expectation of exit code 1 FAILED: on this Windows UE build,
`RequestExitWithStatus(false,1)` during initialization still returns process 0.
That result is retained in `tmp/joint-preview-wrong-packet-v1-20260915.log`.

The launcher therefore checks positive installation, matching cap/time, normal
single-surface startup, finalized recording and all three screenshots, not just
the engine exit status. The repeated wrong-packet run exits the launcher with
failure and records `runtime_capture_completed=false`, engine code 0, refusal
true, and zero installs/screens. Evidence:
`tmp/joint-preview-wrong-packet-v2-20260915-run.json`. Normal engine cleanup is
preserved; there is no forced termination or relaxed geometry/physics gate.
The final successful launcher run is
`tmp/joint-preview-launcher-source-v1-20260915-run.json`: exactly one matching
installation, normal single surface, finalized recording and three screenshots.

Final editor build PASS. Focused Python suite: 54 PASS, including dependency,
cross-snapshot, exact-dry-bank, original coverage and source-union checks.
Report: `tmp/south-fork-joint-preview-final-tests-v1-20260915.xml`.
Final native suite: four PASS, zero failed/not-run/in-process, including preview,
session, downstream-progress and camera contracts. Report:
`tmp/joint-preview-final-native-tests-20260915/index.json`.
All 464 protected source/actor hashes remain unchanged. All owned short preview,
build and test jobs are terminal; only the explicitly retained cook stays live.
Installed experimental editor-tool Python errors for missing `AgentSkill` and
`PythonTestRunner` recur in game mode and also occur in the earlier baseline
log; these are retained, not misreported as a warning-free run.

## Hydraulic progress and next work

The SAME 600 s simulation remains live: session45187 / PID32276, output
`tmp/south-fork-rock-union-cook600s-v1-20260915`. No restart. Complete 100 s
and 150 s snapshots and independent artificial-bank audits pass. At 150 s:
max depth 3.952322866 m, max speed 12.168753620 m/s, max step mass residual
1.247425e-8 m3, and all 86,720 artificial bank-face cells exactly dry.
Inlet 45.306954547 m3/s versus outlet 25.204575995 m3/s is NOT settled.
Reports: `tmp/south-fork-rock-union-{100,150}s-{snapshot,banks}-v1-20260915.json`.
Latest observed live progress was step3480 / 174 s; next full checkpoint 200 s.
Re-poll the actual handle/process and audit complete checkpoints, never restart
on an observation timeout.

Next: examine original-return support at the cap boundary before revising its
abrupt inferred sides; finish settled joint hydraulics and verified raft
contact/traversal; resolve smooth crest/breaking shape and blanket-like froth
in the actual single surface. Do not claim that this 50 s preview is settled.
No fresh uncontended FPS acceptance: the last ordinary 24.225877 FPS / p95
47.78 ms still FAILS 30 FPS / 33.333333 ms. Colorado -> Pacuare -> Futaleufu,
Chilko/Zambezi and remaining water reviews, crew, normalization, the 13 physics
and four presentation regressions, and release checks remain OPEN.
