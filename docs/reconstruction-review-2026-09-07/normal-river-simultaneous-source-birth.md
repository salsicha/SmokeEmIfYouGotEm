# Simultaneous original-source pressure births — September 15

This extends the single-point pressure boundary limit to neighboring sources
that acquire water simultaneously. It is reference mathematics and an original
geometry/operator audit, **not** a conservative front force, time integrator,
native implementation, visual improvement or gameplay acceptance. The full bank
stage's unresolved-activation guard remains unchanged.

## What was missing

The ordinary source-region face enumeration omits dry/dry internal edges because
neither side owns water. That is correct for the original positive-water state,
but insufficient to derive its simultaneous birth limit. An optional ownership
overlay now exposes those original edges without changing the partition, adding
water, moving vertices, welding point contacts or treating dry support as walls.
The default enumeration and physical pressure path are unchanged.

The overlay retains exact original source IDs, rational clipping and projected
edge lengths. Cartesian source traces already expose unowned source IDs. Exact
source minima must coincide for immediate newborn/newborn contact; higher faces
and unequal minima remain disconnected in the leading birth limit.

## Coupled limit

For each original point-source region, set its height above its own minimum to
`e_i = k_i*e`, with fixed positive `k_i`. Its leading volume is
`V_i = R_i*e^3`, where `R_i = c_i*k_i^3`. The parameter `e` is not physical time.
Old volume and physical momentum are fixed; new physical velocities are bounded.

The original harmonic shared-face area between two newborns has leading form
`A_ij = a_ij*e^2`. Its coefficient integrates the original harmonic column on
the common wet support. Rescaling the sloping bed coordinate retains the exact
logarithmic antiderivative and original face width/bed-span ratio; it does not
replace the face by a mean depth. Noncoincident source minima have no immediate
common wet interval. Flat/edge storage is explicitly not covered here.

Let `q_i=sqrt(V_i)*u_i`. Each source's normalized scaled jet is mapped from all
newborn `q` values. A shared face contributes to the divergence row for owner i:

```
k_i*a_ij/(2*sqrt(R_i)) * n . (q_right/sqrt(R_right) - q_left/sqrt(R_left))
```

Its two velocity rows select `q_i`. Old-wet faces and physical reflecting walls
retain their original single-point divergence terms. Each point-cone Gram is
applied through positive squares from its original triangle gradients and exact
volume coefficients, rather than a repaired eigenvalue decomposition. Summing
the mapped factors gives the coupled newborn principal operator `D`.

The old/new normalized cross block is `sqrt(e)*B`; the old divergence columns
for source i scale by `sqrt(k_i)`. For each original pole, with
`v=B.T*(I+beta*Q_old)^-1*q_old`, the leading physical kinetic-energy slope is

```
S = -1/2 * sum(alpha*beta * v.T*(I+beta*D)^-1*v)
```

The coupled solve uses the existing range-normalized 40-CG routine and local
2x2 positive block preconditioning. There is no global dense inverse, increased
iteration budget, omitted connection or extra pressure coefficient. Small dense
matrices appear only as independent unit-test oracles. Independent single-source
slopes cannot generally be summed: three adjacent-source fixtures with equal and
unequal stage scales discriminate this error.

## Actual South Fork bank

Command (repository root, configured Python and original geometry dependencies):

```
python -B physics/scripts/audit_south_fork_simultaneous_birth.py --source-report tmp/south-fork-source-curvature-components-v1-20260914.json --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/south-fork-simultaneous-birth-v2-20260915.json
```

The original 4x4 bank block [12,8] at the old 600-second snapshot has 16 existing
pools and 24 receiving original source regions. It contains four immediate
newborn/newborn internal edges. No original water was changed. Exterior block
cuts are reflecting, not the open river. Receiving provenance remains 16 exposed
rock, four mixed exposed/inferred and four inferred flank sources. Exact source
arithmetic preserves supplied geometry, not additional measurement precision.

