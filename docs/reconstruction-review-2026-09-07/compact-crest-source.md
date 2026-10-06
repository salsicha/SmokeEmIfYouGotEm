# Referenced crest-source storage qualification

September 23, 2026 UTC. South Fork remains unfinished. This trial changes CPU
storage after shoreline clipping, not captured geometry, bathymetry, hydraulic
resolution, crest selection, temporal cadence, normals, foam or collision.

## Exact representation change

The hydraulic grid and shoreline builder retain their original full source.
Before crest refinement, the candidate copies only vertices referenced by the
clipped draw indices, in ascending original-index order. It remaps indices
without removing or reordering a triangle. All current attributes, coarse
crest and shore weights are refreshed on every publication. An empty draw
retains one non-drawn anchor for valid scene-buffer allocation. Invalid indices
are rejected before mutating the mapping. Both original and remapped cell
offsets identify the same ordered triangles.

The original CPU packing and wet/dry geometry still run; this is not a sparse
hydraulic solve. The renderer already compacts its triangle packet, so source
storage reduction must not be mistaken for the same reduction in GPU uploads.
The new source-index accessors also let crest/foam diagnostics measure retained
original anchors without indexing a compact array as the full hydraulic grid.
They report the number actually audited; absent anchors are not measurements.

## Paired actual-game evidence

Two captures each retain all 64 frame pairs, frames 120 through 183. Both
independent histories advance from startup. Execution order alternates in
two-frame blocks; measured candidate work includes remapping, attribute copies,
allocation and crest update. Original coarse/shore preparation and the exact
comparison are outside both timed paths. A publishes reference; B publishes
candidate. Every ordered drawn triangle attribute, rendered correction and
cell offset is exact. B additionally compares target corrections in-game;
A predates that extra assertion, so do not attribute it retrospectively.

| Capture / candidate first | Pairs | Reference mean ms | Candidate mean ms | Faster pairs |
| --- | ---: | ---: | ---: | ---: |
| A v1 / no | 32 | 6.695644 | 5.192472 | 32 |
| A v1 / yes | 32 | 7.339737 | 5.394944 | 31 |
| B v2 / no | 32 | 6.436288 | 4.674428 | 32 |
| B v2 / yes | 32 | 7.019307 | 5.525400 | 31 |

All rows, including the two slower pairs, log hashes and v2 editor DLL hash
are preserved in [the receipt](compact-crest-source/pairs-and-builds.json).
Component gains alone do not authorize default promotion or prove frame-rate,
shoreline, motion, collision or visual acceptance.

## Regression coverage

The initial D3D12 native run passes four tests: ReferencedWaterVertices,
ShorelineFineCrest, ShorelineCrestTargetCache and ShorelineMovingBankCache.
The new synthetic fixture compares 75,768 ordered triangle corners over
40 evolving histories: both coordinate orientations, moving banks, wet/dry
membership changes, hole, all-wet and empty-draw cases, changing attributes
and zero/partial/full temporal blend. Target and rendered corrections match
exactly. These analytical fixtures are not captured river measurements.

Twenty-eight focused Python tests pass; incomplete, duplicate, reversed,
nonexact, malformed and no-compaction pair logs fail closed. A slower candidate
cannot be reported as a speedup. Editor v1/v2 builds succeed in 67.10/68.76 s.
The pre-existing C4701 warning in DetailSourceFootprintTest is not resolved by
this change. A first sandboxed Python retry could not import pytest.__main__;
the explicit runtime/dependency path under the authorized host passes.

## Ordinary whole-game cost and incremental promotion

Four sequential same-v2-binary runs use reference/candidate/candidate/reference,
900 CSV rows each, rows60..840 inclusive, D3D12 at1280x720 on the normal FullReach
scenario with review station8330, four solver lanes, no cook, no paired audit,
no capture screenshots and no concurrent build/native tests. Verified modern
CSV timing uses scope offset1. All frame and nested-scope metrics plus process
receipts are retained in [ordinary cost](compact-crest-source/ordinary-cost.json);
the much larger phase-group report remains locally available with its hash.

| Run / path | FPS | Mean frame ms | p95 ms | Crest update mean ms |
| --- | ---: | ---: | ---: | ---: |
| A / reference | 25.377871 | 39.404409 | 47.5389 | 6.672029 |
| B / candidate | 25.854788 | 38.677556 | 48.4384 | 5.056613 |
| C / candidate | 26.733963 | 37.405603 | 46.6198 | 4.823435 |
| D / reference | 25.164113 | 39.739132 | 48.2018 | 6.869745 |

Both candidate average frame times improve against both controls. Tail latency
is mixed: B p95 is worse than either control, while C is better. ALL FOUR FAIL
30FPS/33.333333ms; no precise causal whole-frame gain or sustained acceptance
is claimed. Combined exactness and measured average cost support an incremental
South Fork-only default in v3, subject to the normal-launch checks below. Other
maps remain unchanged. `-RaftSimReferenceCrestSource` overrides both the default
and explicit `-RaftSimCompactCrestSource` diagnostic opt-in. The failed earlier
base-vertex parallel trial remains disabled by default.

## Final normal-play delivery and limits

Final v3 editor and standalone game builds pass in12.96/85.02s. The standalone
executable was rebuilt, not launched or packaged. Actual captures use the editor
in game mode on the normal FullReach map/scenario. Seven native D3D12 reference
regressions pass; two compact-plus-paired-audit regressions pass separately.
The new component test checks original-anchor mapping, changing banks, an empty
draw and a valid rendering proxy with both published representations.

Normal-start v3, with no optimization override, logs compact=1/reference_override=0.
All24 source images were captured; the15.573s/234-source-frame original movie
fully decodes467frames, including35 identical adjacent frames. Recording rate
does not establish game FPS. Decoded1/6/11s views were inspected: raft movement,
continuous visible water, shoreline and the corrected briefing fade remain;
no new hole was visible in these limited views. Broad smooth foam, coarse canopy
and crew lighting limitations persist. This is not full-route shoreline,
animation, collision or visual acceptance and no new realistic detail is claimed.

All2,034 independently sampled wet support contacts agree with submitted
triangles within0.000190323cm, with zero raw dry/unavailable contacts in that
sample. The foam diagnostic audits8,645 retained original grid anchors out of
50,625 source nodes, explicitly reports a compact (not complete) source prefix,
and measures zero UV3 transport and UV1 bulk-channel error. Unreferenced grid
nodes are not falsely counted as measured. Full contact probes remain locally
preserved with a hash; summary/build/native/media receipts are in
[normal delivery](compact-crest-source/normal-delivery.json).

A separate ordinary final-default300-frame capture, rows60..240, averages
31.918329FPS/31.329961ms, with p9542.2645ms: FAIL. This short interval does not
supersede the longer mixed-tail ABBA evidence, establish sustained30FPS, or
measure the instrumented movie's cost. Normal launch and final cost both confirm
the default without a command-line opt-in. This is a delivered CPU-storage
optimization with exact geometry, not a new river reconstruction or realism gain.

No river is accepted. The exact source audit PID6480 remains the
sole live scientific job; captures retain its verified process handle and
resume it in finally (all statuses0; cost A/final CPU brackets0.015625s,
others0). It was observed advancing after the final capture at3841.31CPU seconds;
no completed derivative report yet. No duplicate cook, new evidence acquisition, captured
terrain/collision/installed4950-field change or nonlinear enablement occurs.
The source-cap decision and South Fork realism/performance work remain open;
Colorado, Pacuare and Futaleufu remain queued in that order.
