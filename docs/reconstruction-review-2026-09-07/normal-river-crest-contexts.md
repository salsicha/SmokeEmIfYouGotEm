# Crest worker-storage lifetime — September 13, 2026

The prior foam-clock turn made verified progress, but normal South Fork still
measured12.764093 FPS/p9586.567ms and failed the visual review. This investigation
targets the measured crest-selection cost without freezing profiles or changing
geometry, timesteps, quality, solver limits or acceptance tolerances.

## Evidence and change under verification

The last ordinary CSV's181 selected rows show181 XY changes and181 profile
changes. Root indices change5 times, shore weights4 and detail-window bounds2;
77 topology levels are built and466 reused. Skipping whole reconstruction is
therefore invalid. Persistent site position/dimension smoothing also changes
actual height inputs, not only unused foam parameters.

`BuildAdaptive` retained coordinate tables, but its per-level preparation called
`SetNum(Contexts)` unconditionally. A coarse level with fewer batches destroyed
the previous fine level's extra tables. Later levels recreated them. The new
normal retained path keeps inactive tables up to the maximum context count seen
by that refinement object. Each batch still exclusively owns its table, every
level joins before preparing storage, and every build advances the height epoch.
**No sampled height survives into another build's calculation.** The existing
4096-entry cap per table remains. Local/fresh memo behavior is unchanged.

`-RaftSimResizeCrestContexts` retains the old shrink/recreate behavior in the
same build. `-RaftSimCrestContextAudit=...` compares identical actual gameplay
inputs through two warmup and eight alternating-order pairs, checking exact
ordered parents, triangles and cell owners. It records timings, context
creation/destruction and retained allocation bytes. Repeated-input timing is
not changing-topology, whole-frame, memory-budget or visual acceptance.

The normal CSV gains context creation/destruction counters and retained table
allocation bytes. These count per-level preparation, not every internal map
allocation or total process memory. The existing native memory gate remains
8192MB and must be measured independently.

The28-frame native `CrestMemoEpoch` fixture now also compares the old shrinking
path, with changing profiles, drifting/translated coordinates, changed winding
and temporarily disabled retention. It requires current-function calls, exact
topology/coordinates, no inactive-context destruction in retained mode and fewer
context creations than the old behavior. Results are pending, not assumed.

Build49769 CLOSED1 in149.71s: the new unsigned-byte diagnostic was ambiguous
between Unreal CSV overloads. An explicit diagnostic-double accessor corrects
the type without changing cache logic; exact at feasible process allocations
below2^53 bytes. In-place patch attempts on the already-modified crest source
failed, even though it was not read-only and a no-write handle check succeeded.
No permissions or other processes were changed. The correction is in the
header, with matching native log formatting. Rebuild86220 CLOSED0 in156.67s;
two pre-existing D6 damping-conversion compiler warnings remain. Raft DLL SHA256:
`207d553bf3434caba33d1d63307154f97a6c0ada1a442d992eff59198b8d52b0`.

Native64724 CLOSED0: **85 clean passes**, zero warnings/failures/unrun,
21.318068s, `tmp/south-fork-crest-context-native-v1-20260913/index.json`.
All six prior GPU fixtures supplied unchanged. The28-frame epoch fixture compares
37,187 expanded vertices exactly across all four implementations. Contexts
created23 versus100, destroyed0 versus84; retained table bytes3,660,356 versus
2,619,144. This establishes the intended lifetime change and fresh-value safety,
not whole-game performance or memory qualification. Playable checks follow.

The same background cook reached4500s/local10000. Both state and artificial-bank
audits pass:5,382,400 finite cells,86,720 exactly dry artificial-bank cells,
volume2,868,997.087442960m3, maximum step residual1.413489015e-8m3. Outlet
102.641989394 versus inlet45.306954547m3/s still shows settling; no promotion.
Next4600/local12000 requires both audits after its complete marker.

## Actual same-input and surface checks

Audit11829 CLOSED0, cook suspension/resume0, no timeout. Report
`tmp/south-fork-crest-context-paired-v1-20260913.json` uses actual frame120:
52,047 source vertices,18,946 source triangles,16,074 added midpoint parents.
Two warmup pairs precede eight alternating-order comparisons. **All eight have
exact parent/triangle/owner arrays and lower retained-context time.** Mean
10.042213ms retained versus12.564313ms shrinking, about20.1%lower. Sampling
9.337425 versus11.861213ms. Each measured old-path call creates and destroys
243 contexts; the retained path does neither. Both end with22,492,972 allocated
table bytes on this identical repeated input. Every call still gets a fresh
height epoch; this is not stale-profile reuse or whole-frame acceptance.

