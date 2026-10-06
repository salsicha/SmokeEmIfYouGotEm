# Current-profile shared corner samples — September 13, 2026

The previous native combination change is rebuilt into normal South Fork and
passes85 engine tests. Ordinary17.724105FPS/p9573.6027ms and native gate
p9553.357399ms still fail30FPS. Broad foam coverage and unfinished terrain/crew
remain unaccepted. This pass targets measured surface work without changing
the river, geometry tolerance, sampling rule, timestep, quality or source data.

## Current measurement

Existing fine-grained timing flags, no source changes, were enabled through the
normal FullReach profiling wrapper. Capture78478 CLOSED0, game exit0, no timeout,
cook suspend0/resume0. Log:
`unreal/Saved/Logs/south-fork-surface-stages-v1-20260913.log`.
Engine frames100–300 contain201 samples of each stage. Inclusive crest time is
19.801175ms, selection12.611218ms (sampling9.476741ms), vertex assembly/history
3.857872ms, targets1.657309ms, normals1.277151ms and topology0.397624ms.
Refinement assembly1.532957ms is nested within selection. Refresh21.480500ms
includes foam/core publication5.100661ms and source preparation5.041416ms.
Surface tick49.656438ms includes refresh and publishing. Do not sum nested scopes.
This opt-in capture refreshed every selected frame, unlike the preceding normal
capture; timings are diagnostic, not an isolated whole-frame comparison.

## Candidate

Each triangle's three corner heights were looked up in its batch-local map,
repeating the same current height across adjacent workers/levels. The candidate
uses point indices to prepare a shared immutable corner table, with a barrier
before selection. Values live in one `BuildAdaptive` call only. Existing points
are append-only during that call; new points are sampled before first use.
Only corners actually required by the original support-region/detail-window
early exits are prepared. Intermediate quarter-grid samples, early exits,
arithmetic, selected edges, assembly order and all tolerances are unchanged.
There is no cross-frame height reuse, quantization or frozen profile.

`FRaftSimCrestCornerSamples` owns the per-build table. The original path remains
available with `-RaftSimRepeatedCrestCorners`. The new opt-in
`-RaftSimCrestCornerAudit=...` runs two warmups and eight alternating actual-input
pairs, requiring exact parents, triangles, owners and expanded coordinates.
Timing includes the preparation cost. The candidate was temporarily the default
for verification; measured regression below rejected it. Production is restored
to original sampling; `-RaftSimSharedCrestCorners` explicitly opts into the
experimental candidate and `-RaftSimRepeatedCrestCorners` overrides that opt-in.

The existing28-frame `CrestMemoEpoch` test now also compares original batch-local
corner sampling and checks sample sharing. A new12-frame `CrestCornerSamples`
test compares original parallel and serial references while moving compact
support bounds, forced detail regions, coordinates and winding.

Normal patch calls intermittently failed to write the existing refinement and
crest source files. Read-only checks found neither read-only attributes nor a
write-handle failure; no byte was written by the handle probe. The existing
Codex apply-patch executable succeeded with scoped escalation. No ACL, security,
process or editor settings were altered. The partial edit was completed before
starting compilation; no broken intermediate source was built.

Unreal build92790 CLOSED0 (22 actions,164.75s). The native solver archive is
unchanged. Engine suite5857 CLOSED0:86 clean passes,0 warnings/failures/unrun,
21.636267s. Report `tmp/south-fork-shared-corners-native-v1-20260913/index.json`.
The same six D3D12 fixtures ran, including both changing-profile corner tests.
Actual-input audit50468 CLOSED0, game0, no timeout, cook suspend/resume0.
Report `tmp/south-fork-shared-corners-paired-v1-20260913.json` records eight exact
pairs at frame120,52,047 source vertices,18,946 triangles and16,074 midpoints.
Only14,874 distinct corner samples served168,585 reads, but total build averaged
11.968000ms shared versus11.018362ms original (8.62%slower); selection including
preparation11.232127 versus10.269515ms (9.37%slower). Six of eight total pairs
and seven of eight selection pairs were slower. Correctness passes; performance
does not. This is rejected as a normal-play optimization, not an FPS gain.

The screenshot from that playable audit was inspected. Broad glossy folds,
blanket foam, unfinished terrain/trees and crew are still not accepted. It is an
instrumented paired run, not a new ordinary-play FPS measurement. Rebuild72064
CLOSED0 in162.01s restores original sampling as default; the test explicitly opts
into the candidate so regression coverage is retained. Raft DLL SHA256
`55a40e75952474d15e84282295a580dcfc7112959aef167858dc74f70869d9cf`.
Restored-default engine suite43554 CLOSED0:86 clean passes, no warning/failure/
unrun tests,19.630552s. Report
`tmp/south-fork-corner-default-native-v1-20260913/index.json`.
Ordinary restored-default play20633 CLOSED0, game0, no timeout, cook suspend/
resume0. No candidate flag or timing audit. Frame audit
`tmp/south-fork-corner-default-frame-v1-20260913.json` measures12.965487FPS,
p9590.3953ms, mean77.127842ms over CSV rows60–240: FAIL30FPS. CSV SHA256
`2fd78878d2cd65163141bf93b6f0f3444cd7f0a79676fa15576eefc2e1e36bcc`.
Unlike the preceding17.724105FPS capture, this run refreshed/selected every one
of181 selected frames. Actual cadence and trajectory differ; neither the FPS
drop nor prior rise isolates a source-code effect. No quality, resolution,
timestep, refresh interval or tolerance setting changed.

Inclusive means: surface52.407546ms, refresh22.752724ms, publish28.378685ms,
crest20.895641ms, selection11.603599ms; do not sum nested scopes. Water calls
14.833270ms/frame. All724 fixed ticks succeed, zero failures, but backlog grows
1.6068 to3.4789s. Native/bridge/committed clocks agree at CSV precision; foam
shutdown29.466668203s is one observation0.066667s behind detail29.533334874s,
versus world34.051836256s. Six exact detail remaps, zero teleports. This is not
real-time or full clock alignment acceptance.

Screenshot `unreal/Saved/Screenshots/south-fork-corner-default-play-v1-20260913.png`
was inspected: broad foam coverage, glossy rounded folds, unfinished terrain/
trees/crew remain. SHA256
`414e107aea92aeb6a1fc3476d75355393b02b46154dbd213862ba150b1bcd082`.
No new native gate was claimed: production sampling has been restored, so the
previous failed native frame/solver gate remains open, not superseded by tests.

At15:08UTC both supplied YouTube URLs were retried directly (both cache miss).
Browser playback initialization and computer-use fallback both failed before
opening video with `failed to write kernel assets: The system cannot find the
path specified. (os error 3)`. No footage viewed, downloaded or inferred from
metadata; no security/settings changes. The video-comparison requirement stays
open. Existing map, material and save hashes remain unchanged after paired play.
The full goal, all visual work and final release/commit remain open.
