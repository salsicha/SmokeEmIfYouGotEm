# Exact water vertex memory path — September 12

This is CPU-cost work on the playable South Fork map, not visual or release
acceptance. Troublemaker remains a rapid within South Fork, never a menu entry.

Fresh instrumented baseline `south-fork-crest-cost-baseline-v1-20260912`
completed normally (session4010, exit0); the exact cook was suspended/resumed
successfully. Stage logs put normals below1ms in sampled frames, versus roughly
3ms source packing and10ms adaptive selection on rebuild frames. Do not sum
nested stages or confuse instrumented logging with a clean release profile.

The change removes default construction immediately before every member is
overwritten in source packing and fine-crest output. Three full source-prefix
copies now use bulk copying. Compile-time checks require the engine vertex to
remain trivially copyable/destructible. No vertex, triangle, field, normal,
color conversion, UV channel, update, tolerance or physical formula is removed
or changed. Source packing still assigns every field before any read; crest
midpoints still follow the same sequential interpolation and correction.

Build `south-fork-vertex-memory-build-v1-20260912.log` succeeds in79.15s
(session49360 exit0). Raft DLL SHA256:
`01e7d6ef0098193cfba82b5fef4f0449ea610f92f31c7dd9aa3c143eda84f1ad`.
The already-pending editor comment correction was compiled too.

Native/D3D12 session18464 exits0:37 successes, zero warnings/failures/unrun.
Report `unreal/Saved/RaftSimValidation/south-fork-vertex-memory-regressions-v1-20260912/index.json`.
Expanded packing regression covers fresh/reused/poisoned buffers, shrink,
empty/regrowth, both serial/parallel paths, every field, exact bulk copies and
untouched suffix storage. Existing fine-crest, shoreline moving-bank,
compact-upload, coordinate, transport, menu and save-migration checks pass.

The first post-change profile (v1, session78707) exits0 and resumes the cook,
but overlaps checkpoint-input preparation. Retain it as contaminated evidence;
do not use it to establish an isolated speedup. Fresh v2 session79193 exits0
without concurrent preparation; exact cook suspend/resume0, no timeout.

Strict completed300-row CSV audit (samples100–250) is
`tmp/south-fork-vertex-memory-performance-v2-20260912.json`. Current CSV SHA256
`f534c9ca97aceb0c10a69dad27c9f1123e1ba64f748b522d0c7c2064e198cce2`.
Development/D3D12/WindowsEditor1280x720, RT off: mean43.233230ms,
p9554.2083ms,23.130356FPS. Prior current-build capture:44.824275ms,
p9553.2544ms,22.309340FPS. Packing2.958503→2.443845ms,
topology3.679140→2.820183ms, inclusive publish18.692862→16.732585ms.
Observed mean is lower, but p95 is worse and STILL FAILS60FPS. Short variable
trajectories are not a controlled sustained or packaged performance claim.

Actual normal-game session86525 exits0. Audit
`tmp/south-fork-vertex-memory-transport-v1-20260912.json`:50,625source vertices,
complete prefix, UV3/CPU transport error0m/s and bulk UV1 error0m/s.
Crest audit `tmp/south-fork-vertex-memory-crest-v1-20260912.json.cartesian-mesh.json`:
712,224 samples, max1.418517685cm<=unchanged2cm, source position change0,
fine correction tracking0.000573158cm. Existing macro-lag/other-relief/GPU
exclusions remain; this is not whole shaded geometry or contact acceptance.

Frames000/039 inspected: broad white cores, upstream dark banding and smooth
breaking shape remain unaccepted. No visual improvement claimed from memory
copies.40uniquePNG/11.626s sampled game, fixed camera; motion audit
`tmp/south-fork-vertex-memory-motion-audit-v1-20260912.json`. Actual movie
`unreal/Saved/VideoCaptures/RaftSim_20260912-143134.mp4`, SHA256
`04127159e00bea451109912540f91ae4c70ccdac50ad4137bb643fb57361881d`.
No continuous-reference viewing or encoder-cadence FPS claim.
Mapdb3080cc… and material094123c7… rehash unchanged; main DLL40f149a1… unchanged.

Visual shape/froth, physical reference motion, frame-time acceptance, full-river
traversal/scenery and every later river/crew/release/commit remain unfinished.
