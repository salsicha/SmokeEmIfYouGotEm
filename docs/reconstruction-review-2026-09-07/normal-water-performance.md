# Normal South Fork water cost and crest audit — September 12

Latest: [exact vertex-memory optimization](normal-river-vertex-memory.md).
37 native tests pass; actual source/transport/crest audits pass their unchanged
gates. Clean current-map mean43.233230ms/23.130356FPS,p9554.2083ms STILL FAIL60.
Packing/topology costs lower, no sustained speedup or visual acceptance claimed.
Current RaftDLL01e7d6ef…, main40f149a1…, material094123c7…, mapdb3080cc….
First post-change profile overlapped input preparation; onlyv2 is isolated.

September12 local-shading follow-up: [current one-second froth/normal profile](normal-river-local-shading.md)
uses material3733e083…, same RaftDLLe3e11f6b… and mapdb3080cc….
Strict completed300-row profile: mean44.902754ms, p9557.6281ms,
22.270349FPS FAIL60; GPU12.708109ms. No sustained or causal speedup claim.
Exact cook suspend/resume0 and gameexit0; actual crest error1.427381505cm
passesunchanged2cm. Earlier current-map timings below are historical variants.

September12 20:29UTC: [current-map baseline and exact moving-bank cache](normal-river-moving-bank-cache.md).
36 native/D3D12 tests pass, including 4,608 fresh-build shoreline comparisons.
Current terrain/canopy/local froth included. Topology mean4.850439→3.743277ms,
but whole-frame45.679583→46.704141ms,21.891618→21.411378FPS: STILL FAIL60.
No whole-frame speedup claimed. Strict completed300-row CSV audits pass;
both isolated captures resume the same cook successfully. Actual screenshots
inspected, uniform/stretched froth still rejected. No gates reduced.
Current RaftDLLe3e11f6b…, map/material/profile unchanged. Details in linked note.

September12 18:43UTC: actual post-alignment crest v9 passes2cm (1.428008269cm,
712,296 samples, unchanged original vertices). Actual normal-map capture and
guided run are recorded in [contact/source evidence](normal-river-contact-and-source.md).
Guidance still fails; earlier timing measurements do not accept the current map.

September 12 18:36 UTC: [contact and geometry-source integration changed](normal-river-contact-and-source.md).
The normal river now binds the recovered-return/inferred-flank mesh already
used by hydraulics; terrain contact follows newly streamed ground. Earlier
timings below predate these changes and are not current-map acceptance.
34 native tests pass; actual post-swap capture and traversal checks are next.

## Latest: serial default rebuilt and verified (18:15 UTC)

The stalled build 31438 exited 1 through its own session control; PIDs 25028
and 11604 then disappeared. No river solver was stopped. Retry
`south-fork-source-pack-default-serial-build-v2-20260912.log` succeeds in
52.33 s. `south-fork-source-pack-default-serial-v1-20260912/index.json`
reports 33 successes, zero warnings/failures/unrun. Raft DLL SHA256
`c4c53a71eea12f6ecaf8297900b1638e9ee22f8ac8c8385a0b633950be226063`.
Serial is now the built default; parallel remains a diagnostic CLI opt-in.

Same-binary comparison, required eight scopes plus all four publish scopes:
`tmp/south-fork-same-binary-packing-comparison-v1-20260912.json`.
Serial CSV v3 mean 46.6654951 ms, p95 58.7264 ms, 21.4291094 FPS;
parallel CSV v2 mean 72.6203148 ms, p95 85.6899 ms, 13.7702515 FPS.
Packing means 3.3467246 versus 4.5963738 ms. Both fail 60 FPS. Other
scopes also vary materially, so do not attribute the whole frame difference
to this change or call the short editor captures sustained acceptance.
All isolated captures resumed the same owned cook with status 0.

Serial CSV v2 was rejected because `ShadowCacheUsageMB` and
`LightCount/UpdatedShadowMaps` each occurred twice. The strict parser was
not weakened; v3 repeats the identical command/configuration, with no
counter edits or gameplay changes. Rejected file retained, no report issued.
Parallel v2 and serial v3 both passed the strict original header checks.

Normal capture v8 telemetry at world ~10 s records one grounded and one dry
support, zero reported penetration, roll -14.79 degrees. This corroborates
contact but does not prove the spawn is invalid: the raft had already moved.
Existing survey guided traversal assumes isolated local coordinates, one ground
mesh and a legacy water carrier. A separate normal-map 120 m/120 s guided
segment test is being built to measure actual full-map behavior without
teleports/manual physics. It uses the real run-progress coordinate adapter,
ordinary crew/guide APIs and captured-ground queries across loaded actors.
It is a provisional centerline diagnostic, not a surveyed safe route or
full-river acceptance. No terrain/collision/water fudge has been applied.

