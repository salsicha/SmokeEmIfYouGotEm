# Native water combination — September 13, 2026

The desktop target remains 30 FPS, p95 33.333 ms, with the unchanged 1.6 ms
native water-step and 8192 MB memory budgets. The prior full-scene run still
fails: 12.611023 FPS, p95 87.8737 ms; native gate average water step 4.314730 ms.

## Measured native work and bounded change

The adapter's water timer encloses the native step and clock checks, not texture
export or upload. Production Cartesian crops use uncalibrated second-order
MUSCL/HLL with two explicit ghost layers. They do not use the legacy first-order
configuration. No timestep, CFL, grid, tolerance, damping formula or boundary
condition changes are part of this optimization.

A fresh opt-in stage-profile build of the current native sources replays the
existing registered 271x161 survey package for 600 steps at 1/60 second. This is
an isolated executable using the recorded inputs, **not** the ordinary moving
FullReach window or a full-game performance claim. The background cook continues.
Initial baseline: 3447.0581 ms total native time, including 461.1839 ms combination
and Manning friction (13.38%). Reconstruction remains the largest stage.

`finish_finite_volume_second_order_step` now dispatches independent rows of the
combination/friction pass through the existing bounded executor at the existing
16384-cell threshold. Each cell retains the same arithmetic, dry-film handling
and floating-point environment. No neighbour reads, reductions or new worker
pool are introduced. Feature forcing and derived-state recomputation remain
after the joined pass, unchanged. Nested execution remains serial.

Initial candidate: 3145.9524 ms total /168.4162 ms combination, against the same
600 steps. That is about 8.74% less total native time in this first pair, not a
whole-frame FPS improvement. Four alternating-order pairs are now complete.
Both complete frame CSVs and all three probe CSVs are byte-identical; the final
43631-cell frame, including all state and derived fields, has SHA256
`7934382caa29e210eda346212eb82c8b838a620c6736bd74cd34aedcf5541109`.

Repeated audit48934 CLOSED0, all eight replays have identical frame/probe exports:
`tmp/south-fork-native-combine-pairs-v1-20260913/report.json`.
Mean total step5.762928375ms baseline versus5.636756917ms candidate (~2.19% less);
one of four candidate total-step timings is slower. Mean combination/friction
0.766819625ms versus0.309317667ms (~59.66% less), faster in every pair. Thus the
first pair's8.74% total improvement is NOT sustained by the repeated results.
The known background cook stayed running; no engine or build ran concurrently.
This supports the narrower component improvement and exact outputs, not a
guaranteed total-step speedup or a full-game performance pass.

Native tests expand the existing parallel-versus-nested-serial comparison to
three roughness values, all three flux schemes, both bed-source modes, wet/dry
films, state replacements and a CFL-subdivided call. Exact arrays and clocks
are required after every call. CTest47104 CLOSED0: all four suites pass in9.39s.
Candidate executable/build: `tmp/south-fork-native-combine-v1-20260913`;
baseline: `tmp/south-fork-native-stages-v1-20260913`. Diagnostic profile timers
remain compile-time disabled in the production archive.

## Playable integration verification

The prior production archive is preserved at
`tmp/native-archive-before-combine-20260913.lib`, SHA256
`e69772d2c856054f6bb37035486e6828c47d3ee3eebdbf9b0261dec6fb9a678c`.
Native archive build89006 CLOSED0; new production SHA256
`b828162b849756b1c15bb1a78fc277e4fd1cec6028b2736597b3b343f2c5ec8e`.
Unreal build62522 CLOSED0: all177 actions succeed in1637.33s. The same two
pre-existing D6 damping-conversion warnings remain. Water DLL SHA256:
`8dc912e0381b944888a3011b912b65d57a45ec2496730fb8297694af19d8a23e`;
Raft DLL SHA256:
`d24dd7ffd031588e615e87b067276e9b692ba5756c3c93b2195d043c8fd45ae2`.
Repeated native replay, engine regression tests, ordinary capture and native
performance gate results follow below. They do not establish a30FPS pass or
visual acceptance.

