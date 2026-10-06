# Unavailable water must not fabricate physical support

Production correction, September24. No geographic/visual reconstruction acceptance.

Previously a scenario-bound non-Cartesian adapter without a loaded window
returned a synthetic wet sample, depth1m. World sampling assigned the probe's
centimetre Z directly to a metre field; river sampling instead returned stage0.
Faulted adapters were not rejected by either sampler. Missing physical evidence
could therefore masquerade as usable water/support with inconsistent heights.

Both public sampling paths now reject Faulted status and return false without
a valid live window. Explicit development tanks remain supported through the
existing real-window path. Live wet/dry samples and off-window behavior are
unchanged. The raft-support entry point inherits rejection from world sampling.
No replacement synthetic plane, source relabeling or solver-mode change was made.

## Verification

- Editor build53.76s and Game build79.29s succeed:
  `tmp/unavailable-water-{editor,game}-v1-20260924.log`.
- Native unavailable-water and Cartesian crest-support suites:2 passed,
  0 failed,0 warnings; `tmp/unavailable-water-native-v1-20260924/index.json`.
  Cases include uninitialized/bound/running-without-field states, world/river/
  support queries, explicit tank stage5m/bed3m/depth2m at probe Z−10000/0/25000cm,
  fault with an existing window, and explicit reload recovery.
- Normal FullReach/full_descent start (no review station),4 solver lanes,
  D3D12,1280×720:900 cost frames, samples60–840 inclusive, confirmed phase offset1.
  Mean22.982146ms, p9531.3109ms, maximum38.221ms. Short first-pool p95 passes
  33.333333ms, not sustained/full-route or packaged acceptance or a speedup claim.
  Report: `tmp/unavailable-water-frame-v1-20260924.json`; CSV SHA256
  `6dce1cf0284f9421ef5cda147af1613f8104545bf56bfb15aa8c5950e2092bdf`.
- Separate motion clip `unreal/Saved/VideoCaptures/RaftSim_20260923-195316.mp4`,
  SHA256 `20c2cc3339257ab1b622f17c74e89dfb0e1349c4a50520006a020037b2763634`:
  fully decoded465 frames through15.466667s,25 adjacent duplicates. Original3s/9s
  frames inspected: raft advances0.12→0.13km, water changes, zero displayed
  incidents/swimmers, no missing sheet in these views. Smooth water, coarse
  canopy and crew shading/pose limits persist. Not full shoreline/contact proof.
  Decode report: `tmp/unavailable-water-motion-v1-20260924/report.json`.

Process receipts:
`unreal/Saved/RaftSimValidation/south-fork-unavailable-water-{cost,motion}-v1-20260924-process.json`.
Both engine exits0/no timeout; cook suspend/resume statuses0. Cost cook CPU delta
before resume0.125s; motion0s. Original cook36692 resumes alone. Cost helper ended
the initial shell sequence; absence of a motion receipt was verified before
launching the separate motion call (no duplicate capture). Captures are editor-
hosted game runs; standalone target build is not packaged-launch qualification.

Healthy South Fork appearance is not intentionally changed. This delivers failure-
path correctness in the rebuilt runtime, not new terrain or froth. Installed4950s
fields and nonlinear OFF stay unchanged. South Fork and the complete ordered
queue/crew/regression/release scope remain unfinished.