## Latest: same-frame profiling; parallel packing not promoted (18:01 UTC)

The normal river, not an isolated rapid scenario, now records optional CSV
surface, crest and solver scopes. The strict parser requires all eight water
scopes when requested, distinguishes missing measurements from recorded zero,
and rejects duplicate headers. Five CSV and three stage-parser tests pass.
UE writes `Category/GameThread/Stat`; actor `Ticks` columns are counts, not ms.
Capture v1 contained a duplicate unrelated FMsgLogf counter and was rejected;
v2 explicitly disables only that logging counter before capture.

Valid baseline `south-fork-full-frame-isolated-scopes-v2-20260912.csv`:
61 samples, frames 30–90, mean 43.5345 ms, p95 49.9199 ms, 22.9703 FPS.
Same-frame inclusive means: surface 32.7118 ms, Cartesian publish 18.7618 ms,
crest update 8.9464 ms, solver 4.3185 ms. Nested scopes must not be summed.
Audit: `tmp/south-fork-isolated-water-scopes-v2-20260912.json`.

A complete-vertex parallel packing experiment is bit-exact in both geographic
orientations, serial/parallel modes and every vertex channel; malformed input
preserves the output. Duplicate input validation was removed only inside the
private shoreline builder; both public entry paths still validate first.
Build `south-fork-parallel-source-pack-build-v1-20260912.log` exits 0 (78.14 s).
Report `south-fork-parallel-source-pack-v1-20260912/index.json`: 33 successes,
zero warnings/failures/unrun, including CareerCatalog and ProgressionMigration.

However, isolated `south-fork-full-frame-isolated-source-pack-v1-20260912.csv`
is slower: mean 48.6198 ms, p95 56.0039 ms, 20.5677 FPS. Packing costs 4.4259 ms,
shoreline topology 5.8135 ms and crest input 0.4294 ms. This is NOT a speedup
or acceptance; host variation prevents attributing all differences to packing.
Comparison: `tmp/south-fork-isolated-source-pack-frame-comparison-v1-20260912.json`.
Serial packing is restored as the source default; parallel packing requires
`-RaftSimParallelSourcePacking` for same-binary experiments. Rebuild and final
verification of this default change are pending below, not assumed complete.

Final-default build session 31438 (`south-fork-source-pack-default-serial-build-v1-20260912.log`)
is stalled before compilation, parent dotnet PID 25028, start 18:00:04 UTC,
child PID 11604 verified by parent identity. A scoped elevated stop attempt
failed with OS access denied on the child; the parent was consequently not
stopped either. Do not launch a duplicate build or infer that the new source
default is in the existing binary. No river solver process was touched.
Both parser suites were rerun: eight successes; scoped diff check passes.

Actual normal-map crest v8 (`south-fork-normal-rapid-crest-v8-20260912.json.cartesian-mesh.json`):
712,296 samples, maximum 1.428123217 cm against unchanged 2 cm gate,
zero original-vertex change. 53,920 active vertices, 61,440 buffer vertices,
22,694 triangles. This excludes other relief and full shaded motion acceptance.
The corresponding actual screenshot was inspected: waves/froth are visible,
but bare scenery, abrupt rock cuts and apparent raft/rock contact remain.
A still image does not prove convincing foam motion or natural traversal.
South Fork remains the scenario; Troublemaker has no menu entry.

## Latest: exact batch-local crest cache (17:32 UTC)

Adaptive crest selection now optionally memoizes exact coordinate/profile
queries in independent 128-triangle batch tables. Each parallel batch owns its
table exclusively; resizing occurs only between joined refinement levels.
Tables survive only this one immutable profile build. The serial caller-owned
cache and uncached parallel mode remain available. Production clipped crests
use the batch cache without changing selection tolerance, refinement levels,
midpoint order, triangle order or source fields. Tests prove exact fresh-serial
topology in both orientations, including moved coordinates, and fewer repeated
profile evaluations. Changed-profile tests retain no stale crest geometry.

