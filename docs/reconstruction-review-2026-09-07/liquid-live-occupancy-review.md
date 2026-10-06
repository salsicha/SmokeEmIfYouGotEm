# Live GPU water-interior support — September 9

The render-only continuity correction now runs on actual current Niagara GPU
data in the unsaved South Fork fixture. It is not a physical-volume correction,
foam simulation, surveyed bathymetry, or photorealistic acceptance. The complete
goal remains active; no saved production assets were changed.

## Implementation and safeguards

`RaftSimLiquidOccupancyGPU` takes the particle-reconstructed scalar and current
solver `SolidVelocity_Boundary` RGBA texture. The live bridge resolves that grid
by name, type, layout and system ID, requires exactly one compatible 68×68×24
grid, and reads its current render-thread buffer after Niagara simulation.

The first GPU pass marks an interior cell only when all 27 cells in its 3×3×3
neighborhood are fluid. Domain-edge cells are excluded. The second interpolates
that support at render-voxel centers and floors reconstruction density with it:
`corrected_phi = min(particle_phi, 0.5 - interior_support)`. Exposed crests remain
particle-derived outside that interior support. No solver grid, particle,
position, collision mesh or boat state is written, and no extra visible surface
is added. The corrected scalar feeds distance generation and the same SimRT.

Only uniform 1×, 2× or 4× registered refinement is allowed. Invalid categories,
nonfinite source values and new liquid in a non-fluid parent cell are diagnosed;
callers reject these, rather than claiming a failed field is water. Ordinary
live-density captures remain unchanged unless `-RaftSimLiquidLiveBulk` is used.
Raw density, corrected scalar/support, actual boundary and displayed surface are
exported only at stop, outside the performance window. The diagnostic audit
buffer is not a production optimization.

## Actual live evidence

`liquid-live-occupancy-12s` exits 0, completes 750 GPU updates and has no engine
error lines or reconstruction diagnostic errors. Independent
`occupancy_audit.json` verifies:

- Current boundary texture exactly equals the separate native grid readback.
- Corrected scalar and interior support differ from the CPU reference by at
  most 4.7684×10⁻⁷, below the predeclared 2×10⁻⁶ / 1×10⁻⁶ limits.
- 13,740 false air samples in fully supported interior become zero.
- 23,067 render samples become wet; zero are in solid, air or external-stage
  parent cells. This is rendered occupancy, not added physical water mass.
- The displayed distance sign agrees with corrected scalar at every sample.

`live_pipeline_audit.json` separately verifies actual particle input: 71,036
particles, maximum packing error 0.001595 mm, valid finite distance/coverage,
and 30 distinct motion images. Capture wall time 40.395 s includes blocking
diagnostics and is not FPS. The final motion image was viewed: the surface is
more continuous internally but remains cyan/plastic, weakly frothy, with exposed
rectangular fixture edges. It is not accepted whitewater.

## Streaming cost check

`liquid-occupancy-benchmark-12s` exits 0 and passes both independent occupancy
and uninterrupted-window audits. Its 480 editor-fixture intervals average
23.063 ms, p95 25.377 ms. The 471 warmed GPU samples average 6.009 ms total,
including 5.410 ms packing+density+occupancy, 0.575 ms distance and 0.0237 ms copy.
The `pack_density_ms` label in the timing audit now includes occupancy; the
source report explicitly records this. The prior no-occupancy run averaged
5.966 ms total. These separate runs do not isolate a precise occupancy cost or
prove a speedup; no large regression is evident. They do not measure packaged
game FPS or satisfy full-scene performance acceptance.

The benchmark final state independently matches the CPU occupancy result to
4.7684×10⁻⁷, removes all 13,598 false-air interior samples, creates no new water
in non-fluid cells and matches displayed distance signs exactly.

## Regression evidence and remaining work

All 81 Python liquid tests pass (2.669 s). The actual-GPU engine test covers
1×/2×/4× refinement, mixed fluid/solid/air/external classifications, all-air input,
invalid integer/fractional categories, domain mismatch and dry-cell preservation.
The expanded full fixture suite has 12 successes and zero failures (25.13 s).
One older grid-frame-transfer test records an unrelated HTTP connectivity
timeout warning; the occupancy test itself is warning-free. The final explicit
finite-output assertion passes the separate final GPU regression (0.03 s,
zero warnings/failures) in `engine-liquid-occupancy-finite-final/index.json`.

The remaining foam mismatch is now identifiable in code: `RaftSimLiquidFoam.h`
still generates/limits foam around the inherited native SDF before the live
reconstruction replaces its geometry. `RaftSimLiquidOptics.h` samples that G at
the new ray hit. Interior support does not fix this mismatch. Next evolve foam
against the current reconstructed surface with persistent history and the
current velocity, preserving single-surface rendering. Evolution must follow
actual simulation steps, not additional frozen-camera/render callbacks. Verify
advection, decay, current surface placement and paused-state stability before
comparing real-reference appearance and motion again. Whole-scene shore/boat
integration and physical/visual acceptance remain open.
