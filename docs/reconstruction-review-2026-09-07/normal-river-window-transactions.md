# Explicit moving control-volume transactions — September 13, 2026

The previous turn fixed a shoreline polynomial defect and passed the short live
state comparison. This turn implements the next missing integration mechanism:
same-instant source handoff and retained-state transfer when the window moves.
This is not a completed playable nonlinear water surface or 30 FPS acceptance.

## Actual source handoff and GPU ownership

Before an overlapping crop changes sampling coordinates, the normal component
samples the old67x67 source/halo and512 independent boundary faces at the current
native instant. The new crop is sampled at that same instant. The immutable new
source owns the closing old-window packet; neither exterior is inferred from
the other. Revisions remain ordered. Overlap state, bed and carrier reference
must agree exactly at their represented world positions.

The nonlinear owner atomically admits both endpoints into its existing bounded
queue. It finishes the old physical interval before dispatching a spatial move.
The transfer copies retained h/hu/hv/foam bit-for-bit; only exposed cells enter
from the explicit source. The previous state remains owned until asynchronous
transfer diagnostics validate the candidate. No production GPU waits, implicit
time advance, endpoint snapping, interpolation of evolved state or depth floor.

A separate cumulative float4 inventory records entered-minus-departed density
by accounting slot. Summing all slots times cell area accounts for movement of
this finite control volume; it is separate from oriented physical boundary flux.
Slots are not persistent world positions. This does NOT feed departing waves or
foam back into the outer hydraulic solver, and does not establish correct reentry
after leaving/revisiting the window. That coupling remains unfinished.
Zero-shift surface projection without an exchange history compiles out this
accounting path and allocates no extra inventory buffers.

Build46723 succeeds88.29s. Native26902 passes90 clean tests in21.834637s.
Four signed moves (16/0,-16/3,0/17,5/-17 cells) preserve every expected state
cell and explicit inventory exactly after actual preceding GPU evolution.
Later source mean depths do not reset surviving state. Missing/mismatched
closing observations, fractional/no-overlap moves and insufficient capacity
are rejected before partial admission. Further tests add two consecutive moves
with intervening evolution and cumulative momentum/foam accounting.

## Real run exposed startup and capacity limits

First normal-map run9898 exits0 but does not produce the requested audit: the
initial implementation attempted to close the saved map's old crop after the
scenario had teleported into a new native domain. It disabled detail at startup.
This failed capture is preserved, not presented as a successful water test.

The component now distinguishes nonoverlapping scenario teleports from ordinary
overlap moves. No old-domain observation is fabricated. Missing closing data
makes a nonlinear move inadmissible, but does not disable the existing playable
solver merely because an optional candidate cannot transfer. The nonlinear owner
still refuses unqualified teleports after its evolution begins; a full reset
lifecycle remains necessary before normal promotion.

Corrected build58328 succeeds16.61s (preceding audit build70568 succeeds21.32s).
Actual run86637 exits0 and resumes the same verified cook32144. Normal water
continues through actual moves; first overlap14,112 cells at source time
3.7333335280418396s, offset(-16,+2). Source admission validates the actual old/new
overlap, not a manufactured fixture. However, four-trial dispatch falls behind:
the16-observation queue fills before the owner reaches that move. It stops
explicitly, retaining unconsumed inputs; no time/source is discarded.

`tmp/south-fork-live-window-owner-v2-20260913.json` records16 completed intervals,
56 graphs,0 completed moves, last complete endpoint1.8666667640209198s and
actual retained-state clock1.933333434164524s, remaining0.06666667014360428s.
The32 accepted observations include both actual first-move packets. Capture SHA
`49da97748ab0aca18d97ac38e0b486f660e9a74e92aa4cf8c3ac9224b5a58ec4`.
This is a capacity FAILURE, regardless of any independent state agreement.

The audit now exposes a bounded1..8 trials-per-graph experiment; default remains4.
It changes batching only, not accepted timestep/CFL/pressure limits. Final build
62369 succeeds18.47s. Independent moving-control-volume parser/replay tests plus
existing owner/temporal/30 FPS budget tests pass41 tests in1.21s.

Full-river continuation84534/PID32144 remains alive. BOTH5300s/local26000 audits
pass; all5,382,400 cells finite and86,720 artificial-face cells exactly dry.
Outlet123.127112415 versus inlet45.306954547m3/s is still settling. Runtime600s
data unchanged; next5400s/local28000 requires both audits after complete marker.

Final pre-pipeline native70743 passes90 clean tests in21.866207s, including two
consecutive moves with intervening evolution and exact return-state/inventory.
The expanded storage tests verify cumulative signed momentum and foam inventory;
ordinary zero-shift frame projection excludes that extra accounting work.

