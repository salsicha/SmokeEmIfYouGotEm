# GPU distance reconstruction — in progress

This is a component validation, not accepted South Fork water or live animation.
The input remains the captured 60-second particle field, SHA-256
`4fa693dc140af6f757194b57ffbad06f83d847eaf6d13e278d5c7d6d5c9920ce`.
No production assets or particle dynamics are changed by the snapshot viewer.

## Interior consistency

The anisotropic density reconstruction contained air inside the solver's
conservatively eroded fluid classification. A full 27-neighbor erosion identifies
10,743 coarse interior cells. A cell-centered interpolation of that confidence
now floors the reconstructed density. This adds 26,008 liquid samples, none
inside a parent cell classified as nonfluid. Air samples within the conservative
core decrease from 26,135 to 209; none remain where confidence is exactly one.

This is not merely an invisible interior correction: exposed top crossings
change by 13.75 cm RMS, with a 1.69 m maximum. Reconstructed volume increases
from 424.12 to 540.79 m³. These are rendering volumes, not a physical mass
measurement. Contact, exposed shape and source agreement still need acceptance.
The generated evidence is `liquid-occupancy-reconciled-60s/report.json`.

## Bounded distance calculation

`liquid_eikonal_surface.py` provides a CPU reference with gradient-corrected
subcell seeds and metric-aware upwind Jacobi updates. Twelve iterations converge
on this captured field. On the original prefiltered density, its distance differs
from the exact reconstructed triangle distance by 3.10 cm RMS and 24.09 cm maximum.
This is an approximate distance field; sphere tracing must be checked in-engine.

The reconciled input/reference is `liquid-occupancy-eikonal-gpu-input`:

- 136 × 136 × 48 voxels over 22.3125 × 22.3125 × 8 m; 50 cm narrow band.
- Input scalar SHA-256: `66a7ecd6af4201a9c85b4aab9a2f8c68caf59f6aa74ddbe19217cefde2352985`.
- CPU RGBA16f reference SHA-256: `0014993d3cb2b8318992b2303c3fd92c7e148cf509710cd4ccee9b38bbc89156`.
- CPU reference generation takes 3.29 s, not real time.
- Top-crossing conversion difference is 6.09 mm RMS / 59.78 mm maximum.

The new `RaftSimLiquidRedistanceGPU` component implements seed, iteration and
resolve passes in the existing render-graph module. It accepts a GPU scalar
texture, writes a distinct RGBA16f volume and preserves the source green channel.
Its function contains no CPU readback. The diagnostic viewer does perform a
blocking readback to compare against the CPU reference before binding the output.
The predeclared check requires finite output, identical sign, and at most 0.1 cm
maximum CPU/GPU difference. This is numerical parity, not visual acceptance.

## Current validation

All 73 focused Python liquid tests pass. The editor build passed (103 actions,
1,420.76 seconds). The actual engine run is
`liquid-occupancy-eikonal-gpu-engine`, complete with no capture error. All 887,808
GPU voxels pass the independently checked scalar identity, sign, finite-value,
distance-error and unchanged-channel gates. Maximum CPU/GPU error is 0.03125 cm;
RMS error is 0.00697 cm. The engine binds the computed render target, not the
precomputed CPU distance texture.

The unchanged original control image has the same decoded SHA-256 as the earlier
exact-source run. All material uniforms and optical controls match; 117,678 pixels
change by more than two levels. The candidate image was inspected: some interior
gaps are filled, but the surface remains overly rounded and plastic, with exposed
rectangular test-window walls and raw diagnostic terrain. It is not photorealistic.
Foam is deliberately zero in this geometry comparison. Capture wall time (88.53 s)
and the blocking compute/readback interval (48.05 ms) are not GPU frame timings.

The GPU timestamp run (`liquid-occupancy-eikonal-gpu-timing`) passed the same
independent audit and produced identical decoded images. Eight warmed GPU
intervals range from 3.739 to 3.778 ms. This measures the reconstruction component
only; it excludes simulation, upload, readback and the rest of the scene. The
instrumentation build passed in 14.65 seconds.

The first engine regression run (`engine-liquid-gpu-redistance`) has ten passes
and one failure. The new five-input analytic GPU test passes changing plane
geometry and empty/full fields (maximum distance error 0.0078125 cm), but fails
exact foam-channel preservation. The failure is retained; more detailed coverage
diagnostics identified downward half-float conversion: input 0.0588235296 became
0.058807373 instead of the nearest half, 0.0588378906. The D3D12 readback uses a
direct byte copy for RGBA16f, so this was not a CPU readback conversion.

