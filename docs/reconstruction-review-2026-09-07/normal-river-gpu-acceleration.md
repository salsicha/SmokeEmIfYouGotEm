# GPU nonlinear acceleration component — September 12

Implementation progress, not playable-water acceptance. The desktop target is
30 FPS, p95 33.333 ms, with the existing quality, timestep, solver, memory and
geometry/contact requirements unchanged. No gameplay water mode was switched.

## Implemented and checked on the actual GPU

Added `RaftSimNonlinearAccelerationGPU.h/.cpp`,
`RaftSimNonlinearAcceleration.usf` and `RaftSimNonlinearAccelerationTest.cpp`
to WaterDetail. The RDG component solves the two rational pressure poles using
the depth-weighted completed-square operator
`A = I + length * (W^T W + 0.75 * b b^T)` and diagonal-preconditioned CG.
It accepts actual depth/bed, the final reconstructed transport connectivity,
and two acceleration right-hand sides. It returns normalized accelerations,
the independently recomputed true residual, invalid-input/failure flags and
iteration counts. The maximum remains 40 iterations; it does not silently
increase the budget, clip depth, or add a water film.

The factored W coefficients avoid intermediate reciprocal depths. Boundary
indexing wraps only for safe array access; a nonperiodic boundary graph bit is
an error. Clamping indices would alias a boundary row into the transpose.
Invalid descriptors fail before dispatch. Invalid selected data is reported,
not accepted as a valid zero-water replacement. A future owner must reject
invalid/failure flags and qualify true residuals before publishing a frame.

