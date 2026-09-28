# V13 playable review: completed tests, acceptance still fails

Artifact date September27 local / completion September28 UTC. This closes the
previously queued work; it does not authorize promotion or later-river work.
All four owners (hydraulics, packaging, timing, capture) have terminal receipts.
No corresponding game, cook, editor, Python or dotnet process was found at review.

## Delivered build versus supporting evidence

V13 contains the opt-in spatial observer and the default-OFF far-field packing
candidate. It retains the450s v8 fields and the same captured/inferred geometry.
BuildCookRun completed in798.77s with frozen input hashes unchanged. The ordinary
Boot/menu launch reached the full river in the cooked standalone. Staged closure
verified2,405 files/917,995,570 bytes without external-source fallback. Existing
optional MetaHuman dependency cook warnings remain; this is not a clean release.

Cooked executable SHA256:
`efe039224bc328d5b335705fc34aa7c925a3c44ab716922982386b87398d7652`.
Receipts: `tmp/south-fork-v13-package-20260927.json` and
`tmp/south-fork-v13-staged-payload-20260927.json`.
No newly accepted appearance or physics improvement follows from this build.

## Actual performance: retain every failure

Five same-build1280x720 offscreen Development runs,1,200 frames each, audited
rows30..1169. Timing waited for packaging AND the hydraulic wrapper/final audits.
No cook/build ran during profiling. Brief read-only host inspections do not prove
complete external-system quiescence. No OS/power/antivirus settings were changed.
All runs exited0 with zero detected runtime errors; every timing gate failed.
Targets remain20FPS, p95 at most50ms and no frame over100ms.

| Run | Mean ms | p95 ms | Maximum ms | Frames >100ms |
| --- | ---: | ---: | ---: | ---: |
| Normal Boot/menu | 44.7079 | 97.2677 | 140.4200 | 50 |
| Station11520 OFF A | 59.3415 | 82.6177 | 108.5646 | 1 |
| Station11520 ON A | 46.2247 | 54.0406 | 100.3354 | 1 |
| Station11520 ON B | 45.4541 | 51.6323 | 105.1900 | 1 |
| Station11520 OFF B | 70.6075 | 89.9774 | 149.4098 | 11 |

Receipts are `unreal/Saved/RaftSimValidation/sf-v13-*-20260927-frame-audit.json`.
Hash-bound retained CSV attribution is `tmp/sf-v13-stage-cost-20260927.json`,
SHA256 `980b90ff230d8dd43b6e6d61dfb5f8ce186cae1f772b69534a397ab3c1e9ad76`.
It preserves missing counters as unavailable, all hitches and both run orders.
Actual CVar application is recorded in each busy-run log, not just its command.

Each busy window contains only ONE far-field pack event. OFF A/B cost4.5873/
4.7258ms; ON A/B cost3.2005/3.3651ms. This approximately1.3-1.5ms event reduction
cannot explain the13-25ms whole-run mean differences. Rebuild rows differ
(774/1088/1113/829), as do cadence/trajectory and other scope timings. The normal
window has no far-field sample/pack/submit event. Default reuse remains0;
whole-run causal speedup and production parity are not established.

All50 normal-menu hitches occur at rows900..1169, whose p95 is115.0503ms.
Earlier blocks have p95 below48ms. Do not dismiss this as an initial cold prefix
or trim it away. Game-thread and surface/solver/crest scopes grow substantially;
normal GameThread p95 is93.9928ms versus GPU29.65ms. Inclusive nested scopes must
not be added. The cause of large run-to-run and late-run variance is unresolved;
neither thermal throttling nor memory exhaustion has been demonstrated.

## Motion and spatial review

The completed passive approach uses the ordinary boat camera, normal FullReach,
review start8310m, default packing, unchanged fields and no paddle input. Its
80 samples move from8314.141m to8487.267m. No runtime error was detected. Absence
of a GroundContact event is not a complete zero-contact ledger or guided route
acceptance. This capture is not a performance measurement.

