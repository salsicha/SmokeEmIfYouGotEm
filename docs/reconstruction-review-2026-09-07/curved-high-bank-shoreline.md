# Curved high-bank shoreline candidate

September28 UTC. v19 normal package and motion/timing checks are complete.
The curved-bank implementation passes six rendered native tests, but all
three v19 frame-time runs fail the unchanged20FPS gate. v20 optimization is
built, passes the same six tests and has completed normal runtime checks.
Menu timing now passes; both rapid timings and visual acceptance still fail.
Do not claim full shoreline, physics, performance or river acceptance.

## Geometry change

For a cell with three wet positive-depth corners and one exactly dry corner
whose bed is above all three wet stages, the normal South Fork near-field
shoreline now follows a curved zero-depth contour rather than the straight
chord between grid-edge intersections. Other patterns retain their existing
geometry: no positive film is reclassified, no diagonal channel connected,
no solver or raft-support dry gate changed. Captured sources and the normal
450s v8 hydraulic fields are untouched.

The specialization evaluates the wet-donor-normalized stage minus the
bilinear bed. Sixteen boundary segments are rooted on radial rays from the
dry corner to the opposite wet edges. Shared grid-edge endpoints stay
canonical; new nodes are cell-local. Concave polygons use ear triangulation,
not a fan across the dry notch. Vertex attributes and crest/shore weights
interpolate from the two water-bearing boundary endpoints. Cache identity
includes eligibility; changing bed/depth recomputes roots and checks affected
triangle orientation, while unchanged roots are reused. All source history,
publication scheduling and simulation time remain intact.

This is finite-segment geometry, NOT exact continuous clipping. An independent
calculation on the retained v18 cell finds midpoint signed-depth residuals
between-0.003134574m and-0.000339434m on the new chord segments. The large
captured interior discrepancy is excluded by the native fixture, but these
small residuals, other shoreline patterns and ground/hydraulic-bed differences
remain open. This number is not a new acceptance tolerance or weakened gate.
Far-field and other-river coverage is not claimed.

For the eligible case, positive wet depths and dry bed above every wet stage
give a single radial transition. Along a ray x=t,y=kt, the ratio of positive
depth and dry-stage-gap weighted sums is a positive linear-fractional function.
Multiplying by (1-Wdry)/Wdry is strictly increasing from zero to infinity:
the bounds on the two affine logarithmic derivatives leave the positive term
k/(1-kt)-k/(1+k-kt). The axis ray is the direct two-corner intersection.
v19 bisects this transition36 times. v20 evaluates the same radial numerator
as a cubic, using safeguarded Newton with36 bisections as fallback. It retains
all16 boundary segments and does not advance or modify the conserved water
state. Cache eligibility now revisits only three-wet-corner candidates after
the existing exact wet/availability/XY validation, not every lattice cell.

## Checks and retained failures

The first editor build failed only because the native fixture's unqualified
FEdge resolved to Unreal's unrelated type. Its failure log is preserved:
tmp/curved-bank-v1-build-console-20260928.log. After qualification and retaining
degenerate-grid handling, editor build v2 succeeded in15.00s:
tmp/curved-bank-v2-build-console-20260928.log.

All six rendered native tests pass, zero errors/warnings/not-run/in-progress:
CurvedHighBank, ShorelineInputValidation, ShorelineOppositeDryFan,
ShorelineCrestWeights, ShorelineFineCrest and CrestHistory. New coverage includes
all16 wet patterns, both world orientations, rotations, both storage modes,
the captured false-wet polygon and20 changing-depth/cache frames including a
positive film. These are scoped fixtures, not full-scene acceptance.
The35 existing presentation/provenance Python checks also pass in0.91s.

v19 package completed exit0 in380.75s; runtime owner66067 also exited0.
Staged closure passes2405files/917995570bytes without external fallback.
All three normal1200-frame runs pass health but FAIL timing:

| Run | Mean ms | p95 ms | Max ms | Frames >100ms |
| --- | ---: | ---: | ---: | ---: |
| Boot/menu |42.3936|51.2997|82.16|0|
|8310|53.0986|84.4859|213.8052|13|
|11520|61.7149|81.4219|182.3827|1|

The8310 topology scope averages4.4190ms, p956.5504ms, max62.8062ms.
Nested scopes cannot be summed, and these runs are not a controlled causal
whole-frame A/B. They justify reducing redundant contour work, not accepting
the performance regression. Reports are sf-v19-*-20260928-frame-audit.json
under unreal/Saved/RaftSimValidation; scope receipts are under tmp.

