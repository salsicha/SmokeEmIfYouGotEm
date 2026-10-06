# Common local inlet side-front flux — not playable acceptance

2026-09-17 UTC. The preceding pressure-residual work exposed a finite-height
side front in the conditional inlet profile. It cannot be advanced using
incompatible wet/dry one-sided pressure tractions. This change supplies a
bounded common local mass and XY momentum flux. It does not advance water.

## Physical law and geometry

The side ray is `s=0`, with depth `h=k*r`, tangential velocity `u` and exactly
zero normal velocity. The homogeneous hydrostatic dry-bed rarefaction has
interface depth `4*h/9` and outward speed `2*sqrt(g*h)/3`. Its mass flux is
`8*h*sqrt(g*h)/27`; normal momentum flux is `8*g*h*h/27`. These are the existing
`subcell_dry_front_flux` zero-normal branch, not a replacement physical model.
The rarefaction structure and dry-state connection are independently described
in the [Clawpack Riemann book](https://www.clawpack.org/riemann_book/html/Shallow_water.html#Dry-initial-states).

With `X=A+u*(R^3-r^3)`, the original ray measure is `3*|u|*r^2 dr`.
An integrated mass primitive is `16*k/81*sqrt(g*k*|u|^2*r^9)`.
The normal momentum primitive is
`8*g*k^2/45 * sign(cross(D,u)) * (-u_y,u_x) * r^5`.
Thus normalization of the ray normal cancels exactly from its momentum
integral. Tangential momentum is the same mass flux times `u`.

Original convex source inequalities clip the ray using the same exact
Bernstein interval classification as the preceding pressure audit. The common
classification helper now returns proven and unresolved radial intervals;
pressure moments retain their original enclosure gate. Radical mass primitives
receive explicit rational square-root bounds. Unresolved crossings contribute
their entire possible flux interval and fail if the requested bound is not met.
There is no depth/time floor, deleted sliver, rounded source relocation, or
finite-difference normal. Rational arithmetic adds no surveyed precision.

A ray on a shared source boundary returns the same outward-oriented flux from
either query. It must be owned once, with its negative used for wet-side debit
and positive used for dry-side credit. Returned paired bounds are correlated;
they are not two independent forces. This API neither chooses the owner nor
mutates a pool. Summing duplicate boundary queries would be incorrect.

## Actual South Fork evidence

Original source-curvature report, registered terrain and 600-second atlas,
block `(12,8)`, unchanged prior observation windows:

- Ten representable conditional streams, 17 routed source pieces.
- Nine pieces have proven positive lateral volume transfer; the other eight
  have zero side-ray intersection. No source crossing is discarded.
- All eleven represented original receivers are queried, including the
  positive sub-float stream. Its ray does not intersect that receiver; this
  does not prove that its full out-of-receiver side flux is zero. The existing
  routing status remains explicitly unrepresented at float time/volume range.
- Two receding/fan inlet records remain unsupported.
- All 601 source/implementation hashes rechecked. Original pool volume and
  momentum unchanged. Previous 55-pair separation checks and moment enclosures
  remain in the report, not converted to a coupled physical state.

Actual audit: `tmp/south-fork-inlet-lateral-flux-v1-20260917.json`, SHA256
`7585d37d043264c92ebfcf404a8fb62fa7ae0222e645bb00c1433d1fde2b9182`.

Focused suite: **48 PASS**, 4.72 seconds. Covers an independent physical-distance
quadrature of the existing Riemann solver, closed forms, common shared-front
queries, source partitions, rotation/winding/large datum shifts, positive
sub-float flux and explicit unresolved-budget rejection. Independent centered
fan integrals on the initially dry half-line match the local interface flux.
Existing pressure and source-face tests remain in this focused run.
JUnit: `tmp/inlet-lateral-flux-focused-v1-20260917.xml`, SHA256
`4c10cca9dbc210ebb51924b4720ac82b9e7094b5e8281ece91541398d8dac769`.

Broad regression: **622 PASS / 13 unchanged FAIL**, 635 tests, 154.62 seconds
(154.599 JUnit), zero errors/skips and one existing warning. All thirteen
failure identities match the preceding suite: four constant-velocity energy
failures, eight nonlinear rational energy failures and one original storage/
face representation mismatch. No tolerances or requirements changed.
Two initial launch attempts collected no tests because JUnit class names were
mistaken for module paths; the final explicit module list was checked before
execution. Those setup attempts are not test evidence.
JUnit: `tmp/inlet-lateral-flux-full-suite-v3-20260917.xml`, SHA256
`ebb9fbb22855a3132df87d80f1032b8862a30f7dbc79f5eb307c279765058b44`.

## Concurrent hydraulic and native checks

Same hydraulic continuation51728/PID36872 reached2400s/local12000. State and
all86,720 exact-dry bank checks PASS on5,382,400 cells. Maximum depth
4.1379203776m, speed6.9553250390m/s, volume2,966,817.6448607133m3 and maximum
step mass residual1.6470207420e-8m3. Outflow95.5047555611m3/s versus
inflow45.3069545472m3/s: **NOT settled, NOT promoted**. Next2450/local13000
requires both audits after its completion marker.

- State: `tmp/control-ablation-2400s-state-v1-20260917.json`, SHA256
  `d0c99ea936e71c5d423e6e1c5b41c2b37cdb6a3736d19203263978ee08d005f9`.
- Banks: `tmp/control-ablation-2400s-banks-v1-20260917.json`, SHA256
  `0d78fe8a8fb470ff099e7432dbcbf929956373c0024d7351ebf2a93e99dfde57`.

Same native replay55459/editor36412 and worker37836 remain directly verified
LIVE after the earlier7200-second hung-shadermap error. Later diagnostics still
list transport permutations4/21. All63 frozen shader hashes match. No restart,
terminal result or native acceptance inferred from the watchdog.

## Required next work and unchanged scope

This supplies only a local instantaneous homogeneous hydrostatic flux at the
conditional profile's side front. It is not a finite-time two-dimensional fan
on sloping terrain. Explicit single ownership, donor depletion, evolving depth
and momentum, consistent energy, source crossings, pressure/bed/curvature
coupling and the original branch transitions are still needed before native
integration. Do not add this flux to the old distributional pressure residual
without a consistent control-volume derivation: that could double-count it.

No installed module, shader, terrain, material or crew changed. Last ordinary
28.057157FPS/p9541.2354ms still FAILS30. Playable South Fork terrain/boulder/
collision/wave/froth acceptance, Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi
and all-scene water, crew, normalization/regressions and release remain OPEN.
Troublemaker remains a rapid within South Fork, never a menu scenario.