Build `south-fork-batch-crest-cache-build-v1-20260912.log` exits 0 (237.29 s).
Two existing double-to-float damping warnings in `RaftSimD6ChaosMeasuredRunner.cpp`
were emitted while rebuilding that unrelated module; no claim of warning-free
compilation. Native/D3D12 report
`unreal/Saved/RaftSimValidation/south-fork-batch-crest-cache-v1-20260912/index.json`
has 32 successes, no test warnings/failures/unrun. Scoped whitespace checks pass.
Actual compile response settings are `/Ox /Ot /Ob2 /fp:precise`, not `/Od`;
do not dismiss the measured performance gap as unoptimized debug code.

Separate uninstrumented, isolated 100-frame CSV (samples 30–90): mean 45.8457
to 43.5961 ms, p95 54.8785 to 51.5630 ms, game-thread mean 45.7333 to 43.3083 ms,
render-thread mean 10.8777 to 10.4943 ms, GPU mean 12.4480 to 12.2564 ms.
FPS 21.8123 to 22.9379. Modest short-run progress, still FAILS 60 FPS and is
not sustained/packaged/visual acceptance. Comparison
`tmp/south-fork-isolated-batch-crest-frame-comparison-v1-20260912.json`, SHA256
`a2054f393001a40b8b709abe942eba6a27cf63363a79438af54500caab6f200e`.
Current RaftSimRaft DLL SHA256
`1d4e3e29bd10efefed7cd86d7f8c8dfe8ec615c2a625ff2025bd9a12223af386`.

Actual normal-map crest V7 at 10.02936 world s has 53,919 active CPU vertices,
61,440 render reserve, 22,692 triangles and 712,224 independent samples.
Maximum target error 1.418609870 cm passes the unchanged 2 cm gate, with zero
original-vertex change and 0.001118422 cm correction-tracking error. Audit
`unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v7-20260912.json.cartesian-mesh.json`,
SHA256 `15b10fedd2541b62033f2b5fd9243df9971fd2179a1ad22c1f2eec5328de0fbe`.
The actual CSV screenshot was inspected; scenery and raft/rock contact issues
remain, and this is still not a natural traversal or shaded-motion acceptance.

Instrumented V12 median actor tick 28.3012 ms versus V11 61.7885 ms is not a
claim of equivalent whole-frame speedup: 15 versus 28 refreshes occur in the
selected 31 frames, with different frame/world-time trajectories. V12 early
selection is commonly 9–10 ms. Report
`tmp/south-fork-isolated-batch-crest-stages-v1-20260912.json`. Next performance
work should collect same-frame CSV water/crest/solver scopes to separate the
remaining costs without relying on differently paced stage-log captures.
All engine jobs are terminal. Map/profile/source/materials remain unchanged.
The superseded flow cook was replaced only after exact pilot and native
replacement proofs; see the expanded-checkpoint record for the new live handle.

## Latest: compact CPU shoreline preserves actual fine geometry (17:12 UTC)

The fine-crest path no longer carries two unused edge-reserve grids through
CPU refinement. Original grid vertices/indices remain unchanged. Canonical
horizontal/vertical lattice slots still identify shared bank edges, but only
encountered edges receive a dense CPU suffix. The fixed-reserve default remains
available and unchanged for non-crest callers and independent comparisons.
Exact cache identity includes the storage mode, masks, XY and bank crossings;
newly active edges are always written. No coordinate welding, reduced resolution,
changed shore convention, hidden surface or relaxed crest threshold.

Build `south-fork-compact-cpu-shore-build-v1-20260912.log` exits 0 in 83.46 s.
Final report `unreal/Saved/RaftSimValidation/south-fork-compact-cpu-shore-v1-20260912/index.json`:
32 successes, no warnings/failures/unrun. Expanded tests compare compact cached
edges against independent fixed-reserve geometry through moving crossings,
missing coverage, changing channels, translated/rotated coordinates and dry/rewet
states. Every drawn corner and all attributes are exact. Independent old-reserve
versus actual compact fine refinement also preserves every triangle corner,
normal/tangent, color, four UVs and cell owner exactly in both Y orientations.
Actual D3D12 raster tests now exercise both storage modes: full/dry/island/cached
height/full counts remain 1936/0/1692/1692/1936, underside 0. Six Python parser
regressions and scoped whitespace checks pass.

Actual normal-map crest V6 at 10.00237 world s: 50,625 original vertices,
53,917 active CPU vertices (previously about 153,295), 61,440 render reserve
(previously 172,032), 22,688 triangles. Over 712,080 independent samples,
maximum crest-target error 1.421023522 cm passes the unchanged 2 cm gate;
original-vertex change 0, fine-correction tracking error 0.001130342 cm.
Audit `unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v6-20260912.json.cartesian-mesh.json`,
SHA256 `c6c47baad915323bdcb58809cebbcf2e14375837bd296d79281cd44a2075a074`.
The historical `active_vertices_including_shore_reserve` JSON field now counts
the compact active CPU array, not the separate render-buffer reserve.

