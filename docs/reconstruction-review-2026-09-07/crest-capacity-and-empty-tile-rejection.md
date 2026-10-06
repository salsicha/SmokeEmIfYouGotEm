# Crest capacity and empty-tile candidates not promoted

September 17, 2026. Commit 0563a034f checkpointed two opt-in experiments, not a
30 FPS fix. This continuation completes empty-tile exactness and actual-input
qualification. Neither candidate qualifies for default enablement. Installed
gameplay, material, quality, topology tolerances and physics remain unchanged.

## Retained topology capacity

The retained-capacity path preserves current selection/profile evaluation and
topology-cache decisions; it only reuses allocation capacity. Its native fixture
passes across 36 moving/deformed roots, crops, winding changes, flat/nonflat
profiles, zero/one/three refinement levels and explicit invalidation. The earlier
33-test native suite passed. Actual capture preserves all 64 pairs, 4,325,576
expanded vertices and 3,166,798 triangles, including three root changes.

Whole-build means are 6.981705 ms reference and 6.948092 ms retained. However,
reference-first pairs worsen from 6.839003 to 6.846546 ms. Maximum measured
topology storage also grows from 2,908,618 to 7,401,287 bytes. The both-order gate
fails; do not repeat this trial to fish for a passing order or enable it normally.

Capture `tmp/crest-topology-storage-pairs-v1-20260917.json`, SHA256
`0ab6dc96c1082acd2bd8e829468ca1eaecf020e6bcf613969ecabb74b02f59e1`.
Analyzer: `physics/scripts/audit_crest_topology_storage_pair.py`; existing
summary is the same stem plus `-audit.json`.

## Empty physical tiles

`SampleWithEmptyTileSkip` returns zero height and foam only after a validated
physical index finds no contributing sites. Invalid coordinates/indexes and
legacy profiles retain the full evaluator. It is opt-in with
`-RaftSimSkipEmptyCrestTiles`; ordinary `Sample` retains its original behavior.

`RaftSim.M4.CrestEmptyTile` checks 183,768 points against both the original
indexed evaluator and the full scan, with exact height AND foam equality.
It covers dense/hash lookup, copied/moved ownership, local/global caps,
non-unit directions, zero-lift foam emitters, support/tile seams, empty input,
large-coordinate fallback and legacy profiles. The fresh native suite passes
34 tests, zero test warnings/failures/not-run/in-process. All five gameplay
translation units compile/link; the existing unrelated C4701 warning in
DetailSourceFootprintTest.cpp remains. The candidate is not installed.

`RaftSimCrestEmptyTileAudit` runs 64 actual changed-input whole builds after two
warm calls, alternating execution order. Independent histories use the current
prepared range and qualified indexed edges; storage retention is off. Ordered
parents, triangles, owners, expanded XY, build/reuse counters and production
topology must match. Python validation retains the original completeness,
finite-value and both-order speed gates without changing native evidence.

| Capture | Vertices | Reference ms | Skip ms | Both orders faster |
| --- | ---: | ---: | ---: | --- |
| v1, ordinary production callback | 4,315,176 | 6.741454 | 6.693919 | Yes |
| v2, shortcut active in gameplay | 4,325,577 | 6.943725 | 6.920669 | No |

Both captures preserve every compared output. In v2, reference-first pairs
worsen from 6.995731 to 7.062803 ms. The first capture's small saving is not
robust qualification. Keep the shortcut off; no additional retry was used to
discard this failure. Neither diagnostic capture is ordinary FPS evidence.

Input reports `tmp/crest-empty-tile-pairs-v{1,2}-20260917.json`, SHA256:

- v1 `d208fbc2b7a9cacc8c8dc0b02ecededad6650467d24f9c7b26a6867bffdf658c`
- v2 `66bac3cf629547cd725f000ce40442700e67419a8b63f189060d30434f1a6e92`

Analyzer: `physics/scripts/audit_crest_empty_tile_pair.py`; summaries use the
same stems plus `-audit.json`. Sixty focused Python audit tests pass. Native
report `tmp/crest-empty-tile-native-v1-20260917/index.json`, SHA256
`714c7845090515a88de574c60b41ea11351f3c6b3386a4457552bafce5dac0d6`.
Candidate DLL SHA256
`452ba32bdaa3c5732f0efe596280faa1d44a4e26d0faf9e23df54b8d4d98222d`.
Native process and both game captures exit 0; both wrappers resume cook 36872
with status 0. Installed DLL remains
`bb80e7c1222bfa027507904f368893f0ed25fb1fc5ce4e8a60889dc1b4e3442f`.

The last ordinary installed measurement remains 27.565906 FPS / p95 42.8224 ms,
failing the unchanged 30 FPS / 33.333333 ms gate. Sheet-like froth, local breaking,
rapid geometry, later rivers, crew, regressions and release remain open.

## Hydraulic continuation and next physical comparison

The original cook PID 36872 is verified live; it was not restarted. Both 3300 s
(local 30000) and 3350 s (local 31000) snapshots pass state/conservation checks
and all 86,720 artificial-bank face cells remain exactly dry. At 3350 s,
maximum depth is 4.142920 m, speed 5.504222 m/s and maximum step conservation
residual 1.647021e-8 m3. Outflow 88.040640 versus inflow 45.306955 m3/s still
precludes settling acceptance. These states are not installed runtime data.

Reports `tmp/control-ablation-{3300,3350}s-{state,banks}-v1-20260917.json`:

- 3300 state `72ebb0992a85cf6e465e8864a40c75e969b48d5486c44978a80fbcdb81d90391`
- 3300 banks `fb514fc0b359e7364d0d2dd893a706938e0e26e848d407e6af37442eeb8de74b`
- 3350 state `fcaee9d2857466563d89a4224a6dbfc2cb3dfe66bd19b44ac108fd017c888988`
- 3350 banks `b2bc0dcdeef621dce6de1bdea00c3900b3013713c63481ccafc717002be1f6ab`

Fresh export `tmp/control-ablation-runtime-3350s-v1-20260917` verifies 841 tiles,
799 source packets and 42,185,039 exact source-bed intersections. It reuses 791
unchanged bed/mask packets and rebuilds eight union packets. Atlas SHA256
`3342c824a76454e71839003d1dee1e234c469c7380c56feebf49714efab7f0bc`.
Coverage checks all 406,823 original-water probes, retaining the explicit
region_0002 rectangle correction and minimum 10 m raft-interior margin.
Prepared 25,600 native water queries at the same comparison center
(-5437.499999998952, 3606.5) m. Native terrain/collision and visual comparison
must pass before drawing conclusions; neither export nor settling is acceptance.

Subsequent native verification, paired captures and the exposed terrain-rendering
correction are recorded in [joint-preview exact ground](joint-preview-exact-ground.md).
Those close the pending native-query check above, not hydraulic settling, water
realism, performance or release acceptance.
