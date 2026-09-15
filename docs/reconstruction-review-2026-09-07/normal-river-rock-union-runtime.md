# Actual full-map rock union and compound runtime source packets

September 15, 2026. This extends the [source reconstruction and fresh
cook](normal-river-dem-rock-union.md). No playable assets, water state, menu,
or material were saved. Troublemaker remains a rapid within South Fork.

## Combined saved-map collision

The test loads `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach` and its
relevant existing physical-ground actors, checking saved actor/mesh hashes.
It first traces the retained terrain, then imports the source-exact candidate
transiently at the ACTUAL rapid actor's placement:
`[-543186.6369777592, -360044.75875617936, 0]` cm, scale `[1,-1,1]`.
No simulation, actor-package save, asset save, or old-water replacement occurs.

All 27,245 probes pass the unchanged 0.1 cm (1 mm) positional gate:

| Probe group | Hits / queries | Maximum error, cm |
| --- | ---: | ---: |
| Retained hydraulic cells, before candidate | 12,800 / 12,800 | 0.00200953983 |
| Same cells, combined solid union | 12,800 / 12,800 | 0.00200953983 |
| Roof-face centroids | 1,021 / 1,021 | 0.00216000838 |
| Exact original vertices, interior-cone rays | 549 / 549 | 0.0325033774 |
| Exposed union-side midpoints | 75 / 75 | 0.000157238506 |

Exactly 118 hydraulic-cell rays switch to the new candidate, matching the
118 changed bed samples. Every other cell retains the original ground owner.
Side probes lie above the original terrain; buried internal closure faces are
not incorrectly treated as exposed union boundaries.

Report: `unreal/Saved/RaftSimValidation/south-fork-rock-union-full-map-v1-20260915.json`.
This verifies sampled static collision in the affected area of the actual map,
not raft traversal, all subcell interfaces, visible materials, or dynamic water.
The prior two vertical extremal-ray failures are retained separately;
`prior_vertical_tangent_gate_closed` remains FALSE. No gate is waived.

## Explicit compound-source runtime packets

`south_fork_rock_union_packets.py` produces a distinct union schema. It validates
the original dependency graph and recomputes every changed source field from
the same `SourceRockUnion`. Self-consistent rehashing of the wrong bed, stage,
mask, frame, domain, or cook identity is insufficient to pass verification.

All 799 original source-window identities and grids are retained. Eight packets
change, with 944 repeated samples (118 physical cells represented in overlapping
packets). Captured masks and captured stages remain exact. Runtime source arrays
from the other 791 packets are reused only after the existing hash, dtype,
shape, frame and exact decoded-value checks. Changed packets use newly written
arrays, never an exemption that reuses the old bed.

Manifest: `tmp/south-fork-rock-union-source-packets-v1-20260915/manifest.json`.
SHA256 `d8a2f5f8de66dd8c937e7aebe05757d267c73cc6dc9f9b94e014d7485a4ced8b`.

The one-second pilot was exported as a DIAGNOSTIC runtime dataset, not promoted:
`tmp/south-fork-rock-union-runtime-pilot-v1-20260915`.
41,987,038 packet/atlas bed intersection comparisons are exact. These include
overlap repeats, not that many distinct physical cells. All 836 state tiles
remain. Atlas SHA256
`cfc94ae92e7ab11737366a8cd9a83878bf2ee02920500c936c23dbea6b6cdfc5`.

Full-footprint coverage audit finds two unavailable cells in one old center
rectangle near a physical exterior face. The existing coverage-repair procedure
writes a SEPARATE candidate streaming manifest; original evidence is retained.
All 406,823 original captured-water probes remain covered, including 3,822 that
need shifted centers. Minimum raft interior margin is 10 m, above the unchanged
8 m gate. Report `tmp/south-fork-rock-union-runtime-coverage-v1-20260915.json`;
checked manifest is the export's `streaming_manifest_coverage_checked.json`,
SHA256 `e750d8857b392212b6abad38a97757eace187a8d21e51c432212d631a237e9f4`.
Coverage alone is not hydraulic/visual acceptance.

## Actual native loader, source fields, and combined ground

The second native test repeats all combined collision checks and configures a
new real `RaftSimWaterRuntimeAdapter` from the candidate export. The 224 m window
uses region_0191 at `[-5437.499999998952, 3646.5]` m. It samples all 12,800
hydraulic-cell positions against the original exported arrays, with no solver
steps, snapshot relabelling, or changes to the saved playable configuration.

Initial v1 verification incorrectly equated the solver's `h > 1e-6` wetness
with the native sample's existing presentation `Depth > 1e-4` flag. Five cells
disagreed. The report is retained. Inspection of
`FRaftSimLiveWaterWindow::Sample` established the two distinct contracts.
v2 checks BOTH explicitly: 2,961 solver-wet cells, 2,956 native-sample-wet cells,
zero flag mismatches. Neither threshold, source depth, nor engine code changed.

Final report `unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json`:
all 12,800 field queries pass, alongside all 27,245 collision probes. Maximum
bed/surface errors are 7.62939453125e-6 m, depth 1.1913647846e-7 m, and velocity
7.6816264905e-8 m/s. Height publication allowances remain 1e-4 m (bed/surface)
and 1e-5 m (depth), with 1e-5 m/s velocity tolerance; collision remains 1 mm.
This is a loader/coordinate/geometry match for the one-second pilot, NOT an
evolved runtime, settled river, renderer, or playable traversal acceptance.

## Long cook and outstanding acceptance

The SAME long cook remains live: session45187, PID32276, output
`tmp/south-fork-rock-union-cook600s-v1-20260915`. No restart occurred.
First complete checkpoint, step1000 / 50 s, passes independent state and
artificial-bank audits. Maximum depth 4.2770837885 m; speed 12.1668771292 m/s;
maximum step mass residual 1.1540668865e-8 m³. All 86,720 artificial bank-face
cells exactly dry. Outlet total about 27.974 m³/s versus inlet 45.307 m³/s:
this is NOT settled. Reports `tmp/south-fork-rock-union-50s-{snapshot,banks}-v1-20260915.json`.
Last observed progress step1200 / 60 s, live. Next complete checkpoint is
step2000 / 100 s. Target remains 600 s, not automatic acceptance at that time.

97 focused source/terrain/region/settling/packet/dependency tests PASS:
`tmp/south-fork-rock-union-runtime-suite-v1-20260915.xml`. All 464 protected
hashes match; no candidate asset saved. Native sessions and short export/audit
jobs are terminal. Only the documented long cook remains live.

NEXT: audit later complete cook checkpoints and settling; qualify the retained
tangent-ray evidence; verify visible source mapping/materials and real motion;
stage the candidate mesh, matching runtime packets and valid coverage together
only with sufficient evidence. Actual raft contact/traversal, subcell coupling,
cresting/breaking/froth, and full-river visual acceptance remain OPEN. No normal
FPS run this turn: last 24.225877 FPS / p95 47.78 ms still FAILS 30 FPS /
p95 33.333333 ms. Prior 13 physics and four presentation-text regressions,
Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene water, crew,
normalization and release all remain OPEN.
