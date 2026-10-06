# Editor Python ownership during normal gameplay

September 23, 2026. A normal-launch/release-log correction, not a water,
geometry, geographic, crew, FPS or full release acceptance claim.

## Observed cause and scoped correction

The preceding unmodified normal South Fork launch logged two Python tracebacks:
`EditorToolset/Content/Python/init_unreal.py` imports an `unreal.AgentSkill`
subclass, and `ToolsetRegistry/Content/Python/init_unreal.py` creates an
`unreal.PythonTestRunner`. Both classes are supplied by Editor modules, which
are not loaded for editor-hosted `-game`. Their content directories are still
mounted and the Python plugin runs their startup scripts. These are actual
startup errors, not evidence of a failed water solver or corrupted map.

Inspection of the installed UE5.8 source establishes the appropriate lifecycle
hook: PythonScriptPlugin loads in PreDefault, registers
`Engine.Python.IsEnabledByDefault`, and reads it at OnPostEngineInit. The
Default-phase game module now sets that default to zero only in an editor build
running a game and not a commandlet. Ordinary gameplay has no Python simulation
dependency. Packaged builds compile out the policy and gain no Python dependency.

Editor/PIE and commandlet defaults are untouched. The engine still applies its
own explicit `EnablePython`/`ForceEnablePython`, `DisablePython` and per-user
override precedence; this policy does not mutate those settings or force them
off. An explicit opt-in can still run incompatible editor startup scripts in
game mode. No engine files, plugins, user preferences, Python startup scripts,
log verbosity or exception handling were edited. A missing lifecycle CVar emits
a warning rather than falsely reporting success.

## Qualification

The first editor build failed because the new test included its sibling header
without the parent-relative path. The v1 log is retained. Corrected editor and
standalone Development builds pass in9.57/62.31s. Existing engine/project warnings
are not reclassified as a clean release build.

Two actual D3D12 editor tests pass: the eight-combination startup policy test
and the existing career catalog regression. The editor log independently shows
Python enabled and both toolset startup scripts executing without Python errors.
A separate actual Python commandlet successfully accesses `AgentSkill`,
`PythonTestRunner`, the editor asset subsystem, and the test runner installed by
the toolset startup script. It writes a read-only success report and exits0.
Its four existing warnings remain. This proves the commandlet/editor startup
paths, not an exhaustive interactive PIE/authoring workflow review.

Normal South Fork startup without a Python command-line override now logs the
policy followed by the engine's independent confirmation that Python is disabled.
It exits0, saves24 images and a15.611-second native recording. All468 encoded
frames decode, with40 exact adjacent repeats. The inspected1/11s views show the
briefing fitting then fading and the raft advancing; smooth whitewater, coarse
canopy and early crew shading remain. No new appearance improvement is claimed.
Both this normal launch and the separate900-frame ordinary run have zero
`LogPython: Error` lines. This fixes the identified startup errors, not all
historical warnings or release issues. Editor-hosted `-game` is not a packaged
executable traversal; the standalone target is rebuilt, not packaged/accepted.

Ordinary rows60..840 measure26.484402FPS, mean37.758073ms, p9547.2133ms:
still FAIL30FPS/33.333333ms. Native nonlegacy timing is confirmed with scope
offset1. This single fresh run does not attribute a performance change to Python
startup. The24 existing project-layout/release-report tests pass; their gates
and historical evidence are unchanged. [Retained receipts](editor-python-game-startup/validation.json)
bind the failed/successful builds, commandlet/editor checks, before/after logs,
binaries, complete motion decode and CSV/full-report hashes.

The separate source qualification process6480 remains the only
scientific job; its protected imports are unchanged. No cook or replacement
source solve is launched. All river realism/reconstruction gates remain open.
