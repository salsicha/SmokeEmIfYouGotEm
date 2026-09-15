# Coupled source-metric rate and weak terrain curvature

This is a full nonlinear **rate candidate on complete fixed wet support**, not
a finite-time river solver. Full continuum consistency must be checked
independently. Wet/front transitions, open boundaries, native shared-surface
integration, convincing water and 30 FPS are still required. No scene is closed.

## Original source curvature, including same-region edges

The affine original triangles have zero Hessian in their interiors, but their
normal slope jumps form an edge-supported Hessian measure. Discarding a source
edge because both triangles share one water region loses this force.
`subcell_source_curvature.py` now retains those edges as well as true source
slope jumps on Cartesian region interfaces.

The two source gradients and the edge tangent are exact rationals of the
original represented mesh. Their tangential slope difference must be exactly
zero before forming the symmetric normal rank-one Hessian measure
(jump(grad(b)).n) n n^T. Inconsistent slopes reject; there is no projection of
inconsistent geometry, welding, mean-bed fitting, or promotion of inference.

The weak curvature tensor uses the original common-wet edge and integrates
the first and second depth powers. The coefficient multiplying that Hessian
is -3 integral(h^2) D(w)/2 + 3 integral(h) mean(grad(b)).w. At a shared water
interface, symmetric state traces distribute the force to both owners; the
source-gradient mean is the two-sided affine jump integral, not a region-wide
mean replacing the original slope variance. Each interface tensor is exactly
self-adjoint. Physical exterior boundaries do not invent an external bed
extension. Unowned wet curvature edges remain explicit unresolved fronts.

## Two spatial geometry terms missing from the prior components

Following the source factors through the complete geometry exposed two more
terms needed by auxiliary transport:

- Inside an original triangle, the region water level is constant but
  adv(h)=-grad(b).u. The local skew contribution is k D(w)-D^T(k.w), where
  k=Gamma_vv u/4=(3/4) integral h grad(b) grad(b)^T u. It retains the full
  original slope covariance.
- At a slope jump inside the same water region, the two kinematic factors
  differ. Their paired source-edge transport must be retained even though
  the hydraulic mass graph needs no separate water unknown there.

Independent volume quadrature tests the first term directly. A same-region
ridge tests the second. These are corrections to the earlier component
implementation, not a claim that its energy checks established model fidelity.
The old component audits remain historical measurements of incomplete forces.

## Combined stage and independently assembled physical momentum

`subcell_nonlinear_metric_stage.py` combines the existing original-source
nondispersive mass/pressure update, the complete changing-volume inverse metric,
source factor/difference transport, the geometric time commutator, and both
parts of the cross-mode tensor. It retains the original two-pole parameters,
positive source integrals, original 40-CG solve and all existing tolerances.

The stage solves C u_t = -base - (C_t-K0 V_t)u/2 - S u and returns physical
P_t=V u_t+V_t u, not canonical momentum substituted for physical momentum.
The source base splits advection and gravity explicitly when applying K0.

`subcell_metric_force_ledger.py` separately assembles D^T and D_t^T tractions
from original common harmonic columns, their analytic rates, each owner's
volume factors and physical walls. Gram stresses provide the explicit local
bed reactions; the original source Hessian supplies the curvature reaction.
Inverse pullbacks use V L^-1 f=f-beta G L^-1 f. Acceleration-metric,
changing-metric, skew and base contributions produce a local physical momentum
ledger. No bed or wall force is defined as the remainder of the final rate.

The full stage rejects unowned source activation, one-sided or unequal wet
support and unresolved curvature fronts before returning a usable rate.
The acceptance flag remains false even when instantaneous mass, energy and
local physical-force checks pass. A no-curvature comparator is retained because
it can pass those same energy identities while representing a different model.

## Completed verification (2026-09-14)

