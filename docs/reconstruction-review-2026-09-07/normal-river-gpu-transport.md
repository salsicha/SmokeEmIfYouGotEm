# Conservative GPU transport connected to pressure — September 13

Previous goal turn made concrete progress on fused pressure reductions. This
turn adds the missing GPU finite-volume transport rate and verifies its
connection to the nonlinear pressure pipeline. It does not yet step or publish
playable state. The full terrain/water/scenario/crew/release goal remains open.

## Implemented

`RaftSimTotalDepthTransportGPU` consumes exact-size total-state float4
(h,hu,hv,foam) and physical-bed float buffers. Six parallel RDG phases validate
inputs and derive velocity/fixed bed slope; reconstruct MC depth/free-surface/
velocity slopes; flatten partially dry original polynomials once; evaluate
shared hydrostatic Rusanov faces; assemble conservative rates and per-group
signal maxima; and reduce the global CFL bound. Closed boundaries reflect
normal momentum only, periodic boundaries wrap. First-order comparison remains
available. There is no CPU readback in the implementation.

The one-pass flattening uses the ORIGINAL polynomial; neighbor flattening does
not cascade through a thin film. Momentum-conserving velocity reconstruction
uses opposite-face depth weights and neighbor bounds. No cell-average depth,
momentum or velocity is clipped/repaired. Bed and depth differences are formed
separately so small positive depth is not replaced by rounded absolute eta.
Returned Geometry, PhysicalBedSlope, Pairs and HydroRate belong to this same
stage and are passed directly to `RaftSimNonlinearPressureGPU` in the native
test. The CPU reference rate/graph are never uploaded as those pressure inputs.

The rate's foam component is explicitly zero: foam transport/production is
NOT implemented by this helper. Global CFL is .4*dx/(max signal x + max signal y),
infinite only for zero signal and zeroed on diagnostics failure. All diagnostic
errors must be rejected before applying rates or publishing a frame. Open
river boundaries, moving-window/mean exchange, GPU front detection and RK
positivity/CFL/true-residual stage acceptance remain missing. FP32 arbitrarily
thin/subnormal evolution is not qualified by the tested1e-20-depth case.

## Exact resting-water cancellation

The owning-cell hydrostatic polynomial and bed source are now combined before
rounding, in CPU and GPU implementations:

`.5*g*(hp^2-hm^2) + g*h*(deta-dh) = g*h*deta`.

The remaining face deviation is `.25*g*(hsb-hsa)*(hsb+hsa)`, opposite on its two
owners. This is algebraically the same hydrostatic Rusanov equation. Four
independent CPU tests compare against the original expanded form for random
depth/bed states, both axes and closed/periodic boundaries (atol8e-14,
rtol2e-14). No physical or acceptance tolerance was weakened.

The initial GPU run also exposed a floating-point contraction artifact: using
one fused multiply-subtract for two equal opposing transport products left
resting-lake mass flux8.94e-8 instead of exactly zero. `precise` products and
subtraction preserve the intended equal-product cancellation. The corrected
GPU run has exactly-zero resting-lake mass and momentum rate AND pressure
force. The strict test was retained, not relaxed.

CPU bank driver SHA256 is now
`5c60d2d5b90eb72e89561fde0e1b4ebd707610fb1f250b6117d61e38666bd85b`.
The completed20s hybrid replay from the prior turn used the previous
`7b439ba2813e59cbce0705f808e3e5e82ffcb42f19a9c0d6e7ef7f535c662bff`
implementation. Preserve that evidence as historical; no new20s trajectory
is claimed for the refactored arithmetic. The live hydraulic cook is a separate
unchanged executable and was not modified or restarted.

## Fixtures and verification

`physics/scripts/export_total_depth_transport_fixtures.py` emits fresh binary
and source/hash manifest files. It quantizes inputs to float32 first, evaluates
CPU double transport, then computes independent pressure from rounded CPU
hydro rates. Cases: dry grid, resting lake with emergent banks, dry-bed dam
break (MC and first-order),1e-20 water on a1000m datum/sloping bed, moving water,
periodic flow, a one-column grid, and captured128x128 South Fork.

Current fixture:
`tmp/south-fork-total-transport-fixtures-v2-20260913.bin`, SHA256
`7a73554c6c2a80cc6fe436919c8693f7604dacc8b581ec0dd97164c0dbf950b9`.
v1 is retained and predates the factored hydrostatic balance. The original
pressure-only fixture remains a separate, source-hashed component reference.

The native filter is `RaftSim.WaterDetail.TotalDepthTransportGPU`, requiring
`-RaftSimTransportFixture=<absolute binary path>`. The expanded69-test suite
now requires BOTH this argument and `-RaftSimNonlinearPressureFixture=...`.
Omission fails explicitly rather than silently skipping GPU evidence.

Initial build45887 failed on test-harness bool conversions and mutable array
view uploads. Fixed build3920 succeeded13.90s. The accidentally dispatched
pre-build test10033 exited1 with no matching test and is NOT verification.
Native38785 then exposed UE shader-parameter parser rejection of grouped
declarations; individual declarations fixed it. Native95635 ran and failed
the exact lake/conservation check above. All failed logs are retained.

Corrected actual-device native77940 CLOSED1success/0warnings/0failures/0unrun,
0.229069099s:
`unreal/Saved/RaftSimValidation/south-fork-total-transport-gpu-v4-20260913/index.json`.
Every fixture has exact wet-graph and bed-slope agreement. Dry/lake rates and
forces are exactly zero; invalid negative depth, momentum without water,
infinite bed and negative foam are rejected. No thresholds were changed after
seeing results. Preset component limits: relative error/residual2e-5, absolute
rate/force error1e-3; closed/periodic mass-rate sum tolerance2e-6 times the sum
of absolute cell mass rates (and exact zero when that sum is zero).

Captured128x128 results:

- Rate max error6.00814819e-5, relative1.17882478e-6.
- Mass-rate sum−6.81247911e-8 versus absolute-rate sum1971.92458.
- Coupled pressure force max error0.000110626221, relative1.14619023e-6.
- True pressure residual2.1377729e-7, all error diagnostics zero.
- CFL0.0111940531s, relative error8.31979841e-8.

Thin1e-20-depth case rate relative error6.58751157e-8 and coupled-force error
6.61838861e-8; no positive input depth rounded to zero in any fixture.
The focused CPU suite39800 CLOSED136passes32.97s, including new algebra,
fixture/input-isolation and existing pressure/breaking/bank tests. This is
the explicitly selected suite, not a claim that every project test ran.
Expanded native61640 CLOSED69successes/0warnings/0failures/0unrun in15.702791214s:
`unreal/Saved/RaftSimValidation/south-fork-total-transport-regressions-v1-20260913/index.json`.

WaterDetail DLL SHA256:
`a21cd54af9564ff46bd676f4ee56c68c6125dce38d8665b1e33488c6750f42ec`.
Final transport shader SHA256:
`3ba7596f2e89d47c8da27d56e5f819c3588445862d3a5e26352312506edcee30`.

## Remaining integration and live work

Cook96057/PID29104 remains live, last3368.5s/local27370.3300/local26000 is the
latest BOTH audited checkpoint;3400/local28000 follows only after its marker.
It is still settling and runtime600s data remains unchanged. No new reference
video playback, playable map/material/save update or ordinary-play FPS capture.
Next add GPU RK stage acceptance and time advancement, then physical river
boundary/mean/window and breaking/froth coupling with one completed render/
contact surface. Single-stage precision is not physical evolution or30FPS
acceptance. All other terrain, river-order, crew, normalization, release and
final-commit requirements remain active.
