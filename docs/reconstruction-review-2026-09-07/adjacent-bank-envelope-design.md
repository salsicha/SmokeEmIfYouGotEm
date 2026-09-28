# Adjacent high-bank contour - delivered in v24, river acceptance open

September28 UTC. The second v22 exposed raw-dry probe has two adjacent wet
corners, so the three-wet-corner ray correction does not apply. The existing
straight edge is not the zero-depth contour of the production mixed sampler.
Do not change the hydraulic wet threshold to make that edge appear valid.

For canonical bottom-wet/top-dry cells with both dry beds above both wet
stages, the mixed sampler reduces exactly to:

    depth(x,y) = max(H(x) - y D(x), 0)
    H(x) = a + b x
    D(x) = c + d x > 0
    zero-depth boundary f(x) = H(x) / D(x)
    k = b c - a d
    f'(x) = k / D(x)^2
    f''(x) = -2 d k / D(x)^3

These are point-reconstruction identities, not a new physical evolution law.
The curvature sign is constant. For convex f, the maximum of supporting
tangents stays below f; for concave f, inscribed chords stay below f.
Linear cases are exact. Retain canonical shared-edge endpoints.

For a tangent at t, the entire interval has the exact identity

    f(x) - T_t(x) = -d k (x-t)^2 / (D(x) D(t)^2).

Adjacent tangent intersection abscissae have a stable form without dividing
by tiny curvature:

    x = (u D(v) + v D(u)) / (D(u) + D(v)).

Sixteen tangent sites give fifteen internal intersections and sixteen boundary
segments. Concave cells use sixteen inscribed chords. This is a conservative
wet-side boundary approximation, not an arbitrary inward offset or depth floor.

## Exact retained case and proof scope

Source: tmp/sf-v22-motion-20260928-contact.json, SHA256
bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.
World probe XY(-539440,-360243.409684)cm gives cell coordinates
(0.6,0.434096837980). At x=0.6:

- Existing straight boundary y=0.472632015561 includes the dry probe.
- Exact hydraulic zero-depth boundary y=0.358887819135 excludes it.
- Tangent envelope equals the exact boundary at this tangent site.

The first prototype incorrectly asserted strict separation of tangent and curve
at every point; corrected to permit their exact contact while retaining strict
probe exclusion and nonnegative-depth certification. No physical gate changed.

Proof recipe: tmp/prove-adjacent-bank-envelope-20260928.py.
Reports: tmp/adjacent-bank-envelope-proof-20260928.json and
tmp/adjacent-bank-envelope-proof-v2-20260928.json (both retained).
Fractions preserve the captured floating-point inputs exactly. Every segment
checks the minimum of its quadratic depth numerator over the full interval,
including interior extrema; this is not a sampled dry-exclusion test.
The captured case and256 deterministic varied cells certify4112 segments:
245 randomized convex cases,11 concave/linear-branch cases, plus the capture.
This does not exhaust degeneracies or all wet masks.

For this one-metre captured cell, the full-interval maximum wet-side boundary
width error is exactly147011807861069/85885759252201472 metres,
approximately0.001711713434m. Convex curve-minus-tangent error is maximal at a
segment endpoint, so checking all retained intersection/endpoints gives this
bound. The1001-point sampled maximum0.001697501476m is smaller and MUST NOT
be substituted for the bound.

## Required next implementation and acceptance

After the existing v23 package/runtime sequence, integrate a scoped adjacent
high-bank branch in the actual shoreline constructor. Preserve disconnected
diagonal channels and low dry advancing fronts. Native regressions must cover
four edge orientations, world rotations/reflections, compact/reserved geometry,
shared-edge identity, nonzero films, changing eligibility, cached/fresh topology,
near-linear limits and conservative segment coverage. Convex boundaries can
make the polygon concave: triangulate without bridging the excluded dry region.

Use the actual new point coordinate for height/attribute and crest-weight
interpolation; tangent intersections are not uniformly spaced fractions.
Implement a production accuracy bound/adaptation policy for arbitrary cells:
the1.712mm captured-case bound does not qualify every other bank.
Keep rendered geometry and raft support on the same resulting triangles.
Then rebuild the normal playable scene and inspect actual motion, retained
contact failures, temporal shoreline behavior and measured cost. No source
files used by the running v23 package or physical replay were changed for this
design. No engine integration, visible repair, whole-shoreline or river
acceptance is claimed from this mathematical prototype.

