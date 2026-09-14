# Distributed GPU nonlinear acceleration — September 12 continuation

The nonlinear acceleration component now distributes vector operations across
the whole grid, with global reductions between PCG stages. This removes the
single-workgroup throughput bottleneck without changing the pressure equation,
40-iteration maximum, stopping criterion, geometry, resolution or tolerances.
It is still a component, not playable total-depth evolution or scene acceptance.

## Implementation

`RaftSimNonlinearAcceleration.usf` retains the original cooperative solver as
phase 0. The distributed path performs a two-level global RHS maximum reduction,
normalized initialization, and up to 40 globally coupled PCG iterations. Each
iteration dispatches W, transpose/diagonal application and partial dot products,
global alpha reduction, solution/residual update and partial norms, global beta
reduction, then direction update. Separate RDG passes provide device-wide memory
ordering. No independent tile solves or cross-workgroup spinlocks are used.

Both poles retain independent normalization, convergence and failure flags.
True residual is recomputed from the rescaled returned solution, not borrowed
from the recurrence residual. Fixed physical bed slope remains independent of
water weights; invalid-input diagnostics and exact dry identity rows remain.
The original path is callable with `bDistributed=false`; default is distributed.
No caller in playable evolution has been added.

## Actual GPU evidence

Build 14797 succeeded in 14.93 s. Isolated native session 96198 completed with
1 successful test, zero warnings/failures/unrun (0.579160571 s test duration):
`unreal/Saved/RaftSimValidation/south-fork-distributed-acceleration-v1-20260912/index.json`.

Both implementations are checked against independent CPU double-precision
face-accumulation solutions for 17x13 and 128x128 grids, closed/periodic boundaries,
zero RHS, dry cells and 1e-20 m thin water, with invalid graph and slope rejection.
Additional distributed tests cover 512x512 periodic and 1x257 closed grids.
Limits remain acceleration error <1e-4 and true relative residual <2e-5.
Distributed maximum observed acceleration error is 1.63523702e-7; maximum true
relative residual is 1.91208072e-7. The 512x512 case takes 29/11 iterations.

GPU timestamp intervals, milliseconds, all retained:

| Path | Eight 128x128 fixed-slope two-pole solve intervals |
| --- | --- |
| Original | 31.323, 31.388, 31.366, 23.433, 4.423, 4.477, 4.472, 4.239 |
| Distributed | 1.167, 1.158, 1.156, 1.156, 1.157, 1.197, 1.176, 1.177 |

Intervals include clear/prepare/solve and exclude input upload/readback. The
original was tested first, so warmup/order effects prevent attributing every
timing difference to the implementation. This is not frame FPS, a 512x512 cost
measurement, or full solver-budget qualification. Multiple RK solves and all
forcing/transport/foam/render costs are still absent from this component result.

The exact owned hydraulic cook PID 29104 was suspended and resumed successfully
(both status 0), recorded in the matching `-process.json`. Replay 8377 had already
exited successfully and was not restarted or paused. The profiler now permits
omitting both replay identity arguments only when that job is no longer running;
explicitly provided missing/mismatched identities still fail closed.

Binary SHA256:
`b51e019a54617d3c3352ae85e96fcf077fe246a6365b70c91b799a4bd38a5ed6`.
Shader SHA256:
`59dc46fbc70b69332b47c815f050e12932020db94715345e911eba4dfdaeda6b`.

Full native regressions 68419 CLOSED with 67 successes, zero warnings/failures/
unrun in 17.706604 s, report
`unreal/Saved/RaftSimValidation/south-fork-distributed-regressions-v1-20260912/index.json`.
CPU fixed-bed replay completed 20 s, but the 20.756 m/s peak still needs physical diagnosis; see
[fixed-bed evidence](normal-river-fixed-bed-pressure.md). Next work must qualify
actual nonlinear RHS/forcing and pressure reconstruction, total-state transport,
boundary/mean/window coupling and the completed shared render/contact frame.
Physical breaking/froth, evidence-based terrain/rapid shape, 30 FPS ordinary-play
acceptance, all remaining rivers/crew/release and final commit remain open.

The 3200 s / local 24000 hydraulic cook checkpoint passed both independent
state and artificial-bank audits. It is still settling; see
[expanded checkpoint](full-river-expanded-checkpoint.md). Rehashed normal map,
V4 water material, saved game and Raft DLL remain unchanged. Scoped whitespace
checks pass; whole-worktree `git diff --check` hit an LFS temporary-file access
denial on an unrelated pre-existing content JSON, not a source whitespace error.
