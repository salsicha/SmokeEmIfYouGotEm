# Current-profile crest selection — September 12

Subsequent user revision: desktop target is now30FPS, not60FPS. Historical
comparisons below retain their original criteria. The latest20.569411FPS /
55.4904ms p95 also fails the new33.333ms frame budget; no scene acceptance.

Reference-video retry remains unavailable: computer-use/browser kernels fail
initialization with missing kernel assets (OS error3), even after reset;
both YouTube web fetches are throttled. No new reference playback occurred.
That is not a blocker for all local implementation work.

## Measured baseline

Owned isolated process88780 exits0; cook29104 identity-checked suspension and
resume both return0. `south-fork-crest-stages-baseline-v1-20260912.log` records
individual crest update stages. Selection dominates rebuilds (for example
frame260:18.1798ms of26.6506ms; vertices4.8911ms, normals1.9474ms).
No mesh density, update cadence or acceptance threshold was changed.

CSV audit `tmp/south-fork-crest-stages-baseline-performance-v1-20260912.json`:
300 rows at1280x720; warmed100..250 mean63.395118ms,15.774085FPS,
p9577.3472ms. CSV SHA256
`cf57f3a53b0fe96836bbe4b5d2b82447a50806ecdb09ce173a97ee478357540a`.
Verbose stage logging is enabled: this run is diagnostic, not an isolated
cause for differences from earlier uninstrumented captures or acceptance.

## Implementation under verification

Parallel refinement previously constructed new coordinate-value hash tables
on each call. Optional retained tables now keep lookup slots. Every call
advances an epoch: even the same coordinate MUST evaluate the current height
function on first use in that epoch. Nothing reuses previous-profile heights.
Each parallel batch has exclusive ownership and levels join before resizing.
Each map has a4096-entry limit; reaching it clears the map and merely repeats
current exact samples. No approximate coordinate welding or lower tolerance.
The normal playable carrier enables retention; `-RaftSimFreshCrestMemos`
retains a fresh-table comparison path in the same binary.

New native fixture compares28 changing profiles, shifted/moving coordinates,
winding changes and disabled/re-enabled retention to independent fresh serial
selection, requiring exact parents, triangle order, ownership and coordinates.
Build25823 succeeds in228.09s (existing D6 damping double-to-float warnings
retained). Native10515 exits0;61 successes, zero warnings/failures/unrun.
Report `unreal/Saved/RaftSimValidation/south-fork-crest-memo-regressions-v1-20260912/index.json`.
The new fixture compares37,187 vertices in28 frames to fresh serial selection.
No speedup or visual acceptance follows from those numerical tests.
Fresh-table same-binary profile48962 and retained-table35669 both exit0,
without timeout; each cook suspension/resume returns0. No heavy parallel
work ran during either profile.

## Actual-game results, still below acceptance

Both runs use1280x720 and300 CSV rows, comparing rows100..250. Fresh tables:
17.732330FPS, p9574.7677ms, crest18.448566ms, selection8.810503ms across all
rows/14.153041ms among active rows, GPU15.708468ms. Retained tables:
20.569411FPS, p9555.4904ms, crest15.775161ms, selection7.075868ms across all
rows/13.698154ms among active rows, GPU13.954097ms. These short trajectories
and refresh counts differ; no sole-cause or sustained speedup is established.
Both FAIL the unchanged60FPS requirement. Report
`tmp/south-fork-crest-memo-performance-v1-20260912.json`.
Fresh CSV SHA a61223ddcf8969c7a0dfc593d5bef739ec376afd26a7dcb59c22b706db8f3eea;
retained SHA30095f8706b31ae49565c02e235a0ec6f7ec2f523f54155ec8aaacefd786cabb.

Build binary hashes: Raft042a5dcd97d4aa6a6152a94490be4ed6b2adef925ae7e1c5a8747f46e4ce26f3,
Waterf992dec3171ee453c529564c763227a81097cf8f3740388efaf1b1cf7a23f0f5,
WaterDetailbf51784a1d502c0ce4451c45b75a72fb5b0e67b201b8774911f8269a7f116f11,
main37fc63e3188eae0fe39f8f5bfff69a632bcf9f0a42db49edcee43db2592a4e71.
After the build, two comment-only clarifications were applied by moving the
header out and back with apply_patch because in-place truncation failed.
No functional source changed after the tested build; no temporary header remains.

Actual-game38330 exits0. Eight unique PNG captures; frames000/007 inspected.
The broad smooth wave/soft froth remains unaccepted, without a claimed visual
improvement from this allocation optimization. No new continuous recording.
Same paired detail sequence104 in BOTH current contact/GPU audits:
2,021 wet points,956 with nonzero detail, max4.071802cm;
support error maximum.000047675115cm/RMS.000023017864cm, no dry/unavailable
queries. GPU4226queries, RGBAerror5.960464478e-8, passed.
Shared crest1,550,016samples, max.600654193cm below unchanged2cm gate;
fine correction tracking.000484325cm, source vertex change0. UV3 transport
and UV1 bulk-channel errors0. Reports `tmp/south-fork-crest-memo-{contact,gpu,
crest,transport}-v1-20260912.json` (crest additionally `.cartesian-mesh.json`).
Ordinary retained profile:657 commits/1hold, maximum queue age.4s including
startup/capture, PDEbacklog.001336s. These are not warmed render-latency gates.

Mapdb3080cc…, material26aa5029…, save181d1e57… rehashed unchanged after play.
Scoped whitespace checks pass. Cook96057/PID29104 remains live at2421/local8420;
2400 independently passed BOTH state/bank audits. Next2500/local10000 needs
both audits after completion; runtime600s unchanged and settling unaccepted.

The actual smooth crest and soft froth remain visually unaccepted. This is
performance work toward the full scene, not evidence that breaking waves are
convincing. South Fork remains the scenario; Troublemaker is only a rapid.
