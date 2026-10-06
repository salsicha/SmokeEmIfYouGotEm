# Compatible position transport and paired native motion

September 11, 2026. South Fork remains incomplete. No map/asset promotion,
photorealism acceptance, game-FPS acceptance, commit or push.

The preceding user-status turn was informational (no implementation progress).
This continuation implemented a measured correction, not just another status
check: optional centered-divergence-compatible particle transport on all twelve
actual river owners. It also established the missing same-step native motion
capture. The correction is **not a complete clumping or discharge fix**.

## Why the previous snapshot could not prove particle motion

`native_transfer_packet` is taken at Neighbor Grid Rasterize Particles. Its
positions are the selected step's input, but its contact/inlet-output attributes
are left over from the preceding transport. Comparing those outputs with this
step's projected velocity falsely suggests stationary particles.

`-RaftSimRegionalAdvectionPacket` now retains:

- Velocity after Extrapolate Velocities Again, immediately before FLIP/PIC.
- Raw pre-contact position/velocity and final position/velocity after FLIP/PIC,
  before owner handoff, with all four native identity words and live counts.
- The immutable native Engine.DeltaTime, WorldToUnit and LocalToWorld matrices.

No new source, mass, particle deletion, contact response, or solver writes are
introduced by this capture. The copied data cannot drift to a later tick.

The actual scaled inverse matrix is not identical to the ideal survey frame.
The replay must also perform `unit*size-.5` in float before round-to-even. Four
near-half-cell classifications were wrong when that intermediate stayed double.
A regression retains the exact half-cell case; tolerances were not enlarged.
The HLSL dump is UTF-16, decoded by the existing BOM-aware shader reader.

## Implemented transport correction

`-RaftSimRegionalCompatibleTransport` is opt-in and requires the paired capture.
It changes position advection only; native FLIP/PIC momentum, centered-tent P2G,
original particle volume, exact registered terrain, inlet relaxation and strict
exit/ownership checks remain intact.

For each component, the normal kernel is
`K(r)=(B2(r-.5)+B2(r+.5))/2`; transverse kernels are linear tents. Because
`K'(r)=(B1(r+1)-B1(r-1))/2`, the continuous grid-coordinate divergence is the
tent interpolation of the existing centered grid divergence. The union of
component supports uses 32 vector loads/query, versus 81 in the older optional
cubic/quadratic APIC experiment. Two queries perform midpoint position advection.
This is not exact finite-time volume preservation or a replacement APIC transfer.

Incomplete four-point support falls back to the existing motion; it is not
clamped into the grid. Native nearest solid/air classifications retain their
ballistic branch. Contact and inlet handling run afterward. These boundary
choices still need physical review; passing an interpolation identity does not
validate them.

**The interface still uses its previous trilinear velocity interpolation after
Project Pressure.** It is not yet using the new particle interpolation or the
post-extrapolation velocity. This controlled position-only experiment must not
be promoted as a consistent final liquid system.

## Actual native results

Authoritative corrected run:
`liquid-native-compatible-transport-600-v2/`.

- Native process session 77931 terminated with code 0; complete capture, empty
  exchange error, no RHI validation errors. Actual step 600, 727332 particles.
- Full `native-transfer-audit.json` passes: zero reduction mismatches; two
  survey-double/internal native-float owner differences, unchanged physical
  outer bounds. This is the existing declared storage-coordinate contract.
- `advection-diagnosis-v3.json` pairs all identities. 723926 grid-driven
  positions replay within 0.000488543 cm (declared tolerance 0.02 cm).
- On 560886 particles whose entire trilinear pressure-corner support is fluid
  and inside the projection audit's owned `[2,size-2)` box, interpolated
  divergence RMS is 0.000266848/s, equal to sampled centered-D to numerical
  precision. Other grid-mode points remain in per-region all-grid statistics
  and every particle remains in position replay; edge points are not hidden.
- `flow-budget.json`: all 598 compact commits verify; 22496 births, 24925
  approved exits, 727295 survivors at 599 plus 37 births at 600. Net storage
  change -50.604167 m³. Final interval inflow 47.047414 vs outflow 34.913793 m³/s.
  **Outflow still declines. This is not steady-flow acceptance.**
- Maximum density is about 14.87 times cell volume in owner 4, worse than the
  earlier uncoupled-position sample's approximately 11.44. Owner 6 remains
  approximately 12.77. No physical improvement is claimed from the density.
- 16842 particles are within 2.5 cm of the exact bed; 2634 of those have nearest
  solid classification. At the owner-4 density maximum, 269 particles lie
  within 1 m; 264 classify fluid and five solid. Median exact-bed clearance is
  approximately 2 cm. Thus nearest-solid ballistic treatment is **not by itself
  an explanation of the whole clump**. Bed-normal velocity/support and actual
  contact displacement also require inspection.

## Retained unsuccessful captures

`liquid-native-advection-paired-600`, `liquid-native-advection-matrices-600`, and
`liquid-native-compatible-transport-600` terminated normally but logged an RHI
counter-overlap synchronization error at the added post-advection readback.
They are **not successful native acceptance runs**. The full transfer audit
correctly rejected the last of them. Do not remove that log gate.

The new capture needed an explicit UAV-to-UAV dependency after Niagara's
overlapped counter use, just as the existing birth/P2G captures do. That was
added before packing, then verified in the clean `600-v2` rerun above.

The old-position matrix capture remains useful as explicitly failed diagnostic
evidence: its `advection-diagnosis-v3.json` reports `rhi_validation_clean=false`.
Numerical motion replay matches within .007404 cm, but interior interpolated
divergence RMS is .0942504/s vs sampled centered-D .000266095/s. This is evidence
of the interpolation mismatch, not an accepted reference run or game benchmark.

## Verification and next action

Builds 35843, 20807, 16244, 26007 and 98775 succeeded (34.12, 34.70, 37.10,
34.94 and 24.86 seconds). All 406 Python liquid tests pass. Engine session
39174 terminated 0: `liquid-compatible-transport-engine/index.json` has 20 clean
successes, no warnings/failures. This includes compiled optional transport on
regional exterior graphs, support checks, native dt and retained FLIP/PIC blend.
Scoped whitespace checks pass. Saved playable-map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

Next, make interface and particle transport use the same velocity/interpolation
and explicit coordinate contract. Then correct the bed-adjacent support/contact
and particle/interface volume drift, testing actual flow and exact bed geometry.
Do not assert the current interpolation-only change solves the outflow decline
or makes the renderer physically consistent. No additional long capture was
needed to establish that this short run already fails physical acceptance.

Only after those failures are resolved should the single visible surface,
froth/spray, raft coupling, shoreline, reference comparison and playable
performance be accepted. South Fork → Colorado → Pacuare → Futaleufu, remaining
water/crew work, cleanup, release checks and final commit all remain active.