Video: `tmp/south-fork-playable-v13-20260927/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-170640.mp4`,
SHA256 `fa5e0d8ec56780d1e11884c2caf14b2d845686ecbe6f0aad82175c79a4093779`.
Decoded evidence: `tmp/sf-v13-spatial-approach-decoded-20260927/`.
The6/9/20/40s frames show changing raft position/heading but broad flat white
foam patches, separate spray puffs and coarse rock flanks remain. These inspected
frames do not establish convincing crest breaking, hole recirculation, shoreline
stability or long-animation acceptance; the entire video was not visually reviewed.

At world10.419s, the selected site at hydraulicXY(-5428,3607) has additional
height0.047042679m and length2m. Its paired downstream sample is(-5430,3606),
2.236m away: surfaces7.7448 ->8.1041m, beds7.4946 ->6.3801m. The0.3593m surface
rise is subtracted by the height calculation while the profile is centered at
the upstream site. Flow direction is approximately(-0.996587,0.082544); the
paired sample is not exactly on the same streamline. This establishes spatial
accounting evidence, not a proven formula bug or permission to amplify height.
The detector's41 eligible candidates are not41 final rendered sites.

Actual adaptive-mesh audit at world10.019s (a DIFFERENT snapshot) measures maximum
target crest error0.810588cm over1,660,680 samples. It checks interpolation of the
prescribed crest, not whether that target is physically correct. It excludes
macro temporal lag, other base relief and GPU perturbations. Do not substitute
the separate coarse crest-only error for this adaptive result.

Spatial report `tmp/sf-v13-spatial-approach-20260927-height.json`, SHA256
`43ead09362fd74a28fa65649acbc8fb7de694a265821ea22caff5c8fad0f66a0`;
selected sites `tmp/sf-v13-spatial-approach-20260927.json`; mesh audit suffix
`.json.cartesian-mesh.json`. No new surveyed wave/underwater dimensions are claimed.

## Completed900s continuation: not settled, not installed

Exact450s restart, unchanged geometry/forcing,9,000 steps of0.05s. All5,382,400
final cells are finite/nonnegative; all86,720 artificial-bank cells are exactly
dry. Maximum per-step mass residual is1.01402e-8m3. Those numerical checks pass.
Troublemaker's8..9km storage rates are+3.01883m3/s (450..600),-2.67729 (600..750),
then-6.45027 (750..900). Later loss is increasing, not monotonic local settling.
Whole-domain750..900 storage still rises5.08631m3/s, masking opposing regional
changes. Region bands are nearest-route storage partitions, not flux sections.
Do not fit the inferred bed to this unsteady stage or promote these fields.

Reports and SHA256:

- `tmp/troublemaker-envelope900-state-v1-20260927.json`:
  `bd200d7187a0905a05b461467ed4563d19024979b10691d12746005cc90f45db`
- `tmp/troublemaker-envelope900-banks-v1-20260927.json`:
  `9dc9586427c88572ebac6b69d43fda766421f71df7e330c74b909e7665842e23`
- `tmp/troublemaker-envelope900-storage-v1-20260927.json`:
  `355165426ccbf9d831074f6037f7ccf8064a7a369af27e5a6c0f09ed0c53db99`

## Next bounded work

1. Use retained frame scopes to isolate recurring/late CPU cost and cadence;
   do not repeat unchanged v13 runs looking for a lucky pass or enable reuse
   based on whole-run means. Production correctness remains required.
2. Review the complete resolved base plus added crest profile in spatial context
   before changing height/placement. No blind gain increase, cosmetic whitening
   or rejected solver enablement. Verify any correction in rebuilt normal play.
3. Resolve local hydraulic transients before field promotion. Any justified
   continuation must be separate from FPS/motion validation, not a duplicate cook.
4. Preserve captured geometry, provenance and all failures. No later-river advance
   until actual geometry, collision, shoreline, animation and performance pass.
