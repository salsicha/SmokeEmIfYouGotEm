# South Fork playable detail shutdown repair — September 26

The startup water-detail failure is repaired in the rebuilt standalone game
and editor. This restores continuous detail updating in the normal playable
scene; it is not new terrain, source acquisition or river acceptance.

## Exact observed failure and repair

The diagnostic packaged Boot/menu run reproduced the failure at cell10110,
grid(126,78), origin(-144.5,-56)m:

- depth0.184797242m;
- velocity(-0.781726241,-0.880908549)m/s;
- aeration/source strength1.00000012, one float step above the allowed1.

The strict guard correctly rejected it. Detail stopped after21 updates and
3.256s. See [exact cell receipt](south-fork-entrainment-roundoff/invalid-cell.json)
and [log](south-fork-entrainment-roundoff/invalid-cell.log). The guard now
reports the cell index, coordinates, all four input values and window origin.

`FRaftSimDetailEntrainment::Build` constructs source strength from the product
of two cubic ramps. The repaired helper uses `t*t*(3-2*t)` in the lower half
and `1-u*u*(3-2*u)` in the upper half, where `u=(B-X)/(B-A)`.
This is the same mathematical smoothstep, but its upper branch approaches1
from below. It prevents the one-ULP source overshoot without clipping
unexplained water inputs or relaxing the downstream guard. The source
thresholds, accepted-crest merge, GPU equations, physics and quality settings
are unchanged. No experimental solver was enabled.

The observed game failure and repaired game are the production evidence.
The separate scalar native sweep did **not** reproduce an old-formula
overshoot (`legacy overshoots=0`); exact compiler lowering responsible for the
optimized producer's rounding was not established. Do not claim that sweep
as a reproduction of the original defect.

## Native regressions

Standalone and editor builds succeeded. All three focused native tests passed
(NullRHI; these test input math, not rendered GPU evolution):

- `EntrainmentRoundoffRange`:2,000,002 samples across both ramp domains,
  bounded and monotone; maximum error against a double-precision cubic
  1.17411645e-7. The observed1.00000012 input is still rejected.
- `InputAndCFLValidation`: strict source/depth/CFL checks plus exact-cell
  diagnostics.
- `AcceptedCrestEntrainment`: existing accepted-source/merge contract.

[Native log](south-fork-entrainment-roundoff/native-tests.log), exit0.

## Delivered executable and normal launch

The existing v4 cooked package is at
`tmp/south-fork-playable-v4-20260926/Windows`. Its standalone executable and
matching symbols were refreshed from the successful Development build.
This is a C++ producer-only repair: cooked assets, shaders and v4 runtime
data were not changed or recooked. The earlier package data verification
remains evidence for those unchanged payloads, not a new cook claim.

Repaired executable SHA-256:
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
The original failed candidate and symbols are retained at
`tmp/south-fork-v4-original-66a090e9.exe` and `.pdb`; older stages remain intact.

Actual inner packaged game, no project/map/station/quality override:
Boot → main menu → FullReach → post-travel CSV. Resolution1280x720,
offscreen rendering, ephemeral profile,1,200 frames with existing audit
rows30..1169. No competing engine/build was running during the measurement.

- mean40.1431ms; p9549.7416ms; max82.0997ms;
- zero frames over100ms; zero runtime Error/Fatal messages;
- detail352 preparations over53.476s, backlog0; renderer texture bound;
- game exit0; executable hash unchanged during run;
- start-water raft samples stay wet, support delta0, no ground penetration.

[Healthy timing receipt](south-fork-entrainment-roundoff/healthy-menu.json),
[game log](south-fork-entrainment-roundoff/healthy-menu.log).
This narrowly passes the user's20FPS/50ms p95 and single-frame>100ms gates
for this start-section run. Maximum consecutive pair153.1562ms is retained
in the receipt, not hidden; the agreed hitch gate is single-frame, not pair.
There is very little performance margin and no full-route acceptance.

## Actual motion and limits

A separate direct-FullReach review-camera run at the ordinary spawn captured
10 frames with paddling, no station relocation and no physics/quality override.
World time12.320289..16.866564s and render frames352..423 advance; speed
1.95..2.54m/s. It exited0, logged no errors and continued detail preparation
for19.898s/133updates with zero backlog. This is not a menu/performance test.

[Motion log](south-fork-entrainment-roundoff/motion.log).
First/last screenshots were inspected: paddles change pose and the shore
moves relative to the raft; water stays rendered without a gross open seam
in this short view. It remains broadly smooth here. This does not prove
breaking-wave realism, boulder collisions or long-duration shoreline stability.

![First repaired motion frame](south-fork-entrainment-roundoff/motion-000.png)
![Last repaired motion frame](south-fork-entrainment-roundoff/motion-009.png)

Next work remains South Fork: longer healthy route/rapid checks, over-budget
busy rapids, geometry/collision consistency, shoreline continuity and physical
validation. Inferred underwater geometry is still inferred. Colorado, Pacuare
and Futaleufu remain queued. No push, history rewrite or captured-data deletion
was performed.
