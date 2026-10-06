# Healthy packaged rapid: CPU-stage localization

September 27, 2026. Supporting diagnosis, **no new playable delivery**. The
previous failed packaged performance gate remains open; these instrumented
timings are not a replacement FPS test or a before/after optimization claim.

One isolated run of the unchanged v4 packaged executable subdivided the busy
11,520 m rapid's work after the startup-health repair. Earlier detailed stage
captures predated that repair. No solver, visual quality, update cadence,
geometry or saved player profile was changed. No engine/build/cook was active
before launch; no new build or cook was needed.

## Run / health

Process 34368, September 27 approximately 10:09–10:10 UTC, exit 0. D3D12,
1280x720, ephemeral profile, normal FullReach assets, full-descent scenario,
explicit diagnostic review station 11520, `-RaftSimWaterStageTimings`, 600-frame
CSV exit bound. This is direct rapid startup, **not normal Boot/menu travel**.
Normal-launch evidence remains the earlier repaired v4 game check.

Binary SHA-256 remains
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523` before/after.
No runtime Error/Fatal records. Shutdown reports 599 paired presentation commits,
31.004 s healthy detail, zero PDE backlog, and no GPU waits. This establishes
healthy operation for this diagnostic, not rendered-wave/collision acceptance.
No new screenshots or visual acceptance are claimed.

## Measured subdivision

Fixed engine frames **120–560 inclusive**, 441 ticks and crest updates, 239
refresh calls. Every requested tick is present; no frame was removed to improve
an outcome. The following are **per-call means**, not additive frame costs:

| Scope / child | Mean ms | Calls |
| --- | ---: | ---: |
| Surface tick | 27.3863 | 441 |
| Tick interpolation (includes publication) | 15.3974 | 441 |
| Refresh total | 21.9635 | 239 |
| Refresh source buffers / coverage | 1.8696 | 239 |
| Refresh source sampling / handover | 2.8409 | 239 |
| Refresh base vertices | 2.9355 | 239 |
| Refresh breaking carve | 2.6910 | 239 |
| Crest update, geometry rebuilt | 18.5727 | 241 |
| Rebuilt adaptive selection total | 11.7628 | 241 |
| Rebuilt profile sampling within selection | 5.6331 | 241 |
| Rebuilt topology assembly within selection | 5.2098 | 241 |
| Rebuilt targets (includes fine-profile/boundary preparation) | 3.0376 | 241 |
| Crest update, retained geometry | 1.8360 | 200 |

No XY-only change without a profile change occurred. All 200 retained updates
used dense history; all 241 rebuilt updates used mapped history. Across all
441 updates, source-prefix copy averaged 0.1394 ms, midpoint interpolation
0.3053 ms and correction history 0.8254 ms. This supports deprioritizing another
minor target-expansion/copy loop experiment. It does **not** authorize retaining
stale profile heights, suppressing work, changing cadence, or loosening geometry
tolerances. Selection sampling and assembly are both substantial, so attributing
the entire selection cost to profile evaluations would also be incorrect.

These scopes overlap and nest. Do not add refresh and publication to derive
total CPU cost, or compare this short instrumented trajectory causally with
the earlier 1,200-frame uninstrumented failure. That retained primary result
is still p95 **85.2731 ms**, versus the user's **50 ms / 20 FPS** goal.

## Diagnostic reliability repair

The stage parser previously accepted a partly missing tick interval, silently
ignored negative/nonfinite timing tokens, and could average different metric
sets with different sample counts. It now rejects missing ticks, duplicate
metrics, missing totals, nonfinite/negative values and changed per-scope metric
sets. Sparse scheduled refreshes remain valid, and their exact frame IDs are
recorded separately. Eight regression tests pass, including missing-frame and
malformed-value fixtures. The crest parser independently verifies all 441
vertex-subdivision records. Sandbox execution initially could not create test
temporary directories; the approved scoped rerun passed. No permission settings
were changed.

## Evidence / next boundary

All artifacts remain under `tmp/`:

| File | SHA-256 |
| --- | --- |
| healthy-rapid-stage-localization-20260927.log | `256ab7e0fe8b3b4e598fe26b97e37b21eae250cf07bee9482c1310faf90039d8` |
| healthy-rapid-water-stages-20260927.json | `ac851724009eb6c34d8db6410297a152ff394cd8f010a07c40c56e4f51481d34` |
| healthy-rapid-crest-stages-20260927.json | `fa9a46522cf9e095f95c9a00015041ed0244fbc794e830c58cfd0d2b269469b6` |

Reproduce reports with `audit_water_stage_timings.py` and
`audit_crest_stage_timings.py --require-vertices`, using frames 120 through 560
and fresh report paths. The run's full arguments are retained in its log.

Do not repeat this unchanged localization. The existing rejected region index,
root incidence, parallel emission, fine-profile cache, blend preparation,
solver lane and RK-combination-view experiments were checked rather than
reintroduced. A future performance candidate must materially reduce current
sampling/assembly work while preserving exact ordered geometry and history,
then pass both-order whole-frame and rebuilt normal-game verification.
Bank/underwater geometry and physical fidelity remain independent open work;
South Fork is not complete and later rivers have not been accepted by this run.