Actual motion covers173.365m with80 telemetry samples. All18 emitter centres
pass unchanged6/3/3cm checks. Video fully decodes2481frames over82.667s;
39 exact adjacent duplicates are retained, not interpreted as engine FPS.
Inspected6s/20s/80s views retain broad flat foam, weak breaking, coarse exposed
bank faces and crew-fit issues. These views do not establish a visibly resolved
shoreline at the particular numerical probe or full river acceptance.

The same-call contact report retains1897 wet support points,165 raw-dry points,
164 ground-occluded dry points and no ground-occluded wet points. Wet support
error is at most0.000047645cm. One different, non-ground-occluded raw-dry probe
remains: positive film0.0000575316m, below the unchanged0.0001m wet flag,
at XY(-541595.3968,-360309.8944)cm. Do not erase positive films or relax dry
support to make this audit pass. Triangle-count/stride changes also preclude
interpreting the occluded count alone as a geometry regression.

v19 receipts: tmp/curved-bank-v19-verification-20260928.json and
tmp/curved-bank-v19-validation-20260928.json. Its input hashes stayed unchanged
through runtime. Decoded views: tmp/sf-v19-motion-decoded-20260928.

## v20 terminal validation

Editor build succeeds in152.90s; six rendered native tests pass, zero warnings
or errors. Verification owner63578/wrapper22760 and native PID1144 exited0.
Separate package completes exit0 in390.22s at07:42:46.8974992UTC.
Runtime owner87111/wrapper40300 completes at07:49:55.0559539UTC, exit0;
motion PID23916 and decoder88575 also terminal. No live engine/build/cook.
Ten frozen input hashes still match after runtime, including the protected
user test, unchanged material and450s v8 manifest.35 focused Python checks
pass in1.58s. Existing missing MetaHuman texture cook dependencies remain open.

All three1200-frame normal runs pass runtime health. Gate remains p95<=50ms
and no frame>100ms; failed timings remain failed:

| Run | Mean ms | p95 ms | Max ms | Frames >100ms | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu |35.8861|42.7280|49.5999|0|PASS|
|8310|54.4922|86.8531|240.2744|21|FAIL|
|11520|58.0752|84.0128|171.8490|2|FAIL|

The8310 topology scope falls to mean2.2415ms/p953.0445ms/max59.4162ms,
but overall rapid timing does NOT improve. Crest selection averages6.6634ms,
p9518.5539ms, max57.4138ms; crest update averages11.2504ms, p9527.7787ms.
These scopes nest and must not be summed. No global speedup or accepted
performance is claimed. The candidate's rapid regression relative to retained
v17 remains a next-step constraint, not a tradeoff silently accepted for geometry.

Motion traverses173.842m over80 samples. All18 emitter centres pass6/3/3cm.
Contact:1898 wet samples, maximum support error0.000047655cm;164 raw-dry,
163 ground-occluded dry and zero ground-occluded wet. The one exposed positive
film remains at XY(-541595.3555,-360309.8791)cm, depth0.0000676392m, below
the unchanged wet threshold. This is not whole-shoreline/collision acceptance.
2481 video frames decode over82.667s,43 exact adjacent duplicates. Inspected
6s/20s/40s/80s views still show flat broad foam, weak breaking, detached-looking
spray and coarse bank/crew geometry. The repaired numerical fixture is not a
demonstrated broad visible realism improvement.

Receipts: tmp/curved-bank-v20-verification-20260928.json,
tmp/curved-bank-v20-validation-20260928.json, tmp/sf-v20-motion-decoded-20260928/report.json.
Staged closure passes2405files/917995570bytes without external fallback.
Binary SHA256:9588beb6145bfa53388611f849eb03b585629c5c810b9336c6e3dc268f746678.
Video SHA256:9073787f5a3d0df5b2a8d876e83aa0a8b6b3785afd3caf667469d7d8758b0af7.
Contact SHA256:9bfcdd353e11b914f021388e3df09cff18efa7f795f9ea0654b276801642718f.

Next work: reduce actual rapid/crest publication cost without dropping elapsed
physics time or coarsening this boundary; retain and resolve the film/contact
and finite-segment residuals. Continue measured rendered breaking/terrain work;
do not repeat unchanged captures or move to Colorado on these scoped results.
No push is authorized or attempted.