Two directions were chosen before finite probes: uniform stage scale, and
`k_i=cbrt(nondispersive_receipt_rate_i/c_i)`. The latter only defines a geometric
probe direction; the nondispersive receipt is not accepted as full-model flux.
Each direction checks seven decreasing heights before every original source and
face knot, against independent positive-water energies and **all 48 newborn
columns of the original full pressure operator**.

| Probe direction | Analytic energy slope | Final slope error | First → final maximum column-scaled error |
| --- | ---: | ---: | ---: |
| Uniform stage | -3.314751954459744e-4 | 0.0224859% | 1.1439443e-4 → 1.7874747e-6 |
| Receipt direction | -6.125017071707947e-5 | 0.0599557% | 6.8581072e-4 → 1.0718013e-5 |

The original 1% energy-slope check and factor-of-three refinement check pass.
The new operator check requires final column-scaled error below 1e-4 and at
least factor-three refinement. Each column has its own scale, bounded below by
one, so a large steep-source column cannot mask a different direction. This is
a numerical limit check, not a terrain/collision tolerance.

Maximum coupled residual is 7.608e-18 (at most the unchanged 40 iterations).
Maximum finite original pressure residual is 2.621e-16 and positive contraction
error is 2.221e-16. Fourteen full positive-water probes perform 672 column checks.
Tiny added volumes, down to 1.967e-25 on the last receipt-direction probe, are
explicit geometry probes, **not** a minimum water volume or time-stepping rule.

In this particular bank state the coupled and independent-sum energy slopes
coincide to rounding: the connected group in parent 3 has zero old pressure
coupling, and the connected pair in parent 10 has nearly zero leading auxiliary
response. Thus energy alone would be weak evidence for the four connections.
The independent all-column check is essential; the manufactured adjacent-source
tests separately demonstrate a nonzero effect on energy.

Final report SHA256:
`8eb941306e0a8c564368c9c2b99a1ac070d98c451207856e08e8fcf89fdcde97`.
All 547 source/implementation hashes matched at completion and recheck; all 464
protected source/terrain/actor hashes are unchanged. Earlier energy-only report
`tmp/south-fork-simultaneous-birth-v1-20260915.json` is retained, but the final
report adds the stronger column evidence and original positive factor action.

## Tests and remaining work

The focused test command covers 18 tests: 13 new simultaneous-birth cases and
five original single-birth tests. It checks dry/dry edge exposure without
mutation, invalid ownership, equal/unequal stage scales, Cartesian contacts,
unequal exact minima, full pressure columns, finite energy refinement, a small
dense solve oracle, stage reparameterization, stale state, invalid scales and
audit input rejection. An initial Cartesian fixture landed exactly on a source
topology event and correctly rejected; its initial water stage was moved from
2.0 to 2.17, with no solver guard or tolerance change.

The first full source run reports 406 PASS / one retained legacy geometry FAIL.
Final combined source/legacy energy verification reports **421 PASS / 13 FAIL**,
150.65 seconds, terminal exit 1. The failures are the same one legacy source
geometry mismatch (maximum 1.776e-15), eight paired-stress nonlinear energy cases
and four constant-velocity nonbreaking energy cases. None is waived, marked
expected or routed to another model. Report:
`tmp/simultaneous-birth-final-suite-v1-20260915.xml`. All owned audit/test jobs
are terminal. Generated reports remain ignored rather than committed.

Next required work is conservative full-metric front work/forces and its
singular birth behavior, edge/flat pressure limits, then verified time/open/native
coupling to the single playable surface. These derived coefficients do not make
the previously rejected bank time step valid. No engine performance was measured
in this turn: the last ordinary 12.257837 FPS / p95 98.2909 ms still FAILS the
30 FPS target. South Fork visual qualification, Colorado → Pacuare → Futaleufu,
all-scene water, crew, normalization, remaining regressions and release remain open.