Engine launch initially did not start because automatic approval review timed
out; one identical retry succeeded. Native29734 CLOSED0:85 clean passes,
zero warnings/failures/unrun,20.932566s. All six existing GPU fixtures supplied
unchanged, real D3D12 renderer. Report:
`tmp/south-fork-native-combine-tests-v1-20260913/index.json`.
The startup log explicitly records the new production archive hash above.
Ordinary FullReach capture14575 CLOSED0, game exit0, no timeout, cook suspend0/
resume0. No diagnostic opt-ins; unchanged1280x720, D3D12, target30 metadata.
CSV rows60–240: **17.724105FPS, p9573.6027ms — FAIL30FPS**. CSV SHA256:
`5b89665eceb8cd357bb37ad49b1a251f61076c539dd3431b58bd0d0b3f59bbb1`.
Report: `tmp/south-fork-native-combine-frame-v1-20260913.json`.
Surface34.408446ms, refresh12.552583ms, publish20.660701ms, crest13.840876ms,
selection6.883087ms, water-step calls13.188771ms per frame. All are inclusive/
nested scopes; do not add them. Refresh/foam/breaking work occurs on108/181 rows,
and selection on110/181, unlike the prior slower capture's every-frame refresh.
Selection's active-row mean is11.325807ms. Settings/cadence policy were not
changed, but actual refresh cadence and trajectories differ; **do not attribute
the whole17.72 versus12.61FPS difference to this solver pass alone**.

Those181 rows contain677 successful fixed ticks, zero failures. Backlog starts
1.0956s, peaks1.2575s and ends0.01623s; native and bridge committed clocks agree
at CSV precision. Six detail-window remaps and zero teleports. At shutdown,
foam33.750001760s and detail33.816668430s each match their own target; the world
clock is34.080346320s. These are not a proof of all-source/material/physics
temporal alignment. The foam observation remains0.066667s behind detail here.

Native gate93893 CLOSED1 for the expected failed report, game exit0, no timeout,
cook suspend0/resume0. Actual v4 report:
`unreal/Saved/RaftSimValidation/south-fork-native-combine-gate-v1-20260913-gate.json`.
422 frames, workload p95 **53.357399ms** and wall p9553.738102ms against33.333333ms;
4 hitches above66.666664ms. Average FV **3.487379ms**, max9.260103ms, against1.6ms:
FAIL. Peak physical **3949.367188MB** against8192MB: PASS. No invalid GPU timings;
map/profile checks pass. Screen percentage87 and all quality levels2 are
unchanged. Offscreen Development evidence is ineligible for packaged release
qualification. The overall gate remainsfalse.

Inspected the actual screenshot:
`unreal/Saved/Screenshots/south-fork-native-combine-default-v1-20260913.png`, SHA256
`96323e279647ba356a227507515bc60a27bf117d32af8838b8d1552d9a63cc56`.
Broad glossy folds and blanket-like foam still dominate; terrain/trees and crew
remain unfinished. No visual or motion-reference acceptance. The normal map,
water material and save retain their pre-run hashes. The optimization is in the
normal runtime, not an offline-only feature, but it does not finish this scene.

During the rebuild, the original live cook reached4600s/local12000. Both
independent snapshot and artificial-bank audits pass:5,382,400 finite cells,
86,720 exactly dry artificial-bank cells, maximum step residual1.413489015e-8m3.
Outlet108.331975333 versus inlet45.306954547m3/s still shows settling. This is
not evidence for promoting that flow state. The runtime600s source and original
cook executable are unchanged; next4700/local14000 needs both audits.

A read-only follow-up checked the full-domain path while waiting for compilation:
it already dispatches tiles in parallel at both RK stages and combination, with
ghost-exchange barriers and ordered boundary-volume summation. The4600s snapshot
has841 tiles, only14 entirely at zero depth, and1,750,427 positive-depth cells.
Adding whole-dry-tile scheduling is therefore not the next optimization priority;
no domain or live-cook change was made. The prior ordinary game's inclusive
surface cost51.242286ms (refresh22.261641/publish27.729598ms) remains the larger
playable bottleneck. These scopes are nested and must not be added again.

At14:10 UTC another reference retry failed: both YouTube links return cache
misses; browser and computer-use runtimes fail before navigation with
`failed to write kernel assets: The system cannot find the path specified.
(os error 3)`. No reference video frames were viewed, no settings were changed,
and no media was downloaded. The computer-use skill's prescribed entry points
were used; this blocks footage inspection, not the remaining engineering work.