v23 actual motion subsequently retained two more adjacent-pair failures:
right-wet XY(-540205.571313,-357415)cm and bottom-wet
XY(-544875,-362923.153609)cm. Their same-call source cells/triangles are in
tmp/sf-v23-motion-20260928-contact.json, SHA256
b2d4a544721bb3c911b09110e9efdc6472935154c4771fc6488a8edbb721c3c8.
Include both, plus the original v22 case, in production regressions.

A potentially cheaper triangulation for this restricted branch follows from
constant-sign f': choose the wet base corner at the end with the greater
boundary height as the fan anchor. For increasing f, segments from (1,0) to
any boundary point remain beneath the monotone boundary; reverse for
decreasing f. Supporting-tangent envelopes inherit the derivative sign.
This avoids adding unmatched subdivisions to the shared fully wet base edge.
This is a design argument only; implement and test actual polygon coverage,
winding, attributes and cache evolution before using it in normal play.

## Production implementation and native verification

September28 UTC: the preceding design-only status is historical. The normal
RaftSimWaterShoreline constructor now uses RaftSimAdjacentBankContour for exactly
two adjacent positive-depth corners with exactly zero depth at both high dry
corners. Positive films and low advancing banks retain the existing path;
linear contours retain their already-exact common-edge chord. No solver,
hydraulic wet threshold, source capture, bed or cooked field changed.

The production branch is ADAPTIVE, not the fixed16 prototype above. Its maximum
transverse geometric error is0.1cm (1mm); this is not a depth floor. Convex cells
use supporting-tangent intersections, concave cells use inscribed chords. For
each parameter interval[u,v], the convex intersection error is exactly
abs(d*k)*(v-u)^2/(2*D(u)*D(v)*(D(u)+D(v))); the concave curvature bound is
abs(d*k)*(v-u)^2/(4*min(D(u),D(v))^3). Subdivide until the bound times the actual
world transverse edge length is at most0.1cm. Nonfinite/unrepresentable bounds
fail the build rather than silently coarsen. Stable tangent intersection height
is(H(u)+H(v))/(D(u)+D(v)), avoiding slope cancellation.

The monotone polygon fans from the higher-boundary wet base corner, retaining
the existing common-edge endpoint nodes and adding no nodes on shared wet base
edges. Height, flow channels and coarse-crest/shore weights use actual along-edge
fractions, not adaptive node ordinals. Cache identity includes pair side and
fan direction; changing adaptive node count triggers a fresh topology build.
The existing three-wet-corner radial path remains unchanged, including its
known finite-chord limitations.

Native recipe: tmp/verify-adjacent-bank-v2-20260928.ps1.
Receipt: tmp/adjacent-bank-v2-20260928-process.json.
Session28923 and native39448 ended0; editor build20.11s, all10 requested rendered
D3D12 native tests passed without failed/skipped/in-process tests, all12 frozen
inputs unchanged. Completion2026-09-28T10:40:16.3574457Z. Protected user water-test
SHA256 remains d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3.
The v1 failure receipt/log remain: a test's unqualified FEdge collided with an
engine type and a local C shadowed the cell index. Both compiler errors were
fixed before v2; no test or geometry gate was relaxed.

New RaftSim.M4.AdjacentBankContour coverage:

- Three retained pair cases, four bank sides, compact/reserved nodes, mirrored
  world axes and rotated cells:96 geometry variants, each built old/new. Each old
  chord includes its captured dry probe; each new contour excludes it.
- Whole submitted triangle edges have nonnegative bilinear depth within1e-9m
  numerical roundoff, including interior quadratic minima; a bilinear saddle
  has no strict interior minimum. Winding, point sampling and actual-coordinate
  height/crest attributes also pass.
-256 deterministic varied metric cells certify continuous conservative segment
  depth and the maximum entire-interval1mm geometric error, not only samples.
- Exact-linear and both near-linear curvature signs are representable.
-32 cache frames match fresh construction in topology, ownership and every
  submitted attribute, including actual adaptive node-count changes, fan-sign
  changes, tiny positive films and low banks. Unchanged topology reuses cache.

Existing nine endpoint/curved-bank/crest/cache tests also pass; the curved-bank
suite includes all16 wet masks. These are native correctness checks, not a
whole-reach collision/shoreline/performance or visual acceptance.

## Preserved storage and the one pending playable owner

Lossless LZX compression completed for unused v4-v20 packaged executables/Engine
files and v22 runtime data/symbols.3591 before/after file hashes match, zero files
deleted. Captured data, current v23 baseline and v21 timing-control package are
untouched. Receipts:

- tmp/old-stage-executables-compression-v1-20260928.json:528 files, session31628,
  wrapper25240, completed2026-09-28T10:39:58.4243443Z, terminal0.
