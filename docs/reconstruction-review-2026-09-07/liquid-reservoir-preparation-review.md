# Explicit exterior water support — prepared, not running in the engine

September10,2026. The previous turn made implementation progress but its
relaxation candidate still failed. This turn prepares actual exterior fluid
support and independent signed core/buffer balance. The full goal remains active.

## Why this changes the next implementation

Current runtime ownership ends exactly at the rapid's physical control volume.
The two-cell computational halos are pressure/grid resources, not owners of
exterior water particles. The existing strict exit classifier consequently
rejects any return flow at a prescribed inlet. A sponge did not solve that.

The next candidate gives the rapid a one-metre exterior water band on all four
sides, with corners included once. The original core is an internal interface,
not another source or retirement plane. External forcing belongs at the outer
buffer boundary. This is necessary support, NOT sufficient proof of a correct
open boundary: the current outer classifier still assumes one-way prescribed
inlet rows. Genuine signed backflow/outer exchange and wave-transmission behavior
still need an explicit physical implementation, not a moved failure boundary.

The primary [open-boundary description](https://github.com/DualSPHysics/DualSPHysics/wiki/3.-SPH-formulation#315-open-boundary-conditions)
describes fluid/buffer transitions in both directions and buffer support for
neighboring fluid. It is an SPH implementation, not validation of our FLIP code.
No claim that the prepared band is already such a solver.

## Prepared data and invariants

`prepare_liquid_reservoir.py` produces
`tmp/south-fork-liquid-exterior-reservoir-20260910.json` from the unchanged
registered triangle mesh and unchanged numerical hydraulic prior. It checks
hashes, vertical datum, exact ownership, domain metrics and original seed IDs.
Dry hydraulic cells never become water merely because terrain interpolation
differs. Sites are sampled at their actual float32 encoded world positions.

- 10389 exterior particles, nominal216.4375m³ vs quadrature216.42838676m³.
 Quantization difference0.00911324m³; minimum original-bed clearance7.02835cm.
- New IDs719335..729723 do not replace any core ID.
- Bed authority remains registered terrain including inferred submerged bed.
 Stage/velocity remain uncalibrated numerical priors; vertical velocity is zero.
- No runtime, kernel-support, backflow or visual acceptance flags are asserted.

The outer geometry/source package is
`tmp/south-fork-liquid-reservoir-window-20260910`, with247×83×8m fluid bounds,
494×166×24 physical cells and the original0.5×0.5×(1/3)m spacing. It contains
177954 top triangles /187728 closed triangles; all4226 captured rock returns
remain included. Artificial side/bottom closure remains explicitly inferred.
Original top-surface error is5.8211e-12m.

`merge_liquid_reservoir_state.py` and the optional explicit-edge partition API
produce `tmp/south-fork-liquid-reservoir-regions-20260910`:

- 729724 total particles; every719335 original core position, velocity, ID and
 owner is unchanged. Only original outer faces expand; all17 internal shared
 cuts retain their world positions.
- 12 owners, maximum158248 initial particles and1800960 reconstruction voxels
 per region. Existing163840 burst /2000000 voxel caps remain unchanged.
- 6144 source sites at the new OUTER faces only, totaling47.02471224393831m³/s.
 This is not the old47.0068m³/s source duplicated at an internal interface.
- Independent original region-state audit verifies every particle/source once,
 all82004 physical XY cells, and exact canonical payloads.

The new source, scalar boundary and vector boundary were built from an actual
native face-flux audit of the proposed outer rectangle, not by extrapolating
the old boundary rows. Source wet-subface error is2.2204e-16m³/s; no unresolved
dry source faces. Minimum source-bed clearance0.00457939m. Neither measured
river discharge nor engine source-volume calibration is claimed.

## Independent signed mass balance

`liquid-reservoir-outer-native-flux/report.json` uses the same source scenario,
geometry, hydraulic field, solver binary and native face arrays as the old core
audit. The one-microsecond native step gives outer net0.117496952766m³/s versus
measured0.117497575444m³/s (error6.2268e-7m³/s).

`audit_liquid_reservoir_flux.py` independently sums each of656 native buffer
cells, including corners, and checks cancellation of the core interface:

- Core net inflow0.112933867176m³/s.
- Buffer net = outer minus core =0.004563085591m³/s.
- Actual buffer storage derivative0.004563085085m³/s.
- Conservation difference5.0549e-10m³/s, within the unchanged native audit gate.

This is a native finite-volume source check, NOT a successful3D backflow run.

## Contact and regression evidence

`tmp/south-fork-liquid-reservoir-geometry-20260910` has complete regional
contact and boundary pages. Independent geometry audit verifies:

- 729724 seed contacts bitwise equal to the original parent query;
- 90780 computational XY centers and98304 independent support probes;
- 365010 extended triangles against the original mesh, unchanged anchors;
- 1320 exterior rows exactly once,6040 shared /2736 exterior halo columns.

Outer exact face beds are in
`tmp/south-fork-liquid-reservoir-face-bed-20260910/physical_face_bed.json`:
311/310/1284/1285 original-triangle knots, maximum independent height
error2.1316e-14m. No midpoint-bed substitution or stage change.

352 liquid Python regressions pass. Added18 tests cover unique corner/strip
ownership, no core duplication, unchanged world cuts, bad metrics/partitions,
unchanged allocation caps and signed interface cancellation/backflow. Existing
UE code/binaries were not changed this turn, so no new engine pass is claimed.
All preparation processes are terminal (84037,67384,3200 included); no UE was
launched. Last prior15 engine regressions concern the old relaxation dataset.

## Next required work

Wire the new dataset through a validated, versioned runtime selection (the
probe and several audits still hardcode the original paths). Preserve core
versus outer-interface identity in telemetry; do not treat core backflow as
retirement. Implement current pressure/velocity support and explicitly accounted
outer signed exchange, then test native particles, actual reflection/discharge/
storage and the visible single surface. Merely enlarging the window and passing
the old gate briefly would not establish the requested physical behavior.

South Fork and every later scene/crew/normalization/release task remain open.
No saved map, production promotion, final commit or push.
