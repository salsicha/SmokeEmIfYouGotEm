# Continuous shoreline: persistent ownership — September14 UTC

Current result: the complete independent comparison FAILED. See
[history failure and startup correction](normal-river-continuous-history-failure.md).
The launch/status notes below preserve the preceding work sequence.

Desktop remains30FPS / p9533.333ms, physics120Hz. No geometry, source,
accuracy, CFL, pressure, memory or visual-quality gate changes. The candidate
is still opt-in; normal playable water and project completion are not accepted.

## Persistent model identity

`RaftSimAdvanceTotalDepthGPU` now forwards the selected reconstruction through
every trial and both RK2 stages. Summary word3 records bit0=open boundary and
bit1=continuous shoreline. A different requested mode is rejected before an
effective trial; existing state, compensated time, counters and model identity
are retained, proposed dt becomes zero, and fatal status remains latched.
`RaftSimBeginNextTotalDepthIntervalGPU` also checks the same model before
admitting another interval. Defaults remain binary, preserving mode words0/1.

`FRaftSimNonlinearEvolutionGPU` owns a construction-time const model choice,
retained across source observations, consecutive intervals and window moves.
There is no mid-history setter or command-line gameplay promotion.

Build33479 succeeds in87.58s. Native67298 exits0:
`tmp/south-fork-continuous-owner-native-v1-20260914/index.json`,36 clean tests,
zero warnings/failures,70.49s. Existing bounded partition/direct-indirect and
owner source/move/queue tests run with the continuous model. Interval admission
checks both models, including a refused model change; new GPU tests cover both
switch directions in pending and completed intervals and verify failure latching.
These are ownership checks, not full physical-history or sustained-cost evidence.

## Original source-history replay and independent reference

New `RaftSim.Diagnostics.ReplayedNonlinearOwner` reads the original captured
FP32 packets without requantization, evolves through the real persistent owner,
and saves the final state, clock, accepted face inventory and window exchange.
Input remains `tmp/south-fork-qualified-range-owner-v1-20260914.json`, SHA256
`bf20b0b6c467b78d5d1b02a7174f502e1de3cba89996ee7f3b32cf0dfe5736ec`.
The original observations remain in output for exact independent provenance
comparison. Draining between observations is explicitly a replay diagnostic,
not live queue throughput. Binary replay must be byte-exact to its original
final state; continuous replay must instead pass a separate same-model CPU
history from the original initial state, never GPU interior checkpoints.

First native60395 FAILS after29 intervals at the first move. Artifacts
`tmp/south-fork-continuous-owner-history-v1-20260914.json` and
`tmp/south-fork-continuous-owner-history-native-v1-20260914/index.json` are
preserved. The replay harness had submitted the expanded closing capture row
separately, then submitted the opening packet owning that same closing revision.
The existing strict owner correctly refused the duplicate revision. The harness
now submits the ORIGINAL atomic closing/entering bundle, letting the owner queue
both original rows once. No row, state, revision, boundary or validation gate is
changed. This is a harness fix, not a solver accuracy pass. One descriptor-cache
warning was also reported. Corrected build25615 succeeds in14.73s.

`audit_live_moving_owner.py` obtains the immutable model from captured metadata,
requires matching persisted mode bits, and uses that model at every independent
CPU interval. For replay outputs it first verifies every observation and the
endpoint/move/origin against the original captured history and records its hash.
Unknown/mismatched model identity is refused.40 focused Python checks pass
in26.62s, including no-mutation and model-mismatch tests.

Corrected native replay71187 exits0, one pass WITH descriptor-cache warning,
36.73s: `tmp/south-fork-continuous-owner-history-native-v2-20260914/index.json`.
Output `tmp/south-fork-continuous-owner-history-v2-20260914.json` SHA256
`03978a0630ec7db6f29f966303bb586203ce8752468cedfef0ad67dd2096ae5e`.
Completes72 intervals, two moves,1080 accepted trials,74 graphs at the exact
original9.066667139530182s endpoint. Summary[16,16,1,3], diagnostics[0,0,0,1],
remaining0. All80 output observations compare exactly to the original capture.
The changed-model final state is correctly NOT byte-identical to the binary
control. This is completed native ownership, not independent accuracy.

Independent CPU25447 is running from the original initial state with the
continuous model, output target
`tmp/south-fork-continuous-owner-independent-history-v1-20260914.json`.
Binary-default full native suite/control26684 exits0:125 clean and one passing
WITH descriptor-cache warning, zero failures,71.75s. Report
`tmp/south-fork-continuous-owner-default-native-v1-20260914/index.json`.
`tmp/south-fork-binary-owner-history-v1-20260914.json`, SHA256
`5bd60fe23efb9e2f00fa832b71a586780649adebc461f0dd14f3f35fd7f39112`,
completes the same72 intervals/two moves/1080 accepted trials and is
FINAL-STATE-BYTE-EXACT to the original live capture. Mode stays1; all diagnostics
remain valid. The retained isolated capture is also unchanged. The warning is
in the full-history replay test, not the125 clean regressions.
Broader Python regressions64597 pass89 tests in33.20s (overlap with the40-test
suite above). Independent continuous full-history accuracy remains pending.
Then qualify
broader physical/stability behavior and warmed cost before normal surface/contact
integration and real-motion captures. Last valid gameplay18.899245FPS/p9570.33ms
still fails the30FPS target. All later rivers, crew, platform, release and final
commit work remain open.

Both6600s/local12000 expanded-cook audits pass (see the full-river checkpoint
record), but outlet115.2529 versus inlet45.3070m3/s is still unsettled. Same live
cook74818/PID41820 continues without restart; next COMPLETE6700s/local14000
requires both audits. No runtime source promotion.

Reference-video retry in this work: web requests for YouTube `ZEG1kvjNI30` and
`2XTbOCNDcZQ` again return cache misses. After reading the computer-use skill and
its required guidance/confirmations, supported `@oai/sky` initialization fails
before any page access: `failed to write kernel assets: The system cannot find
the path specified. (os error 3)`. The supported browser surface also fails with
the identical initialization error. No video was viewed, downloaded or used as
new visual evidence; no bypass attempted. Solver/reference work continues.
