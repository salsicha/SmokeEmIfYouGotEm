# South Fork: pressure surface and same-step native fields

The queue remains active. This is pressure diagnosis and instrumentation, not
accepted river physics, visuals, performance, or a completed South Fork scene.
The preceding user-status turn was informational; this continuation made
new native captures and added paired pressure instrumentation.

## Confirmed reference defect

The current collocated pressure gradient samples two cells apart. Atmospheric
pressure at the empty cell centre places the boundary beyond the actual water
surface. The CPU reference now optionally uses a supplied signed interface to
weight both the pressure matrix and velocity correction by the same reciprocal
interface fraction. It leaves the old operator unchanged without that field.

Reference: [Bridson fluid notes, section 4.5.1](https://www.cs.ubc.ca/~rbridson/fluidsimulation/fluids_notes.pdf).
The source derives the zero-pressure condition at the liquid/air crossing. Our
adaptation uses the existing centred gradient's **2h** span, not a nearest-cell
formula transplanted into a different discretization. No empirical theta floor
was introduced; nonfinite or inconsistent phase/pressure inputs are rejected.

`liquid-hydrostatic-pressure-diagnosis.json` compares identical authored,
fractional-height still-water geometry. The old operator converges to nearly
zero divergence yet creates 5.983 cm/s horizontal velocity and up to 57.24 cm
of excess pressure head after one step. Supplying the exact interface eliminates
those errors to numerical precision in that test. This does **not** prove the
river drainage cause or provide a live river surface. The correction is not yet
installed in the native river solver.

## Actual transfer support

`diagnose_liquid_transfer_occupancy.py` reads the selected native P2G totals,
excludes duplicate XY halos, and reports deposited volume separately from the
volume of all touched cells. It never calls support a measured water volume.

At step 600 of `liquid-native-reservoir-inward-flow`, 701276 actual particles
deposit 14598.34088 m³ in the physical grid. Nonzero support spans cells with
19799.25 m³ total volume, a ratio of 1.35627. In particular, 35162 cells carry
positive deposited density at most 0.1 of a full cell. The existing resolver
marks **any positive weight** as rasterized support. Terrain/exterior can still
override the resulting boundary classification, so this statistic alone was
insufficient to identify pressure-fluid cells.

## Paired native pressure packet

Added the optional `-RaftSimRegionalProjectionPacket` diagnostic switch. It
requires the existing native transfer packet and exchanged regional projection.
For the same selected native step and every owner it now retains:

- boundary, velocity and divergence immediately after Compute Divergence;
- pressure after the last Solve Pressure iteration and halo exchange;
- actual grid velocity immediately after Project Pressure.

Copies are read-only and occur in the actual dependent render-graph stages.
Native half/full precision is retained in files and recorded explicitly. A
missing field, wrong size/format, duplicate capture, mismatched step, or failed
write rejects the packet. No later stop-time CurrentData is relabeled as paired.
This optional capture does not alter the pressure solve or particle lifecycle.

`diagnose_liquid_projection_packet.py` reconstructs D M G from those fields;
predicted velocity and actual post-projection readback are separately labeled.
The two unsupported Z stencil edge layers and duplicate XY halos are excluded
from composed-stencil statistics. No new interface is fabricated from density.

### First native capture

Build 28828 succeeded. UE 66092 terminated successfully. Capture directory:
`liquid-native-reservoir-pressure-packet` (four-field version before the actual
post-projection velocity was added). 600 requested steps, all 598 compact commits
valid; storage changed by -593.58333 m³ over 9.96667 requested seconds. Full
native particle/identity/neighbor/P2G audit 22375 passes: 701269 particles, zero
reduction mismatches. This is not physical steady-flow or FPS acceptance.

The paired pressure inputs contain 201449 interior fluid cells. 16944 carry
positive deposited density <=0.1; none has exactly zero mass. Native pressure
spans -60206.89 to 376643.31 cm²/s². Reconstructed input divergence differs from
the native scalar by RMS 0.00006348/s (maximum 0.00048828/s). The pressure field
predicts residual divergence RMS 0.01881794/s versus input 0.15612272/s: about
12.05%. That prediction needed an actual post-projection velocity check.

### Actual post-projection GPU velocity

Build 55930 succeeded after adding the fifth field. UE 85515 terminated with
exit 0; directory `liquid-native-reservoir-pressure-output`. All five fields
were retained for all twelve owners at native step 600. All 598 compact commits
are valid; 729724 original + 22496 births - 50979 approved exits = 701241
survivors, followed by 37 births for the selected P2G step. Independent native
audit 57077 passes all 701278 particle identities, neighbor data and deposits,
with zero reduction mismatches. Storage is still -593.39583 m³; not accepted.

The actual GPU velocity gives divergence RMS **0.01865356/s**, versus the
captured input's **0.15663394/s** (about 11.91% remains). The independently
predicted output is 0.01865897/s. Predicted/native velocity differences are
RMS 0.01743 cm/s, maximum 0.12498 cm/s; native velocity is half precision.
No replacement pressure solve or modified fluid boundary was used to produce
this result. Of 201509 interior fluid cells, 16973 carry positive deposited
density <=0.1. These observations establish actual native residual divergence
and low-weight fluid classification; they do not establish that either alone
explains the entire drainage, shoreline or visual problem.

Validation: 376 Python liquid tests pass; engine regression 87665 terminates
successfully with all 18 tests clean (no warnings, failures or unrun tests).
Both builds, both native captures and both audits are terminal. The saved review
map remains unchanged. No new beauty capture or playable FPS measurement.

## Remaining work

The live liquid/air interface must be reconstructed consistently from the moving
water, terrain and external reservoir, then used by pressure and rendering. A
flat authored stage, arbitrary density threshold, or render-only occupancy
repair is not a validated substitute. Native convergence and signed reservoir
backflow/storage remain unresolved. Preserve the existing explicit failure
gates rather than silently removing out-of-domain water. After these physical
checks, review the actual single surface, foam, raft coupling, shoreline and FPS.
No map promotion, scene completion, commit or push in this pass.
