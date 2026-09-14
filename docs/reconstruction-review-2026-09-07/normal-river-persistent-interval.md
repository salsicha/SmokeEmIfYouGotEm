# Retained consecutive GPU intervals — September 13, 2026

The GPU breaking-front work passed88 native tests on the observed interval;
normal gameplay remains the legacy solver. This change adds the next fixed-grid
ownership primitive, not a playable solver switch or moving-window owner.

`RaftSimBeginNextTotalDepthIntervalGPU` admits a consecutive interval only when
the previous GPU transaction completed successfully at the exact requested
start. It aliases the evolved state and cumulative accepted boundary ledger.
There is no fresh-source overwrite, time snap, extrapolation, ledger reset or
CPU completion readback. State, compensated progress, interval summary,
diagnostics and accepted ledger remain one retained transaction.

Successful admission resets only the interval counters, diagnostic flags and
remaining/proposed duration. Clock words stay bit-exact. Error-free normalization
accepts equivalent high/low encodings, while even a one-ULP low-word time mismatch
is rejected. Host timestamps and interval duration must be exactly representable
in the existing clock/float-duration format; unsupported precision is rejected,
not silently discarded. No new tolerance or timestep relaxation.

Pending, failed, exhausted, inconsistent or mismatched GPU records return fatal
status2/diagnostic bit64 with unchanged input clock, state, inventory and counts.
Input buffers are immutable, so a refused request does not mutate the previous
transaction. Existing transport/frame checks still validate actual state and
inventory contents. The caller must preserve grid/bed/world-face identity and
boundary mode; this primitive does not establish those from observation IDs.

## Verification

Build85834 succeeds16.04s. Native45718 exits0:89 clean passes in20.162893s.
Fourteen initial admission cases cover open/closed transactions, equivalent and
100-million-second clocks, incomplete/failed/exhausted records, mismatch,
nonfinite clock, invalid mode/counters/flags and a one-ULP time difference.
Additional corrupt proposed-dt/counter/accepted-flag and empty-completion cases
bring the final set to20. Build63016 succeeds13.54s. Final native74276 exits0:
89 clean passes in22.069469s, including all20 admission cases and retained
two-interval hybrid evolution. Report
`tmp/south-fork-persistent-interval-native-v2-20260913/index.json`.
Eight desktop frame-budget tests also pass in0.19s; the target remains30FPS.
Final-harness version1 nonbreaking compatibility93576 exits0 with one clean
temporal test in0.438915s, including consecutive-interval retention. Report
`tmp/south-fork-interval-nonbreaking-compat-v1-20260913/index.json`.

The actual observed hybrid interval is divided at its midpoint. Both halves
sample the original declared linear boundary bracket; the midpoint is not
misrepresented as an independently recorded third observation. Across graph
lifetimes, the second half starts from the first half's evolved state and
accepted boundary ledger, never a refreshed mean field. One-slot versus
four-slot graphs produce all five final records bit-exactly.

Both intervals finish at.033333335071802139s with remaining0/status1.
Against the independent full-interval CPU control, h/hu/hv relative errors are
5.529277e-8/5.193387e-8/5.497928e-8; maximum absolute error9.536743164e-7,
within unchanged2e-5 relative/1e-4 absolute gates. Water change
-.0678304189976m3 plus cumulative outward flux.0678290765584m3 leaves
-1.34243922555e-6m3 float-storage balance error. No repair or double-precision
conservation claim. Source foam is0, so this is not foam-production evidence.

Final interval shader SHA256
`ae38d6312ce9e824e035fad17f1377dcb8b8f8da528a660995666701e0e22817`.
WaterDetail DLL SHA256
`d7e5cedef814065405529f6221c7e0645581217bb77e43b3d6dd672923fe70c9`.

## Remaining integration

A bounded owner still needs to queue immutable actual observations, keep each
boundary bracket until fully consumed, and carry state/time/inventory through
the actual moving-window exchange. It must reject incompatible world/bed/face
identity and retain unfinished physical time under load. This fixed-grid handoff
is only one part of that owner. Long-time boundary/model qualification,
foam entrainment and shared normal render/contact publication remain open.

Normal mapDB3080..., materialE0C961... and save181D1E... hashes are unchanged.
Latest ordinary gameplay remains18.899245FPS/p9570.33ms, FAIL30; no new scene
capture or performance claim follows from these concurrent regression tests.
Terrain, rapid shape, convincing froth and crew are not accepted. Troublemaker
remains a rapid inside South Fork, not a menu scenario. Remaining rivers,
normalization, release checks and final commit remain in scope.

Same expanded-domain continuation84534/PID32144 passes BOTH5100s/local22000
state and bank audits; still settling, no runtime600s replacement. Next
5200s/local24000 requires both audits after its complete marker. No restart.
