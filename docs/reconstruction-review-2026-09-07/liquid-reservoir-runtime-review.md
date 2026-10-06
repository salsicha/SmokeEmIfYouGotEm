# Reservoir runtime and rotated-coordinate precision

2026-09-10 local / 2026-09-11 UTC. South Fork remains incomplete. These are
native particle diagnostics, not accepted appearance, real discharge, gameplay
performance, or a promoted production scene.

## Runtime dataset installation

`RaftSimLiquidDataset.h` selects only `core-v1` or `reservoir-v1`. Default remains
the original core. Before creating components it verifies actual bytes against
parent, ownership, geometry, exact face-bed, original mesh, extended contact and
all twelve regional file manifests. Unknown keys, changed hashes and traversal
are rejected. No map or saved Niagara asset is modified by dataset selection.

`liquid_dataset.py` supplies the same allowlist to the runner and native audits.
Legacy captures without a descriptor retain the core path, but explicit null,
conflicting keys or changed descriptor hashes do not silently fall back. Shared
columns are compared against the independently constructed complete tuple list;
the reservoir has 6,040, not the original core's 5,960 columns.

Actual startup: `liquid-native-reservoir-initial`, five native steps, three
commits, all twelve owners, source seed 173193. Engine session 91192 completed.
`native-transfer-audit.json` verifies 729,873 particles (729,724 initial +149
births), native identities, neighbor representation, raw P2G and exact regional
reduction. Zero mismatched reduction components; 20,200 nonzero shared cells.
Volume 15,189.673366 m³ versus nominal 15,205.687953 m³ lies within the existing
177.873933 m³ arithmetic envelope. This is startup accounting only.

## Longer run rejected, not hidden

`liquid-native-reservoir-flow`, 600 native steps /598 compact commits, completed
capture in 73.886 seconds. First rejected transaction: step292, owner3, birth
sequence54513, east face row229, non-outgoing reason8. Row inward speed is zero.
The latch retains actual endpoints and the actual uploaded frame. A later
snapshot after rejection is not a valid state-conservation acceptance snapshot.

Its 290 successful commits end at step291: 729,724 initial +10,907 births
−27,117 approved exits =713,514 survivors. Net nominal storage is −337.708333 m³.
This is startup drainage, not demonstrated steady discharge or calibrated flow.

`first-rejection-precision.json` distinguishes errors in arithmetic from errors
caused by representing the original survey frame as floats. Using the exact
uploaded float inputs in float64, the rejected endpoint's normal coordinate is
24,699.99992154778 cm, inside the 24,700 cm face. The old GPU expression returned
24,700.001953125 cm. Its arithmetic error is .00203157722 cm. The separate
original-double-frame comparison also places it inside; these are not conflated.

## Shared calculation correction

`RaftSimLiquidPhysicalFrame.ush` now retains subtraction and rotated-product
residuals using the engine's DoubleFloat operations and demotes only the final
coordinate. This helper is shared by routing, exit classification and native
inlet advection. It does not clamp positions, widen the physical box, add an exit
tolerance, delete particles, increase damping or relax failed-commit gates.

Epic documents the two-float arithmetic and its performance trade-offs in the
[Large World Coordinates rendering reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/large-world-coordinates-rendering-in-unreal-engine-5).
The installed UE5.8 shader implementation was inspected before use. Using this
operation does not establish scene performance; that must still be measured.

The GPU regression uses the actual failed start/end and 36 additional points at
three locations on each face, on either side and at the face. Expectations are
calculated from the actual float-stored points/frame with a double calculation,
rounded once. True outside points remain outside. It also checks regional owners.

First regression attempt (`engine-liquid-rotated-frame`) rejected its fixture:
the routing API requires at least two physical owners and orthonormal double
inputs before upload. The corrected fixture models that production contract;
`engine-liquid-rotated-frame-v2` has 17 clean passes, no failures or warnings.
Build50289 succeeded in36.64s. Python liquid suite:358 tests pass.

## Current follow-up