### Separate isolated whole-frame measurement

Both captures pause only the same identity-verified owned cook, automatically
resume it in finally, and use the same controls and samples 30–90 described
below. No stage timing or crest audit is enabled in either CSV capture.

| Metric | Before CPU edge compaction | Compact CPU edges |
|---|---:|---:|
| Frame mean, ms | 53.1846 | 45.8457 |
| Frame p95, ms | 68.9392 | 54.8785 |
| Game-thread mean, ms | 52.9720 | 45.7333 |
| Render-thread mean, ms | 10.5309 | 10.8777 |
| GPU mean, ms | 13.2785 | 12.4480 |
| FPS from frame time | 18.8024 | 21.8123 |

This is a short sequential comparison, not sustained/packaged acceptance or
proof against thermal/other host-load variation. Still FAILS 60 FPS. Comparison
`tmp/south-fork-isolated-cpu-shore-frame-comparison-v1-20260912.json`, SHA256
`3a31373ce5cfc881b53d4f7e0810597e8cb127bf981a1559dcd26e7e9a8355ed`.
Current DLL SHA256 `28da3b61c129ee5d1730d184b3e2729595af9a3f7f82dd3f08d0d5009c437cac`.
Screenshot `unreal/Saved/Screenshots/south-fork-full-frame-isolated-cpu-shore-v1-20260912.png`
was inspected: continuous water/crests/froth visible; bare scenery, abrupt rock
cuts and apparent raft/rock contact remain unaccepted. Not natural traversal.

Separate instrumented V10/V11 actor runs are NOT evidence of further total
actor improvement: median 34.8485 versus 61.7885 ms in frames 30–60, with 15
versus 28 refreshes in those 31 frames. Different frame trajectories cross the
unchanged 1/15 s refresh interval differently. V11 also has a crest audit after
10 world s, outside this early timing interval. Do not add nested stage times
or conflate these runs with the uninstrumented CSV. Report:
`tmp/south-fork-isolated-cpu-shore-stages-v1-20260912.json`. Remaining source,
clipping/refinement and refresh cost still needs controlled optimization.
All build/editor/capture jobs are terminal; the same cook resumed successfully
and CPU advancement was checked. Map/profile hashes remain unchanged.

## Latest: exact parallel source sampling and isolated load check (16:59 UTC)

Cartesian curved-coordinate live/immutable-atlas samples and final source
handover now run per vertex in parallel, with joins before consumers. Legacy
and world-coordinate paths remain serial. Source values, dry masks, missing
source handling, terrain-probe requests and feathering formulas are unchanged.
The native source test compares 11,881 serial/concurrent live and baseline
queries exactly. The opt-in actual-game source audit independently reruns both
phases serially against the same state, compares all outputs, and restores the
parallel result before rendering. It is not a full-water or visual audit.

Final build `south-fork-parallel-source-build-v2-20260912.log` exits 0 (36.74 s).
`unreal/Saved/RaftSimValidation/south-fork-parallel-source-v1-20260912/index.json`
reports 32 successes, no warnings/failures/unrun. Actual source audit
`south-fork-normal-source-equality-v1-20260912.json` passes at 10.11465 world s:
50,625 samples, zero different samples, all masks/probes/feathers/heights exact.
SHA256 `9f4cea33561dbcba854a03e1cc083b76d7bfa9916a89e40cbb0169afcf00f129`.
Actual crest audit `south-fork-normal-rapid-crest-v5-20260912.json.cartesian-mesh.json`
passes the unchanged 2 cm target: maximum 1.420575895 cm over 712,080 samples,
zero original-source vertex changes. Correction tracking error 0.001016617 cm.
This still excludes macro temporal lag, other relief and GPU perturbations.

The separate loaded-machine full-frame run changes mean 95.3576 to 92.7781 ms
and p95 115.1640 to 111.5175 ms. Do not overstate that small measured gain.
To distinguish implementation cost from offline-cook contention, a second run
temporarily suspended only the owned cook PID 37616 after exact executable and
start-time checks. A finally block resumed the same process successfully;
subsequent CPU advancement confirmed continuation, without a restart.

| Metric | Source-parallel, cook active | Same binary, cook paused |
|---|---:|---:|
| Frame mean, ms | 92.7781 | 53.1846 |
| Frame p95, ms | 111.5175 | 68.9392 |
| Game-thread mean, ms | 92.7886 | 52.9720 |
| Render-thread mean, ms | 14.0678 | 10.5309 |
| GPU mean, ms | 29.5638 | 13.2785 |
| FPS from frame time | 10.7784 | 18.8024 |