Initial controlled checks pass for the exact planar null, an independent
distributional ridge force, same-region and grid-aligned curvature ownership,
tensor symmetry, original factor-volume quadrature, mass/energy/local force
budgets, lake rest, velocity reversal, flat bed-force nullity and front rejection.
The final focused suite completed with 343 passes and one retained original
storage/face geometry failure (maximum difference 1.77635684e-15). The retained
energy suite completed with 25 passes and 12 failures. No gate was waived.
Original scene/geometry/capture/actor hashes: 464 checked, all unchanged.
No native or visual result has changed.

The independent nonlinear reference uses both original dual poles, the full
stationary depth potential and canonical curl, then the original analytic
coordinate derivative back to physical momentum. Cell averages in that
continuum sampler do not replace any source moment in the candidate stage.
All tests use fixed physical domains and unchanged error gates.

The completed source-grid comparison uses two turning-flow profiles on a fixed
16 m domain with 8/16/32 grids. Full-rate RMS errors are:

| Seed | 8 | 16 | 32 | Successive refinement ratios |
| --- | --- | --- | --- | --- |
| 2843 | 0.0161843461 | 0.0046616384 | 0.0012188864 | 3.4718, 3.8245 |
| 2845 | 0.0160274437 | 0.0049553244 | 0.0013098240 | 3.2344, 3.7832 |

The no-curvature comparator also refines and is closer on these coarse grids.
This measurement therefore does **not** discriminate the complete curvature
model or establish full continuum consistency. Across the six full candidates,
maximum absolute energy rate is 1.066e-12, local momentum-ledger error 2.763e-13,
and original pressure residual 2.804e-13. All acceptance flags remain false.
Report: `tmp/source-nonlinear-model-v2-20260914.json`, SHA256
`1e844a0f9dd78f87f8db00ac5ca397e346bd06f1dfb50f4ebcf04d34027c10cc`;
529 recorded implementation hashes matched at completion.

The original 258-pool South Fork component audit now includes 6,471 factor
faces, including 4,636 same-region geometry faces. It still reports 57 unowned
wet traces, 21 one-sided owned faces and 55 differing wet extents. This component
audit includes only the tensor derivative part, not the combined full rate.
Report: `tmp/south-fork-source-curvature-components-v1-20260914.json`, SHA256
`200bb1ad31b0d2e363ae04b3d8136652ddd684110f7355539f9ce5b709b63ab7`;
48 recorded source hashes.

Two 4x4 original-state block controls preserve the actual atlas volumes and
velocities. Both impose explicit reflecting test boundaries, not open-river
boundaries; neither advances a finite trajectory:

- Channel block [6,6]: 16 pools and 302 same-region curvature edges. Full-rate
  gates pass: local momentum error 3.198e-14, absolute energy rate 4.264e-13,
  pressure residual 3.976e-16. Its terrain authority is 2/5 (inferred submerged
  prior/flank), **not captured bathymetry**. Report
  `tmp/south-fork-nonlinear-channel-v1-20260914.json`, SHA256
  `e79a90b7eeea97a3681bf7ec14a0dd943befde75ae7bed8e90bb79267726f807`.
- Rock-bank block [12,8]: rejects unresolved source activation before returning
  a rate. Original water state is unchanged. Authority 3/4/5 mixes exposed rock
  with interpolation/inference. Report
  `tmp/south-fork-nonlinear-rock-bank-v1-20260914.json`, SHA256
  `8eb4506337df6541ab53a26711d15748546b2a57a148b8f57191d30fdcd40729`.

Both block reports recorded 538 matching hashes; both retain false gameplay and
full-model acceptance flags. Generated reports and test XML stay ignored in
`tmp/`; source scripts, tests and this review are versioned.

Next: a finer or otherwise discriminating independent continuum check, then
finite-time wet/front coupling, actual open-flow boundaries, and native playable
shared-surface integration. The latest existing runtime profile is still
20.803 FPS with p95 64.972 ms, failing the 30 FPS / 33.333 ms target. Terrain,
breaking waves, convincing froth and later scenarios are not accepted here.
