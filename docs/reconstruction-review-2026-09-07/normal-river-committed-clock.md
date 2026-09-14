# Normal river committed clock — September 13, 2026

The desktop target remains **30 FPS**, p95 <=33.333 ms and the two-frame hitch
threshold 66.667 ms. This is a correctness change, **not a performance pass**.
The fresh ordinary FullReach capture is **12.496034 FPS / p95 90.7015 ms**.
The earlier 20.877573 FPS capture discarded water time and is preserved as history,
not a same-work performance baseline. Simulation backlog now remains visible.

## Runtime change

The raft caller no longer clips its frame delta to 0.25 s. The bridge's fixed-step
queue retains requested duration in double precision rather than discarding
catch-up debt with `fmod`. The existing four-tick-per-render-frame work limit is
unchanged. Every accepted fixed tick advances water and the raft's existing
substeps; water is no longer advanced only once per rendered frame. The default
water step remains 1/60 s and raft substep 1/120 s. There is no larger timestep,
CFL relaxation, increased solver budget, quality cut, FPS cap or state clipping.

The native adapter checks actual field-clock advancement before publishing its
committed duration/frame. Invalid or mismatched advances latch a fault. In the
explicit oversized-request test, native code advances its legacy-clamped 0.1 s
of a requested 0.2 s before this guard refuses publication: this is **not** a
native-state rollback or successful 0.2 s integration. Normal fixed steps pass.

The moving Cartesian detail component now accumulates the adapter's successfully
committed duration, not independent render-frame elapsed time. Equal observations
hold detail; regression, nonfinite time or a fault disables this component rather
than inventing elapsed time. Refresh-age and presentation telemetry still use
frame time. Explicit standalone review tanks retain their separate review clock.
The adapter's committed timeline survives a cold spatial boot; the actual native
field clock starts a new local epoch. Source packets still record that actual
native clock. Existing remap/teleport behavior is unchanged.

This does not promote the experimental total-depth PDE into normal play, establish
full source-epoch/frame ownership, or remove asynchronous presentation latency.
Ordinary gameplay still uses the existing qualified legacy detail path. Continued
temporal-boundary evolution, nonlinear stability, outgoing-wave behavior and
breaking/froth acceptance remain open.

## Verification

Build21090 CLOSED0, 157.36 s. It includes two existing double-to-float compiler
warnings in `RaftSimD6ChaosMeasuredRunner.cpp` at the unchanged damping calls.
Native24013 CLOSED0: **83 clean passes**, zero warning/failure/unrun tests,
21.109785 s, report `tmp/south-fork-clock-native-v1-20260913/index.json`.
The previous six actual CPU/GPU fixtures remain unchanged and were all supplied.
The three new tests are:

- `RaftSim.Clock.FixedQueue`: 300 frames each at 60/30 FPS, bounded hitch catch-up
  with no lost ticks, failure retaining uncommitted debt, invalid inputs and
  unrepresentable duration refusing work.
- `RaftSim.Clock.CommittedDetail`: nonzero origin, held/advanced observations,
  invalid/regressed time preserving the previous observation.
- `RaftSim.Clock.NativeBridge`: real native 8x8 FV tank, 30 rendered frames
  executing 60 water/raft ticks, exact adapter/native time agreement, cold spatial
  boot preserving committed duration, and the explicit mismatched-step fault.

Eight frame-CSV parser/budget tests also pass (0.004 s). The preceding 261 CPU
solver tests are historical, not rerun here; no CPU solver equations changed.

Built DLL SHA256:

- Physics: `0a831a6a8e0e9028a13aad72c355c1c7b37bafeced2db98887c5e4d937908d39`
- Raft: `d78cc54a3af8696679f7e01defb91b28348893eea20e229d1c25e2d611908313`
- Water: `7f7fd7df4609e98542e2a644590f7f38119fb7584b719744d9ce4520d9aff919`

## Actual playable captures