Geometry report with prefix `south-fork-crest-context-geometry-v1-20260913`
samples1,550,232 independent sevenths across50,515 submitted triangles.
Maximum target crest error0.594094855cm is below the unchanged2cm gate;
fine-correction tracking0.001776397cm, source-vertex change0. No full shaded
motion or combined macro/detail latency acceptance is inferred.

Carrier/detail reports with prefix `south-fork-crest-context-{carrier,detail}`
share frame117:2,020 wet contact points,945 affected, zero unavailable;
maximum carrier error4.765238100e-5cm.4,226 independent GPU texture queries,
maximum RGBA error5.960464478e-8, pass. Ordinary performance, original-behavior
control and process-memory gate measurements follow.

## Ordinary captures and unchanged budgets

Default41188 and shrinking-control59541 both CLOSED0; cook suspension/resume0,
no timeout. `tmp/south-fork-crest-context-frame-v1-20260913.json` reports181
rows60-240 per capture,1280x720, target30. These changing trajectories are not
the identical-input comparison above and do not prove a whole-frame gain.

| Metric | Retained default | Original shrinking control |
| --- | ---: | ---: |
| FPS | 12.611023 | 13.265546 |
| Frame p95 ms | 87.8737 | 81.0985 |
| Surface tick mean ms | 51.242286 | 49.278278 |
| Crest update mean ms | 20.263411 | 20.360462 |
| Crest selection mean ms | 11.318934 | 12.254688 |
| Four water calls mean ms | 18.455262 | 17.037338 |
| Contexts created across181 frames | 0 | 42,755 |
| Contexts destroyed | 0 | 42,771 |
| Peak retained-table bytes | 64,151,216 | 37,661,488 |

Scopes are nested/inclusive; do not sum them. **Both fail30 FPS.** Lower crest
selection cost does not establish an overall FPS benefit. Moving-input retained
tables use more memory than the repeated identical-input pair; the distinction
is measured, not hidden. CSV allocation counters are diagnostic numeric values,
not total process memory or allocation-by-allocation heap tracking.

Default CSV SHA256:
`48c8e9d85a9f8aa98a5ff40b3c8187e4ebf278644066c1f4ebf1d8b17b4ac048`.
Shrinking CSV SHA256:
`06675aea4a7a30bf1ddbc41f9b5854393dadf4450cbc51d2d13313d2ba9fac15`.
Both run724 successful fixed ticks, no failures. Default debt grows1.4736 to
3.7423s, control1.3428 to2.9090s. Default shutdown foam27.866668120s, detail
27.933334790s, world34.023340359s;5 exact detail remaps,zero teleports,419
frame copies,zero skipped copies. The one-interval foam ordering offset and
native backlog remain open.

Native gate10245 CLOSED1 because the gate correctly failed, not because the
game crashed: game exit0, no timeout, cook resume0. Fresh report:
`unreal/Saved/RaftSimValidation/south-fork-crest-context-gate-v1-20260913-gate.json`.
269 frames, workload p9583.102898ms, wall-clock p9584.580498ms,237 hitches above
66.666664ms. Native water step average4.314730ms exceeds the unchanged1.6ms
budget. Peak process physical memory3976.246094MB **passes8192MB**. No invalid
GPU timing samples; profile/map checks pass. Resolution1280x720, screen
percentage87, existing quality levels unchanged. This offscreen Development
run is explicitly ineligible for packaged release qualification. The storage
change has verified component-cost and exactness benefits; real-time capacity
and full release performance remain unqualified.

Ordinary screenshot was viewed:
`unreal/Saved/Screenshots/south-fork-crest-context-default-v1-20260913.png`, SHA256
`35988a699ad348f61958ed17d6f98885ddc6e1e6d71673f099a3195d054aaf14`.
Broad glossy folds, blanket-like foam and unfinished terrain/vegetation/crew
remain unaccepted. No reference motion was viewed. Protected map, transmission
material and player-save hashes remain unchanged; South Fork remains the
scenario, not a new Troublemaker menu entry. No commit made.

All four gameplay processes are closed and the same cook84534/PID32144 is live,
last4530.5s/local10610. Latest4500/local10000 BOTH audits pass, still settling;
next4600/local12000 BOTH only after completion. The full remaining scene,
water/terrain realism, crew, release and final-commit goal remains active.