Same 100-frame capture and samples 30–90, normal map/8330 m start, 1280x720,
D3D12, Development and capture controls as below. Runs are short, sequential
and have different time-step trajectories. The difference is a load-isolation
diagnostic, NOT an additional code-speedup claim or sustained/packaged/visual
acceptance. Both still fail the 60 FPS gate. Compare future optimizations with
controlled background load. Current RaftSimRaft DLL SHA256:
`83265a890f71f69e36aa6e5c50163ccfca7f921f9d25018dd7dd5dd1c8e4324a`.
CSV comparison: `tmp/south-fork-isolated-source-frame-comparison-v1-20260912.json`.
CSV names: `south-fork-full-frame-{parallel-source,isolated-source}-v1-20260912.csv`.
The actual source-equality screenshot was inspected: terrain and froth are
visible, but bare scenery, abrupt rock cuts and raft/rock contact remain open.
No natural traversal, convincing moving froth or full river completion claimed.

## Latest: exact parallel selection, compact uploads, full-frame evidence (16:32 UTC)

Two production-path changes preserve the visible geometry rather than reducing
its resolution or relaxing the existing0.5cm selection/2cm acceptance thresholds:

- `FRaftSimSurfaceRefinement` can evaluate independent triangle selections on
  worker threads, then assembles midpoints/triangles/cell owners in original
  serial order. Its parallel mode requires a pure thread-safe height function
  and never accesses the mutable serial memo table. The shoreline actor supplies
  its immutable captured shared support-site profile. Removed the ineffective
  production profile-value cache; the generic serial memoization remains tested.
  Both coordinate signs and moved coordinates match fresh serial topology exactly.
- `RaftSimShorelineMeshComponent.cpp` packs only vertices referenced by the
  actual triangle list. Remapping preserves each corner's converted position,
  normal/tangent handedness, color and all four UV channels; coincident vertices
  with different attributes are not welded. CPU source/clipped/fine geometry and
  anchor indices stay untouched. GPU allocation remains stable through dry/rewet
  changes, while updates copy only the referenced dense prefix. An actual late
  V9 frame uploads12,046 vertices versus172,032 reserved (~93% fewer vertices),
  preserving68,064 indices. No source/scenery/solver/material/map/profile edits.

Parallel build exits0 in235.02s. Compact buildV1 failed a signed/unsigned check;
corrected buildV2 exits0 in18.63s. Final native/D3D12 report
`unreal/Saved/RaftSimValidation/south-fork-compact-water-upload-v1-20260912/index.json`
has32 successes, zero warnings/failures/unrun. Includes exact packet attributes,
coincident-but-distinct vertices, value-only updates, dry/rewet remapping,
persistent proxies, actual raster membership and fine-crest/scenario regressions.
Six Python parser tests pass (three stage-timing, three new full-frame CSV tests).
Scoped diff whitespace checks pass. All build/editor/capture jobs are terminal.

### Separate actual full-frame capture

New `physics/scripts/audit_unreal_frame_csv.py` checks completed CSV structure,
finite measurements and available sample intervals; rejects incomplete/truncated
or concatenated captures and absent metrics. It preserves only relevant capture
metadata and never marks release acceptance. Engine CSV captures100 frames;
statistics below use zero-based CSV samples30–90 inclusive (61 samples), not
engine frame IDs. No per-water-stage timing or crest audit is enabled in these
runs. Same full normal South Fork map,8330m start,1280x720 D3D12, ephemeral profile,
default `CaptureRaft 12` camera/paddling; ray tracing0, WindowsEditor Development.

| Actual metric, ms | Parallel crests/full uploads baseline | Compact uploads |
|---|---:|---:|
| Whole-frame mean |107.4548|95.3576|
| Whole-frame p95 |131.0923|115.1640|
| Game-thread mean |107.2933|95.5189|
| Render-thread mean |37.0259|13.9567|
| GPU mean |33.1435|29.1110|
| FPS from total measured frame time |9.3062|10.4868|