The preparation pass is parallel across cells. One cooperative 256-thread
group owns the entire coupled solve and loops over all cells, using global
scratch and uniform synchronization; there are no independently solved tiles
or cross-group spinlocks. HLSL synchronization semantics were checked against
[Microsoft's AllMemoryBarrierWithGroupSync documentation](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/allmemorybarrierwithgroupsync)
and [RWStructuredBuffer documentation](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/sm5-object-rwstructuredbuffer).
This establishes an implementation contract, not physical validity or speed.
The single-group approach and supported 512-axis descriptor limit still require
maximum-size and performance qualification. Tested grids are 17x13 and 128x128.

Build 76621 succeeds in 18.72 s. Actual-device test 70398 exits zero:
`unreal/Saved/RaftSimValidation/south-fork-nonlinear-acceleration-v2-20260912/index.json`.
It records one success, zero warnings/failures/unrun tests, on AMD Radeon
graphics / D3D12 SM6. The earlier v1 launch never reached a test because its
sandboxed shader-cache service could not initialize; its log is retained.
Only that owned editor was stopped, then normal cache access was approved.

The CPU double-precision reference builds divergence/gradient by face
accumulation, independently of the GPU coefficient stencil. Manufactured
solutions include variable depth/bed, a dry cell, 1e-20 m positive depth,
nonperiodic and periodic boundaries, zero forcing and invalid connectivity.
Predeclared diagnostic limits (1e-4 acceleration error, 2e-5 true relative
residual) were not relaxed. Results:

| Grid / boundary | Maximum acceleration error | True relative residual | Pole iterations |
| --- | ---: | ---: | ---: |
| 17x13 closed | 8.39076325e-8 | 1.50818403e-7 | 30 / 11 |
| 17x13 periodic | 1.12514644e-7 | 1.72915911e-7 | 30 / 11 |
| 128x128 closed | 1.25836288e-7 | 1.87885336e-7 | 29 / 11 |
| 17x13 zero forcing | 0 | 0 | 0 / 0 |

These are component checks, not the actual river's pressure RHS or a scene
acceptance fixture. No nonlinear forcing, pressure-force reconstruction,
transport/RK, physical boundary/mean exchange, breaking or froth is implemented
by this component. The existing total-state storage component and this solve
are not yet connected to a completed render/contact frame in playable water.
The existing 116 focused Python tests were passed in the previous turn; they
were not rerun or increased merely because this GPU test passed.

WaterDetail DLL SHA-256:
`7d6d61cdc8d2e78576a2adc7e3dab445f4ea0b06eade0fcec45b5b3b76708eb5`.
Shader SHA-256:
`7dfffc77f8b83ab2a6a381e625f2847c5b55a3fd90c3cabbd878648a5e606f86`.
GPU C++ SHA-256:
`057abfb9e4fe89b13f6952dac2f566a3b453263c97ed4fa06322f89341eba535`.
Test C++ SHA-256:
`5ba83a509401dc06beda5c4c87d66d3edf6b49c22bd0dc82f4953fee73931a29`.
Only the public-header diagnostic comment was clarified after the build;
executable code and the tested shader are unchanged.

The full established native suite, session 10924, also exits zero:
`unreal/Saved/RaftSimValidation/south-fork-acceleration-regressions-v1-20260912/index.json`.
It records **67 successes, zero warnings/failures/unrun tests**, 18.843008 s
test duration. The new acceleration test, CareerCatalog and ProgressionMigration
all pass. Raft DLL remains
`ebd2936315c832530d1ebb32a25ee77b78f07ce3a0600c7eb893aa2ae5c1b3f6`.

## Longer river replay is still unaccepted

Corrected weighted 20-second replay 20297 / PID 30532 has now terminated,
**failed**, using the unchanged v2 command/input from the previous storage report.
At 6.0000 s: 720 steps, zero retries, maximum speed 7.11917 m/s.
At 8.00257 s: 1,220 steps, 11 retries, maximum depth 6.62217 m and maximum
speed **47.9215 m/s**; worst pressure residual 1.72853e-4. At 10.00047 s:
1,653 steps, 40 retries, maximum depth 5.90995 m and current maximum speed
8.20411 m/s. Recovery of the current maximum does not erase the earlier spike.
Do not promote this model or describe the earlier five-second pass as proof
of long-run stability. The GPU manufactured-solution pass does not fix this
physical/numerical failure.

Terminal v2 report:
`tmp/south-fork-depth-weighted-pressure-bank-twenty-second-v2-20260912.json`.
It stops at **11.4874585363 s**, 2,471 accepted steps / 342 rejected trials,
because the next stage-CFL step would be 9.83614e-10 s, below the unchanged
diagnostic floor. Maximum speed is 75,001,601.3493 m/s, maximum depth 16.92955 m,
and worst pressure residual 0.00195022504. The fastest cell is (y85,x50),
depth **0.2892817198 m**, bed 5.651535 m, momentum
(20620652.7762, -6747650.94934). This is not merely velocity division at a
vanishing-depth bank. Hydrostatic energy is 7.5434210165e15 (not full SGN energy).
The saved `.last-admissible-state.npy` means positivity/finite-state admission
only, not physical validity; SHA-256:
`2a01ab30dc006b35ec2a0121a0059a4e70f235c0af6ad4417ed6927858d8e86b`.

Original centered five-second replay 2816 / PID 14124 has also terminated,
**failed**, at 2.19022696086 s after 7,763 steps and 2,237 rejected trials,
exhausting its 10,000-trial budget. Maximum speed 10,384.1251 m/s occurs at
(y100,x106), depth 1.2947797e-19 m. Preserve
`tmp/south-fork-nonlinear-pressure-bank-v1-20260912.json` and its
`.last-admissible-state.npy`, SHA-256
`56cfdab40fc1fc0693e5903f58f9b2b64946083059855dbc06c57dfbd1648ada`.
Both process handles are closed. Neither failure was clipped, restarted or
relabelled as a completed replay; shell exit zero is not a diagnostic pass.

Cook 96057 / PID 29104 was observed at local step 21,260 / time 3,063 s.
The last BOTH-audited checkpoint remains 3,000 s / local 20,000; wait for
`frame_022000/complete.json` before auditing 3,100 s. It is still settling,
and runtime remains the previously audited 600-second state.

## Remaining acceptance

No new FPS capture, playable motion capture or reference-video playback was
made. The last measured ordinary-play result remains 21.571211 FPS,
p95 52.6052 ms: below the 30 FPS target. Component-test duration is not GPU
simulation cost or a frame-rate measurement. Map, V4 material and saved game
rehash unchanged. Terrain, rapid shape, physical breaking and froth, a shared
render/contact surface, all remaining rivers/crew/release checks and the final
commit remain active requirements. South Fork remains the scenario;
Troublemaker remains a rapid, not a standalone menu scenario.
