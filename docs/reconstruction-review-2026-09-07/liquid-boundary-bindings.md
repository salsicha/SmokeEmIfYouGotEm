# Full boundary bindings and computational margin

September 8. South Fork and the full queue remain incomplete. No production
asset or level has been replaced, and no commit has been made.

## Correction to earlier reports

The earlier axis diagnosis inspected custom-HLSL argument labels but missed
the module bindings supplying them. Actual compiled `ComputeBoundary` binds:

| Grid face | Exposed control |
| --- | --- |
| -X | Left |
| +X | User.Open Outlet (direct binding) |
| -Y | Back |
| +Y | Front |
| -Z | Down |
| +Z | Up |

The recent Back=false/Down=true candidate therefore closed a river side and
opened the floor. The original source factory was correct on this point.
Current factory and transient code restore Back=true/Down=false. Historical
wet-start and exact-triangle reports now explicitly retain this limitation.
Their particle contact measurements are not erased or re-labelled.

The regression checks all six compiled axis bindings, the exposed control
defaults and the separately bound positive-X outlet. The first run's test
pattern used the wrong compiled control prefix and failed (7 passed, 1 failed);
it is retained in `engine-liquid-boundary-bindings`. Corrected pattern run
`engine-liquid-boundary-bindings-final` has 8 clean passes, no failures/warnings.
The process exit code alone was insufficient: Unreal returned zero even for
the failed regression, so the JSON test totals were inspected.

## Corrected-boundary actual GPU capture

`liquid-terrain-boundary-bindings-v2`, log `CaptureLiquidTerrainBoundaryBindingsV2.log`:
720 steps at 1/60s, complete=true, 33.29s diagnostic wall time (not gameplay FPS).
At 12s: 77,995 live particles, zero nonfinite positions/velocities, zero sampled
bed penetration, 61 particles outside the physical fixture. Mean speed
59.398cm/s. Upstream/centre/downstream counts 46,597/15,551/5,200, with mean
downstream velocity 21.131/7.181/20.091cm/s. Weak flow and inlet accumulation
persist. The fixed opacity-one image was inspected: pale, broad smooth liquid
with holes and edge strips, not realistic whitewater.

## Isolated grid-margin candidate

`RaftSim.LiquidTerrainMomentumReview grid-halo` inherits corrected controls,
registered wet initialization, exact shared pressure/contact terrain, corrected
world-to-grid velocity transfer and full neighbor gather. It increases only
the horizontal computational extents to 2231.25cm and maximum-axis count to 68.
Cell size remains 32.8125cm. The two-cell EMPTY numerical border then lies
outside the native 21m physical faces. Source coordinates/velocities/discharge,
initial particles, terrain and physical retirement box remain unchanged.

Capture metadata and readback distinguish computational from physical extents.
Outside-particle and regional flow measurements still use the original 21m
window. This is a boundary-placement experiment, not prescribed grid inflow,
calibrated liquid volume or outgoing-stage coupling. Acceptance requires actual
GPU contact/flow results, sustained mass exchange, realistic motion/optics and
the unchanged performance budget.

## Margin result — not accepted

Actual GPU capture `liquid-terrain-grid-halo`, log
`CaptureLiquidTerrainGridHalo.log`, completed 720 steps/12s in 22.72s diagnostic
wall time. Actual pressure dispatch is 34x68x24 (red/black half-X dispatch),
consistent with a 68x68x24 grid. Both candidates have zero detected bed
penetration at every captured age (0.1, 0.5, 1, 4, 8 and 12s).

| At 12s | Corrected controls, no margin | Two-cell outer margin |
| --- | ---: | ---: |
| Live particles | 77,995 | 23,576 |
| Outside physical 21m domain | 61 | 111 |
| Maximum analysis-bin occupancy | 6,827 | 70 |
| Median speed, cm/s | 41.334 | 38.942 |
| Mean upstream X velocity, cm/s | 21.131 | -22.699 |
| Mean centre X velocity, cm/s | 7.181 | -6.776 |
| Mean downstream X velocity, cm/s | 20.091 | 28.888 |

Bins are independently computed floor(local_position/32.8125cm), not a readback
of NQ occupancy. The margin removes pathological inlet clustering but does not
maintain the wet state: initial live count 77,238 falls to 23,576 despite ongoing
sources. Flow reverses upstream and centrally. The fixed opacity-one image was
inspected; broad pale/smooth coverage and edge strips still fail visual gates.
No claim that a lower particle count or shorter diagnostic run is a performance
fix. The candidate remains opt-in and unsaved.

Final expanded Unreal suite `engine-liquid-grid-halo/index.json`: 8 clean
passes, 0 failures/warnings, 14.40s. GridFrameTransfer now exercises six variants,
including cell-size and physical-face invariants for the margin. Thirteen
focused liquid Python tests pass. Saved contact, registered level and project
hashes remain unchanged.

Next: prescribed incoming normal velocity and outgoing stage/pressure on the
native faces, with the outer numerical band as support. Stock pressure solve
uses SolidVelocity components to drive normal flux adjacent to SOLID cells;
ProjectPressure imposes matching normal components. A driven wet ghost boundary
can use that mechanism, but must not turn real terrain into a moving wall or
force unsupported tangential no-slip. Incoming particle counts alone are not a
boundary condition. Verify cumulative entry/exit and storage, then sustained
contact, motion, optics, raft support and performance. Do not prune crowded
water or restore the arbitrary neighbor cap to mask the problem.