Thread/GPU intervals overlap; never sum them. These short warmed, sequential,
shared-machine runs have varying simulation trajectories. They show measured
progress, **not sustained packaged performance,60FPS, motion, reference or
traversal acceptance**. The unchanged60FPS frame budget is still failed badly.
Baseline binary SHA256
`d24ea6699b2ce06bcb96064faf11d9735d14ed8adcbc34ecaa47168b420e991c`;
compact binary
`2887520a35d367e17150d7ad40799c0ec5f18671b7d470a72cadd7c5a35d1e23`.
CSV files: `unreal/Saved/Profiling/CSV/south-fork-full-frame-{baseline,compact}-v1-20260912.csv`.
Comparison `tmp/south-fork-full-frame-compact-comparison-v1-20260912.json`, SHA256
`bfa1d17145c783cb841467f253ba008d94eeeed110e302427fce93460b8ce674`.

Separate instrumented CPU runs V7→V8 reduce water-actor median108.4131→70.6193ms
(frames30–60), and selection commonly45–69→12–16ms. V9 actor median76.5368ms
does not imply an additional actor-time gain from compact uploads: that upload
work is outside the actor tick, and the trajectories/load differ. Source sampling
still takes~9.8ms/refresh, with substantial interpolation/refinement/solver cost.
Reports `tmp/south-fork-parallel-crest-cost-v1-20260912.json` and
`tmp/south-fork-compact-upload-stage-cost-v1-20260912.json`; raw stage logs V8/V9.

### Final independent crest target check

Normal-map V4 audit exits0: maximum current crest-target error **1.429276756cm**
over712,296 samples, original source-vertex change0,1,873 fine vertices,
22,694 submitted triangles. Fine correction tracking error0.000328481cm.
`unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v4-20260912.json.cartesian-mesh.json`,
SHA256 `8c342bd3fa5bbe800882bc8536012bedafe040150785e83df3b6399aec54f462`.
The target-only scope still excludes macro temporal lag, other relief and GPU
perturbations. ScreenshotV4 was inspected: terrain/froth remain visible, but
sparse scenery and raft/rock interaction remain unaccepted. No visual completion.

NEXT reduce the remaining common CPU source-sampling/interpolation/refinement
cost using current full-frame evidence, then continue actual motion/froth/raft/
reference/traversal checks and scenery completion. No isolated rapid scenario.
The1100s full-river snapshot independently passes state/mass/exact-dry bank gates
but remains unsettled; cook49780/PID32032 is live at1165.5s, next complete1200s.
The map still uses audited600s source data. The full remaining goal stays active.

## Previous checkpoint (16:06 UTC)

Added exact analytic value reuse across geometry-only changes. Values are keyed
by exact world XY, invalidated whenever the complete profile key changes, and
evicted above 262,144 cached entries before another build. Eviction only changes
query cost. Every changed shoreline still rebuilds/refines; no frozen crossings,
rounded profile key or altered amplitude. New tests compare moved-coordinate
selection with a fresh build and verify zero repeat queries for unchanged
coordinates plus complete invalidation when replacing the profile.

Build `south-fork-exact-crest-values-build-v1-20260912.log` exits0 (236.14s).
Native/D3D12 `south-fork-exact-crest-values-v1-20260912/index.json` has31 successes,
zero warnings/failures/unrun. Three timing-parser tests also pass; scoped diff
whitespace checks pass. The actual normal-map V7 capture exits0, but water-actor
median **108.4131ms**, p95 **162.1084ms** (frames30–60), does not establish an
improvement over V5's107.1342ms. Publishing median70.4051ms. Exact report SHA256
`017fa4c20679a000a3cfda9f1d98d1c7a4d6a691709294501071e15b3a8f0aa3`:
`tmp/south-fork-exact-crest-values-cost-v1-20260912.json`.
Opt-in `WaterCrestPerf` identifies adaptive selection as the largest fine-update
stage, commonly45–69ms in the sampled run; further query/selection optimization
is needed. Do not label the exact cache a demonstrated normal-river speedup.

Fresh separate actual topology audit (V3, exit0) still passes: **1.431618874cm**
maximum current crest-target error across712,872 samples, unchanged source
vertices,1,881 fine vertices,22,710 submitted triangles. Fine correction tracking
error0.000199795cm. Report:
`unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v3-20260912.json.cartesian-mesh.json`,
SHA256 `9fa4d2839430ca29fbcf31176360a5fd647d4f3675eaa0e140c88de2411db824`.
Its explicit target-only scope below remains unchanged. The actual V3 screenshot
was inspected: visible froth/terrain, but sparse scenery and raft/rock contact
remain unresolved. No completed motion/reference/traversal/performance acceptance.
No build/editor/capture remains running at this checkpoint; offline cook49780
continues independently. The broader goal stays active.

## Latest: actual fine crests integrated; performance still fails (15:56 UTC)