Independent comparison6788 completed evolution but failed JSON serialization
on a NumPy Boolean. Its partial report/state output is preserved. The writer now
uses a native Boolean and validates serialization before opening outputs; a
regression covers this. Fresh replay32654 exits0 with a FAILED accuracy report:
`tmp/south-fork-live-window-comparison-v2b-20260913.json`. At1.933333434164524s,
26 cells exceed1e-4; maximum0.004802509481 at y73/x68 transverse momentum.
Relative h/hu/hv errors2.813618e-5 /1.185931e-5 /4.132642e-5 also fail the
unchanged2e-5 gate for two components. GPU float water balance2.871708e-4m3.
The four-interval shoreline pass does not establish longer-time accuracy.

Actual eight-trial capture37221 exits0 and resumes cook32144, but also reaches
the16-source capacity limit before completing the first move:23 intervals /
43 graphs,0 moves. `tmp/south-fork-live-window-owner-v3-20260913.json` preserves
the failure and its actual source packets/reference fields. Batching alone is
not enough; no sustained capacity or physics acceptance is claimed.

Inspection identifies a scheduler stall: every pending CPU status copy blocks
the next graph even though the GPU already owns immutable progress and guards
completed/failed intervals. The owner now permits at most two additional graphs
within that SAME bracket while one readback is pending. It never reuses pending
readback storage or changes endpoints early. A completed earlier status implies
later same-bracket graphs preserve state/clock/inventory as no-ops. The zero-run-
ahead control is retained for tests. Build93945 succeeds21.72s; fresh native and
actual capture verification are required before relying on this change.

Native9957 exits0 with89 clean successes plus1 success with a D3D12 descriptor-
cache exhaustion warning, no failed/unrun tests. All twelve clock/slot/run-ahead
configurations retain exact state and endpoints; the test had accumulated all
twelve GPU stress cases in one automation frame. Keep this warning in evidence.
The cases now run as separate complex-automation entries, preserving all twelve
configurations plus the full window/invalid-input transaction case. No warning
suppression, descriptor-budget increase or removed assertion. Build56657
succeeds14.63s. Expanded native54830 exits0:102 clean successes, zero warnings,
failures or unrun cases,25.009760s. The warning is resolved through independent
automation frames, without deleting stress cases or changing runtime budgets.

Actual pipelined capture97329 exits0 and resumes cook32144. It completes31
observed intervals /472 accepted trials and the first real move at exactly
4.000000208616257s. There are75 graphs, including15 dispatched while an earlier
same-bracket status was pending. Final origin(-5458,3567)m, progress
(4,2.086162567138672e-7,0,0), one completed move, no owner failure or pending
readback. Actual first move(-16,+2) retains14,112 cells and exposes2,272.
`tmp/south-fork-live-window-owner-v4-20260913.json` SHA256
`a3eb1133e8eff1b0d3bae3953b20b1c39ed8b8d661c1a72ab2e74a7ab1400586`.

Nine source observations remain retained; the latest is5.066666930913925s.
The1.0666667223s backlog means this is NOT sustained-capacity qualification.
Nor does completing a move override the known longer-time numerical failure.
Independent through-move replay23901 completes with a FAILED state-gate report:
`tmp/south-fork-live-window-comparison-v4-20260913.json`. At the exact four-second
endpoint,140 cells exceed1e-4; maximum0.008853043960 at new-grid y68/x60,hu
(GPU-0.2594363689423 versus CPU-0.2505833249821). Relative h/hu/hv errors
5.014856e-5 /2.658572e-5 /2.603809e-5 all fail2e-5. The independent replay
validates the same-time(-16,+2) move and14,112-cell overlap, but does not override
the evolved-state failure. Maximum per-slot window-inventory difference is
2.591143e-5; total GPU water balance residual3.746917e-4m3 is recorded, not repaired.
GPU water change-217.142122373m3 = physical outward47.350535234m3 subtracted plus
moving-window exchange-169.791961830m3, within that recorded float residual.
All GPU state is finite, maximum depth3.357236147m, speed7.910498744m/s.
Next numerical work must isolate the longer shoreline divergence on identical
recorded inputs. A passed remap is not permission to promote the failing PDE.
No ordinary FPS measurement was taken with this extra diagnostic work.

Final test-split Raft DLL SHA256
`eace3f6d673f5b9451261213aa4c1c7b736050b05869b394c21528b68def80bd`;
WaterDetail DLL SHA256
`5675d303906d4f7994eece8f091d886188fb8067a860643b0d7285957620850c`.
The saved normal material remains unchanged at
`e0c9613bc16125c0f991dc29c6421359cd0fbd6903ab0481657ed544bca55f2c`.

At the final checkpoint, BOTH5400s/local28000 full-river audits pass. Depth
3.699729907m, speed6.309647578m/s, volume2,806,620.921452779m3; all5,382,400
cells finite and86,720 artificial-face cells exactly dry. Outlet123.410437732
versus inlet45.306954547m3/s remains unsettled. Runtime600s data unchanged.
Continue the same live cook84534/PID32144; next5500s/local30000 requires BOTH
audits after complete marker. All builds, UE captures, native tests and CPU
comparisons launched in this turn are terminal. No commit or solver promotion.

Computer-use skill and browser-control retries both fail at runtime initialization
with `failed to write kernel assets ... path specified (os error 3)`. Neither
reference video was opened or viewed. No reference match is inferred.
