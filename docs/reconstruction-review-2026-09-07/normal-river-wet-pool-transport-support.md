# Physical energy and wet-pool transport support

September 14, 2026. **Component progress; actual transport qualification fails.**

This work connects the exact wet-pool geometry to physical-momentum energy and
a pool-aware nondispersive mass/momentum/bed-force path. It does not promote a
new native solver. The real patch needs dry-source activation in 18 cells,
including 17 cells that already contain other wet regions. Adding an unknown
only for the one completely dry cell would not resolve the actual wet fronts.

## Physical-momentum energy and volume work

`physics/scripts/subcell_wet_pool_primal_energy.py` uses the existing positive
inverse factors derived algebraically from the original pressure poles:

`K = S^-1 = K0 I + sum(alpha * Q * (I + beta Q)^-1)`.

These are not fitted replacement poles. The energy is evaluated in its positive
auxiliary form, retaining both original source depth/slope factors and both
velocity components. `Q*z` is evaluated through the original factors, not by
subtracting nearly equal pressure vectors.

The new reverse pass computes all fixed-physical-momentum volume derivatives
without a separate pressure solve for every pool. It differentiates the exact
local Gram matrices, physical-velocity normalization, shared harmonic face
areas, both owners' divergence denominators and physical reflecting walls. The
hydrostatic contribution uses the exact source-volume potential. Its split
contributions remain available for subsequent auxiliary/bed-force coupling.

Independent checks include forward volume directions, individual perturbed
volumes, original-pole dense inverse matrices, physical/canonical momentum
round trips, the prior flat variable-depth formulation and absence of a same-cell
energy connection across a dry ridge.

## Pool-aware base transport

`physics/scripts/subcell_wet_pool_transport.py` considers **all original source
face traces**, not just the common-wet pressure graph. Source triangle IDs remain
attached to wet owners and unassigned dry support.

For fully supported fixed-topology fixtures, it applies the existing exact
pressure-secant mass flux, paired momentum flux and independently integrated
pool bed force. It includes reflecting physical walls and optional conservative
dissipation. Each pool's bed force is also compared independently with its own
hydrostatic boundary pressure integral, exposing missing geometric coverage.

A face can be dry on one side while that side's original triangle already
belongs to a wet pool. Such faces participate in mass transport. They are not
discarded because their common-wet pressure area is zero. A regression exercises
that case explicitly.

If a wet trace instead reaches an original triangle with **no current wet pool**,
the path records the source IDs, receiving parent cell, segment and wet column
area. It returns `volume_rate=None` and `momentum_rate=None`, rather than exposing
partial rates as a usable evolution. It does not invent dry pressure unknowns,
reflect the flow, delete water or assign the receiving region to a disconnected
pool. Conservative one-sided activation is still required.

Even on complete supported fixtures, the nondispersive base is not the full
rational transport equation. In the retained four-pool sloping fixture:

- Nondispersive energy-identity error: 2.7755575615628914e-17.
- Independent hydrostatic geometry-closure error: 5.551115123125783e-17.
- Work under the full two-pole physical energy: **-0.004193213814734642**.

The last quantity is an uncorrected model defect, not accepted physical breaking
or dissipation. The momentum rates are not projected to make it disappear.

## Actual South Fork evidence

Final report: `tmp/south-fork-pool-transport-v2-20260914.json`.

SHA256: `8ec47eb323e99c30a41e5254019b3137de5537223176764dfed1830420f2de70`.

The audit retains the original 600-second atlas, captured-source hashes, exact
registered mesh, 256-cell footprint, 255 wet cells and 258 separated pools. Both
original pressure poles still pass the independent static checks. Actual input
momenta are the original source velocities multiplied by each pool's volume.

| Physical-energy check | Result |
| --- | --- |
| Positive kinetic energy | 2156.913766390772 |
| Hydrostatic potential | 9369.056889819043 |
| Inverse-factor true residuals, 40 iterations | 3.6009e-16 and 2.0533e-16 |
| Canonical velocity vs dense original response inverse, maximum pool-scaled error | 1.1547e-14 |
| Original-pole momentum round-trip error divided by each pool volume | 1.2750e-10 |
| Reverse vs independent forward volume-work error | 2.0194e-15 |
| Positive energy vs contraction error | 4.5475e-13 |
| Largest scaled energy directional-probe discrepancy | 1.9074e-8 |

Physical-energy component controls pass. Perturbation sizes are 1e-4, 5e-5 and
2.5e-5; the scalar energy differences are roundoff-affected, not a convergence
rate measurement. These energy values must not be compared as a runtime gain
with the previous canonical-velocity-shaped diagnostic; those inputs had a
different coordinate interpretation.

The actual transport-support audit **exits 1**, with complete rates unavailable
for both central and dissipative modes. It records 66 unowned wet subsegment
entries, referencing 46 distinct original dry source faces across 18 cells:

`140, 141, 143, 155, 156, 158, 171, 172, 174, 175, 188, 204, 220, 236, 238, 251, 252, 253`.

The raw entries include tiny float-overlap pieces; they are not 66 distinct
physical wet fronts. No threshold was used to discard them. Their summed wet
column area is 2.429514242302173 m2, with a largest single entry of
0.1883945677993253 m2, so the missing support is not merely endpoint roundoff.
These are cross-sectional areas, **not measured discharge**.

The completely dry cell 158 receives candidate support from cell 159 along
original source faces 600739 and 199537, with wet column areas
0.0023193682561967956 and 0.0466864883149149 m2. The other 17 receiving parent
cells already contain wet pools elsewhere. The trace ledger also finds 28
singly wet segments whose two source triangles already have pool owners; those
are included in the base assembly, not treated as unowned activation requests.

No full-state mass or energy conservation is claimed from this incomplete
assembly. The report leaves those rates null, and its base balance gate
unavailable rather than passing it.

## Tests, provenance and next work

Final exact-subcell/triangle suite: **122 passed** in 10.91 seconds, including
24 new physical-energy/transport tests. Report:
`tmp/subcell-pool-transport-tests-v1-20260914.xml`.

Retained original pressure/stress/constant-velocity suite: **34 passed, 12 failed**
in 9.23 seconds, exit 1. All eight paired-base nonlinear energy failures and
four legacy constant-velocity failures remain visible and unwaived. Report:
`tmp/subcell-pool-transport-retained-gates-v1-20260914.xml`.

All 464 protected source/capture/map/profile/actor hashes remain unchanged.
Original vertex authority is preserved; inferred submerged terrain, connecting
flanks and interpolated gaps have not been relabeled as measured bathymetry.
No native code, scenario, ordinary water state or rendered surface changed.

Next implement conservative activation on the reported original source support,
with explicit wet connectivity and one-sided energy/momentum accounting. Do not
spread incoming volume over all disconnected pools in a receiving cell. Couple
the now-available physical volume work to the full rational auxiliary advection
and bed force, then qualify topology events, wet fronts, finite time, open and
refinement boundaries before native/shared-surface integration.

South Fork's actual visual and 30 FPS gates remain failed. Colorado, Pacuare,
Futaleufu, all-scene Chilko/Zambezi water reviews, crew realism/fit/animation,
normalization, outstanding regressions and release remain open. Troublemaker is
a rapid inside South Fork, not a standalone menu scenario. The full goal remains
active; the missing implementation is not an external blocker.
