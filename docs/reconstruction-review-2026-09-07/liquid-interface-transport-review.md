# South Fork: explicit interface preparation and GPU transport

2026-09-11. Previous goal turn made progress by rejecting a raw density cutoff
against the actual river. This continuation implements initial interface data
and the native GPU transport operator. It does not yet connect that operator
to the continuous regional simulation, pressure boundary, or visible renderer.
All scenes remain incomplete; no acceptance gate has changed.

## Initial interface from the existing terrain and hydraulic prior

`physics/scripts/prepare_liquid_interface.py` creates one R32F scalar per region,
with exact native computational cell dimensions and coordinate handedness.
The scalar is `z - stage` in centimetres, negative on the liquid side. It is
**not signed distance**. Liquid occupancy also requires being above the exact
registered terrain; the scalar's extension underground is not rendered water.
Dry hydraulic samples do not invent water between the coarse source bed and
the exact triangle surface: their initial level is at/below the exact solid.
Particle density is not used to decide whether the surface exists.

Inputs retain registered geometry, original wet-stage prior, region metrics,
and SHA256 provenance. The hydraulic prior and submerged bed remain explicitly
uncalibrated/inferred, not surveyed bathymetry. No positions, boulders, terrain,
source discharge, water elevations, or saved assets were adjusted to improve
the result.

Prepared package: `tmp/south-fork-liquid-interface-20260911/manifest.json`.
All 729,724 original particles have complete interpolation stencils. There are
64 particles above the interpolated scalar zero set, compared with 9,025 for
the previous density candidate. The largest discrepancy is 37.07088994 cm,
so this is **not accepted initial coverage**. It needs subcell representation /
particle correction, not an upward shift of the entire river surface. The
prepared fields were not installed in the running river or saved map.

## Actual GPU implementation

New files:

- `RaftSimWaterDetail/Public/RaftSimLiquidInterfaceGPU.h`
- `RaftSimWaterDetail/Private/RaftSimLiquidInterfaceGPU.cpp`
- `Shaders/Private/RaftSimLiquidInterface.usf`
- `physics/scripts/liquid_interface_transport.py` (independent CPU reference)

The operator carries the previous scalar using the supplied current grid-local
velocity in cm/s and the actual anisotropic cell dimensions. It uses midpoint
(RK2) backtracing and centred trilinear interpolation. Source and destination
are distinct textures. No camera-relative offset, density reset, artificial
wave displacement, or new plane is introduced.

Only a caller-specified half-open XYZ ownership box is updated. Halo and
boundary samples outside it remain bit-identical. Traces that exceed the
available sample stencil and nonfinite inputs/results increment explicit GPU
error counters. An invalid cell retains its old value for diagnostic containment;
that is **not** a successful timestep or a substitute boundary condition.
Callers must reject steps with errors and supply proper halo/exterior values.
The implementation allocates an R32F result and a three-word diagnostic buffer
and uses one transport dispatch; it does not read back particles.

This is a transport primitive. It does not claim conservative level-set volume,
particle correction, boundary exchange, pressure coupling or playable speed.
Trilinear transport is diffusive over repeated steps; that remains a reason
to implement and test particle correction / appropriate higher-order transport,
not to ignore volume drift or silently regenerate a surface each frame.

## Verification on actual river fields

`prepare_liquid_interface_transport_cases.py` verifies the successful native
capture's dataset, original seeds, all 598 compact transactions, paired fields
and final population before preparing cases. Inputs are the actual twelve
regional initial scalar fields and native **post-pressure** velocity fields at
step 600 from `liquid-native-reservoir-metric-sor`. Their combination is an
operator test, **not a reconstructed step-600 interface or coupled trajectory**.

Case package: `tmp/south-fork-liquid-interface-transport-cases-20260911`.
Each input/reference binary has an independently verified hash and size.
The exact uploaded float32 scalar, float16 velocities and float32 metric/dt
are evaluated with float64 CPU arithmetic. The three additional analytic
cases check stationary water, metric translation, and a deliberately excessive
trace that must report 192 rejected cells. The tests also reject invalid
metric/timestep/layout/aliasing and check caller-owned boundary preservation.

The new `RaftSim.Editor.LiquidInterfaceTransportGPU` engine test compares all
2,181,600 grid samples. Maximum GPU/CPU difference is **0.000350952148 cm**,
below the predeclared 0.02 cm arithmetic test tolerance. All actual-region
interior test traces have available stencils; the deliberately invalid trace
case is reported, not clamped into success. This scope excludes the outer two
Z layers and XY halos; live floor/roof/exterior treatment is still required.

Five new CPU tests cover stationary transport, analytic metric translation,
spatially varying midpoint velocity, invalid traces and input validation.
All **395 Python liquid tests** pass.

## Build and engine results, including failed attempts

- Build session 68031 succeeded in 32.75 s.
- Engine session 64798 failed before tests: the shader parser rejected multiple
  root parameters in a comma-separated declaration. Parameters now have separate
  declarations. The failed log remains `liquid-interface-transport-engine.log`.
- Engine session 36251 terminated with exit 0 but the report had **one failed
  test**, because the diagnostic buffer lacked `BUF_SourceCopy`. Numerical
  agreement alone was not accepted. One other test had a warning. Retained:
  `liquid-interface-transport-engine-v2/index.json`.
- Added the required diagnostic-buffer copy access. Build 72510 succeeded in
  15.48 s.
- Engine session 3614 terminated with exit 0. Authoritative report:
  [engine v3](liquid-interface-transport-engine-v3/index.json): **20 clean passes,
  zero warnings, zero failures, zero skipped tests**. RHI validation enabled;
  no RHI error or fatal error in that log.
- Python case preparation session 71243 also terminated successfully.
- All processes are terminal; no native flow job was launched this turn.

## Next required work

Connect the explicit scalar to actual aligned regional timesteps, retain it
between RDG graphs, and exchange internal halos without resetting them to the
initial stage. Read/verify the native simulation timestep rather than assuming
that requested wall time is authoritative. Handle actual exterior stage/inflow,
outflow/backflow and floor/roof boundaries explicitly. Correct under-resolved
initial coverage using physically consistent interface/particle information.

Then use the SAME moving interface for ghost-fluid pressure distances and
render reconstruction. Pressure weights must match in the matrix and velocity
update, as in the existing CPU ghost-fluid reference. Re-run full-river native
mass/identity/pressure/storage/backflow audits and actual engine motion/render
and FPS checks. The old long run still fails at step 641; this uncoupled
operator test does not fix or invalidate that evidence.

No scene promotion, map edit, visual acceptance, final commit, or push occurred.