The resolve shader now explicitly selects the nearest half, ties-to-even, before
the typed UAV store. Already-half coverage remains an exact no-op. It uses HLSL's
[half conversion intrinsics](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/f32tof16)
to identify adjacent representable values and compares their error explicitly;
it does not assume an implicit store's rounding policy. The unchanged exact
coverage assertion now passes. The final run, `engine-liquid-gpu-redistance-final`,
has **11 passes, zero warnings/failures**, 23.05 seconds. Initial failure and
diagnostic failure reports remain intact. The 3.739–3.778 ms timing above predates
this small coverage-conversion change; do not present it as a final shipping cost.

Next is live scalar generation and an ordered GPU hookup that consumes the current
simulation output without a CPU readback or frozen snapshot. Then verify foam,
actual motion, whole-scene shore integration and performance. The occupancy and
anisotropic density stages still run offline; the GPU distance component alone
does not make the whole reconstruction real time. No production promotion or
scene acceptance is claimed.

## Live particle-to-surface continuation

The input limitation described above is now partly resolved in the unsaved
review scene. `RaftSimLiquidDensityGPU` implements spatial bins, weighted
covariance/eigenbasis fitting, number-density-normalized cubic kernels,
moment-matched voxel filtering, fixed-point density accumulation and a scalar
resolve. It retains unshifted particle centers and the CPU reference's bounded
aspect ratio and sparse fallback. The bin halo covers every potentially
contributing kernel and its fitting neighborhood. Four GPU diagnostics detect
invalid input/counts, invalid neighbor chains, invalid kernels and overflow.

The 80,629-particle comparison in `liquid-gpu-density-r32/parity.json` passes
the predeclared independent numerical gates:

- Maximum kernel matrix error: 0.00002716 per metre.
- Maximum relative normalized kernel-weight error: 0.00000793.
- Maximum density error: 0.00002902; RMS: 0.0000007793.
- All 14,859 top-crossing columns remain present; maximum height difference
  is 0.02081 mm, RMS 0.000607 mm.
- Original R32f scalar readback agrees exactly with the GPU accumulated field.
- No invalid-particle, neighbor, kernel or overflow diagnostics.

Two retained failures preceded that result. The first shader launch failed
because Unreal's parameter parser did not accept multiple bound declarations
on one line; the declarations are now separate. The next calculation passed
kernel/density comparisons but failed a lossy R32f-to-half readback check. The
readback was corrected to copy original float32 bytes, without relaxing the
gate. That diagnostic's `quit` command did not close the editor, so its completed
owned process was identified and stopped. The new Python launcher exits cleanly.
The two one-shot GPU intervals (9.428 and 23.785 ms) include diagnostic buffer
copies and are inconsistent; they are **not** a stable runtime or frame-rate
measurement.

`RaftSim.LiquidLiveDensityReview start` installs a callback after Niagara adds
its simulation passes. It packs the current GPU float-position attributes and
GPU instance count directly, runs density and distance reconstruction, and
updates the existing visible `SimRT` red channel. The existing green coverage
channel is preserved. It neither changes particle/solver grids nor introduces
a second mesh. `stop <unused-output-dir>` removes the callback and performs a
single blocking verification export. World cleanup also removes the callback
before its pinned component's simulation is destroyed. This is origin-tile,
fixed-domain review integration, not an all-river production migration.

The first live run completed but produced a render-graph validation error because
Niagara had already marked its texture for external read-only access. The bridge
now explicitly resumes internal tracking for its copy and restores external SRV
access afterward. The failing `liquid-live-density-12s` report is retained.

The corrected `liquid-live-density-access-12s/live_pipeline_audit.json` verifies:

- 750 GPU updates, with 71,016 final live particles.
- Packed positions agree with an independent final simulation-cache readback
  within 0.001504 mm maximum, 0.0001953 mm RMS.
- Finite signed distance and bounded coverage; all four GPU diagnostics zero.
- Thirty distinct fixed-camera motion frames, with no engine error lines.
- Capture completes and exits cleanly. Its 39.54 s wall time includes blocking
  captures/readbacks; it is not a performance benchmark.

The first and last motion images were inspected. Relief changes and travels,
but the material still appears cyan/plastic, much of the foam is not convincingly
white, and the rectangular diagnostic volume remains exposed. No photographic
likeness, whole-scene shoreline, raft coupling, stable runtime budget or long-run
acceptance is established. Conservative occupancy reconciliation is still CPU
only and is **not** silently included in this live result.

The 75 focused Python liquid tests pass. The post-integration engine regression
run (`engine-liquid-live-density-final`) has 11 passes, zero warnings/failures,
23.91 seconds. Next: finish coherent bulk/foam treatment on the live field,
measure uninterrupted GPU/frame cost, and calibrate actual animated renders
against references before production/shoreline integration. Do not rerun the
unchanged frozen snapshot milestone as a substitute for those steps.
