# Original-source auxiliary transport: incomplete nonlinear force components

These changes extend the nonlinear metric work to the original wet source
triangles and oblique region faces. They do **not** constitute a full momentum
stage: terrain-curvature cross work, compatible front/pressure work and finite
evolution remain missing. No native, gameplay, visual or 30 FPS claim is made.

## Geometry and operators retained

`subcell_auxiliary_transport.py` supplies three components:

- Shared-source auxiliary factor transport. At each actual source trace, use
  the two original triangle slopes, both original relative depths and the
  paired face-normal velocity. A two-node Gauss rule exactly integrates the
  cubic polynomial m(fL^T fR+3 bL^T bR/4), with f=[h,-3 grad(b)/2],
  b=[0,grad(b)] and m=mean(h) mean(u).n. The left/right jet forces are an
  explicit transpose pair. The existing divergence and its transpose map
  (D u,u_x,u_y) between these jet forces and physical vector forces.
- Original-source geometric commutator. It integrates the Eulerian factor-time
  term at fixed original terrain points, not an arbitrary derivative of a
  changing Gram square root or moving quadrature-node coordinates.
- The derivative part of the symmetric cross-mode tensor, using the actual
  graph derivatives and their transposes, including oblique edges and walls.
  Its coefficient is the original integral
  c=integral h^3 D w - (3/2) integral h^2 grad(b).w. No mean-depth cubic or
  mean-slope kinetic form is substituted.

For the commutator let a=Gamma00=integral h^3,
c=Gamma0v=-(3/2) integral h^2 grad(b), and c_dot=V_dot d(c)/dV. With D_dot
the existing analytic face/volume derivative, the exact integrated expression is

    J u = (D^T a D_dot u - D_dot^T(a D u+c.u) + c D_dot u)/2
          + (c_dot D u-D^T(c_dot.u))/4.

An independent wet-triangle quadrature checks v^T J u directly using
F=h D-3 grad(b)/2 and F_t=eta_t D+h D_t. The moving wet boundary contributes
zero here because the original integrand contains h. Both original inverse
pole factors and their 40-CG limits remain unchanged.

The tensor derivative part is
-sum_j D_j^T[c(D_i z_j+delta_ij div(z))]. Its exact self-adjointness does
not make it the complete terrain tensor: the source-integrated counterpart
of s Hess(b) is still missing. The audit includes T^T N_derivative-N_derivative T
but never labels that as the full nonlinear force.

## Fronts, original slopes and numerical range

Only the common positive wet trace is included in these paired components.
Unowned wet traces, one-sided owned faces and differing wet extents are
reported explicitly. A physical reflecting exterior carries no advective
transfer; an unowned wet source trace is not reclassified as a wall.

Exact source datums and intervals are retained before float conversion.
Integrating the shallower side and adding the positive stage difference avoids
cancellation of thin positive depths. A nonzero transport coefficient that
cannot be represented rejects; there is no depth floor or coefficient deletion.

An oblique test initially exposed inconsistent slopes among the old
rounded/clipped copies of the same source triangle. Those copies are not
averaged or promoted to an original slope. The authoritative exact-source
fixture passes; a separate test preserves rejection of the inconsistent legacy
fixture. This does not waive the existing source storage/face discrepancy test.

## Completed original South Fork check

Report: `tmp/south-fork-source-auxiliary-v3-20260914.json`.
SHA256: `3e4fbbe2f5a30d1dd4af433be4845614541bdac0f25f3a4df58f59d70557ab88`.
All **47** recorded source hashes match. The unchanged original 600 s atlas
snapshot retains 258 separate water regions, original physical momentum and
the original captured/inferred vertex provenance. Submerged prior and inferred
flanks remain inference, not measured bathymetry.

The audit assembles 1,835 shared source traces and reports **57 unowned wet
traces, 21 wholly one-sided owned faces and 55 differing wet extents**. These
counts are not evidence of complete hydraulic support. No new state is evolved.
V_dot is a prescribed zero-sum coefficient direction, explicitly not a chosen
mass flux. Both original inverse poles pass the unchanged component gates:

| Control | beta 0.10059130463209877 | beta 0.010519806479012348 |
| --- | --- | --- |
| Factor transport work | 7.82e-14 | 2.78e-13 |
| Independent commutator quadrature error | 1.13e-15 | 1.12e-16 |
| Tensor derivative pairing error | 9.10e-13 | 4.55e-13 |
| Pulled component work | 1.78e-15 | 2.14e-14 |
| Maximum solve residual | 3.61e-16 | 2.06e-16 |

Maximum component force magnitudes are 9.73092 and 6.60488 in the original
variables. These are incomplete component values, not river accelerations or
evidence of safe finite evolution. Zero work alone cannot distinguish the
complete model from the incomplete modes, as the prior smooth-terrain audit
already demonstrated.

Tests completed with no waivers:

- `tmp/source-auxiliary-suite-v1-20260914.xml`: **320 PASS, 1 retained geometry
  FAIL**. Includes 19 new controls for quadrature, transpose pairing, original
  moments, flat-model reduction, oblique edges, disconnected pools, unresolved
  fronts, rotation, datum shifts with collapsed float projections, original
  moving-state component scope, and explicit range/legacy-slope rejection.
- `tmp/source-auxiliary-retained-v1-20260914.xml`: **25 PASS, 12 retained energy
  FAIL**. No old implementation was redirected or marked xfail.

All owned audits and test runs completed. Temporary reports remain ignored;
source, tests and this evidence record are versioned.
All 464 protected source/scene/capture/map/actor hashes were checked unchanged.

## Next required implementation

Finish the original-source terrain-curvature part of the cross-mode tensor
and its physical face/bed-force ledger, then combine it with the already
verified changing-volume metric and compatible mass/pressure update. Source
slope jumps inside a single water region still contribute curvature even
though they are absent from the inter-region hydraulic graph. They must not
be erased by differentiating a region-averaged bed. Qualify the full nonlinear
continuum limit and finite-time wet/front/open behavior before native/shared-
surface integration. South Fork visuals and 30 FPS, all later rivers in the
requested order, crew, normalization, regressions and release remain open.
