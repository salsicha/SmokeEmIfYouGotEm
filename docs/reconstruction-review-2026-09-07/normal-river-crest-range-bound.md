# Normal-play conservative crest range — September 15

This increment reduces the cost of reconstructing the existing playable crest.
It does not change that smooth prescribed profile into an overturning wave,
enable the unresolved nonlinear wet-front solver, or establish visual acceptance.
South Fork remains the scenario and Troublemaker remains a rapid within it.

## Actual bottleneck and selected change

A fresh ordinary-map run with explicit stage instrumentation measured 131
engine frames 120–250. Surface tick averaged 36.653361 ms, including 23.389347 ms
interpolation/publication and 13.221235 ms refresh. Publication itself averaged
22.087064 ms; its clip/refine/enqueue portion was 18.876160 ms. The 81 active
refreshes averaged 21.292158 ms each. These are nested instrumented CPU scopes,
not whole-frame FPS, and must not be added across scopes.
Report: `tmp/south-fork-stage-baseline-v1-20260915.json`; original log SHA-256
`c23987569377f293c6d97e55450cc487f9f037345706d7a72fbe14036a9b83dd`.
The native solver already uses optimized compilation and bounded row workers;
no unoptimized-build explanation or new solver speedup is claimed.

Adaptive crest selection tests three vertices and quarter-triangle interior
points against the same continuous physical profile. It can avoid these
expensive evaluations when a conservative range over the whole triangle's box
is narrower than the unchanged 0.5 cm selection tolerance. Every barycentric
weight is nonnegative and the weights sum to one: both the sampled height and
the interpolation of the vertex heights lie in that same range. Their absolute
difference therefore cannot exceed its width.

`RaftSimBreakingHeightRange.h` bounds the original physical crest, negative toe
and positive tail lobes separately. The rectangle is transformed into each
site's current flow frame. Intervals include the float quadratic cross-flow
bend; the nearest point of each interval to a Gaussian's center bounds that
Gaussian from above. Local/global owner caps cannot extend the resulting range
containing zero. Smooth edge envelopes lie in [0,1] and are conservatively
omitted from the bound. Coordinate, float arithmetic and exponential/product
roundoff cushions enlarge the bound, never the accepted error tolerance.

The callback returns only a range width, never a replacement height. If the
bound is unavailable, invalid, negative, or too wide, the complete original
selection executes. Legacy/nonphysical sites disable the shortcut. Dynamic
detail-window refinement retains precedence. Every retained fine vertex still
uses the exact original height evaluator, source attributes and shoreline
weight. No grid, tessellation level, 0.5 cm selection / 2 cm independent shape
gate, physical amplitude, normal rule, timestep, cadence, foam or contact rule
changes. No cached profile value survives its original validity epoch.

## Native and actual-input evidence

Initial native build caught an implicit integer-to-bool conversion in the new
test; this was corrected explicitly. The completed candidate build and the
subsequent normal-default build pass. The initial broader compile also retained
the two pre-existing D6 damping double-to-float warnings.

Both native runs pass 21 tests, with zero failed, skipped/unrun, in-process or
warning results. The new tests cover 80,000 original height samples, rotating
and nonunit flow directions, mixed local/global caps, zero height, large
coordinates, support boundaries, and curved crest/toe locations. Eight changing
profiles preserve every ordered midpoint parent, triangle, cell owner and
expanded coordinate while reducing exact height calls from 82,338 to 45,124.
Invalid bound fallback and forced detail-window refinement are checked. Existing
crest, conforming topology, shoreline, GPU bounds, shared fine surface and
accepted entrainment tests remain in the selected native regression set.

Initial actual-game audit: 64 alternating-order changed-input pairs after two
warm builds, frames 125–251. All pairs match the original ordered topology,
ownership, expanded coordinates and production topology: 4,305,271 vertices
and 3,127,386 triangles compared. No audit arrays are published.

| Call order | Original adaptive build | Bounded adaptive build | Faster pairs |
| --- | --- | --- | --- |
| All | 10.867741 ms | 8.228150 ms | 64/64 |
| Original first | 11.202550 ms | 8.153344 ms | 32/32 |
| Bounded first | 10.532931 ms | 8.302956 ms | 32/32 |

This is about 24.3% less adaptive-build CPU time, not a 24.3% game FPS gain.
Capture: `tmp/south-fork-crest-range-pair-v1-20260915.json`, SHA-256
`67336f7aa126f7ffe8808188c4697bd86f53248bed232589269a8675f0b1095d`.
Decision: `tmp/south-fork-crest-range-decision-v1-20260915.json`.
The strict parser requires all 64 numbered pairs, valid original counts and
timings, changing-frame history, exactness, and a timing win in both orders.
Its tests and the reused comparison/stage parser tests total 27 PASS.

