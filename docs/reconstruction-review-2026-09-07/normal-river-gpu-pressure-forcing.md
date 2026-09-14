# GPU nonlinear pressure forcing and reconstruction

September13 follow-up: [fused reductions and like-for-like timing](normal-river-fused-pressure.md)
supersedes the cost investigation and live-job state below. Full GPU transport
and playable integration remain open; the20s hybrid replay has now completed.

September12 continuation. The prior turn made concrete progress on hybrid
breaking. This turn adds the missing GPU nonlinear pressure pipeline, not just
another matrix solve. It remains unintegrated with playable transport/stepping.

## Implemented contract

`RaftSimNonlinearPressureGPU` consumes one stage's total(h,hu,hv,foam) state,
actual hydrostatic FV rates, matching(h,bed), reconstructed wet-face graph,
fixed physical bed slope and nonbreaking fraction. Seven parallel RDG phases
calculate velocity, discrete advective/divergence terms, kinematic quadratic/
curvature forcing, normalized base acceleration, correction RHS, reconstructed
integrated/bottom pressures and conservative pressure momentum force. The
existing coupled two-pole40-iteration GPU solve sits between RHS and pressure
reconstruction. There is no CPU readback in this path.

The model is the same experimental rational SGN extension as the CPU reference,
not an exact Whitham-GN/DtN solution. Actual FV h_t and momentum rates enter the
kinematic identities, including derivatives of depth-dependent water weights;
fixed bed slope has no time derivative. The same hybrid fraction enters forcing,
elliptic operator and pressure reconstruction. Depth powers are factored to
avoid unnecessary float32 underflow. No positive-depth floor or velocity cap
has been introduced.

Inputs/strides/counts are checked. State depth must exactly match the geometry
depth. Dry momentum, negative foam, invalid slopes/graphs/fractions, nonfinite
input rates and nonfinite intermediates are diagnostic failures. Zero failure
outputs are NOT a physical fallback. The caller must reject any input/solver
error and qualify the returned true residual before using the force or publishing
a completed state. Transport, RK stage rejection, GPU front detection, the
physical mean/boundary/window contract and shared render/contact publication
are not yet implemented in this helper.

## Independent represented-input reference

Generator `physics/scripts/export_nonlinear_pressure_fixtures.py` first rounds
state/geometry to float32, constructs the actual FV graph/rates on that state,
rounds rates/slope/fraction, then evaluates the CPU double-precision pressure
reference. This compares the arithmetic on representable inputs rather than
silently folding input-rounding differences into solver error.

Fixture artifact:
`tmp/south-fork-nonlinear-gpu-fixtures-v1-20260912.bin`, companion manifest `.json`.
SHA256 `5ec417add6f371bf1f38d6b9b76281ff9e1f4195905d4a29833b477d3a9b105b`.
Seven cases include a lake, closed and periodic nonlinear fields, mixed/zero
fractions with dry/1e-20m cells, and the actual captured128x128 South Fork state
with nonbreaking/front fractions. No positive input depths rounded to zero.
The captured cases' maximum depth rounding is1.192092896e-7m and maximum momentum
rounding4.759681858e-7. These are explicit input differences, not evidence that
all later shallow-state evolution is float32-safe.

The native test requires its reproducible fixture explicitly; it fails instead
of skipping when the fixture is missing. Generate before running it:

```powershell
python physics/scripts/export_nonlinear_pressure_fixtures.py --output tmp/fresh-pressure-fixtures.bin --snapshot tmp/south-fork-paired-strain-input-v1-20260912/live_01.json
```

Pass `-RaftSimNonlinearPressureFixture=<absolute binary path>` to the editor
automation command. Omitting `--snapshot` generates the five portable synthetic
cases. The native filter is `RaftSim.WaterDetail.NonlinearPressureGPU`; the
current68-test suite includes it and therefore also requires that argument.
Fresh output names preserve earlier evidence. The generator manifest records
source and implementation hashes. Its deterministic/no-input-mutation tests pass.

## Actual-device verification

Initial build26826 failed only on an unavailable test numeric-limit helper.
After replacing it with the standard C++ helper, build66951 succeeded16.76s.
Actual D3D12 test56193 CLOSED with one success, zero warnings/failures/unrun,
0.236863300s:
`unreal/Saved/RaftSimValidation/south-fork-nonlinear-pressure-gpu-v1-20260912/index.json`.