- tmp/v22-staged-data-compression-v1-20260928.json:3063 files, session86686,
  wrapper40232, completed2026-09-28T10:41:13.4656987Z, terminal0.

Free space after the second completion was15,928,033,280bytes. This is a live
disk reading, not a compression-only savings measurement while builds ran.
The unchanged14GiB staging gate passed.

ONE normal v24 BuildCookRun is live: session98175/wrapper37452, started
2026-09-28T10:41:40.7066662Z. Recipe tmp/package-adjacent-bank-v24-20260928.ps1;
receipt tmp/adjacent-bank-v24-package-20260928.json; stage
tmp/south-fork-playable-v24-20260928. Follow this owner; do not duplicate or
change its frozen inputs. On terminal0 independently verify completed receipt,
unchanged hashes and staged closure, then run the prepared
tmp/validate-adjacent-bank-v24-motion-20260928.ps1. Decode/review the new video
and contact report before claiming visible delivery, stability or motion.

The original prescribed physical replay33152 remains live(index0 checked,
index1 started); it was neither restarted nor edited. Any concurrent game
checks are NON-TIMING. No isolated20FPS result, river acceptance, nonlinear
solver activation or move to Colorado is justified by this implementation.

## v24 normal playable delivery and remaining limits

The pending-owner section above is historical. Package98175/wrapper37452 ended0;
BuildCookRun434.72s. Completed receipt
tmp/adjacent-bank-v24-package-20260928.json records
2026-09-28T10:49:37 completion, all18 frozen inputs unchanged. Staged closure
tmp/adjacent-bank-v24-staged-closure-20260928.json passes2405files/917995570bytes
with no external-source fallback. Known missing MetaHuman face dependencies
remain release issues: a successful cook is not a clean release qualification.

Normal runtime session52530/wrapper32320 ended0. Receipt
tmp/adjacent-bank-v24-motion-20260928.json completed
2026-09-28T10:52:11.6253744Z. Default Boot -> actual main menu -> FullReach ->
600 post-travel captured frames passed exact ordering, normal selective-mode
and zero-error checks. The separate rapid recording retained80 motion samples,
8313.076->8483.933m (170.857m). All18 emitter centres pass6/3/3cm placement.
Both launches were concurrent with the original source replay33152: no isolated
FPS statistics or20FPS acceptance; no isolation guard was bypassed.

Contact evidence: tmp/sf-v24-motion-20260928-contact.json.1859 wet support points,
maximum support/carrier error0.000047554025cm.155 raw-dry points are all classified
as ground-occluded by the registered ground sampler; zero exposed raw-dry,
unavailable or ground-occluded-wet points in THIS sample. It is one early-frame
sample with geometry-dependent triangle stride. The changed sample locations
do not establish that every earlier probe, shoreline segment or collision is
fixed. The three exact retained adjacent-pair cases are independently covered
by the native regression. Existing three-wet finite-chord discrepancies remain
outside this repair; terrain-source/occlusion and whole-traversal checks remain
required. Do not make dry hydraulic support wet to conceal a mismatch.

Decoder13271 ended0. All2482 original1280x720 frames decode with increasing
PTS0..82.7s;56 exact adjacent duplicates. Report/frames:
tmp/sf-v24-motion-decoded-20260928/report.json. Engine views at6/20/80s were
inspected: the raft traverses the rapid and reaches calmer water; broad flat
foam ribbons, weak breaking geometry, coarse rock/bank forms and crew/paddle-fit
problems remain. This is narrow shoreline delivery, not a broad water realism,
continuous-animation, full collision or surface-continuity acceptance. Encoded
frame rate is not measured game FPS. No cinematic enhancement or substitute
water layer was used.

Binary SHA256:
727819bb18d829477ed274eef8096cd495db909c2490e19a3b161c63d8159484.
Video SHA256:
d60f4bc4d8972cc2f876572db636c07abd13509015a91b030e55da588f5e0041.
Contact SHA256:
86219d95126c617e53b8977601e68f54a09cbb4818e57affb369a6dd103283fa.
After runtime/decode the18 frozen input hashes and the original video/contact
hashes were independently rechecked. Implementation commit a62f136d5 is local;
no push. No package/game/decode process remains live in this chain.

The SAME physical replay33152 remains live, CPU6351.75s at the last check,
index0 checked/index1 started. Preserve its sources; do not restart it or claim
that source-text/native tests complete the physical breaking model. Keep the
full river queue, actual water realism and isolated20FPS gates open. Latest
free space10,548,801,536bytes does not meet the14GiB next-package gate; no data or
old package was deleted. Further space recovery must preserve captured evidence
and valid timing-control packages, not lower the gate.
