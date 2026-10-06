# Live GPU grid audit — pressure projection inconsistency

September 8. South Fork and the full ordered queue remain incomplete. No
production physics settings, scenes or assets were changed by this diagnostic.

## Actual readback, not a reconstructed particle grid

`RaftSim.LiquidGridReadback` in `RaftSimEditorLiquidGridReadback.cpp` selects
the active driven-boundary component, resolves its Niagara grid interfaces by
system-instance ID, and reads their live render-thread textures. It exports
Pressure, Velocity, SimFloat, SolidVelocity_Boundary, StartVelocity and SDF.
Disabled 3-cell/1-cell high-precision placeholders have no allocated texture and
are excluded. The original capture that included them failed its completeness
assertion and is retained as `liquid-terrain-grid-readback`.

Half-float source grids are read as RGBA16F. The first active-grid capture
converted R32 pressure to half precision and overflowed20,342 values at12s.
That is a **readback conversion failure**, not evidence of nonfinite simulation
pressure. The current reader copies the original R32 bytes slice-by-slice
through staging textures. `liquid-terrain-grid-readback-f32` has finite pressure
throughout, range -341,587.59 to372,269.31 at12s. The reader is blocking and
unsuitable for a gameplay timing benchmark. It does not modify simulation data.

Per-grid metadata records dimensions, tiling, attribute offsets, original pixel
format and output encoding. X is fastest, followed by Y and Z. Niagara's generic
interface bounding-box metadata is not the actual world transform: use the
captured system transform and user extents. `analyze_liquid_grid_readback.py`
decodes packed scalar/vector fields and rejects ambiguous/truncated input.

## Boundary and storage evidence

At12s, live ghost boundary flux west/east/south/north is approximately
41.3964/-45.0868/2.24735/1.47347m³/s, close to prescribed targets within source
half-float precision. The adjacent velocity-cell values integrate to
41.3957/-45.1804/1.87069/1.47344m³/s over the driven ghost support. This is not
claimed to be an exact staggered-face flux: the installed solver is collocated.
The south deficit coincides with three driven ghost cells adjacent to solid
terrain cells. The outgoing edge also has prescribed ghost support adjacent to
empty cells (43 in the160-iteration run). Boundary support needs consistent
terrain/free-surface treatment, not arbitrary velocity amplification.

At0.1s/12s, whole-fluid-cell volume estimates are850.669/1,020.423m³; rendered
negative-SDF voxel counts give662.011/719.891m³. Initial registered water volume
is about680.811m³. These distinct estimates expose why marker counts or whole
fluid-cell counts must not be presented as calibrated volume. Rendered SDF
volume is also not a calibrated subcell conservative measure. Cumulative
physical-face transport and storage convergence remain unverified.

## Convergence test and operator evidence

Baseline `liquid-terrain-grid-readback-f32` uses40 pressure iterations. A separate
capture `liquid-terrain-pressure-160` overrides only User.Pressure Iterations to
160 before activation; production defaults remain40. Both are12s actual-GPU
runs. On cells with all six neighbors fluid:

| RMS, 1/s | 40 iterations | 160 iterations |
| --- | ---: | ---: |
| Before-projection divergence | 0.126225 | 0.121564 |
| Final velocity central divergence | 0.112642 | 0.108013 |
| Nearest-neighbor Poisson residual × dt | 0.084305 | 0.000003582 |

These are different evolved states, not same-state iteration snapshots. The
160-iteration pressure equation converges tightly, yet divergence remains.
Compiled HLSL independently identifies the inconsistency:

- `Grid3D_ComputeDivergence` uses velocity at i+1 and i-1 divided by2dx.
- `Grid3D_ComputeGradient` uses pressure at i+1 and i-1 divided by2dx.
- `Grid3D_PressureIteration` solves the six-neighbor i±1 Laplacian with dx².

In fully fluid interior, composing those centered divergence and gradient
operators instead yields an i±2 Laplacian divided by4dx². The pressure equation
therefore does not invert the velocity correction's divergence operator.

The live160-iteration fields validate this explanation away from boundaries:
on11,698 cells with fluid support through two cells in each axial direction,
observed final-divergence RMS is0.05387865/s. Applying the actual centered
operator to the captured pressure predicts0.05386626/s. Observed-minus-predicted
RMS is0.00042541/s, consistent with half-float velocity/divergence readback and
storage precision. See `grid_operator_analysis_12s.json` in that capture.

## Next implementation

Correct the discrete pressure/velocity operators together, including normal
boundary faces, terrain/free-surface fractions and particle-to-grid/grid-to-
particle sampling. A consistent staggered finite-volume representation is a
candidate; do not change only one stencil and silently reinterpret the existing
collocated samples. Also account for actual dx32.8125cm and dz33.3333cm instead
of assuming cubic cells. Re-run the same live-grid residual, transport/storage,
contact and visual checks. Increasing production pressure iterations is not
the fix and would worsen the user's performance problem.

Current data tests:20 focused liquid tests pass, including decoder byte counts,
scalar tiling and preservation of pressures beyond half-float range. C++ build
passes. Physical/visual acceptance remains false.

Final Unreal regression `engine-liquid-grid-readback/index.json`:8 clean passes,
0 warnings/failures,16.06s. These regressions do not assert conservation.
