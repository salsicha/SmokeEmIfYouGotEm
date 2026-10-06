# Tracked surface volume and crest-preserving transport

2026-09-11. South Fork remains incomplete. The previous goal turn made progress
on native-representable density/contact correction. This turn distinguishes the
actual tracked interface from a rejected density candidate, implements a
terrain-aware geometric volume measurement, and prepares a higher-order scalar
transport reference for GPU integration. No game surface or saved map changed.

## Correcting the interpretation of the gap diagnostic

The preceding 6583 outside particles / 759 missing occupied columns describe
the fixed 0.5 **density candidate**, not the actual native tracked interface and
not pixels in a rendered game screenshot. That candidate must not replace the
native scalar simply because its deposited kernel integral preserves volume.

`audit_liquid_particle_surface.py` assembles all twelve actual owner interiors
and physical-edge halos exactly once. It validates the existing native scalar
transport/clock/halo audit and samples the same retained pre-advection scalar
against original and corrected particle positions in the surveyed parent frame.

Evidence: `liquid-particle-surface-v2.json`, source particle package
`tmp/south-fork-liquid-local-contact-retry-v1-20260911` (manifest
`26fb949874f54194df52eb982d596536e47602fa3588c06aefe7edc8bb6c45b9`), native capture
`liquid-native-residual-600-v1` (stages
`cf016de8b61dd325f01fe76313f6241fac4f924730137e0d3a63777d95ab2a8e`).

- Original particles outside tracked scalar: **129**.
- Corrected particles outside the still-unmoved tracked scalar: **181**.
- Newly outside after correction: **52**; newly inside: **0**.
- Material-scalar change RMS: **0.0104013 m**, maximum **0.265577 m**.
  These are scalar values, not geometric signed distances.
- All 726905 particle samples have complete stencils. No outside marker was
  deleted, moved back, or relabelled as spray.

Thus the density correction still needs consistent interface transport. Keeping
the old interface is not correct either, even though its coverage is much better
than the density candidate. Parent-frame sampling is explicit; this report does
not claim bit-identical native per-owner float demotion at every marker.

## Geometric volume, not cell-count volume

New `liquid_interface_volume.py` integrates every negative interval along Z
exactly for each XY query of the trilinear scalar. It clips intervals against
the **unchanged exact registered triangle bed**, including multiple vertical
liquid intervals rather than reducing everything to one height per column.
Horizontal Gauss quadrature splits at scalar grid knots and adapts per column.
Successive-order differences are numerical estimates, not certified error bounds.
No phase mask, density cap, water-height shift, solid-kernel reinterpretation or
terrain modification is used to manufacture matching volume.

The half-sample Z endcaps use an explicitly declared linear extension of the
first/last two scalar samples to the grid faces. Their volumes are reported
separately, not presented as directly captured samples.

| Quantity | Native tracked scalar | Corrected density candidate |
| --- | ---: | ---: |
| Above-bed volume estimate, m3 | 15301.800953 | 14573.001842 |
| Difference from marker volume | +1.04297% | -3.76953% |
| Lower extrapolated cap volume, m3 | 0 | 0 |
| Upper extrapolated cap volume, m3 | 0.412120 | 0 |
| Unresolved columns at maximum order 128 | 0 | 29 |
| Sum of last per-column absolute differences, m3 | 1.113625 | 0.829111 |

Nominal marker volume is **15143.85461798869 m3**. Both candidates still fail
surface/particle consistency. The density candidate's 29 unresolved columns are
retained in the report; this is not convergence or volume acceptance. Native
scalar resolved-Z volume is 15301.388832 m3, so the small upper-cap model does
not explain its discrepancy. The v1 report stopped at order16 (1687/2633
unresolved columns); v2 refines the same geometry without relaxing the 1e-4 m3
per-column successive-order criterion. Both reports are retained.

## Higher-order transport implementation

