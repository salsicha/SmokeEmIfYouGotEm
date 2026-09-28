# Adjacent high-bank contour — design evidence, not delivery

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
