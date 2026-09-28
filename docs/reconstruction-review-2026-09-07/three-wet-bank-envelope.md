# Three-wet conservative envelope reference - September 28 UTC

Status: exact geometry construction, capture-bound proof and a verified native
candidate kernel; **not normal-renderer integration or playable delivery**.
Normal v24 is unchanged. The known
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

## Native candidate and independent stored-coordinate proof

`RaftSimThreeWetBankContour.h` now implements the candidate using outward-rounded
binary64 intervals. It restores the calling thread's floating-point state;
the tested x86 path disables FTZ/DAZ while proving geometry. Other architecture
control implementations are explicitly unverified. The normal shoreline
builder does NOT include/call this header yet. No game command-line opt-in was
added, and no incomplete solver was enabled.

The first native run compiled but correctly failed its new test. Degenerate
segment triangles repeat one endpoint; all coefficients supported solely on
that exact point need the corresponding polynomial identity. The missing
identity was added, including positive/negative controls. Ten existing native
regressions passed even in the first failed run. The failed v1 receipt remains.

The v2 native suite passed, but the independent Fraction audit found that a
rounded shared endpoint in the v22 case was microscopically dry. Its ideal
rational position was valid; its stored binary64 position was not certified.
No negative-depth tolerance was added. The candidate now rounds the endpoint
toward water above an outward-rounded root bound, and uses the factored edge
polynomial to prove the stored coordinate. This rounding rule MUST be shared
by every neighboring cell when integrating with canonical production edges.

The v3 and optimized v4 native suites both pass eleven tests with zero warnings,
failures, not-run or in-process tests. The independent
`physics/scripts/audit_native_three_wet_bank.py` reloads17-digit coordinate
strings as exact binary64 rationals, verifies edge incidence, complete polygon
area, every wet triangle, dry band triangles and the geometric band width. It
reports ideal endpoint and actual stored-coordinate certification separately.
All FOUR v3/v4 cases now pass strict stored-coordinate wet certification:

| Case | Boundary segments | Wet triangles |
| --- | ---: | ---: |
| Original v22 bank | 67 | 69 |
| Original v18 bank | 35 | 37 |
| Symmetric high bank | 16 | 18 |
| Thin positive donor | 33 | 35 |

The auditor's twelve synthetic rejection tests pass1.37s, covering changed
hashes, missing/duplicated triangles, bad indices, nonfinite vertices,
inconsistent boundaries, shifted endpoints, oversized bands, reordered case
identity and false playable-acceptance flags. These are audit tests, not extra
captured-source cases. The earlier sixteen exact-reference tests remain valid.

## Native cost and remaining integration work

The v4 implementation carries already-computed endpoint roots down the
subdivision stack and reuses invariant root bounds and coefficient identities.
All exported boundary/inner/polygon coordinates and triangle indices are
bit-identical to v3 in all four cases. Same-binary A/B/B/A controls also compare
every node/bound and triangle index, not just a checksum or sample point.

For the difficult v22 cell, actual root solves fall256 ->68. Eight samples per
policy give median3.621750ms with reuse versus6.452300ms with repeated solves.
These are native kernel times concurrent with the original source replay, NOT
isolated game FPS or a river-wide cost acceptance. A few milliseconds PER BANK
still makes construction frequency and real bank counts important. Do not
enable this kernel wholesale and claim the performance problem solved.

Current authoritative native receipts:

- Recipe: `tmp/verify-three-wet-native-v4-20260928.ps1`.
- Receipt: `tmp/three-wet-native-v4-20260928-process.json`.
- Engine report/log: `tmp/three-wet-native-v4-20260928-native/index.json` and
  `tmp/three-wet-native-v4-20260928-native.log`.
- Editor build11.92s, terminal exit0; native exit0,11 tests passed. Completed
  `2026-09-28T11:57:11.6791163Z`. All14 frozen input hashes independently match.
- Native export: `tmp/three-wet-native-v4-20260928-geometry.json`, SHA256
  `7763b4e6ded3ffdbc56c104569b9038fe7cd2c8b6ecdf34b582095a376edb404`.
- Exact reload: `tmp/three-wet-native-v4-20260928-exact-audit.json`, SHA256
  `3e707b4641977da2e239dcfa112151bf780806076c86873b2297d9bafef36e3a`.
- Rejection tests: `tmp/native-three-wet-audit-v1-20260928.xml`.

Next integrate canonical shared-edge wet rounding and account for world-space
transform rounding, then variable bank metadata, transported attributes/crest
weights and topology-cache identity. Changes to certified ears, not merely
node count or winding, must invalidate cached connectivity. Measure real
construction frequency/cost before normal enablement; then package and verify
actual normal launch, motion, contact, shoreline continuity and performance.
Native Entry-map tests are NOT actual river views or animation validation.

The original physical source replay33152 completed terminal exit0 at
2026-09-28T12:03:19.7417947Z after checking all11 supported records. Its report
is130,803,564bytes; unsupported2/7 remain outside that tested set. Its independent
terminal/hash/ledger reload16732 is live (session56370); do not duplicate it.
`tmp/verify-prescribed-physical-reload-20260928.py` refuses to run until
the original receipt confirms terminal success, then checks all13 records,
unchanged unsupported branches, provenance and exact saved kinetic ledgers
without rerunning the expensive source solves. Normal v24 remains unchanged.
