# Parallel breaking-water vertices in normal play — September 13

The previous turn verified total-depth foam transport. This turn inspected live
state ownership, retried the reference videos, and reduced a measured CPU cost
in the existing playable South Fork renderer. The new total-depth solver still
does not own normal evolution; open-boundary/window integration remains open.

## Implementation and same-input evidence

The breaking vertex pass now runs concurrently for Cartesian scenes, with one
writer per vertex and a join before subsequent foam advection or field changes.
Per-site arithmetic and accumulation order within each vertex are unchanged.
Console settings are sampled on the game thread, not queried from workers.
Maximum boil displacement is reduced after the workers finish, without atomics.
Legacy/non-Cartesian scenes retain serial execution.

The coarse crest evaluator can share the fine mesh's immutable exact spatial
index when compatible; spatial-row review and unsupported profiles keep their
existing evaluator. `-RaftSimSerialBreakingVertices` supplies a same-binary
serial/full-scan control. No quality, physics timestep, geometry/contact gate,
foam formula or crest shape is changed.

`-RaftSimBreakingVertexAudit=<fresh path>` clones the current pre-pass input,
then compares the normal output to serial/full-scan evaluation of that same
input. In actual FullReach run26509 at10.068637s, all50,625 vertices with9support
sites match bit-for-bit: positions, source foam, macro crest, tongue suppression,
presentation mask and maximum boil displacement. The audit records parallel=true
and indexed=false; it does not establish that the indexed branch ran, nor the
specific reason it was unavailable in this sample. Existing indexed-profile
regressions cover its supported and fallback cases separately.

Audit: `tmp/south-fork-breaking-vertex-exact-v1-20260913.json`, SHA256
`60398ddcb5430f8b9d97c27a652a26448d050c81a70fa27b90b7a701d3c0c319`.
First build48753 failed on an unbraced UE_LOG conditional in the diagnostic.
Corrected build30263 succeeded43.03s; failure output is retained.
Final actual-D3D12 native66811 closed exit0:74passes, no warnings, failures
or unrun tests,18.327023s. Includes water/shoreline/contact/crest regression
coverage and South Fork/Troublemaker catalog semantics, not full scene acceptance.
Report: `tmp/south-fork-breaking-vertices-native-v1-20260913/index.json`.
Actor SHA256: `5834a99fe898c73c8bfc413d2c20a56d7f95d261b057b6a3ba006f6b4dc0ece6`.
Raft DLL SHA256: `3c131116bf00d5565b351c112dd0942d611e657cbe840ab9bdf9c83d0cbc0987`.

The CSV reporter includes the optional nested BreakingVertices scope and still
treats absent historical columns as unavailable, not zero. All8reporter tests
pass. In-place replacement of these two Python files failed despite writable
attributes; apply_patch's scoped move/edit/move-back succeeded. No temporary
edit files remain. No CPU PDE changes or rerun of its previous148tests is claimed.

## Actual performance, still below 30 FPS

All profile processes closed exit0: pre-change stage baseline84719, same-input
audit26509, serial control93003, normal default98331. Every run verified the
same cook29104 identity and returned suspend/resume status0. No native tests or
build ran concurrently with the isolated profiles. Resolution1280x720 and
quality/physics settings are unchanged.

The same-binary comparison uses CSV rows60–240 inclusive:

| Measured run | FPS | p95 frame ms | Breaking pass, active mean ms |
| --- | ---: | ---: | ---: |
| Serial control | 20.176301 | 56.6490 | 2.852847 |
| Normal parallel | 21.509721 | 53.5233 | 1.852976 |

There are92versus91active refresh rows. Overall breaking-pass means are
1.450066versus0.931607ms per recorded frame. Normal game-thread mean46.226925ms,
GPU15.306082ms: still CPU-bound. Different raft trajectories/refresh timing and
machine variability prevent attributing the entire FPS difference to this pass.
The previous23.365478FPS/p9547.2488ms capture remains history, not overwritten
or presented as this binary's latest measurement. Neither current run meets
30FPS/p9533.333ms; no sustained or packaged acceptance is claimed.

Report: `tmp/south-fork-breaking-vertices-comparison-v1-20260913.json`.
Serial CSV SHA256: `4da294d0619e4f2183af64e4f925df8eb1b736fc28ea3760ebd21f3228217dac`.
Parallel CSV SHA256: `0a5cab03e7dffe3bebcfa759d0f1e009e84c4fb7fac32ebe9b3d80874d380cef`.
Final runtime:691paired commits/1hold,34.041668simulated seconds,
0.006105s backlog,6exact remaps/0teleports. These aggregates are not a warmed
render-latency acceptance gate.

## Visual/reference and remaining work

Both actual audit/default screenshots were inspected. Broad smooth crests and
extensive soft white foam remain unaccepted; the optimization intentionally
preserves them. Latest screenshot:
`unreal/Saved/Screenshots/south-fork-parallel-breaking-default-v1-20260913.png`,
SHA256 `d3f2b8cc636bd851236e80da4edd514aaf2cd068b86c16d0486d84b87aafe004`.
No continuous-motion recording or reference playback is claimed.

The computer-use skill guided a fresh browser retry of YouTube ZEG1kvjNI30.
Browser initialization still fails with missing kernel-assets path, OS error3.
Web fallback returns cache miss for that clip and2XTbOCNDcZQ. Neither was viewed
or downloaded. This access failure does not block the independent code work.

Map, material and user-save hashes remain unchanged. South Fork remains the
scenario; Troublemaker stays off-menu. Cook96057/PID29104 is confirmed live
again at3836.5s/local36730;3800s remains the latest BOTH-audited checkpoint,
with dry artificial banks but unsettled flow. Runtime600s fields are unchanged;
next3900/local38000 requires complete-marker plus both audits.

Next work remains persistent total-state ownership, physical open boundaries,
conservative source/window exchange, evolved wet render/contact eligibility,
and convincing breaking/froth production. Adaptive crest selection remains a
large CPU cost. Terrain/rapid reconstruction, all later rivers/crew,30FPS,
release and final commit requirements stay active.
