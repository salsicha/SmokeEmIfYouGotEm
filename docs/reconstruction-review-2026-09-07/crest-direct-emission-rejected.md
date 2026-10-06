# Direct serial crest emission: not qualified

September 27, 2026. Supporting performance experiment, **no playable delivery**.
The current packaged South Fork failure remains authoritative. This trial has
been removed from source, not promoted or installed in the packaged game.

## Distinct candidate

The trial allocated the same maximum four-child output capacity as the
existing emitter, wrote indices and owners directly into that bounded storage
in the original serial order, then exposed only the written prefix. It kept
the original midpoint discovery and edge lookups. Unlike the rejected parallel
emitter, it added no per-triangle staging, prefix construction or worker jobs;
unlike inline edge storage, it retained the installed indexed chains.

Selection, tolerances, sampled heights, topology, physics, presentation cadence
and quality were unchanged. The trial was default-off. No captured data, scene
packages, cooked fields or saves were modified by this experiment.

## Build limitation, not hidden by passing tests

The full Editor Development build **failed**, exit 1 after 438.37 s, in unrelated
shared landscape-editor edits. `RaftSimEditorLandscapeBuild.cpp` has literal
newlines inside three C++ strings (lines 22, 29, 46 at inspection).
`RaftSimEditorLandscapeGeometry.cpp` has unresolved `PACUARE_LAUNCH_STATION`,
`PACUARE_REACH_STATION` and `PACUARE_CAMERA_A` placeholders. These edits were
preserved, not reverted, assigned guessed values or reported as fixed.
Log: `tmp/direct-emission-build-20260927.log`.

The runtime, game and automation DLLs had successfully compiled and linked
before that failure. Bounded tests and comparisons used those modules with the
existing editor module. They are **partial-build diagnostics**, not a successful
full editor build or release validation. No unchanged full-build retry was run.

Three native tests pass with zero failures/warnings/not-run results:
`RaftSim.M4.CrestEdgeHashSelection`, `RaftSim.M4.CrestTopologyStorage`, and
`RaftSim.WaterDetail.RefinementTopologyCache`. Extended comparisons cover exact
ordered parents/triangles/owners/current coordinates and cache decisions across
moving profiles, cropped/reversed roots, empty/nonempty selections, 0/1/3 levels
and invalidation. Those temporary extensions were removed with the candidate.

## Actual-input component comparison

64 alternating-order pairs after two warm builds; frames 122-185; 1,948,038
expanded vertices compared. Every pair matches the reference and production
topology exactly, including cache decisions. Report mode is explicitly
`add_vs_direct_serial_emission_both_indexed`; its historical `legacy` timing
labels mean original serial Add, and `indexed` means direct serial emission.
Both paths use the installed indexed edge map. Construction is included.

| First path | Pairs | Original build ms | Direct build ms | Original assembly ms | Direct assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 32 | 12.238068 | 11.828472 | 4.413244 | 4.033505 |
| Direct | 32 | 12.038247 | 11.362669 | 4.359025 | 3.665759 |

The component gain justified a whole-frame comparison, not promotion.

## Whole-frame decision

Four audit-free runs, same runtime modules, normal FullReach assets, diagnostic
station 11,520 m, 1280x720 D3D12, ephemeral profile. Each completes 1,200 frames,
exit 0, no runtime Error/Fatal records. The strict existing analyzer uses all
rows 30-1169 (1,140 samples), confirmed nonlegacy timing and offset 1, unchanged
20 FPS / 50 ms p95 gate. No timing rows were excluded for their outcome.

| Order | Mode | Mean frame ms | p95 ms |
| --- | --- | ---: | ---: |
| 1 | Original A | 76.374696 | 85.9580 |
| 2 | Direct A | 71.087870 | 111.8013 |
| 3 | Direct B | 94.969332 | 115.1307 |
| 4 | Original B | 86.078038 | 98.9859 |

The candidate fails repeatable whole-frame improvement: p95 is worse in both
orders, and mean improves in only one. All fail the target. Variable trajectories
and other shared-host work prevent interpreting the difference as a precise
causal regression; the guarded launches found no other engine/build/cook at
entry, but this is not proof of an otherwise idle machine.

Each has 1,199 paired commits and zero internal PDE backlog. That is **not** a
real-time physical acceptance: committed water time is 72.72-80.13 s versus
87.30-115.14 s wall time. No change to time budgeting or solver settings was made.
No new rendered-view, continuous motion, collision or shoreline pass is claimed.
These direct starts are not Boot/menu or rebuilt-packaged verification.

## Removal and preserved evidence

All four candidate-only source diffs were reviewed and mechanically reversed;
they are empty afterward. The patch writer lost workspace write access during
removal, so a scoped approved Git reversal was used, without changing ACLs or
other edits. Its first read-only check rejected PowerShell-converted line
endings; the byte-preserving native pipe succeeded. No source evidence was lost.
Packaged v4 remains SHA-256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.

Raw logs, reports and bounded helpers remain under `tmp/`. Candidate helpers
require the now-removed experiment; they are not production acceptance scripts.

| Evidence | SHA-256 |
| --- | --- |
| direct-emission-pairs-20260927.json | `a06fb877cfff3351e6cbf66c15774e158285c6f652740a62626fb1bec2dd796e` |
| direct-emission-native-20260927/index.json | `b1a94547e6dc180af04d505673a5cb7815d0ea837ec468c777a254221c29b546` |
| direct-emission-control-a-20260927.json | `6a74478bf165541779f954c7562feaf569d3756989e1acc042cdd65fa8ebc94a` |
| direct-emission-candidate-a-20260927.json | `ee6a2ba05fdebbf6212bfee9c8822d93b37821b0cba5183f6fd0c36bfd14a5ea` |
| direct-emission-candidate-b-20260927.json | `d8f1b2f79b849414122b139f7f62cf95df25bc2797ef149c47210bbb2c069732` |
| direct-emission-control-b-20260927.json | `d54faa0db54ec44e675b892b8c7ee84c9c35538d22f40cd5a7cf76e59b30ecb4` |