`liquid-native-reservoir-precise-flow` completed the same600-step configuration
in74.180s (session52923 terminal0). It still rejects, now step286, same owner3/
birth54513/eastrow229. The GPU coordinates now exactly match single rounding of
the actual float-input double calculation. This verifies arithmetic correction,
not physical flow success. Actual endpoint normal coordinate is now
24700.001167016344cm: stored tangential positions themselves drift outwards.
The start is24700.000797231267cm, rounded to the closed boundary24700cm. Prior
submerged plane projection triggered (marker2) but its float output did not
preserve zero normal displacement. Captures explicitly record
`native_physical_frame_model=double-float-demote-v1`.

Added `RaftSimLiquidPrescribedNormal.ush` only to the existing prescribed-plane
response (not bulk advection, above-stage water, exits or general contact).
It evaluates the normal residual in double-float, solves the dominant world
component and selects its nearest inward-representable float. The other world
components remain unchanged. This represents the prescribed displacement
without outward rounding drift; it adds no boundary epsilon or particle sink.
The GPU fixture compares the captured failure and64 sign/scale/flux cases to
independently calculated C++ double results plus nextafter rounding. Build63646
succeeded36.55s, but engine22730 rejected the test shader's late registration.
Moved the development-only test into the existing PostConfigInit water-detail
module, without changing module startup configuration. Build68744 succeeded
20.70s. `engine-liquid-prescribed-normal-v2` (62358 terminal0) passes all18 tests:
17 clean and one with a Google generate_204 connectivity timeout warning.
Native captures name the new operation
`native_prescribed_normal_rounding=inward-representable-v1`.

## Verified ten-second native run; longer physical failure

`liquid-native-reservoir-inward-flow` (46988 terminal0) completes600 native steps
with598 successful atomic commits and no rejected exit. Capture walltime78.786s
is diagnostic overhead, **not gameplay FPS**. Full independent transfer audit
(97132 terminal0) verifies701,276 actual particles, identities, neighbor state,
P2G and raw regional reduction; zero mismatched reduction components. Physical
grid volume14,598.340876m³ versus nominal14,609.917102m³, within the unchanged
170.584631m³ arithmetic envelope. No per-exit trajectory or steady-flow claim.

New `diagnose_liquid_flow_budget.py` checks every compact commit against actual
native spawn records and prepared seed/volume identity, bins inflow/outflow and
storage, and stops at the first failure without treating later records as valid.
The timestep is explicitly the runner's requested1/60s, not independently
measured GPU time. All363 Python liquid tests pass, including five budget tests.

Ten-second ledger through commit599:729,724 initial +22,496 births −50,981 exits
=701,239 survivors, followed by37 births at retained P2G step600. Net storage
−593.4375m³. Nominal input stays about47m³/s; interval output declines from
117–123m³/s to86m³/s. This is not an accepted steady river stage/discharge.

`liquid-native-reservoir-inward-flow-30s` (40699 terminal0) completes its capture
but FAILS physical transaction635, owner4/birth97114, westrow71, reason8.
The endpoint is genuinely outside: localnormal .321890833→−.079085517cm. GPU
coordinates match the single-rounded independent calculation. Intersection
z899.909079cm, exactbed871.620879cm, prescribedstage883.149719cm, zero prescribed
inward speed; this is above-stage backflow, not numerical drift. Inlet marker0
confirms neither below-stage plane correction nor positive-inflow relaxation
was applicable. Do not expand those conditions just to suppress this evidence.

Only633 commits through634 validate in that run:729,724 +23,812 −53,268 =700,268
survivors; storage−613.666667m³ over10.55 requested seconds. The remaining
post-failure snapshots do not prove state conservation or 30s sustained flow.
`first-rejection-diagnosis.json` and `storage-budget.json` retain the failure.

The outstanding physical work remains explicit core/buffer signed exchange,
outer backflow/free-surface/pressure coupling and discharge/storage verification.
Moving the boundary or passing a coordinate regression does not satisfy those
requirements. Actual water shape, motion, raft support, foam/spray, shoreline,
collision and playable FPS require later scene evidence. Review-map SHA256
remains36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96.
All build, engine and audit handles from this pass are terminal. No promotion,
new beauty capture, scene completion, commit or push.