`liquid_interface_highorder.py` implements limited BFECC using the existing
RK2 characteristics and compact velocity basis: forward transport, reversed
transport, correction of the original scalar, then a third forward transport.
The input and caller-owned halos remain unchanged. Invalid forward traces still
invalidate the step. Cells without complete owned round trips, or touching the
explicit solid mask, use the valid original lower-order transport. Only
nonzero-weight donor corners contribute to extrema bounds and readiness.

New extrema are bounded by the actual contributing original scalar range.
This limits a scalar interpolation correction, not particle positions, density
or physical mass. It is not a substitute for volume conservation or particle
correction. The implementation remains CPU-only, **not installed in native
Niagara or the visible renderer**.

Primary basis: [Selle et al., An Unconditionally Stable MacCormack Method](https://physbam.stanford.edu/papers/stanford2006-09.pdf)
describes both MacCormack and BFECC, extrema controls and boundary fallback.
[Enright et al., Animation and Rendering of Complex Water Surfaces](https://graphics.stanford.edu/papers/water-sg02/)
motivates maintaining the evolving interface rather than relying on rendering
alone; no claim is made that the current code implements their full particle
level-set method.

Failed attempts are not hidden: the two-pass MacCormack reference failed the
predeclared translating-crest requirement (error below half the lower-order
error); excluding zero-weight donors fixed a limiter defect but not that
accuracy failure. BFECC with reversion at extrema also missed the same target.
The final donor-bounded BFECC variant passes the **unchanged** target:

- 24 steps, 0.3-cell translation per step, analytic Gaussian crest.
- Lower-order profile error norm: **0.50302524**.
- Final higher-order profile error norm: **0.23229276** (46.18% of baseline).
- Crest heights: lower-order **0.366385**, higher-order **0.532951**, sampled
  exact profile **0.684426**. This is improved but visibly/numerically imperfect.

No inference of complete real-whitewater accuracy follows from this synthetic
translation test. Momentum transport and particle-correction maps are untouched.

## Actual river-field reference cases

`prepare_liquid_interface_highorder_cases.py` validates the current native
capture and evaluates all twelve same-step scalar/velocity/solid fields.
It preserves source hashes and algorithm snapshots; immutable capture inputs
are referenced rather than redundantly copied.

Package: `tmp/south-fork-liquid-interface-highorder-cases-20260911`.
Manifest SHA256:
`6d892811165d2eaea6c100ce1afc30d97a153bbcbe48e07d93df25ecab4b074c`.
All **2178720** samples are retained in expected float32 outputs. All twelve
forward traces are valid; no errors are masked by the accuracy fallback.
Maximum change from the lower-order output is approximately **0.642274 cm**
(owner5). This difference is not proof of accuracy improvement in that actual
state: there is no analytic next-state ground truth. The package is an operator
reference at step600, not an evolved high-order 600-step river.

## Verification and next action

529 `test_liquid*.py` tests pass (7.640s). Fourteen new tests cover affine and
anisotropic volume, exact vertical intervals, thin/disconnected sheets, explicit
caps, unresolved quadrature, translated crests, caller boundaries, solid fallback,
no new extrema, zero-weight donor corners and unhidden invalid traces.

All owned jobs are terminal: surface-v1 session50801 exit0; refined surface-v2
session22734 exit0/146.35s; actual-field cases63700 exit0/175.33s; tests21977 exit0.
No UE/build was launched this turn. No native solver, game scene, collision,
crew or captured terrain files were changed. No final commit or queue closure.

Next: implement the tested high-order scalar update on GPU and verify it against
all prepared actual fields; integrate proper intermediate halo/solid handling
before any continuous regional run. Couple the density correction to the same
interface and measure terrain-clipped volume, coverage and sustained source/exit
storage together. Do not replace the tracked interface with the rejected density
isovalue, apply a global river-height shift, or claim photo/FPS acceptance from
these CPU tests. Then continue the full original scene/crew/cleanup/delivery queue.