The visible Cartesian clipped single surface now receives conforming adaptive
fine crests from the same continuous profile used by raft support. Original
source positions and shoreline segments remain unchanged; foam/current/wake
attributes follow the same midpoint parents. Cell ownership and anchor sampling
use the submitted fine triangles. This is inside the normal South Fork scenario,
not a Troublemaker scenario or a second foam surface.

Actual normal-map audit at 8330 m after 10 world seconds:
`unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v2-20260912.json.cartesian-mesh.json`
(SHA256 `4f338dd1ebfe1bf7e7187600aa29a96ba94ed0d8b83c12c8f813412e500a6a0f`).
Maximum current crest-target interpolation error is **1.434352153 cm** across
713,592 independent samples, passing the unchanged 2 cm target. Original source
vertex change is zero. There are 1,891 added fine vertices and 22,730 submitted
triangles. This audit isolates the current analytic crest target on actual
submitted topology; it excludes macro temporal lag, other relief and GPU
perturbations. It does **not** establish full shaded motion or traversal acceptance.

The first fine implementation regressed measured water-actor cost. Exact
compact-support culling now skips refinement queries only where the shared
profile is identically zero. Both geographic orientations compare bounded and
unrestricted refinement parents, triangles and cell owners exactly. Build
`south-fork-fine-crest-support-bounds-build-v1-20260912.log` passed (232.26 s);
`south-fork-crest-support-bounds-v1-20260912/index.json` reports 31 successes,
zero warnings/failures/unrun.

Normal-map full-render timings, selected frames 30–60, water-actor median:
49.2022 ms before fine crests (V3), 161.5253 ms with fine crests (V4),
107.1342 ms with exact support culling (V5). Report:
`tmp/south-fork-crest-bounds-cost-v1-20260912.json`.
These are instrumented CPU observations sharing the machine with the offline
cook, not total frame/GPU timings or deterministic matched trajectories.
**Performance remains unacceptable.** V5 capture shows visible froth/terrain,
but bare scenery, a raft at a rock and unresolved visual/motion issues; it is
not a successful traversal. Next identify the remaining fine-update cost with
opt-in `WaterCrestPerf` stages, retain exact source/shore/crest guarantees, then
repeat actual crest and motion/cost checks. Earlier evidence below is historical.

## Result and remaining failure

Two production-path optimizations remove work that cannot contribute visible
water. Terrain, source fields, 1 m sampling, optical/hydraulic smoothing,
wet/dry topology, crest amplitudes and the saved normal scene are unchanged.
Thirty native/D3D12 regressions pass. This is progress, **not playable-frame
or realism acceptance**.

A separate actual-game crest audit at 8330 m inside the normal South Fork
scenario finds nine active shared breaking sites. The continuous crest reaches
0.511849642 m, but interpolation on the current 1 m macro triangles has a
maximum error of **0.161403641 m**, exceeding the existing **0.02 m** target.
RMS is 0.002167097 m over 249,450 samples in 9,978 fully wet cells. The worst
point is hydraulic east/north (-5438.5, 3606.5), not route chainage/lateral.
This measurement covers the shared analytic crest only, excluding hydraulic
mean, pockets, boils and GPU perturbations. It is not an independent measurement
of the fully shaded moving surface.

**Next:** integrate source-preserving, conforming fine crest geometry into the
actual Cartesian clipped single surface, with shared support, normals, foam,
shoreline membership and geographic transforms. Reuse the earlier bounded
crest work but do not enable its rapid-origin-only refinement box or restore a
Troublemaker menu scenario. Verify the unchanged 2 cm target and full-frame cost
in the normal river. Remaining source sampling (~12 ms/refresh), mesh publishing,
renderer/GPU/solver costs, sparse scenery and full traversal/reference review
are still open. No completion claim or final commit.

## Implemented changes

- `RaftSimWaterSurfaceActor.cpp`: opt-in `-RaftSimWaterStageTimings` reports
  buffered per-stage CPU timing. Disabled mode performs no clock reads/logging.
  In Cartesian single-core mode, skip the hidden raised-foam sheet's full-grid
  calculation/upload and the hidden legacy base mesh upload. Preserve the actual
  foam transport, core color/current/wake channels and source geometry. Explicit
  optional paddle-ripple mode still computes its required inputs.
- `RaftSimWaterShoreline.cpp`: the owning exact cache retains initialized unused
  reserve vertices during topology rebuilds. Every active edge is rewritten;
  every changing crossing still rebuilds topology. Public fresh construction
  still initializes all reserve nodes. No tolerance, shore simplification,
  missing-water workaround or stale active triangle is introduced.
