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

## Clock-capacity follow-through: retained captures expose actual simulation lag

The existing `physics/scripts/audit_unreal_frame_csv.py` now reports requested,
committed, native, adapter and backlog counters as seconds/counts, never as
millisecond timing scopes. Missing counters remain unavailable, partial counters
are rejected, and no diagnostic result grants simulation-capacity acceptance.
All21 unit regressions pass, including four new clock tests covering lag despite
passing frame time, missing/partial data, invalid counters, failures and native
origin changes. No game rebuild or unchanged timing replay was needed.

| Same audited rows30..1169 | First backlog s | Maximum backlog s | Last backlog s | Fixed ticks |
| --- | ---: | ---: | ---: | ---: |
| Normal Boot/menu | 0.010613 | 3.3244 | 3.3244 | 2859 |
| Busy OFF A | 0.8460 | 4.8891 | 0.001383 | 4109 |
| Busy ON A | 0.7633 | 0.9583 | 0.016059 | 3206 |
| Busy ON B | 0.4417 | 0.4417 | 0.005237 | 3136 |
| Busy OFF B | 0.5928 | 10.8995 | 8.9365 | 4329 |

Zero failed-step flags do not mean real-time motion. Normal-menu native, adapter
and committed clocks match at printed precision; queue residual is at most
0.0001001s after independent CSV rounding. At the last audited row the requested
clock is57.2077s but only53.8833s has been committed. The busy starts retain an
approximately0.0667s native origin offset; its range is only0.0001001s at printed
precision. This is reported, not mislabeled as a dropped physical tick.

The bridge preserves elapsed debt, advancing at most four fixed water/raft ticks
per render frame. Normal rows30..899 stay below0.016667s debt; the last block
grows to3.3244s. Its solver aggregate cost per completed tick rises from about
3.48-3.53ms to5.31ms, while mean surface Tick increases from21.25-21.96ms to
34.78ms. More ticks per frame alone therefore do not explain the slowdown.
This is evidence of capacity loss, not a proven thermal/OS or solver root cause.
Do not hide it with timestep inflation, dropped elapsed time or a higher work cap.

Different accumulated debt and total committed work further disqualify attributing
whole-run OFF/ON means to the one sparse buffer-pack event. The next performance
investigation should separate per-tick cost from per-frame surface work, retaining
the existing clock contract and all failed rows. Water shape/recirculation still
needs the spatial model correction and actual playable verification described above.

Reports `tmp/sf-v13-<case>-20260927-clock-capacity.json` retain source CSV hashes,
full timing failures and clock summaries. The four busy files contain duplicate
unmeasured `NumInstanceTransformUpdates` headers; the existing explicit exception
records their indices without combining/dropping columns or permitting ambiguous
clock/timing metrics. The normal capture requires no exception. Report SHA256:

- normal-menu: `5e1528ad0672fdd7f2c09000226753d1ef3954509e94af5bb0d22b2f58b4d7dc`
- rapid11520-off-a: `9ff2fa5c3759426fa2a9deba8ee31149d980d3aca84394bafb83d11925f6b39b`
- rapid11520-on-a: `0746d0427c64e6578265b1f0a626c9e8210b59a78d6efb25c0d312fcd18a479d`
- rapid11520-on-b: `8474b56bea0125ee99ff6f978ee045e77ab7aabfd80348b04415b41b9460a049`
- rapid11520-off-b: `e09cee90015413d8c823cbb4214399569d81f54d510b7a70d86cb63d99ccd2ad`

## Crest cadence follow-through: more costly geometry updates, not more calls

The retained normal-menu CSV has exactly one counted crest update per audited
frame. The late slowdown is therefore not an increase in crest calls per frame.
Same-row change flags separate geometry-changing updates from unchanged-target
history updates. Inclusive CPU scope means are shown below; surface Tick includes
crest work, so these columns must never be added.

| Rows inclusive | Geometry-changing frames | Crest ms, geometry changed | Crest ms, targets unchanged | Surface Tick ms, geometry changed | Surface Tick ms, targets unchanged |
| --- | ---: | ---: | ---: | ---: | ---: |
| 30..299 | 134/270 | 10.436 | 2.041 | 15.067 | 28.744 |
| 300..599 | 148/300 | 9.754 | 2.160 | 14.576 | 28.589 |
| 600..899 | 149/300 | 9.994 | 1.993 | 14.584 | 27.825 |
| 900..1169 | 189/270 | 14.602 | 2.069 | 37.559 | 28.282 |

Two effects coexist: geometry-changing frames rise from about half to70%, and
their mean crest-update cost rises from about10ms to14.60ms. The unchanged-target
crest cost stays near2ms. No profile-change events occur. XY changes occur on all
geometry-changing rows; occasional index/detail-window changes also occur earlier.
This is conditional timing evidence, not a normalized cost per vertex, proof of
redundant reconstruction, or thermal/OS diagnosis. Moving shoreline coordinates
are legitimate inputs; do not suppress necessary geometry updates to pass timing.

Next, compare these categories in the already-owned isolated v14 captures before
proposing a runtime optimization. A candidate must preserve changing shoreline
geometry, history interpolation and actual shared-surface contact. Increasing
frame duration can alter refresh cadence; these same-row correlations do not
establish frame-time causality or explain all parent-surface work.

Reproduction: `physics/scripts/audit_crest_update_cadence.py` with intervals
`30 299`, `300 599`, `600 899`, `900 1169`. Report:
`tmp/sf-v13-normal-crest-cadence-20260928.json`. Input CSV SHA256:
`08712ec5812946289534c40f4163e4d6de29d7dcfa55994bd8e2a35a9073153c`.
The analyzer reuses completed-CSV validation, rejects missing/ambiguous counters,
and keeps multiple-call rows unresolved. Missing early values are not zeros.
This is supporting diagnostic work, not a playable change or acceptance.

### Refresh co-occurrence identifies the late expensive population

The v2 cadence report additionally splits each category by positive same-row
Refresh scope (measured work, not a refresh-call count). In rows600..899, all149
geometry-changing updates have zero measured Refresh work: crest9.994ms,
surface Tick14.584ms. In rows900..1169,81 such no-refresh updates remain close
to that cost: crest10.481ms, surface15.092ms. The other108 geometry-changing
rows also contain Refresh work and are much more expensive: crest17.692ms,
selection6.470ms, Refresh30.342ms, surface Tick54.409ms. These nested scopes
are not additive. The81 late unchanged-target refresh rows remain near earlier
costs: crest2.069ms, Refresh21.296ms, surface28.282ms.

Thus the pooled geometry-changing slowdown must not be mistaken for uniform
cost growth. The expensive joint population is the next comparison target.
The current Tick publishes/interpolates before its15Hz refresh check; that
ordering can separate refreshed geometry from the publication frame. No source
edit, dropped refresh, added simulation debt or quality reduction is justified
by this correlation alone. Preserve the same-row scope identities; elapsed
FrameTime has its separately verified one-row association and is not used here.

Report `tmp/sf-v13-normal-crest-refresh-cadence-v2-20260928.json` retains the same
source hash above. Six cadence tests and21 existing CSV tests pass27/27, including
joint-category separation without changing total crest cost or call categories.
The existing v14 hydraulic/validation/motion owners remain untouched. Retained
default boat views at11s and20s still show broad flat foam; neither this timing
analysis nor sparse image review establishes breaking, collision or motion acceptance.
