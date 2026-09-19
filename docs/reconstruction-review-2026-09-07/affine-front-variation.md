# Prescribed-boundary primitive energy derivatives

2026-09-19 UTC. Supporting physics only; no visible gameplay change.

`AffineFrontPressureVariation` now differentiates the same prescribed-boundary
two-pole energy with respect to original owner depth moments, bed slopes,
directed face columns, physical/canonical momentum and each active exterior
mass flux. Both divergence and the boundary lift retain their owner's volume
denominator derivative. The boundary contribution is not absorbed into a
residual or discarded at the exterior.

The two momentum coordinates require different formulas. Physical momentum's
conjugate remains canonical velocity `v`; canonical momentum `m=Mv` has
conjugate `Bv/M=(p-q)/M`, **not** physical layer velocity `p/M`. For the
canonical geometry derivative, the lifted boundary-only jet and homogeneous
auxiliary jet contribute with opposite signs. Reusing the old reflecting
derivatives, or simply negating the physical derivatives, omits boundary work.

Optional solved-state reuse verifies each original prescribed pole equation,
each boundary-shift equation, original represented pole weights/order, and
physical momentum reconstruction exactly. It does not trust success flags or
stored energy derivatives. A forbidden-solve test verifies that the reuse path
does not solve again. Fresh and reused paths give identical primitive gradients.

## Validation and integration guard

**93 tests PASS** in81.81 s across the new derivative module, existing fresh/
reused reflecting derivatives and audit tests, both moving-pressure modules
and prescribed trace tests. Report:
`tmp/affine-front-variation-combined-20260919.xml`.

The23 new cases include independently rebuilt complex-step partials for every
primitive in **both** momentum coordinates at the unchanged1e-10 comparison
gate; exact primitive-time work against the full affine energy derivative;
reused/fresh equality;1e-400 corruption rejection for velocities, weights,
lengths and momentum; incompatible trace/shift rejection; direction-shape
validation; dry-owner/topology rejection; and both old-consumer entry paths.

The reflecting-only `FrontPressureVariation` now explicitly rejects affine
metrics, including its fresh-solve path which could otherwise silently produce
homogeneous derivatives. This corrects the previous plan's unnecessary delay:
direct inspection proved that file is absent from BOTH protected input maps of
the active source replay. All protected/current implementation hashes were
rechecked after this change: **zero mismatches**. No running source implementation
was changed or restarted.

## Still open and live work

These are energy derivatives, **not a conservative nonlinear force/time step**.
Gravity, the compatible transport bracket, interacting fronts and source
activation must still be coupled. Natural/radiating river-pressure conditions
and native40-CG/30FPS costs remain unqualified. Do not enable nonlinear gameplay
or present a derivative identity as evidence of convincing breaking water.

The original momentum replay remains live at PID14076, startUTC
2026-09-19T00:58:32.2675546Z, session35230. Case0 passed and case1 is in progress.
It does not yet cover this new primitive-variation module; a completed source
report and independent source-derivative qualification remain required. Preserve
that job and its protected inputs; do not duplicate expensive pole solves.
While it runs, normal-play publication/mesh cost remains an independent route
to advance the30FPS requirement rather than repeatedly polling the same case.

Sole hydraulic cook12672/session79088 also continues unchanged. The new
12200 s/local4000 snapshot passes BOTH state and artificial-bank audits:
3.997739 m maximum depth,5.388385 m/s maximum speed,1.17982e-8 m3 maximum
per-step residual; all86,720 artificial-bank sample cells exactly dry. It is
**not settled**: outlet105.530710 versus inlet45.306955 m3/s. Next12250/local5000
requires completion and both audits.

Ignored-tmp receipt hashes:

- `affine-variation-hydraulic-4000-state-20260919.json`:
  `5af86c875156d6175c4dd5b807a0fdd85b7ae003cb7ad04a4b68b6dd89267136`.
- `affine-variation-hydraulic-4000-banks-20260919.json`:
  `8e14f47ce94f3a9e5c1ab936493c8c70f7d29544f971b8d8dc41281e39b3a164`.

Normal map, terrain/collision, captured data and installed4950 s fields are
unchanged; nonlinear remains OFF. No new build, motion, collision or performance
acceptance. Latest25.003520 FPS/p95 48.329 ms still fails30FPS. The cap evidence
decision remains pending. South Fork and the complete ordered river/all-scene/
crew/normalization/regression/release queue remain OPEN.
