# South Fork selective detail edges — September 28 UTC

Candidate, not river acceptance. South Fork remains the first unfinished river.
Normal v20 rapid timing failed (8310 p95 86.85 ms; 11520 p95 84.01 ms).
The unchanged gate is 20 FPS / p95 <=50 ms / no frame above100 ms.

## Change and constraints

The 16-segment curved high-bank boundary produces thin triangles. Detail
refinement previously split all three edges when the triangle exceeded the
12.5 cm detail span, including already-short edges. The candidate splits only
requested long edges, retaining conforming shared edges and every original
shoreline vertex. Macro-profile error still requests all edges with the same
0.5 cm selection tolerance and three levels. Two-edge green subdivision uses
the shorter L-infinity diagonal, or falls back to all-edge splitting if its
child-size bound cannot be met. Geometry-dependent diagonal choices participate
in topology-cache validation; matching edge masks alone are insufficient.

The ordinary South Fork FullReach scene enables this path. Other scenes and
macro-only refinement retain the reference path. `-RaftSimLegacyDetailEdges`
is a same-build diagnostic reference, not a normal-configuration acceptance run.
The crest-state same-input cache includes the mode, including false/true/false
transitions. No hydraulic field, fixed time step, elapsed-time handling,
shoreline root, material, bathymetry, collision or captured source was changed.

## Native evidence and retained failures

- v1: 8/9 pass; three oblique strips violated the strict12.5 cm size gate.
  Maximum12.6534991192 cm. Failure preserved, not relaxed away.
- v2: 8/9 pass; after size-bound repair, moving geometry reused stale green
  diagonals. Eight cached/fresh mismatches and three span failures exposed it.
- v3: 9/9 pass after cache identity/diagonal validation repair. Eighteen rotated
  moving strips preserve winding, area, exact roots, internal edge incidence2,
  and cached-parallel versus fresh-serial ordered topology.54–96 triangles
  versus128 reference in those fixtures, with maximum span <=12.5 cm.
- Independent interior samples of the actual physical crest evaluator give
  maximum0.288429260254 cm error against the unchanged2 cm gate,4836 triangles.
- v4 integration: editor build succeeded259.23 s;10/10 rendered D3D12 native
  tests pass, zero failed/warnings/not-run. Adds actual crest-state mode-switch
  publication and macro-only exact-reference checks.35 provenance/presentation
  Python tests pass in1.72 s. These are supporting evidence, not real-time cost
  or visual acceptance.

Native reports: `tmp/selective-detail-v1-native-20260928/index.json` through
`tmp/selective-detail-v4-native-20260928/index.json`. Build/test recipes and logs
use the corresponding unique version stems. Protected user water-surface test
SHA256 remains `d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3`.

## Completed playable verification

The v21 package completed exit0 in459.99 s at2026-09-28T08:41:58.9449621Z;
exec96180/wrapper36236 and editor/native owners are terminal. All14 frozen
inputs unchanged. Runtime owner98632/wrapper39384 completed exit0 at
2026-09-28T08:48:40.8509011Z; motion8064 and decoder1063 are terminal. No live
engine/build/cook remains. All14 input hashes still match after runtime.
Package receipt:
`tmp/selective-detail-v21-verification-20260928.json`; package log:
`tmp/south-fork-v21-package-20260928.log`. Fresh stage:
`tmp/south-fork-playable-v21-20260928/Windows`.

`tmp/validate-selective-detail-v21-20260928.ps1` checked staged
payload closure, actual Boot/menu launch,1200-frame menu/8310/11520 profiles,
then80 motion samples, contact export and18 spray-emitter anchors. All four
game logs verify selective edges enabled=1, legacy_override=0. Fewer fixture
triangles alone do not establish lower runtime cost. Receipt:
`tmp/selective-detail-v21-validation-20260928.json`. Existing missing MetaHuman
texture cook dependencies remain unresolved; successful package is not a
clean full-release dependency audit.

Staged closure passes2405 files/917995570 bytes without external fallback.
Three1200-frame runs pass runtime health, with zero runtime errors:

| Run | Mean ms | p95 ms | Max ms | Frames >100ms |20FPS gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu |39.1859|46.9125|60.6124|0|PASS|
|8310|46.1917|69.0185|191.3952|7|FAIL|
|11520|49.7417|72.3977|171.6286|2|FAIL|

At8310, crest update mean9.4459 ms/p9526.7330 ms, selection mean5.6670 ms/
positive mean10.7138 ms/p9518.5309 ms. v20 had update mean11.2504 ms and
selection mean6.6634 ms/positive11.3208 ms. Whole rapid timing is lower in this
capture, but this is NOT a controlled same-build causal A/B. Solver time also
differs (mean9.5359 versus11.9225 ms). Nested scopes must not be summed. The
unchanged rapid gate still fails; no accepted FPS improvement is claimed.

Actual motion advances173.713 m,8313.610 to8487.323, with80 samples. All18
emitter centres pass6/3/3 cm checks. Contact report:1900 wet points, max support
error0.0000476702 cm;129 raw-dry points, all129 ground-occluded; zero occluded
wet points and zero unavailable. Changed triangulation changes the sampled
probes: the earlier exposed positive-film point was not independently retested,
so its absence here does NOT resolve it or establish whole-shoreline acceptance.

Original video fully decodes2480 frames over82.633 s with45 exact adjacent
duplicates; recording FPS is not engine FPS. Inspected6s/20s/80s engine views
show raft travel through the rapid and into calmer water. Broad flat white
foam, weak breaking, detached-looking spray, coarse banks and crew-fit issues
persist. No broad visible realism improvement or temporal shoreline stability
acceptance is claimed. Delivery is the normal-scene geometry optimization with
native coverage/detail constraints and actual playable checks, not a completed
reconstruction. No solver/field/material changes or push.

Decoded views/report: `tmp/sf-v21-motion-decoded-20260928`.
Frame receipts: `unreal/Saved/RaftSimValidation/sf-v21-*-20260928-frame-audit.json`.
Scope/clock receipts: `tmp/sf-v21-*-20260928-scopes-and-clock.json`.
Binary SHA256: `fedc692d34feb87ced605176103d14942c4c0d512de6b2fe9eeabad2e85a504a`.
Video SHA256: `e41ecf4fd80ef64a749be5d84ac0d28326adacab6edc72c4176bcf5a0970cc8c`.
Contact SHA256: `dc6f4821f0b0e3544885b1b1d78b2608441cc8ae41e4bbecd8670825ad91c832`.

Next: attribute remaining rapid/crest cost with the retained same-build legacy
control or a distinct measured repair; do not rerun unchanged captures for a
passing score. Resolve the retained film/boundary cases and visible breaking/
terrain shortcomings without weaker physics, detail or quality gates. South
Fork remains unfinished; Colorado must not start on these results.

## Staging headroom without deleting retained evidence

Windows LZX compressed only explicitly scoped old staged runtime-data folders
and PDBs in v14,v15r2,v16,v17,v19. All15,315 before/after file hashes match;
compact logs total4,674,261,237 bytes saved. No deletion, hardlink alias, source
change or modification of current v20 stage. The v19/v20 UCAS hashes differ,
so neither was deduplicated. Compression is reversible with Windows compact.
Receipts: `tmp/old-staged-data-compression-20260928.json` and
`tmp/older-staged-data-compression-20260928.json`. The14 GiB package headroom
gate was preserved, not lowered.
