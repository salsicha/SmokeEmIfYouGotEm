# V12 CPU cost and far-field rebuild investigation

September 27, 2026. Supporting diagnosis only: no new playable delivery,
performance acceptance, geometry change or solver setting change.

The retained isolated busy-rapid CSV has SHA-256
`e880ec02f0758df9b3b405179d835808123d8b63b9cb9db8e2bd0ce3057ef316`.
Its frame receipt has SHA-256
`3795b5783445fbf3927bf4d664f13cd294200d8872d9fd48a16bb8d620f36a35`.
`tmp/audit-sf-v12-stage-cost-20260927.py` validates those inputs, 1,200 rows,
the retained 30..1169 window, finite measurements, receipt p95 and hitch count.
Output: `tmp/sf-v12-stage-cost-20260927.json`.

Busy FrameTime mean/p95/max remain 46.514631/53.7239/103.5941 ms.
GameThread mean/p95 are 45.043309/53.1334 ms, GPU 15.788194/18.1238 ms.
The recurring surface cost is substantial: SurfaceTick mean26.088505 ms,
CrestUpdate10.308358 ms and CrestSelection5.818058 ms. These are nested
inclusive scopes; do not add them or treat their individual percentiles as
components of the frame percentile.

## The isolated hitch is not the recurring p95 problem

CSV row1081 has the sole FrameTime over100 ms. The previous row1080 carries
GameThread100.6302 ms, SurfaceTick81.3963 ms and Refresh76.3936 ms, including
far-field Update18.3146 ms. Its far-field Sample/Pack/Submit are respectively
1.8734/5.1362/5.3494 ms. Shoreline Topology is11.5758 ms, but that category is
shared by near and far components; the CSV does NOT attribute it exclusively
to near-field topology. Scope nesting and frame-boundary alignment preclude
summing these numbers into an exact hitch explanation.

A second hash-checked scan found far-field Sample, Pack and Submit nonzero
ONLY at row1080 within the 1,140-row audit window. Therefore optimizing that
rebuild is a plausible hitch treatment, not evidence of a fix for the busy
p95 failure. Removing the ring, reducing radius/density, skipping a required
recentre or hiding water would alter coverage and is not an acceptable shortcut.

## Source review and next bounded experiment

`RaftSimWaterSurfaceFarField.cpp` rebuilds a globally anchored322x322 lattice
at the default640 m radius/4 m spacing. It computes fresh source attributes,
packs a fresh local vertex array, then submits the clipped mesh. The current
`BuildClipped`/topology-cache implementation reads/copies that rvalue source;
it does not actually take ownership. Near-field publication already has a
qualified retained packing buffer, while both far-field paths allocate fresh.
A separate far-field scratch buffer is therefore a concrete capacity-reuse
candidate. Preserve original
color math: the previous vector-color candidate failed its timing-order gate.

Before enabling a candidate, add native coverage of repeated rebuilds,
changed texture origin/carrier hole, grow/shrink and unavailable-source retry.
Compare every source attribute and drawn triangle with fresh packing, confirm
that the consumer still leaves the scratch allocation owned by the actor, and
measure both invocation orders plus isolated ordinary-play frame costs. Also
review original engine motion for shoreline/coverage continuity. A packing
microbenchmark alone cannot accept this change or the river.

### Candidate native correctness passes; runtime qualification pending

The Cartesian path now has actor-owned `FarFieldSourcePackingScratch`, separate
from the near-field scratch. `raftsim.FarFieldReusePacking` defaults to0: the
normal game still allocates fresh. Enabling the candidate changes only the
output buffer supplied to the existing parallel packer; all source attributes
are recomputed with original color math. The curved far-field path is unchanged.

The existing native `RaftSim.M4.CartesianShorelineSurface` test now compares
fresh and retained actual mesh publications, including every source/reserve/
shore attribute and index. It poisons retained attributes, exercises changed
texture origin and carrier availability, grows/shrinks the lattice, checks
same-size allocation ownership and the unchanged-key early return. These checks
PASS in the native fixture. Unavailable-source retry, real
production-input timing and whole-frame/visual review remain additional gates.

Editor build28379 completed exit0 in499.14 s, log
`tmp/farfield-packing-editor-build-v1-20260927.log`. Dependent native test
wrapper22259/PID24236 also completed exit0; no build/test from this sequence
remains live. Recipe `tmp/run-farfield-packing-native-v1-20260927.ps1` verified
unchanged source/DLL hashes across the D3D12 offscreen run. Four native tests
PASS, zero failed, not-run, in-process or test warnings:

- `RaftSim.M4.CartesianShorelineGeometry`
- `RaftSim.M4.CartesianShorelineSurface`
- `RaftSim.M4.ShorelineInputValidation`
- `RaftSim.M4.SurfaceSourcePacking`

Report `tmp/farfield-packing-native-v1-20260927/index.json` SHA-256:
`4d914409b15d9352c30df92baacc23e196fd883badfc95f7d60a44e96f9a01da`.
The far-field fixture starts at66x66 nodes/18 drawn triangles and also changes
radius from128 to132 m and back. This is not a full-reach production-input
or rendered-motion test. Existing engine startup warnings (including optional
MetaHuman content and driver/TSR notices) remain outside the zero-warning test
results; do not call this a clean release log.

No FPS measurement is valid during the ongoing hydraulic solve. The packaged
v12 game has not been rebuilt or changed. No runtime performance gain or visual
improvement is claimed, and the candidate is not qualified for default use.

The carrier's undrawn prefix is also built before the unchanged-key early
return. Moving only that prefix construction after the return can avoid work
on cache hits without reusing stale mask values; this is a separate smaller
candidate, not the observed18 ms rebuild cost or a physical-water improvement.

No new engine/build/performance run was started during the existing exact
450->900 s hydraulic continuation99863 (native12676/wrapper34600). At the
latest inspected log it had reached step1690/time534.5 s; final settlement
and bank audits remain pending. Keep v12/450 s playable fields installed.
Do not duplicate the solve, promote a snapshot without review, or advance
to Colorado while South Fork remains unaccepted.
