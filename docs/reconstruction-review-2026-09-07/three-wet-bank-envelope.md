# Three-wet conservative envelope reference - September 28 UTC

Status: exact geometry construction and capture-bound proof, **not native
integration or playable delivery**. Normal v24 is unchanged. The known
three-wet finite-chord deficit, water realism and 20 FPS gates remain open.

## Defect and an unsafe shortcut

The balanced 16 radial rays fix the endpoint-spacing problem but their
straight boundary chords still cross negative reconstructed depth. The new
regression reproduces this using the original v22 binary32 cached bed/depths.
It also rejects a tempting shortcut: a diagonal from the opposite wet corner
to the zero-depth point on ray t=3/4 has a negative numerator approximately
-0.000037743155 at 0.009 of the way from the boundary. Thus increasing radial
resolution and fanning from one wet corner is not sufficient. The current
native curved-bank path already uses ear triangulation; preserve that insight.

## Exact construction

Canonical dry corner is (0,0). With bilinear weights w and positive donors at
the other three corners, the sign of the unchanged mixed sampler is the sign
of its numerator N:

    N = sum(w_i H_i) - w_0 sum(w_i (B_0 - B_i)), i=1,2,3.

This is a bidegree-(2,2) polynomial. On any triangle, expand the bilinear
weights in barycentric coordinates. Elevate the first degree-two term to
degree four by multiplying by (lambda_0+lambda_1+lambda_2)^2. The homogeneous
power coefficients divided by positive multinomial factors are the quartic
Bernstein coefficients. Their signs certify the whole triangle, not just its
corners, edges, centroid or a dense grid. Inconclusive bounds subdivide exactly;
exhausting the proof budget fails closed, never relaxes a depth threshold.

The reference constructs a radially ordered boundary with small wet-side
advances from zero-depth roots. Advances are bounded by half the specified
geometric width and half the remaining distance to the cell border. Exact
shared-edge crossings are unchanged. Each candidate interval must prove its
complete boundary segment wet and a triangle from the dry corner to its
contracted endpoints dry. Dyadic subdivision refines only unresolved spans.
An optional node removal must satisfy the same complete wet/dry certificates.

Finally, triangulate the retained polygon with individually wet-certified
ears. No fixed-anchor fan is substituted. The dry triangles cover the omitted
corner outside a narrow strip. Each strip endpoint is within the specified
L1 distance of its corresponding outer endpoint; convexity bounds every
intervening strip point's distance to the outer segment. Thus any omitted
positive water is confined to that geometric band, while no retained triangle
contains negative depth. This is a geometric approximation, not a physical
depth floor or permission to delete a positive donor.

For world positions P+x*X+y*Y, local width <=0.1/max(|X|,|Y|), with X and Y in
centimetres, bounds the world-space band to 1 mm by the triangle inequality.
This covers rotation, reflection, unequal scale and nonorthogonal axes.

## Evidence and scope

- Module: `physics/scripts/three_wet_bank_envelope.py`.
- Capture binding: `physics/scripts/audit_three_wet_bank_capture.py`.
- Tests: `physics/tests/test_three_wet_bank_envelope.py`.
- Recipe: `tmp/verify-three-wet-envelope-v2-20260928.ps1`.
- Receipt/log/XML: `tmp/three-wet-envelope-v2-20260928-*` and matching `.log`/`.xml`.
- Exact rational proof packet: `tmp/three-wet-envelope-v2-20260928-capture.json`.
- Packet SHA256: `5ef90266c04078af34de8fe90870a972a5a871f28ae9ee650cc28fac30f9600b`.

Sixteen tests pass in27.60s, zero failures/errors/skips; terminal exit0 and
completion2026-09-28T11:31:31.5964734Z. Seven frozen inputs independently
rehash unchanged after completion, including the protected user surface test.
Tests cover both v18/v22 banks, eight varied high banks, exact polynomial
agreement with the independent donor sampler, thin positive donors, invalid
inputs, vertical datum/unit invariance, geometric partition area, the retained
dry probe, and physical band bounds under reflection/rotation/shear/scale.
The earlier14-case run also passed; it is retained, not substituted for v2.

The capture audit rereads the actual v22 contact report, requires unchanged
SHA256 bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f,
finds the unique retained raw-dry probe and uses its SAME-CALL cached bed/depth
values. It does not silently substitute the later current hydraulic samples.
No captured source, terrain, bed, physical solver or licensing record changed.

The captured envelope has69 initial segments and67 after certified node
removal, versus16 in normal v24. There are69 retained wet triangles. Exact
rational proof duration is NOT native cost or game FPS. This larger topology
must not be presented as a free or already delivered rendering improvement.

## Required native implementation and verification

1. Port the polynomial/certificate and adaptive geometry while preserving
   canonical shared crossings. Explicitly account for floating-point rounding;
   a sampled minimum or arbitrary negative-depth epsilon is not this proof.
2. Keep local source identity and fractions for transported attributes and
   crest weights. Generalize the three-wet bank metadata from16 fixed segments
   to variable counts. Rebuild on count/ear-connectivity changes and check cached
   output against a fresh build under changing beds/depths/films and transforms.
3. Validate all output triangles and the dry-side band, not merely roots.
   Failures must be surfaced; do not silently mark an unproved old chord safe.
4. Measure native construction/cache cost before enabling a more expensive
   normal path. Then rebuild and verify normal Boot/menu/rapid motion/contact,
   shoreline continuity, support/collision and actual rendered animation.
5. Isolated20FPS testing awaits the SAME live physical-source replay33152's
   terminal/report/hash check. At this checkpoint it remains live at index1,
   CPU advancing; no duplicate was launched and none of its loaded inputs changed.

No new engine build, package or game launched in this reference step. Free
disk space remains about10.5GB, below the unchanged14GiB next-package gate;
safe additional headroom is needed before staging. This does not block the
native implementation work itself. South Fork remains first in the queue.
