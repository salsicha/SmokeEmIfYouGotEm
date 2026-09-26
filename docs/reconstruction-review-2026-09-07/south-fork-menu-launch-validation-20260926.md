# South Fork Boot/menu profiling validation - September 26, 2026 UTC

The reusable profiler now has an explicit `-NormalMenuLaunch` mode. Previously,
`-NormalScenarioStart` suppressed the review station but still loaded the river
map directly. Earlier separately launched Boot/menu captures remain valid; this
fix does not reinterpret their launch paths.

The new mode starts the project default map, issues the actual main-menu
scenario command, and uses the existing native post-travel CSV hook. It rejects
review stations, experimental arguments, solver overrides and replay/input modes.
The receipt requires Boot, main menu, river travel, river-world timer, requested
capture length and one CSV completion in order. It records the actual CSV path,
hash, timing-mode confirmation and launch mode, rejecting stale CSV timestamps.

`test_profile_menu_launch.ps1` exercises the production functions: project-only
versus direct-map prefixes, valid ordered receipts, missing/duplicate/reordered
events, wrong world/frame count, unsafe filename and ten conflicting options.
It passes, along with all other `test_profile*.ps1` scripts and the joint-preview
and constriction-review identity checks. These tests alone are not engine proof.

## Actual engine run

Executed the existing rebuilt Editor-hosted game with:

```powershell
./unreal/Scripts/profile_south_fork_current_map.ps1 -Label south-fork-menu-launch-20260926 -NoCookWorkload -NormalMenuLaunch -ProfileFrames 1200
```

Exit 0, no timeout, no cook, Boot/menu travel confirmed. D3D12, 1280x720,
WindowsEditor Development, offscreen, ephemeral profile, ordinary scenario start.
No review station, solver override, boarding/leg-fit flag, quality reduction or
geometry/field change. No native code changed or build/package was restaged.

- Log: `unreal/Saved/Logs/south-fork-menu-launch-20260926.log`.
- Process receipt: `unreal/Saved/RaftSimValidation/south-fork-menu-launch-20260926-process.json`.
- CSV: `unreal/Saved/Profiling/CSV/Profile(20260925_185606).csv` (local-time filename).
- CSV SHA256: `b03be789f0f4e9a0592afbae62288cf5b09cb846739512874a87c42b1f30e7a8`.
- Timing audit: `tmp/south-fork-menu-launch-cost-20260926.json`.

All 1200 CSV frames parse with required water scopes and confirmed nonlegacy
timing (scope offset 1). Rows 30-1170 inclusive: 1141 frames, mean 37.237254 ms
(26.854827 elapsed FPS), p95 45.9231 ms, maximum 72.0698 ms. This bounded interval
passes the current 50 ms p95 / 20 FPS target and has no frames over 100 ms.
It is slower than the earlier unpaired capture; no optimization or regression
cause is established by comparing these runs.

Four drift samples show changing raft positions and speeds 1.367, 1.186, 1.124,
1.213 m/s. Each reports wet=1, support delta=0 cm, ground penetration=0 m.
These are sampled motion/contact observations, not continuous collision proof.

This is a delivered validation-workflow repair, **not a visible reconstructed
river improvement**. No images were captured in this timing run. Geometry,
shoreline/surface continuity, full-route collision and animation, long-duration
and packaged performance acceptance remain open. South Fork remains first;
Colorado, Pacuare and Futaleufu are not advanced on this result.