Both run the existing South Fork FullReach map/scenario at 1280x720, target metadata
30, unchanged quality. The wrapper pauses only the identity-verified owned cook
PID32144/start `2026-09-13T10:55:07.5804942Z`. Audit13236 and default46208 both
CLOSED0, suspend/resume status0, no timeout. Process reports are under
`unreal/Saved/RaftSimValidation/south-fork-clock-{audit,default}-v1-20260913-process.json`.
No heavy build/test/replay overlapped these captures. Known editor Python startup
errors for unavailable `unreal.AgentSkill`/`PythonTestRunner` remain in the logs;
they were not suppressed or counted as successful engine-plugin initialization.

Audit capture reports:

- `tmp/south-fork-clock-temporal-audit-v1-20260913.json`: 512 actual GPU boundary
  faces pass, native endpoint times0.0666666701/0.1333333403 s, exact bed,
  maximum normalized error5.957916e-8, all error counters zero. This is boundary
  interpolation, not complete PDE evolution of this new longer bracket.
- Carrier/detail reports with the same prefix: same frame110, 2020 wet contact
  points, 944 detail-affected, zero unavailable, maximum carrier error4.768249e-5
  cm; 4226 independent GPU queries, maximum RGBA error5.960464e-8, pass.
- End of audit run: water/detail target27.200001419 s, detail backlog0, frame
  elapsed34.066557348 s. Native/raft backlog is not confused with detail backlog.

Fresh ordinary CSV:
`unreal/Saved/Profiling/CSV/south-fork-clock-default-v1-20260913.csv`, SHA256
`54e0baec721267cc6a2ce0ce4702d091a192203a050c6507e3ce29969cb4016a`.
Frame report `tmp/south-fork-clock-default-frame-v1-20260913.json`, rows60–240
inclusive,181 samples. Diagnostic capture separately measures12.554735 FPS /
p9587.8286 ms; its report is `tmp/south-fork-clock-audit-frame-v1-20260913.json`.

| Ordinary capture metric | Mean ms |
| --- | ---: |
| Frame | 80.025388 |
| Game thread | 79.478489 |
| GPU | 21.783225 |
| Render thread | 17.597994 |
| Surface tick | 53.513756 |
| Cartesian publish | 30.563280 |
| Shoreline SetMesh | 27.727005 |
| Crest update | 23.345163 |
| Surface refresh | 21.683081 |
| Four native water calls per frame, combined scope | 16.837475 |
| Crest selection | 14.139594 |

Scopes are nested/inclusive and threads overlap: **do not sum this table**.
Different physical trajectories and refresh work also prevent attributing the
whole frame difference to the extra native calls. Both the 30 FPS and 1.6 ms FV
budgets remain unqualified. The CPU surface/crest path is still the largest
measured cost and needs optimization without dropping physical time or geometry.

Every selected ordinary frame runs four fixed ticks (724 total) with zero failed
ticks. The CSV bridge, adapter and native clocks agree exactly at its printed
precision. First/last requested times5.5789/19.9787 s, committed4.0667/16.0667 s,
backlog1.5122/3.9120 s. Queue identity differs by at most0.0001 s from independently
rounded CSV columns; the native tests above use unrounded doubles. Backlog grows:
**this is a failed capacity result**, not real-time operation. At shutdown the
water/detail target and actual detail simulation are29.000001512 s versus
34.094403613 s frame elapsed. Detail backlog is0; the bridge owes the remaining
time. Five exact detail remaps, zero detail teleports,435 completed-frame copies,
zero skipped-busy-ring copies. Observed source/exterior bed-overlap checks stay
exact across the moving window.

The actual ordinary screenshot was viewed:
`unreal/Saved/Screenshots/south-fork-clock-default-v1-20260913.png`, SHA256
`8b55e30f5c7bd65b32537dfd3ee98ea6449073a364bdf8b87c1575d082dd987b`.
Broad glossy folds and blanket-like foam remain; terrain/vegetation/crew are not
accepted. No convincing-froth or motion/reference comparison is claimed.
Protected map, transmission material and save hashes are unchanged from the
previous record. South Fork remains the scenario; no Troublemaker menu entry was
added. Reference clips remain requested; no footage was viewed this turn.

The same background cook84534 remains live, last observed4356.5 s/local7130 after
both successful resumes. Prior4300/local6000 BOTH audits remain latest; perform
both4400/local8000 audits only after its complete marker. No cook output promoted.
The remaining scene sequence, release checks and final commit stay active.