RHS, correction, both pressure fields and force are compared independently with
the CPU fixture; returned true residual is separately checked. Preset component
limits are relative error/residual <2e-5 and absolute force-component error
<1e-3. These are precision checks, not substitutes for geometric/contact or
full-scene acceptance tolerances. The older acceleration-operator tests keep
their unchanged1e-4 acceleration-error limit.

| Captured case | Max force-component error | Relative force error | True residual | Pole iterations |
| --- | --- | --- | --- | --- |
| Nonbreaking | 0.000122785568 | 9.84083572e-7 | 2.29461549e-7 | 40/24 |
| Hybrid fraction | 0.000153422356 | 9.73932596e-7 | 2.12536547e-7 | 40/23 |

Lake and zero-fraction force outputs are exactly zero. Synthetic nonlinear
force errors are below1e-6. Bad state-depth agreement, infinite input rate and
negative fraction are rejected. No error limit was changed after seeing results.

Full native regression32415 CLOSED with68 successes, zero warnings/failures/
unrun in16.305213928s:
`unreal/Saved/RaftSimValidation/south-fork-full-pressure-regressions-v1-20260912/index.json`.
156 focused Python tests pass36.82s (session62463 CLOSED).

## Cost and running work

Timing-only test instrumentation was added after the full native run; build2556
succeeded15.17s. It retains BOTH force and true-residual outputs so RDG cannot
cull residual evaluation from the interval. Eight repeated captured solves per
fraction case bracket forcing/solve/residual/reconstruction, excluding uploads,
readback, FV transport, RK, rendering and scene work. No timing is frame FPS.

Isolated timing26860 CLOSED, native test1success/0warnings/0failures/0unrun,
0.305978209s. Both exact owned jobs were successfully suspended and resumed
(all status0), with editor exit0/no timeout recorded in
`unreal/Saved/RaftSimValidation/south-fork-full-pressure-timing-v1-20260912-process.json`.
The profiler verifies exact cook29104 and
hybrid replay40864 identities and resumes both in a `finally` block. It now
accepts the explicit pressure test/fixture and the known hybrid replay command
as well as the earlier acceleration/fixed-bed modes; no arbitrary process is
paused.

All measured128x128 full-pressure intervals, milliseconds:

| Fraction | Eight samples |
| --- | --- |
| Nonbreaking | 8.341, 8.313, 8.328, 8.332, 8.309, 8.389, 8.286, 8.296 |
| Hybrid | 8.323, 8.311, 8.305, 8.319, 8.314, 8.374, 8.297, 8.267 |

This cost is NOT qualified for the complete water-update budget. No samples
were discarded. The previous roughly1.2ms number used a different manufactured
RHS and operator-only measurement; subtracting it does not isolate the forcing
overhead. Next distinguish actual-RHS operator cost, residual retention,
forcing/reconstruction and scheduling effects with like-for-like measurements.
Do not reduce the40-iteration maximum, resolution, simulation rate or physical
requirements simply to make this measurement pass.

Current timing-build WaterDetail DLL SHA256:
`75541904dabf76674ed3a6b8d5a82f5c6e5779128c11833d2ab7e42a88ef7cce`.
Pressure shader SHA256:
`eb049858bec457e665fbf767ff4bc81fd2792bc585aa7a61e2baa41fd5d14dd1`.
The full68-test report used the immediately preceding DLL
`4df577db7c35a3bdd2a8dcfec917fa6a0ec6d1950462c9b00926be0b9e98b886`;
only optional timing test code changed between those builds.

Hybrid20s replay23543/PID40864 is live, last14.503964s/1946steps/404retries,
peak15.637795223m/s, residual2.275818715e-6. It is not completed or physically
accepted. Cook96057/PID29104 remains live,3200/local24000 last BOTH audited,
3300/local26000 next after its marker. Normal map/V4 material/save hashes are
unchanged, and no fresh ordinary-play FPS or reference playback occurred.
Next: complete GPU conservative transport and stage acceptance, physical
boundary/mean/window exchange, breaking-energy/froth evolution and one completed
render/contact frame, then validate actual play and all remaining scene/source,
river/crew/30FPS/release/final-commit requirements. The full goal stays active.
