# Bounded row-parallel live solver — September 12

This pass targets the actual normal-game solver cost, not a replacement water
model or a smaller simulation. The previous goal turn was progress: it changed
the normal Troublemaker terrain/collision/flow and verified an actual traversal,
while leaving the visual and performance failures explicit. The full queue
remains active.

## Implementation and numerical constraints

`solver_row_executor.hpp` provides at most three persistent worker threads plus
the calling thread. For grids of at least16,384 cells, immutable-input MUSCL
slopes and flux-update rows are dispatched in eight-row stripes. Each stripe
owns its rolling north-face cache; at its first row, the south face is computed
again from the same source state. There are no shared output cells or reordered
floating-point reductions. Small grids and boundary/face diagnostic reductions
retain serial execution. Equations, grid, substep/CFL policy, precision, source
bed, wet/dry threshold, positive films, forcing and state publication are unchanged.

The executor waits for all workers before returning or propagating an exception.
Concurrent solver instances serialize dispatch ownership; nested use falls back
to serial execution. Workers receive the calling thread's floating-point
environment, including SSE rounding/denormal control, and restore their previous
environment afterwards. Unreal explicitly joins the workers during module
shutdown, before Windows DLL unloading; repeated shutdown is safe. The module
logs its linked solver archive identity so a cached old binary cannot masquerade
as the new runtime.

## Completed verification before runtime integration

- Initial three alternating300-step replays from the current float32 playable
  flow package: every saved CSV (all primitive/derived fields and wet masks)
  is byte-identical. Median process time including exports6.822→5.262s (22.86%
  lower). These are offline times, not improved game FPS.
- Final implementation with shutdown/FP guards:600-step serial/parallel replay,
  all11 saved frames byte-identical. Process10.018→6.765s in one pair; baseline
  binary lacks internal timing, so no baseline solver-only time is claimed.
- Additional120-step cold-start replay at the original0.1s/CFL.2 also matches
  every saved frame exactly. This ran concurrently with compilation and MUST
  NOT be used as a performance comparison.
- Three native CTest suites pass after adding worker barrier/exception/recovery,
  nested/concurrent dispatch, caller rounding and repeated-shutdown tests.
- Large131×129-grid tests force the actual parallel threshold and compare every
  state field exactly with nested-serial execution over12 changing steps for
  HLL/Roe/Rusanov, with/without bed coupling, wet/dry transitions, positive films
  and explicit state replacement. All pass within each of the three suites.
- A test-only vector accessor typo and an incremental build without the Visual
  Studio environment initially failed; both corrected, no gate changes.

Reports are retained in `tmp/troublemaker-row-solver-comparison-20260912`,
`tmp/troublemaker-row-solver-final-comparison-20260912`, and
`tmp/troublemaker-row-solver-cold-parity-20260912`.
Final candidate executableSHA:
`d4dfd6012c972bb54268ecca933c13dde2e922b2f85039f6282e8f99ba7eb3d5`.
Baseline executableSHA:
`1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50`.

## Runtime integration

The actual UE solver archive is rebuilt:
`385a1622637a573c47f48f38981cb47e33182f0c58cc3ba9e066daf28152b565`.
Previous archiveSHA:
`fd988c73f10f2f1423b421fc3b6e78928d9124acba789e9fae05b75f1a51a35c`,
retained as `tmp/troublemaker-row-solver-v2-20260912/previous-playable-raftsim_water.lib`.
The full179-action Unreal consumer build54787 is now TERMINAL/SUCCEEDED,
exit0,1860.25s. The rebuilt normal-game runtime logs the exact archive SHA above
and explicitly joins its workers before module unload. Scoped diff whitespace
checks pass. Map/new ground asset and real-user-save hashes were freshly
verified unchanged from the preceding sparse-rock integration.
No scene assets, fields, graphics settings or acceptance budgets changed in
this pass. Convincing breaking water and terrain remain unfinished.

First separate normal-game performance run is terminal with clean process exit
and log closure at04:17:44UTC. Report:
`unreal/Saved/RaftSimValidation/troublemaker_row_solver_perf_20260912.json`.
Same normal map/scenario,1280x720,87%screen percentage,10s warmup/12s sample;
all content remains enabled.857 frames, mean14.447ms (prior18.294),
p9527.256ms (prior29.798), mean solver4.943ms (prior8.666),
meanGPU7.422ms (prior7.426), one>33ms hitch (prior7). This is an actual
normal-game diagnostic improvement, not an offline timing or release result.
Frame16.667ms and solver1.6ms gates STILL FAIL; memory3517.88MiB passes.
The existing engine EditorToolset/ToolsetRegistry Python startup errors
(`AgentSkill`, `PythonTestRunner`) also occur in the baseline; not new solver
errors and not silently counted as a globally clean startup.

Native `RaftSim.Survey.SouthForkPlayableGuidedTraversal` is TERMINAL/SUCCESS,
zero errors and the existing `r.MotionVectorSimulation` render-thread warning.
Report: `unreal/Saved/RaftSimValidation/troublemaker-row-solver-traversal-20260912/index.json`.
Samples: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_041845.json`.
It reaches110.088m in62.879s; maximum route error3.109m remains below the
unchanged5m gate.556 wet samples,2,224 fixed water probes, no missing ground
or water queries, no grounded samples, minimum tube clearance30.659cm.
One shared carrier, matched current mesh/flow, fixed bounds and normal-game
progress remain correct throughout.13 station captures were made; crux004
was inspected and still does not demonstrate convincing breaking-water motion.
The earlier timing-sensitive route failure is retained, not erased by this pass.
Separate normal-game motion capture is TERMINAL with log closure04:21:09UTC
and explicit worker join before module unload. Fresh screenshots
`unreal/Saved/Screenshots/troublemaker_row_solver_playable_20260912_000..003.png`
were generated; first and last were inspected. The prior large flat-sided
rock faces remain obvious; froth transport is present, but this numerical
optimization does not fix the rapid's insufficient breaking shape or motion.
Four native Unreal regressions pass with zero errors/warnings, command88467
exit0: hydraulic crest scale, spatial breaking locality, playable crest
reconstruction and conforming refinement. Report:
`unreal/Saved/RaftSimValidation/troublemaker-row-solver-native-20260912/index.json`.
No visual or full-goal acceptance is claimed.

Independent repeat with identical settings is TERMINAL, log closed04:23:30UTC,
workers joined; no engine process remains. Report:
`unreal/Saved/RaftSimValidation/troublemaker_row_solver_perf_repeat_20260912.json`.
857 frames, mean14.458ms, p9526.461ms, solver5.020ms, meanGPU7.431ms,
one>33ms hitch,3503.22MiB. The two separate runs support a repeatable solver
cost reduction of about42%, not a60FPS or release claim. Both frame and solver
gates remain failed. The normal map, captured mesh and real user save were
rehashed after runtime tests and are unchanged from the recorded identities.
All owned builds/tests/captures/performance runs are terminal; no duplicate
build, altered budget, hidden scenery or profile mutation was used.

Next work remains the actual inferred rock-side/shore shape, insufficient
breaking motion and remaining frame/solver cost, followed by full-route and
later-river integration. Do not repeat this completed build or present the
optimization as a new visual transformation. Full goal remains active.
