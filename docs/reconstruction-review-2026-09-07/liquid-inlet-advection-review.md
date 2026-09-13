# Native prescribed-inlet advection — work in progress

September 10, 2026. South Fork and the full queue are not complete.

The previous exact-bed replay failed at native step30 because one particle
crossed outward through east-face row277, whose prescribed normal flow is
inward3.1862347cm/s. It was96cm above terrain. Accepting that reverse exit would
contradict the prescribed inlet/source accounting. The grid sets inlet velocity
in virtual exterior cells, but particle advection previously had no corresponding
physical inlet-plane condition. The exit gate correctly caught the discrepancy.

## Implemented boundary treatment

`RaftSimLiquidInletAdvection.h` now supplies a native particle update before
swept terrain contact, only for validated regional parent-exterior profiles:

- Intersect the original proposed particle step with the full physical domain.
  Require an interior start and an unambiguous first horizontal face.
- Only a non-outgoing row and a hit below its stage and above the actual contact
  triangles can impose inlet motion. Outlets, roof/floor/corner, dry/invalid
  queries and above-stage spray are untouched and still face the original gate.
- Reintegrate the step's normal displacement with the prescribed inward speed
  and set its normal velocity to that speed. Preserve tangential proposed motion
  and velocity. This is prescribed boundary momentum, not zeroing all velocity,
  reflecting a particle, moving the domain, lowering terrain, or deleting mass.
- Existing terrain contact runs afterwards. Native IDs, birth rates, volumes,
  outgoing ledger, commit gates and original exterior source tables are unchanged.
- Retain the raw proposed position/velocity and selected face in the transient
  particle payload so an independent audit can compare actual native response.
  Those additional7 float components are diagnostic overhead, not FPS acceptance.

Applying particle-level boundary constraints in addition to grid constraints is
an established pattern; see PhiFlow's separate grid boundary and particle
advection correction functions in its [official fluid API](https://tum-pbs.github.io/PhiFlow/phi/physics/fluid.html).
That supports the general separation, not a claim that this particular inlet
scheme is validated by the source. Our prescription and tests remain project
implementation decisions requiring the actual flow/discharge/visual checks.

## Evidence

- Build20713 succeeded191.05s (including git working-set discovery timeout).
  No engine source or saved map/system assets changed.
-308 liquid Python tests pass. Seven new tests cover four reflected world faces,
  tangential preservation, correct normal displacement/velocity, unchanged
  outgoing flow, dry/spray/invalid/roof/corner cases, zero-normal flow, and actual
  crossing bed rather than a cell midpoint, rotated/translated frames and invalid
  timesteps.
- `liquid-native-inlet-advection-debug`, UE53885 terminal0,32 captured native
  steps with full step30 retained. All compact commits pass. Actual step30
  control is `[1,0,718008,53]`, versus the previous failed `[0,64,718008,54]`.
  The last commit control is `[1,0,717992,42]`.
- `inlet-audit.json` checks54 actual proposed exterior candidates at step30
  against float64 math and original barycentric terrain. One inlet correction
  is present (owner7/east); all53 outgoing candidates remain unchanged.
  Position error0.0006560203cm, velocity error2.0277e-7cm/s. Boundary-supplied
  velocity impulse `[5.55540497,2.19563941,0]`cm/s; no tangential impulse.
  Sampled path clearance96.4521cm. This audit does NOT certify continuous swept
  clearance, sustained discharge, mass history, or visual/performance quality.

`liquid-native-inlet-advection-flow`, UE5590 terminal0, captured120steps/118commits.
It is still REJECTED: first failed control atstep50 `[0,64,716865,122]`.
The original dense/P2G audit(session37269 terminal1) rejects that transaction
before accepting later state. Capture walltime80.57s is not game FPS evidence.

`liquid-native-inlet-step50-debug`, UE15552 terminal0, retains fullstep50 in a
52-step replay. This repeat first failed atstep15 `[0,64,719136,123]`, not50.
Its step50 snapshot therefore contains3632 already-exterior origins and120 new
approved crossings; it does NOT isolate the first failure. Later negative-time
extrapolated intersections in its initial diagnosis are not valid crossings.
The diagnostic now suppresses such intersections for invalid origins.

Next: retain a bounded first-rejection trajectory directly on the GPU, tagged
with native step and owner, before later failed commits can obscure the cause.
Do not keep choosing a guessed full-capture step when the first failure moves
between runs. No exit policy or acceptance gate was weakened. The first-failure
trace needs actual positions, origin, route, face/row and rejection condition;
save only after stop, without per-step CPU readback or massive history buffers.
Then diagnose/fix that failure and rerun original dense mass/identity/P2G checks.

All processes from this pass are terminal. The14 engine regression rerun remains
required after this integration. No promotion, commit or push.
