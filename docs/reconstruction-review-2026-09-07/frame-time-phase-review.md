# Frame-time phase and longer playable performance checks

2026-09-18 UTC. The previous goal turn made progress by restoring the interrupted
hydraulic cook. This turn improves performance diagnosis and verifies another
complete hydraulic checkpoint. It does not improve the rendered scene or its
speed. All failed timings below are retained.

## Engine timing semantics

The installed UE5.8.1 source establishes an important phase distinction:

- `Engine/Source/Runtime/Core/Private/ProfilingDebugging/CsvProfiler.cpp:150`
  defaults `csv.UseLegacyFrameTime` to false.
- Its `FCsvProfiler::UpdateFrameTime` at line4369 measures elapsed time since
  the previous call, immediately after the frame limiter wait. The source
  explicitly describes this interval as belonging to the prior logical frame.
- `Engine/Source/Runtime/Launch/Private/LaunchEngineLoop.cpp:5704` invokes it
  after `OnBeginFrame` and before the current game work.

Consequently default-mode elapsed time in CSV row i must be associated with
water scopes in row i-1, not row i. Legacy EndFrame timing has a different phase.
The existing CSV metadata does not establish which mode was active. This does
NOT change independent FPS/p95 distributions or invalidate direct same-input
component comparisons. It prevents an incorrect same-row workload attribution.

The profiler now explicitly requests the unchanged default mode and requires
runtime log confirmation before recording offset1, with a hash of that log.
The CSV auditor offers optional `--frame-time-scope-offset`; no phase is inferred
from whichever correlation looks best. The caller must establish the mode
outside the CSV. It groups elapsed samples by positive Refresh/Selection timings
and records the exact paired row indices. Missing predecessor rows or required
scopes reject, rather than shrinking the requested interval. Empty groups remain
empty; absent scopes are not filled with zeroes. Positive timing is not the same
as call-count evidence. Nested scopes are never added to manufacture frame cost.
The unchanged overall p95 gate includes every requested elapsed sample once.

50 focused Python checks pass, including synthetic anti-correlated frame rows,
both explicit phases, missing predecessor/scopes, invalid values, empty groups,
and the unchanged exact budget boundary. Final XML:
`tmp/frame-phase-focused-v2-20260918.xml`, SHA256
`044c1cc69a2da1ee16d146670c62219d442227b4290a428b52432c4b47d5cb59`.
PowerShell identity/mode/replay/command-builder checks pass. The initial validator
rejected Unreal's Boolean `false` and CRLF output; the corrected tests cover both.
No native code, gameplay asset, resolution, quality, mesh, physics cadence,
contact tolerance or acceptance threshold changes. No native rebuild is needed.

## Actual captures, including slower results

All runs use the ordinary South Fork scenario,1280x720,D3D12,RT0. No component
audit or stage-timing flag is enabled. The900-row runs use the fixed inclusive
interval60..840; the default300-row run uses60..240. These are development
captures, not packaged/sustained/full-route/visual acceptance or a causal A/B.

| Capture suffix | Rows | Average FPS | p95 ms |30FPS gate |
|---|---:|---:|---:|---|
| recovered-normal-900-v1-20260918 |900|21.960643|61.1927|FAIL|
| phase-confirmed-900-v1-20260918 |900|23.672683|52.5633|FAIL|
| phase-final-300-v1-20260918 |300|24.116386|49.8761|FAIL|

Every label starts `south-fork-`. CSVs are under `unreal/Saved/Profiling/CSV`.
All game processes exit0 without timeout. Identity-checked suspension/resume of
cook8900 succeeds for all three; CPU observations differ by0.125s,0s,0.125s,
respectively. The middle wrapper exits1 because of the initial log-parser bug,
NOT a game failure. Its original process report remains unchanged, including
`csv_frame_time_mode_confirmed=false`; corrected read-only validation of its
original log confirms the explicit false setting. The final300-frame run
verifies the corrected wrapper end-to-end, exit0, mode confirmed and log hashed.

The phase-confirmed900-row workload groups contain:

| Positive refresh timing | Positive selection timing | Count | Mean elapsed ms | p95 ms | Over33.333333ms |
|---|---|---:|---:|---:|---:|
|No|Yes|389|37.38|46.85|337|
|Yes|No|388|46.82|54.59|388|
|Yes|Yes|4|70.92|85.51|4|
|No|No|0|unavailable|unavailable|0|

Thus simply scheduling refresh and selection on different frames is NOT enough
in this capture: both large separate groups already exceed the budget. The
selection-only group averages15.45ms Cartesian publication and9.49ms water
stepping; the refresh-only group averages21.81ms refresh. These are workload
associations, not marginal causal costs. A per-station coverage cache was
considered but not implemented: its Cartesian range query is a cheap guard,
and no measurement justified another tiny lookup optimization. Further work
must reduce actual refresh/publication/solver work while retaining the same
quality, geometry and cadence, alongside the unfinished physical water model.

Final reports and SHA256:

- `tmp/recovered-normal-900-profile-v1-20260918.json`:
  `d4f13b6d82548250054fab70413497e9398bebd896f1a7d7d23cc7d4a39c27dd`.
- `tmp/phase-confirmed-900-profile-v2-20260918.json`:
  `d9c12da4edb0ec11139930e8a273c45d49feb8b9eef234459d971dc4932df581`.
- `tmp/phase-final-300-profile-v1-20260918.json`:
  `b1b6a26b91443d99c3b7bd5872a4a413b023982330658534704359429d077bd7`.

The final CSV SHA256 is
`956e10a30c555f6dc812256d31403dbaee523d0c4003223bed26d7e27bcec478`;
its confirmed-mode log SHA256 is
`73e7edc9e721fea4288218ae599a2468fc8ec0aa16b2301783a206282291481b`.

## Hydraulic continuation and remaining delivery

7750/new local1000 passes BOTH full-state and artificial-bank audits. All
5,382,400 cells are finite/in bounds, and all86,720 artificial-bank face cells
are exactly dry. Maximum depth3.8129814083407667m, speed5.349398990907991m/s,
maximum step residual1.3192849923626682e-8m3. Outflow106.80461017775323m3/s
still exceeds inflow45.30695454719997m3/s: NOT settled; installed4950 stays.
Reports: `tmp/control-ablation-7750s-{state,banks}-v1-20260918.json`.
Depth SHA256 `3cd58d76e90da48960a794f5b085e1348afdb5f04dc8bcd25ea380fb8e4f6c8a`.
Cook8900/startUTC2026-09-18T06:34:59.2598919Z/session68256 is confirmed live,
advancing beyond7767 seconds. Next7800/local2000 needs its completed snapshot
and BOTH audits. Revalidate the process identity before control.

Nonlinear runtime stays OFF. No new reference or visual-motion acceptance.
South Fork terrain/crest/froth/contact, conservative coupled mass/momentum and
joint-interface/wetting evolution,30FPS, then Colorado/Pacuare/Futaleufu,
Chilko/Zambezi, crew, normalization,13 physical regressions and release remain
OPEN. Troublemaker stays a rapid inside South Fork, not a menu scenario.