Do not repeat the unchanged candidate, ABBA or failing full-editor build.
South Fork remains first, with reconstruction/physical fidelity and performance
open. The separate shared landscape edits must be completed before a full
editor build can be claimed.

## Restoration boundary

The scoped restoration build succeeds, exit 0, 266.16 s. It rebuilt only
`RaftSimRaft`, `RaftSimAutomation` and `SmokeEmIfYouGotEm` using UBT's `-Module`
selection; it does not validate the separate landscape-editor changes.
Log: `tmp/direct-emission-restored-modules-20260927.log`.

The post-restoration three-test launch was refused by the shared-process guard
before starting an engine or creating a log. At 12:37 UTC another build was
active (`dotnet` 29168, `cl` 1136). No other process was stopped. Earlier three
native passes remain candidate-era evidence, not post-restoration passes.
Once that build finishes, recheck the three original tests named above against
the completed runtime, not the rejected candidate. No repeated ABBA is needed.

During the shared work, the Pacuare launch/reach placeholders were replaced
with concrete constants; the multiline-string errors were still present at
the final source inspection. Thus the initial full-build failure is historical
evidence, not a claim that every original error is unchanged. A later full
successful build must establish resolution. Packaged game remains untouched.

## Later shared-build verification (September 27 follow-up)

The separate landscape compilation blocker has now been repaired by the shared
work: `tmp/pacuare-editor-build9.log` reports `Result: Succeeded`, 29.19 seconds,
including a rebuilt `UnrealEditor-RaftSimEditor.dll`. The previously malformed
strings in `Landscape/RaftSimEditorLandscapeBuild.cpp` now contain escaped
newlines. This supersedes the unresolved compilation status above; it does not
establish a successful map build, packaged game, or South Fork acceptance.

The next shared build (`pacuare-editor-build10.log`, observed dotnet 38228 /
cl 9500) subsequently succeeds in 30.80 seconds. A shared engine run then
starts (PID18480), so no competing engine or cook was launched. Neither shared
build was started by this follow-up, and no shared source file was edited.
The post-restoration three-test recheck still needs its own completed report;
do not infer a native regression pass from compilation. The unresolved work
is that test plus the established geometry/physics/performance acceptance
gaps, not the now-repaired landscape compilation failure.

## Deferred-test safety follow-through (September 27, 14:04 heartbeat)

The shared Pacuare map build is still active (PID38404). Its log at14:07:19
reports a3,862MiB mesh-compilation estimate with about2,760MiB available to
the compilation budget. An attempted concurrent NullRHI regression launch was
rejected by auto-review before execution because the engine-overlap guard was
missing. No test ran, no report was created, and no other process was stopped.
Pure-memory test bodies do not justify ignoring shared engine/memory pressure.

Prepared `tmp/check-south-fork-restored-runtime-20260927.ps1` for the next idle
window. It refuses all observed engine/build/cook processes, refuses existing
evidence paths, checks runtime DLL hashes before/after, and requires exactly
the three original tests to succeed without warnings/errors/skips. The helper
has passed a read-only PowerShell syntax check, not an engine regression. The
first sandboxed parser call was disallowed by constrained language mode; its
subsequent printed success string was invalid and is not validation evidence.
The separately approved parser-only check succeeded with stop-on-error enabled.
Do not start this helper until shared engine work has finished. No new source,
scene, cook, packaged game, performance or river acceptance is claimed.

## Completed restored-runtime check (September 27, 15:05 UTC)

The shared engine work had exited. The full process guard passed and the
prepared helper ran once, owned engine PID32140, with Entry/NullRHI. All three
original tests succeeded with zero warnings, failures, skips or tests left in
process: `RaftSim.M4.CrestEdgeHashSelection`, `RaftSim.M4.CrestTopologyStorage`
and `RaftSim.WaterDetail.RefinementTopologyCache`. Engine and helper exit0;
the engine log has no Error/Fatal entries. Report timestamp15:05:36UTC.

The helper verified both runtime DLL hashes unchanged before/after. The four
candidate source paths have no Git content diff, and the direct-emission flags
and member are absent. No rejected candidate was reintroduced. This closes the
post-restoration test deferral above; it is not another candidate experiment.

| Evidence | SHA-256 |
| --- | --- |
| `tmp/direct-emission-restored-native-20260927/index.json` | `c2939e9d70d7c855d8936d9cd73cd7f23af2f36b9fbdef8ada743e728abeef21` |
| `UnrealEditor-RaftSimRaft.dll` | `72c186473fb6e101923ac997d32827f9a833bb26e9c21b08aae37166bd86fbcc` |
| `UnrealEditor-RaftSimAutomation.dll` | `5a0161c45d5b03476dd7ad875a852252ff1bf15399b865e5b2e1f66a4b12ad0e` |

These are supporting regressions, not a new playable delivery. No map, geometry,
cooked field, package, solver or quality setting changed. No new motion,
collision, shoreline, surface-continuity or20FPS acceptance was attempted.
South Fork remains first and unfinished. Do not repeat the unchanged
restoration test or rejected direct-emission experiment on future heartbeats.
