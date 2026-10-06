# Base-water parallel trial: exact component, rejected default

September 23, 2026 UTC. Supporting performance investigation, NOT a delivered
playable improvement, reconstruction or release acceptance. Ordinary whole-frame
evidence rejects default promotion despite exact and faster paired component work.

## Candidate and default rollback

The candidate evaluates independent base-water vertices in joined 256-vertex
batches. The original
Y-major/X-minor serial order still accumulates every station and global
statistic. No floating-point tree reduction, omitted vertex, coarser surface,
changed expression, normal, foam, temporal cadence or threshold is substituted.
Game-thread-only settings are captured before dispatch; workers write distinct
existing array elements. It was provisionally enabled in v3 normal South Fork
for qualification, but both ordinary candidate runs were slower than both
serial controls. Final v4 restores serial default in every map. The candidate
requires `-RaftSimParallelBaseVertices`; `-RaftSimSerialBaseVertices` overrides
it. Do not count an opt-in candidate as playable delivery. No intended appearance
or physics change is introduced by either execution path.

The instrumented baseline measured 2.842429 ms per base-vertex refresh;
crest sample work was 4.589946 ms per rebuild. These diagnostic stage costs
are not whole-frame FPS. Their complete receipts are retained in
[the evidence directory](base-vertices-parallel/).

## Actual-input equivalence and component cost

Two independent v2 native game captures each compare 32 successive refreshes
between frames 120 and 183, publishing serial in A and candidate in B. Each
pair starts from the same complete pre-state, alternates execution order and
compares every mutated array, persistent history and ordered statistic exactly.
Copy/restore/comparison is outside measured evaluation; allocation, worker
dispatch, joining and serial accumulation are inside. All 64 pairs match.

| Capture / first path | Pairs | Serial mean ms | Candidate mean ms | Faster pairs |
| --- | ---: | ---: | ---: | ---: |
| A / serial | 16 | 2.554994 | 1.930012 | 15 |
| A / candidate | 16 | 2.406982 | 1.948399 | 13 |
| B / serial | 16 | 2.729307 | 2.010188 | 15 |
| B / candidate | 16 | 2.474556 | 2.009525 | 12 |

Means improve in both orders in both captures; 9 individual pairs are slower.
All rows and log hashes are retained in [A](base-vertices-parallel/pairs-a.json)
and [B](base-vertices-parallel/pairs-b.json). No v2 DLL hash was retained before
the final v3 rebuild; do not attribute the v3 binary hash to those earlier pairs.
Candidate v3 enabled the path by default for qualification; final v4 reverses
that promotion. The exact-state audit remains available for further work.

## Ordinary whole-game evidence: failed promotion

All four runs use the same v3 binary, serial/default/default/serial ordering,
normal FullReach/scenario with diagnostic station 8,330 m, D3D12 1280x720,
four solver lanes and 900 CSV samples. Rows 60..840 are retained inclusively;
no stage/paired audit, screenshots, build or native test overlaps the captures.
The verified `csv.UseLegacyFrameTime=0` mode uses scope offset 1, not a phase
chosen for correlation. Full report hash, every metric and process receipts are
retained in [the cost evidence](base-vertices-parallel/ordinary-cost-rejected.json).

| Run / path | FPS | Mean frame ms | p95 ms | 30 FPS / 33.333333 ms |
| --- | ---: | ---: | ---: | --- |
| A / serial | 27.156637 | 36.823410 | 45.6249 | FAIL |
| B / candidate default | 24.917022 | 40.133207 | 48.5326 | FAIL |
| C / candidate default | 26.958607 | 37.093905 | 45.3311 | FAIL |
| D / serial | 27.223261 | 36.733292 | 44.1704 | FAIL |

Both candidate mean costs exceed both controls. Variable trajectories and host
load prevent a precise causal regression estimate; this is nevertheless not
evidence for enabling the candidate. Neither the faster component nor the best
individual run satisfies the overall gate. No whole-game speedup is claimed.
Future work must address this result, not repeat unchanged promotion attempts.

Old cook/replay PIDs are terminal. Explicit `-NoCookWorkload` rejects incomplete
or conflicting identities and any observed live Cartesian cook, without touching
unowned jobs. The only source audit, PID 6480 with validated start time, is held
through a retained process handle and resumed in `finally` for each capture.
All four suspend/resume statuses are zero; CPU brackets are A/B/D zero and
C 0.015625 seconds. This polling/bracketing is not a zero-external-load guarantee.