- Native checks use hidden-buffer sentinels and compare the actual visible
  clipped carrier. An additional 32 changing-bank 225x225 updates compare active
  geometry/UVs/indices against independent fresh builds. Existing exact-cache
  tests compare all active attributes through wet/dry/availability/XY changes;
  actual D3D12 raster checks still cover both geographic orientations.
- `physics/scripts/audit_water_stage_timings.py` records log hashes and selected
  frame interval, with independent nested-scope statistics. Three parser tests
  pass (interval/statistics, duplicate rejection, missing-data rejection).

## Actual normal-game timing evidence

All three runs use `L_SouthForkAmerican_FullReach -game -RenderOffscreen`, full
D3D12 rendering, 1280x720, ephemeral profile, `south_fork_full_descent`, and
`-RaftSimWaterReviewStation=8330`. The latter only selects a start within the
normal river. No renderer/scenery reduction, special rapid material, separate
scenario, video recording or crest-audit workload was used for timings.
Each uses `RaftSim.CaptureRaft 12 <unique-label>` with default camera/paddling.
All processes exited 0. Captures were inspected; visible terrain, raft and
froth remain, but scenery is bare and final wave motion is unaccepted.

Selected frames 30–130 inclusive, median milliseconds:

| Stage | Original V1 | Hidden uploads skipped V2 | Reserve writes skipped V3 |
|---|---:|---:|---:|
| Entire water-actor tick (not entire game frame) | 60.6312 | 47.0631 | 44.3208 |
| Hydraulic/presentation refresh | 46.1162 | 38.69285 | 36.4722 |
| Unused overlay/finish stage | 6.80635 | 0.2799 | 0.2490 |
| Per-frame interpolation | 14.6260 | 14.4149 | 11.1189 |
| Cartesian clip/bounds/enqueue | not split | 9.3776 | 6.3629 |

Nested stages must not be summed across scopes. All runs share the machine
with the ongoing full-river offline cook. They use real elapsed time and can
follow different trajectories; the faster run refreshes less often per rendered
frame (92/74/67 refreshes in the 101-frame interval). These are directional
instrumented observations, not matched-simulation deterministic speedup proof,
GPU timings, total FPS, or a passed performance gate.

Raw logs: `unreal/Saved/Logs/south-fork-stage-timing-v{1,2,3}-20260912.log`.
Screenshots: `unreal/Saved/Screenshots/south-fork-stage-timing-v{1,2,3}-20260912.png`.
Exact report: `tmp/south-fork-water-stage-comparison-v1-20260912.json`, SHA256
`22fa60139605951fedcd2a2e1dd99caa3bc47c80a224491ae4e8221dc9356b82`.

Reproduce statistics with:

```powershell
python physics/scripts/audit_water_stage_timings.py unreal/Saved/Logs/south-fork-stage-timing-v1-20260912.log unreal/Saved/Logs/south-fork-stage-timing-v2-20260912.log unreal/Saved/Logs/south-fork-stage-timing-v3-20260912.log --report <fresh-report.json>
```

Final build: `unreal/Saved/Logs/south-fork-shore-reserve-build-v1-20260912.log`,
exit 0, 22.84 s. Final 30-test report:
`unreal/Saved/RaftSimValidation/south-fork-shore-reserve-v1-20260912/index.json`,
30 successes, zero warnings/failures/unrun. Installed experimental Python-plugin
startup issues remain separate and unresolved for clean release.

## Actual normal-game crest evidence

Separate run, no stage timing; same full map/start/render settings, with
`-RaftSimCrestSamplingAudit=<absolute-fresh-json>`; audit runs after 10 world
seconds. Process exit 0. Report:
`unreal/Saved/RaftSimValidation/south-fork-normal-rapid-crest-v1-20260912.json`,
SHA256 `158ac1da8bb7781426369b676d3e6e0cc64ef349430c982bd752d351d2df2033`.
Log: `unreal/Saved/Logs/south-fork-normal-rapid-crest-v1-20260912.log`.
The attempted `waterinventory` argument was placed in the camera slot and did
not produce an inventory; do not claim it did. To request that inventory later,
use explicit `8 4 22 waterinventory` after the capture label. Crest-audit results
are independent of that camera setting.

Saved normal map SHA256 remains
`09dcd41fd37013cbb2fc0d4e94de952ca45731937b517aad0e518d8922afec2d`;
user profile remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
No scene packages, source geometry, collision assets or flow-source data were
edited during this work.
