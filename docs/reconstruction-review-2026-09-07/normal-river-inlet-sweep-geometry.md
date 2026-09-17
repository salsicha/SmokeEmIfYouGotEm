# Original-source inlet-connected geometry

September 15, 2026. This implements conditional geometric support, not an
accepted pressure/force/time law or a playable water change.

## Representation and bounds

`physics/scripts/subcell_inlet_sweep_geometry.py` places incoming water at its
original edge, not at the receiving source's minimum. It clips the stream to
original convex source fragments and returns bounded depth moments, powers
zero through three. Original source IDs, bed gradients and elevations remain.

For original edge A+s D with positive bed rise B, conditional primary height
coefficient k, and constant incoming velocity u, observation time R^3 gives

    X(r,s) = A + s D + u (R^3-r^3)
    h(r,s) = k r - B s
    0 <= r <= R, 0 <= s <= k r/B

Here r^3 is entry time. Projected measure is 3 |cross(D,u)| r^2 ds dr, so

    integral h^p dA = 3 |cross(D,u)| k^(p+1) R^(p+4)
                      / [B (p+1) (p+4)], p = 0,1,2,3.

Volume matches the integrated original outward-wet mass flux. This is
conditional leading constant-velocity advection, NOT the coupled shallow-water
or rational front solution. Its free surface is not horizontal. Hydrostatic
pool APIs cannot consume these moments as a drop-in physical state.

The constructor rejects the original edge knot and fan regime. The actual
audit additionally retains donor storage/face knots and represented-normal
branch bounds. Receiver-direction validation rejects reversed flow. Shared
endpoints come from exact original polygons, not rounded XYZ face exports.

Polygon half-planes become cubic constraints in entry-time root r and linear
constraints in edge fraction s. Rational Bernstein bounds certify polynomial
envelope intervals for exact integration. An unresolved switch interval keeps
[zero, full incoming strip moment on that interval], never a deleted sliver.
Failure to meet the requested integration bound raises an error.

Default bounds are 1e-12 of each incoming moment per fragment; the combined
audit gate is 1e-10. These are integration bounds, NOT water deletion thresholds
or relative accuracy claims for each arbitrarily tiny piece. Zero-lower-bound
pieces are explicitly NOT proven wet. Out-of-block bounds remain visible;
fragment totals are not renormalized. No original physical state is updated.

## Actual South Fork evidence

Report: `tmp/south-fork-inlet-sweeps-v2-20260915.json`.
SHA-256: `2740042da70ac04007c123aa30d57d4c3dcfaf970552b5ea98e9ca898d19c446`.

The original bank block (12,8), 600-second atlas state and registration remain.
Of 13 immediate faces:

- Ten have represented conditional outward sweeps: eight above the receiving
  minimum and two at it.
- One positive speed near 1.916e-126 has nonzero exact geometry but eligible
  time/volume below floating-point range. It remains unresolved for physical
  updates; no tiny-speed cutoff or epsilon water is introduced.
- Two receding faces remain outside this outward construction.
- Seven routed streams have proven positive portions in additional sources;
  three enter sources with initial wet-pool ownership. The later
  [exact wet-support audit](normal-river-inlet-wet-contact.md) corrects the earlier
  inference that these are already-wet regions: all three incoming portions
  have zero overlap with actual initial wet support at the audited times.
  This does not resolve stream-stream overlap or permit unconditional merging.
- Maximum combined moment-bound width / incoming moment is
  4.973799150320648e-14. Maximum exact projected inlet versus represented-normal
  flux relative discrepancy is 1.7967382807780432e-16.

All 563 audit-source and 464 protected source/actor hashes were rechecked.
Captured DEM/exposed rock remain separate from submerged priors, interpolation
and inferred flanks in the provenance. Rational arithmetic adds no survey
precision. V1 is retained; V2 adds direction checking and distinguishes proven
positive portions from uncertainty-only portions.

## Verification and remaining work

62 focused tests PASS: 14 new geometry tests plus original point-front flux and
source-activation controls. They cover four moments, high-inlet placement,
exact/irrational edge switches, oblique clipping against independent quadrature,
translation/orientation, original shared-bed equality, point contact, reversed
flow, tiny speeds and insufficient integration-bound rejection.

`tmp/inlet-sweep-full-suite-v1-20260915.xml`: 548 PASS / 13 FAIL, zero errors
or skips, one existing JUnit warning, 115.21 seconds. All 13 failure identities
match the preceding full suite: four nonbreaking energy, eight paired nonlinear
energy, one legacy storage/face consistency failure. No old gate was changed.

NEXT: resolve source-crossing/overlapping streams and existing water; couple
non-horizontal wet support to one-sided transport, pressure and curvature;
complete fan/receding and rational time evolution, edge/flat/mixed transitions,
then native single-surface integration. Original energy/work/local-ledger and
40-iteration pressure-solve gates remain required.

No native, material, terrain, menu or playable visual change occurred here.
Last ordinary performance remains 22.429181 FPS / p95 54.7266 ms: FAILS 30 FPS.
Broad froth and smooth faces remain unaccepted. Colorado, Pacuare, Futaleufu
(in order), Chilko/Zambezi/all-scene water, crew, normalization, regressions and
release remain open. Troublemaker stays a rapid within South Fork, not a menu
scenario.