## Builds, regressions and normal-start motion

Candidate v3 editor and standalone game builds succeeded in 40.27 and 111.85 seconds.
The standalone executable was built, not launched or packaged. Actual captures
use the rebuilt editor in game mode on the normal full-river map/scenario.
[Candidate build/test hashes](base-vertices-parallel/builds-and-tests.json) are retained.
Thirty-four focused Python audit/capture tests pass, including 15 base-pair
tests. Identity/absence runner guards preserve their exact process ownership.

The first NullRHI native run had 9 passes and one failure: FineCrest requires
a real rendering proxy and NullRHI provides none. Geometry checks passed, but
that does not waive its proxy assertion. The [failed receipt](base-vertices-parallel/native-nullrhi-failed.json)
is preserved. Repeating unchanged tests with real D3D12 gives
[10 passes, zero warnings/failures/skips](base-vertices-parallel/native-d3d12.json).
Covered areas include source packing, shoreline geometry/moving-bank/crest
caches, relief, smoothing, hydraulic crest scale, spatial breaking and froth history.

The candidate v3 normal-start capture has no review-station override or parallel enable flag;
the runtime confirms `parallel=1 forced=0 serial_override=0`. This is a direct
normal map/scenario launch, not a menu-click test. It records 24 source PNGs and
239 native source frames over 15.610 seconds. All 468 encoded movie frames were
decoded, 0 through 15.566667 seconds, with 29 exact adjacent duplicates over
the entire clip. Encoded 30 Hz is NOT measured game FPS. The initial process
receipt's undecoded flag is superseded only by the separate decoder receipt,
not silently edited. [Capture](base-vertices-parallel/startup-process.json) and
[decoder evidence](base-vertices-parallel/startup-decoded.json) retain hashes.

Source endpoints and decoded 6/11-second views show raft/camera motion and
continuous visible water in those views, with no obvious new split surface.
Water remains broad/soft, canopy angular and repetitive, with dark understory
and crew/vest/lighting edge artifacts. No new visual realism is claimed.
Sampled support agrees with submitted wet triangles, including paired detail:
2,034 wet contacts, 401 detail-affected, maximum error 0.0001904072251 cm,
RMS 0.0001086080759 cm, zero unavailable/raw-dry/ground-occluded points.
[Contact summary and raw hash](base-vertices-parallel/startup-contact.json).
This is not GPU upload/latency, full-hull collision or full-route acceptance.

## Final serial-default verification

Final v4 editor/game rebuilds succeed in 40.79/61.65 seconds. The unchanged
D3D12 suite again has [10 passes, zero warnings/failures/skips](base-vertices-parallel/native-d3d12-v4.json).
A fresh normal-start capture confirms `parallel=0 forced=0 serial_override=0`,
with no force/serial flag and no station override. It retains 24 source images,
217 native frames over 15.642 seconds and a fully decoded 469-frame movie,
0..15.6 seconds, 38 exact adjacent duplicates. Decoded 1/11-second views were
inspected: raft/camera move; the same coarse canopy, soft water and crew/lighting
limitations remain. Startup title text also clips at the lower image edge.
Neither recording cadence nor still inspection establishes frame-rate acceptance.

The final support audit has 2,034 wet points (387 affected by paired detail),
maximum 0.0001901733422 cm / RMS 0.0001098014599 cm difference and zero
raw-dry/unavailable/ground-occluded points. These are sampled support contacts,
not full hull/traversal acceptance. [Final binary, capture, decoder, contact and
process receipts](base-vertices-parallel/final-serial-v4.json) preserve the
rollback verification. An additional final 24 audit/motion tests pass; the
earlier broader 34-test receipt is retained separately. All original failed
and candidate evidence remains available. No default CPU gain is delivered.

The source audit remains the sole live qualification, still on case 1 with no
complete derivative report. Its CPU time advances after the final safe resume;
the files it imports were not changed. Preserve this job rather than restart it.

## Unchanged scientific and reconstruction scope

No captured terrain, boulder/source evidence, collision, bathymetry, cooked
field or map content changed. Installed 4,950-second fields remain installed;
the unsettled 15,000-second cook is not promoted. Nonlinear solver stays OFF.
No source-import changes, duplicate cook or source replay were made.
South Fork remains first unfinished; Colorado, Pacuare and Futaleufu remain queued.
