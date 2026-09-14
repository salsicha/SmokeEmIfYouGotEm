# Exact crest-support region broad phase — September 14

Candidate REJECTED for ordinary gameplay. Ordinary gameplay retains linear region scans
unless `-RaftSimIndexedCrestRegions` is supplied. The already-qualified midpoint
dependency scheduling remains enabled. Desktop target is 30 FPS, not yet met.

The existing adaptive selector checks each triangle's AABB against the OR of
all supplied nonzero-profile regions. A candidate immutable balanced AABB tree
replaces this linear scan, preserving exact leaf `FBox2D::Intersect` semantics.
Internal node bounds use unions of the original endpoints. Centers determine
grouping only; no center/tolerance/grid is used to reject a triangle. Unusual
invalid or nonfinite inputs fall back to the original scan. Tree construction
happens for each current profile build, not a stale-source cache.

Triangle sampling, interpolation error tolerance, detail-window selection,
refinement levels, ordered midpoint parents, triangle ordering and ownership
are unchanged. The default remains opt-in until native and actual-input
verification and paired timing justify otherwise.

Native controls cover 40,000 independent box-union queries including exact
touching corners, empty regions and invalid-box fallback, then 12 changing
adaptive reconstructions with a moving detail window and changing heights.
Build30598 TERMINAL exit0 in275.44s. Native87164 TERMINAL exit0: all six
requested tests passed in0.855400s, including the40,000-query/12-reconstruction
test plus CrestMidpointExpansion, CrestHistory, ShorelineCompactUpload,
ShorelineCrestTargetCache and ShorelineFineCrest. Parser/midpoint/budget suite:
20 PASS in0.52s; expanded final suite with release/CSV checks45 PASS in1.31s.

`-RaftSimCrestRegionAudit` performs two independent warm builds on every actual
changed input in frames100–250, alternates call order, compares parents,
triangles, origins and expanded coordinates, and explicitly logs unchanged
calls. The parser requires every frame120–250, preserves duplicate calls and
includes per-build index construction in timing. These extra reconstructions
are diagnostic overhead, never ordinary-game FPS evidence.

The reference videos were retried during compilation: web cache misses for
both; browser initialization failed with missing kernel-assets path (os error3).
No new footage was inspected. Physical wetting/energy, wave/froth/contact,
terrain, later rivers, crew, release and full-project acceptance remain open.

## Actual-input outcome: retain the linear scan

Game process6875 TERMINAL exit0. Strict report
`tmp/south-fork-crest-region-paired-v1-20260914.json` accounts for ALL131frames,
131build calls and1explicit unchanged call (including a repeated build frame).
Actual inputs contain only9support regions. Both paths have identical parents,
triangles, origins and8,803,559 expanded vertices /6,383,576 triangles.
Log SHA256 `23497c1ec867002670bca76145b88e44e90f809bd0d05f50d8c2cfa4608fbadd`.

Mean complete build: linear16.441969ms, indexed16.407001ms. Mean saving0.034968ms
is not a reliable gain: serial-first order gives-1.718665ms, indexed-first
+1.762030ms. Medians14.429901/14.904100ms; p9525.835898/25.716100ms.
Therefore do NOT promote the index. No quality reduction or shifted tolerance
was attempted to create a win. The existing128batch, original region scan and
previously-qualified parallel midpoint expansion remain ordinary defaults.

Both additional full reconstructions are diagnostic overhead. The CSV has all
300samples and completed footer (`tmp/south-fork-crest-region-paired-csv-v1-20260914.json`)
but its7.059529FPS is NOT normal-game performance or a new regression result.

## Fresh ordinary visual capture

Process36318 TERMINAL exit0, full South Fork scenario, station8330,
shore-left view, no region/audit flags. Label
`south-fork-post-midpoint-normal-v1-20260914`. Video
`unreal/Saved/VideoCaptures/RaftSim_20260914-061537.mp4`:
44actual source frames over6.451s;194encoded frames fully decoded.
Encoding at30Hz is not gameplay at30FPS. The extracted1s image was inspected:
broad blurred white foam patches and sheetlike crest faces remain conspicuous
around the rock controls. Visual FAIL remains, rather than accepting motion
or a successful decode as convincing water. ROI image-change statistics are
uncalibrated camera-space diagnostics, not physical-flow measurements.

Evidence: `docs/reconstruction-review-2026-09-07/detail-motion/south-fork-post-midpoint-normal-v1-20260914.json`
and its `_01s.png`. Next inspect the active material's foam coverage/density
authority and optical filtering before choosing any visual change. The current
helper blends four grid occupancies, two scales and two advected phases; a
sharper rectangular-grid candidate was previously rejected. Do not repeat that
rejected change or replace physical wave qualification with cosmetic foam.

## Active material authority checked, not inferred from helper filenames

The current saved parent SHA256 is
`adb56123f1e07c7cdfe2f6cd0da2db1c2e44f12d8ebb147a640ad9899a73c0c3`,
exactly matching `south-fork-committed-normal-install-v1-20260914.json` and
its saved six-property graph. The actual coverage node Custom_14 embeds the
original whole-cell cubic interpolation (`RaftSimFrothCells.ush`), NOT the
rejected narrower rectangular-grid helper. Its density parameter defaults to3;
the runtime actor does not override this except on the explicitly disabled
foam diagnostic path. Coverage follows `1-exp(-amount*density)` and four
corner occupancies, two scales and two committed-clock advection phases.

Custom_20 is the registered moving foam authority, combining exterior vertex
density with the registered detail texture's optical amount. Custom_21 reads
the same registered committed clock. These are not MaterialExpressionTime
animations. The material still contains a separate historical drift-foam
graph, but the runtime explicitly sets DriftFoamAerationGain,
DriftFoamSpeedGain, DriftFoamOpacity, DriftFoamSurfaceGlow and
DriftFoamRoughness to0. Do NOT call its mere presence proof of active extra
foam or remove it blindly across other material users. Disabled dynamic graph
cost is a potential separate GPU investigation, not measured savings.

No material, foam source, density or clock was changed in this turn. The next
optical investigation should preserve transported quantity and its committed
clock while testing whether resolved irregular clumps can avoid the current
whole-cell gray transition without the previously rejected rectangular
sharpening. Require actual material integration/captures and GPU/coverage
tests; a synthetic pattern or expected-mean calculation alone is insufficient.