The measured optimization is enabled for normal play. The explicit
`-RaftSimReferenceCrestRange` switch retains the original selection path.
`-RaftSimCrestRangeAudit=ABSOLUTE_JSON_PATH` compares independent original and
bounded builds against current production topology; it refuses to overwrite
an existing capture. The final default native report is
`tmp/crest-range-default-native-v1-20260915/index.json`.

The rebuilt normal default repeats the full actual-input audit: another 64/64
exact and faster pairs, frames 125–230, 4,305,182 vertices / 3,127,228 triangles.
Original mean 10.712986 ms versus bounded 8.252667 ms; original-first means
11.389893 / 8.596922 ms and bounded-first means 10.036078 / 7.908412 ms.
The enabled production topology matches both independent audit builds.
Second capture: `tmp/south-fork-crest-range-default-pair-v1-20260915.json`, SHA-256
`77baae70b15660dd59a5bb81746a04d645b07e1252d2978fa30bbd7992b2630e`.
Across both actual runs, every one of the 128 pairs is exact and faster; the
records remain separate rather than hiding run/order differences in one mean.

The final default build passes in 37.91 seconds (five actions). Native tests
again finish 21 PASS / zero failed, warning, unrun or in-process results.
The first ordinary-performance launch was not created: automatic approval
review failed because its model was at capacity. Read-only checks found no
Unreal process, log or CSV; the identical scoped command then started normally.
## Fresh ordinary performance and inspected captures

The ordinary 300-frame run has no range audit or stage-timing flag. Original
1280x720, D3D12, Development/WindowsEditor settings and target-30 metadata remain.
CSV rows 120–250 average **22.429181 FPS**, mean frame 44.584776 ms and
**p95 54.7266 ms: FAIL** against the unchanged 33.333333 ms target.
Report: `tmp/south-fork-crest-range-default-performance-v1-20260915.json`.
Original CSV SHA-256:
`6a5908cecce71766ca2701315bf7a661d670831b82cb084f4f5b78f73be5dcca`.

Surface tick averages 27.003125 ms, publication 15.794453 ms, refresh 9.955118 ms
(68 active rows), crest selection 4.271743 ms (69 active rows), and water-step
calls 9.896238 ms per frame. Scopes remain inclusive/nested. This is not a
native single-step budget measurement. The earlier 13.420531 FPS run refreshed
on 115 of these 131 sample rows, not 68; trajectories, timing and machine load
also differ. Do not attribute the whole-game difference solely to this change.
Only the repeated same-input paired tests isolate the adaptive-build saving.
Neither short offscreen run is packaged, sustained or release acceptance.

The fresh ordinary recording finalized with 93 source frames over 6.049 seconds:
`unreal/Saved/VideoCaptures/RaftSim_20260915-102844.mp4`, SHA-256
`1eacc4924c0d3c4bb77ccf7be2daf911816eef66f94e204515732889782337ff`.
All 181 encoded frames decoded successfully through PTS 6.0 s. Encoding at
30 Hz is not game FPS. Original still `_001` and decoded frames at 3 and 5
seconds were inspected, not merely inferred from image-change statistics.
The raft moves downstream/out of the fixed view, but broad merged white froth,
smooth green water faces and broad rock flanks still dominate. No convincing
breaking-wave, froth, terrain or full-motion/reference acceptance is claimed.
This optimization does not add visible detail. The inspected original still is
`unreal/Saved/Screenshots/crest-range-default-motion-v1-20260915_001.png`, SHA-256
`55d4b984d9587d927a96d45b2b0004830880c56193e547304e48cf31b7527961`.
Decoded frames/report: `tmp/crest-range-motion-decode-v1-20260915`.

Final default native report SHA-256:
`f2bf931ffcc1ab30d030c73dcf82f2349b3a7eab2c934ade36b7e75c84905f2e`.
Final Raft DLL SHA-256:
`a53d4350e8a0a1c4a612e7f9a0a524b17cb2ba9fc501f9d005980ea56a33a1f1`.
All 464 protected source/actor hashes remain unchanged after the engine runs.
All owned builds/tests/game runs are terminal. Generated reports, captures and
build outputs remain ignored; no runtime/source asset is removed or replaced.

## Acceptance still required

Actual breaking-surface/froth deformation and compatible point/edge/flat/mixed
front forces, complete-front transport and native single-surface integration
remain open. The previous flat-source derivative is not a front update. The
thirteen retained source/energy regressions are not waived by native rendering
tests. Captured terrain provenance and inferred submerged/flank geometry remain
distinct. Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene water, crew
fit/motion, normalization and final release qualification retain their scope.
