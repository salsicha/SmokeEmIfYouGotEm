# Finite-time local dry-front predictor on an original affine bed

2026-09-17. A local evolution component now follows the instantaneous front
flux. It does **not** advance the spatially varying South Fork inlet or qualify
the full dispersive river solver. Installed gameplay, materials and geometry
are unchanged; no new visual, motion or FPS claim.

## Physical model and implementation

The homogeneous wet/dry shallow-water Riemann problem has a rarefaction joining
the wet state to zero depth, with distinct constant-wet, fan and dry branches.
Reference: [Clawpack Riemann book, shallow-water dry states](https://www.clawpack.org/riemann_book/html/Shallow_water.html).

For an affine bed with constant gradient `s`, the implementation derives the
local sloping-bed solution by substituting `X=x+g*s*t²/2` and `u=U-g*s*t` into
the depth and momentum equations. This accelerating-frame extension is our
derivation, separately tested against the two-dimensional equations; it is
not a claim that the reference supplies the full river model.

`subcell_affine_dry_fan.py` accepts the original depth, velocity, bed plane and
an unnormalized front normal. It clips the original convex source polygon at
the moving rarefaction head and dry front, then integrates mass, both physical
momentum components and mechanical energy including original bed potential.
Donor-side changes and receiver-side water come from the same finite-time
solution. Bed force is `-g*s*volume`, not a fitted momentum remainder.

Quadratic-field arithmetic retains the exact square root required by the
original depth and normal. No rounded wave speed changes the input depth; no
positive sub-float fragment is discarded through a float-vertex export.
Floating conversion is presentation-only and uses a converged enclosure.
Affine products are integrated with exact barycentric simplex moments. A
different source slope or nonconvex source polygon rejects explicitly.
This arithmetic adds no measurement precision to captured coordinates.

## Independent controls and actual-source exercise

**51 focused tests PASS**, no skips. Included controls cover the following:

- Exact paired donor loss/receiver gain and the existing homogeneous interface
  mass, momentum and energy transfers.
- Fixed-control-volume finite-time balances against independent analytic
  upstream boundary flux and bed-impulse integrals, for uphill/downhill slopes
  and positive, zero and negative initial velocity.
- Second-order refinement of an independent two-dimensional PDE residual.
- Independent depth quadrature, original polygon partitions, rotation, normal
  scaling, energy-datum changes, and positive rational/irrational sub-float water.
- Existing initial-support and lateral-energy controls, without changing gates.

JUnit `tmp/affine-dry-fan-focused-v2-20260917.xml`, SHA256
`6655643543ca998e059f0e13725c2c1520712e26750445282340170e575de553`.

The same broader physical-water suite plus these tests reports **717 PASS /
13 FAIL**, 730 tests, zero errors/skips, one existing warning, 146.12 seconds.
All thirteen failure identities match the preceding suite: four legacy
constant-velocity energy, eight nonlinear rational energy and one original
storage/face representation failure. No gate, skip or threshold changed.
JUnit `tmp/affine-dry-fan-full-suite-v1-20260917.xml`, SHA256
`74fa7144e2b06f500e4fa461e373acd2118b7298361a98b5405bf52545d3faeb`.

The actual-source exercise uses all eleven previously dry-qualified rays,
including the sub-float ray and original cell 171. For each, it selects the
original interface value at `r=R/2`, checks its registered triangle against the
protected mesh, and evaluates a local predictor for `R³/10`. All eleven have
positive dry-side receipt and exact wet/dry partition sums for mass, momentum
and energy. Two original receding/fan branch records remain unsupported.
Captured-rock versus inferred-flank authority stays explicit.

Crucial limitation: this predictor extends **one sampled interface state**
uniformly over its local wet half-plane. It is not the original varying inlet
profile and does not modify its water state. Original triangle boundaries can
exchange water and energy; exact partition sums are not a closed-triangle time
conservation claim. The 616 protected source/implementation hashes are checked
before and after the exercise. No original source or water array is written.

Report `tmp/south-fork-affine-front-predictor-v1-20260917.json`, SHA256
`f4f6954345eb58eb99d415796c00b3fa56162098b387d68c3380b353c1c6f40d`.
All algebraic coefficients, original local inputs and before/after budgets are
retained rather than replaced by rounded summary values.
An independent reload rechecks all eleven exact serialized budget partitions
and all 619 source/report/predictor hashes. Installed gameplay DLL and production
water-material hashes also match the preceding review.

## Hydraulic continuation and next integration

Same PID 17516/start UTC 2026-09-17T12:52:03.0749210Z remains live. Completed
4500s/local18000 passes state/conservation and all 86,720 artificial dry-bank
checks. Maximum depth 3.831071008 m, speed 5.508648147 m/s, volume
2,868,957.318802 m3, maximum step residual 1.521822357e-8 m3. Outflow
103.557730375 versus inflow 45.306954547 m3/s: **not settled or promoted**.
Reports `tmp/control-ablation-4500s-{state,banks}-v1-20260917.json`; depth SHA256
`d641eb1bcb72d5dd22fb20ec7892884596b2bc8853bc94c3811bc0709106b981`.
Next 4550s/local19000 needs its completion marker and BOTH audits. No restart.

Next incorporate the actual inlet's spatial variation, interactions between
moving fronts, original bed-slope junctions and coupled donor depletion;
derive/check the dispersive metric and energy work rather than appending this
fan to the old distributional pressure term. This local model must not be
silently substituted for those requirements. Then native/playable integration,
source-consistent breaking/froth, reference motion and sustained 30 FPS remain.
South Fork -> Colorado -> Pacuare -> Futaleufu, all-scene Chilko/Zambezi reviews,
crew, normalization, regressions and release are all still in scope.
Troublemaker is a rapid within South Fork, never a menu scenario.
