# Secondary wet-front receipts and inlet-connected placement — September 15

The eight unresolved curvature edges now have an original face-flux
classification using newborn velocity from incoming momentum divided by
incoming mass. Seven point outward and one inward. This is conditional on the
original **nondispersive** receipt velocity, not acceptance of it as the full
rational front law. No original physical water is advanced or modified.

## Piecewise integration, not a velocity cutoff

`subcell_point_birth_front_flux.py` integrates the existing dry-bed Riemann
branches on a point source's growing original face. Before the first original
storage/face knot, write the local depth as `h`, wave speed `c=sqrt(g*h)` and
face measure `ds=2*L*c/g dc`. Here `L` is the exact original face width per
unit bed-height rise. The integration retains the wet, fan and dry branches:

- positive normal velocity: original wet branch below `h=u_n^2/g`, fan above;
- zero normal velocity: fan for every positive depth;
- negative normal velocity: dry below `h=u_n^2/(4g)`, fan above.

The fan mass integrand is `(u_n+2*c)^3/(27*g)`. Its zeroth, first and second
wave-speed moments supply mass, normal/tangential momentum, nonadvective
pressure and original energy flux. Polynomial integrals are evaluated as
rational combinations of the represented inputs and wave-speed endpoints,
avoiding cancellation or premature loss of tiny velocity coefficients. Final
outputs are ordinary finite floats. This is not a new dispersion model or
replacement Riemann solver, and introduces no water floor or velocity cutoff.

Independent checks use the unchanged original four-node wave-speed quadrature.
They cover all three branches, switching depths, tangential momentum, energy,
pressure, original face subdivisions and zero depth. At a point source the
leading outgoing mass rates are

```
u_n > 0: mass = L*u_n*h^2/2             (inside the original wet branch)
u_n = 0: mass = 16*L*sqrt(g)*h^(5/2)/135
u_n < 0: mass = 0                      (below its original fan threshold)
```

A finite-depth fan must not be replaced by the positive-velocity asymptotic
formula outside its branch. One actual Cartesian normal speed is
`1.9156665383107728e-126`: it remains positive with an exact nonzero branch
threshold, while the tested finite-depth flux is fan-dominated. No probe
water is fabricated at an unrepresentably small asymptotic wet state.

## Paired secondary mass coefficients

For the conditional primary profile `h_i=k_i*t^(1/3)`, with `k_i` derived from
the original positive receipt and exact cubic storage, a mass rate `A*h^p`
integrates to `A*k_i^p/(1+p/3) * t^(1+p/3)`. The audit emits an equal donor
loss and recipient gain for each term. It does not treat secondary sources as
additional order-`t` primary births or erase the corresponding donor loss.

The volume time powers are `5/3` for fixed outward velocity and `11/6` for
zero-normal fan flow. These are conditional asymptotic coefficients, **not**
a coupled conservative time step. Physical velocity/force evolution, branch
changes, source geometry limits and subsequent receipts remain unresolved.

## Actual bank inventory and the placement problem

The source-locked audit retains original block [12,8] and the 600-second
snapshot, with 16 old pools and 24 primary receiving sources. It finds:

| Original newborn/unowned face category | Count |
| --- | ---: |
| Immediate face contact | 13 |
| Delayed original face contact | 10 |
| Immediate curvature-jump faces | 8 |
| Outward curvature-jump faces | 7 |
| Receding curvature-jump faces | 1 |
| Outward secondary transfer terms, all immediate faces | 11 |
| Transfer terms whose inlet contacts the receiving source minimum | 2 |
| Transfer terms whose inlet lies above that minimum | 9 |

The 11 outward terms target ten distinct source regions. The broader
13-face inventory has eleven distinct receiving regions; provenance is ten
exposed-rock regions and one inferred-flank region, not eleven measured
geometries. All source IDs, parent indices, normals, branch thresholds and
receiving-face contact volumes are retained.

For nine transfer terms, a minimum-centered hydrostatic receiving pool starts
away from the incoming face. Its exact stored volume before that face opens
is positive. Merely appending that pool would not establish the required
connected inflow geometry. The audit therefore retains the mass receipt but
does **not** assign an accepted connected-pool update or a receiving height
time power for those terms. The two minimum-connected receipts carry the
conditional `5/9` height power, but their full physical updates remain
unaccepted as well. Incoming-face wet-region geometry and compatible force
transport are required next; mass balance alone does not settle placement.

## Verification

All 13 immediate faces are compared at seven original sub-knot heights:
91 original mass/momentum/energy/pressure comparisons, maximum relative error
`1.2582787860158389e-15`. Matching donor loss and recipient gain coefficients
have exactly zero ledger error. Original physical water remains unchanged.

Final report: `tmp/south-fork-secondary-fronts-v2-20260915.json`, SHA256
`ce2a97247b2faabfd7a94cacfe979aad491c87ee636ec88852a6cde1b9cffd15`.
All 561 source/implementation hashes and 464 protected source/actor hashes
match. Original source/registration arithmetic is retained; exact arithmetic
adds no measurement precision. The block exterior is reflecting, not the
natural open river.

Initial new module: 23 PASS. Expanded focused suite with the existing original
source-activation tests: 48 PASS, including 26 new tests. A preceding focused
command named a nonexistent dry-front test file and ran zero tests; that
failed command/report is retained and is not counted as verification. Tests
also cover malformed/duplicate receipts, conditional fan/outward time powers,
original face-knot rejection and explicit non-acceptance flags.

Full retained source/legacy-energy suite: **534 PASS / 13 unchanged FAIL**,
zero errors/skips, 118.17 seconds, terminal exit 1. Failure identities exactly
match the preceding 508 PASS / 13 FAIL run: one legacy source-face rounding
consistency failure, eight paired-stress energy failures and four constant-
velocity energy failures. The existing JUnit record-property warning remains.
No gate is waived. Report: `tmp/point-front-flux-full-suite-v1-20260915.xml`,
SHA256 `321fc7a9341a6cb04e0874697ed9663c132e5bd205bbefdc69d78f1a0ad4bf56`.
All owned audit/test jobs are terminal.

No native build, fresh engine capture, performance gain or playable visual
change is claimed. Last ordinary South Fork remains 22.429181 FPS / p95
54.7266 ms, failing 30 FPS; broad froth and smooth faces remain unaccepted.
NEXT inlet-connected receiving geometry and one-sided force/transport,
complete rational front/time coupling, edge/flat/mixed transitions, native
single-surface integration and actual motion/reference qualification.
Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene water, crew,
normalization, outstanding regressions and release remain open. Troublemaker
stays a rapid within South Fork, not a menu scenario.
