# Physical/canonical pressure map on moving source geometry

2026-09-18 UTC. Reference component committed in `4e1298b7c`, not a native
solver, nonlinear force closure, or playable water improvement. Normal South
Fork FullReach is unchanged; the known-broken nonlinear runtime remains OFF.
Troublemaker remains a rapid inside South Fork, never a scenario-menu entry.

## Implemented map and energy

For actual source-volume mass `M` and the preceding unnormalised pressure
kinetic matrix `C`, the implementation retains the original two pressure poles:

`B = c M + sum_j w_j M (M + lambda_j C)^-1 M`.

This is the root-free form of `sqrt(M) S sqrt(M)`, not an inverse-pole fit or a
mean-depth replacement. The original represented binary pole constants and
`c = 1 - float(np.sum(WEIGHTS))` are retained. Their represented zero-mode sum
is exactly one; `c` itself is not the exact rational `1/15`.

Given physical momentum `p`, canonical velocity is `v = B^-1 p`, layer
velocity is `M^-1 p`, and kinetic energy is `p dot v / 2`. The analytic
physical-time derivative differentiates both exterior mass factors and the
interior inverse. It gives `v_t = B^-1 (p_t - B_t v)` and
`E_t = v dot p_t - v dot B_t v / 2`.

The original auxiliary pole equations independently reconstruct both momentum
and its derivative. Their nonnegative energy terms must sum exactly to the
physical energy, and their independently differentiated sum must equal the
same energy rate. Symmetry, positive active mass, positive-semidefinite `C`,
and strictly positive solve pivots are checked without floors, clipping or a
pseudoinverse. Positive sub-float volumes are retained; dry fragments have no
velocity unknown. Rational/quadratic-field arithmetic avoids coordinate or
wave-speed conversion through floating point.

These are exact dense reference solves, NOT a native 40-CG budget pass. Supplied
momentum rates do not become a qualified nonlinear force law merely because
the coordinate and energy identities hold.

## Focused validation

The final serialized focused suite has **69 PASS**, zero failures/errors/skips,
43.125 seconds. Report `tmp/moving-pressure-metric-focused-v3-20260918.xml`,
SHA256 `7399de81473ea26b39dc11a19c4ad5217fbfd312f250ae43e97673cf32a65b67`.
The commit turn independently reran the same 69 tests: PASS in40.26 seconds.

Checks include an independent normalized NumPy matrix construction; exact
physical/canonical round trips and both pole residuals; independent physical
time differences with second-order refinement; omission of mass-normalization
work; the original zero mode; positive sub-float mass; quadratic-field state;
invalid/indefinite matrices; and corruption of the metric time derivative.

The first eight-test run had six passes and two failures. The independent
time-difference probe needed finer resolution, not a looser tolerance: the
unchanged velocity gate now uses divisors200,400,800,1600,3200. A test's incorrect
assumption that the represented zero-mode sum differed from one was corrected;
the implemented constants were not changed. The earlier68-pass suite predates
the independent reconstruction corruption control; the final69 cover it.

The broader suite completes with **768 PASS / 13 FAIL**,781 tests in62 modules,
zero errors/skips,262.53 seconds and one existing JUnit warning. Comparing the
serialized failure identities against the preceding suite gives exactly the
same13: four constant-velocity energy, eight paired nonlinear energy and one
legacy storage/face consistency failure. Report:
`tmp/moving-pressure-metric-full-suite-v1-20260918.xml`, SHA256
`8928d8d6306fd833dabb9e3c5736203228c84205092d5a57f8f08fb29f83940a`.

Inspection reconfirms the geometry failure's representation boundary: legacy
`cell_triangles` clips already-rounded float vertices repeatedly, whereas
`triangle_cut` computes original rational intersections before one conversion.
Their endpoint heights differ by up to1.77635684e-15 in this regression.
Snapping the legacy endpoints or loosening equality is not a complete repair:
the float-vertex API still cannot retain positive fragments whose projected
vertices collapse. The exact fragment representation retains those fragments,
but all dependent storage/face consumers must share it before the legacy
requirement is resolved. No source geometry or regression assertion changed.

## Original-source audit still running

`audit_south_fork_moving_pressure_metric.py` consumes
`tmp/south-fork-affine-front-pressure-v1-20260918.json`, SHA256
`95988c6fb0ba57e937ef73b5dce980985e99c48663f67fa881888c3e1d1f2286`.
It uses the recorded original wet/dry momentum and physical-time momentum
rates, verifies their volume ownership, and preserves unsupported records.
Input and imported implementation hashes are captured before evaluation and
must remain unchanged at completion.

The original process17228, started2026-09-18T01:51:57.8200933Z, session43933,
is verified LIVE. Case0/source601454 passed in96.7073165 seconds; case1/source
601453 is still computing. Increasing process CPU time confirms active work;
there is no terminal result or all-case acceptance yet. Do not restart because
a polling interval has no output. Intended fresh output:
`tmp/south-fork-moving-pressure-metric-v1-20260918.json`.
After completion, independently reload the serialized report, verify all13
original records and every protected hash, and distinguish11 supported cases
from the two unsupported cases. No full source-case pass is claimed here.

## Remaining integration

The local front remains one uniform initial state on one affine bed with an
explicit reflecting pressure boundary. Interacting fronts, varying inlet,
slope junctions, open boundaries, conservative nonlinear mass/force evolution,
native iteration-budget validation and shared render/contact integration are
still required. The thirteen existing physical regressions remain unwaived.

The publication-path inspection found no newly qualified runtime optimization;
adaptive crest sampling and geometry publication remain material costs. No
new engine build, capture, visual improvement or FPS acceptance is claimed.
Physical breaking and convincing froth remain unfinished. The last ordinary
profile's p9538.0726ms still exceeds the unchanged33.333333ms requirement.
South Fork precedes Colorado, Pacuare and Futaleufu; Chilko/Zambezi, crew,
normalization, outstanding regressions and release qualification remain open.
