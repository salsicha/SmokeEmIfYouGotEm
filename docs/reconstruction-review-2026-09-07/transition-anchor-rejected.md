# Downstream crest-anchor trial: not promoted

September 28 UTC / September 27 local. A real rebuilt-scene comparison, not a
source-text-only test. The placement-only hypothesis did not establish a useful
visual improvement. The trial was removed from runtime source; the small
[reproduction patch](transition-anchor-rejected.patch) preserves what was tested.
Do not reapply or repeat this unchanged trial as the next realism fix.

## What changed and what did not

The trial placed the shared crest origin at the detected downstream subcritical
sample rather than the upstream sample. This tests the mismatch between where
the existing formula subtracts resolved rise and where its residual is applied.
Rendering, raft support, foam, pocket/boil and other site consumers received the
same eased origin. The residual-height formula, depth/Froude inputs, length,
spilling fraction, solver, fields, material and captured/inferred terrain stayed
unchanged. No blanket height gain or second water surface was introduced.

The trial was restricted to the normal South Fork Cartesian single/shared-surface
path and remained OFF by default. A native helper selected the endpoint without
branching on rise sign, avoiding a new positional discontinuity around zero rise.
Moving the origin can alter deduplication survivors and subsequent physical
trajectories; identical formulas do not prove identical selected-site budgets.
This was an inferred representation trial, not surveyed crest placement.

Editor build `tmp/transition-anchor-editor-build-v1-20260928.log` succeeded in
83.71 seconds. Actual native tests `BreakingTransitionAnchor`,
`HydraulicCrestScale`, and `SpatialBreakingLocality` all passed: three successes,
zero test warnings/failures/unrun/in-process. The new test covered unchanged
residual scale, common support/foam origin, upstream source suppression and
translation invariance. It did not establish real-river physics or appearance.

## Actual normal-scene recordings

One owner ran the native tests, then OFF and ON sequentially in the same rebuilt
editor-hosted game, ordinary boat camera, full South Fork map, passive start at
8310 m, 1280x720 D3D12, ephemeral profile, 80 one-second samples after a two-second
delay. Both exited zero with no detected runtime error and confirmed CVar
application. No concurrent cook/build or new solver was used. This was NOT a
cooked-release comparison, Boot/menu requalification or FPS measurement.

| Evidence | OFF | ON |
| --- | ---: | ---: |
| First / last sampled station (m) | 8312.359 / 8486.437 | 8312.718 / 8478.068 |
| Selected sites at height snapshot | 14 | 14 |
| Strongest transition origin (hydraulic m) | (-5428, 3607) | (-5430, 3606) |
| Maximum submitted-mesh target error (cm) | 0.83746 | 0.83786 |
| Mesh audit samples | 1,657,584 | 1,681,056 |
| Maximum source-vertex change (cm) | 0 | 0 |
| Decoded frames / duration (s) | 2497 / 83.2 | 2494 / 83.1 |

Both mesh errors satisfy the existing 2 cm interpolation limit for the prescribed
crest. These audits exclude macro temporal lag, other base relief and GPU
perturbations. ON's mesh snapshot at 10.0109 s differs from its selected-site
snapshot at 10.4109 s; do not treat them as one exact state. Neither interpolation
accuracy nor encoder cadence establishes convincing water motion or game FPS.
No contact report was generated; this is not a complete zero-contact ledger.

The original 9, 20 and 40-second frames from EACH recording were visually
inspected. Both show broad smooth water faces, flat white foam and separated
spray rather than a convincing collapsing crest/recirculating hole. The ON
20-second frame still has a broad white sheet on the right. Station, camera and
physical-time differences prevent a pixelwise causal claim that ON increased
whitening, but it plainly does not establish the required improvement. The
whole videos were decoded, not continuously visually reviewed.

This remains unlike the localized steep faces, irregular troughs and collapsing
whitewater recorded in the earlier [real-reference review](reference-review.md).
No new reference footage was viewed, no wave dimensions measured and no new
shipping rights inferred during this trial.

## Evidence identities and restoration

Owner/recipe: `tmp/transition-anchor-review-v1-20260928-process.json` and
`tmp/review-transition-anchor-v1-20260928.ps1`. All native/capture work completed;
do not restart it. Physical asset/config/bundle manifest hashes still matched
the retained v13 package receipt after capture.

- Native report `tmp/transition-anchor-review-v1-20260928-native/index.json`:
  `1e1266dfe99316e65220360f8ee748382edeb4a86eb5973c834061018a1c899b`.
- OFF video `unreal/Saved/VideoCaptures/RaftSim_20260927-173414.mp4`:
  `cf04563db3b50d7447ad70d706661bd944407fc5487fed257fd9da1ae954b965`.
- ON video `unreal/Saved/VideoCaptures/RaftSim_20260927-173607.mp4`:
  `c17fd673045aec8331691e55f517d357580766dafcdec02f68ff86c8e4c6dc36`.
- OFF decode report `tmp/sf-transition-anchor-0-decoded-20260928/report.json`:
  `6fbcff793fa1fe94769a83e8f6e31a8155d9372538251ef8286cf4ec01f0fa4b`.
- ON decode report `tmp/sf-transition-anchor-1-decoded-20260928/report.json`:
  `120c5bec4538285d524962125dbd8b3f99e5b4f920d26b1279aa888ae0f28de9`.
- Reproduction patch SHA256:
  `e084528d917ecd0f8f89212ef7833e25c60a006a382fdfbedf932450baf41c15`.

The first decoder finished its full report, but `Select-Object -First` truncated
its console pipeline and stopped the two-file wrapper. The second video was then
decoded separately with output fully drained, exit zero. No first-video overwrite
or engine recapture was needed.

Runtime edits, temporary helper and temporary native test were removed with
scoped patches, restoring the original source without touching unrelated work.
The retained patch passes `git apply --check` against the restored source. A
baseline editor rebuild succeeded (exit zero, 48.67 seconds), recorded in
`tmp/transition-anchor-restored-build-v1-20260928.log`. No post-restoration game
run is claimed. Packaged v13 was never modified.

## What this rules out

Moving the same bounded static profile is insufficient as the next appearance
delivery. Do not promote it merely because tests or tessellation pass, and do
not replace it with an uncalibrated gain/foam multiplier. The combined resolved
surface and evolving breaking/roller dynamics still need a physical correction;
the unsteady 900-second fields cannot supply a settled calibration target.
Performance/clock lag, collision, shoreline and reference-motion acceptance
remain open. No river, crew or release gate is closed by this trial.
