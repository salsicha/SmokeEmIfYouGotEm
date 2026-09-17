# Exact crest topology publication and hydraulic continuation

Recorded 2026-09-17 UTC. This is measured implementation progress, not scene,
physical-wave, sustained-performance, or release acceptance.

## Exact publication optimization

The publisher now copies the existing signed triangle indices into unsigned
output storage in one byte copy, and partitions the existing cell-owner scan
into 1,024-cell batches. Each batch starts at the exact lower bound in the
ordered triangle-owner array. Unordered owners or offsets use the original
serial publisher. No selected triangles, winding, vertices, water geometry,
profile samples, thresholds, or temporal history are changed or omitted.

The original publisher remains available with
`-RaftSimReferenceCrestTopology`. The read-only paired diagnostic is
`-RaftSimCrestTopologyPublishAudit`; it does not qualify ordinary frame rates.

Six native tests pass without warnings or skips on both the initial isolated
candidate and the final default-enabled build: CrestTopologyPublish,
ShorelineCrestTargetCache, ShorelineExactCache, ShorelineFineCrest,
ShorelineInputValidation, and ShorelineMovingBankCache. The new test checks
empty/single/batch-boundary/large arrays, dry gaps, repeated owners, sentinel
offsets, integer-division semantics, unordered fallback, and signed index bits.
Nineteen Python publication-audit and existing frame-CSV checks pass.

The actual South Fork paired run completed with exit 0. All 64 consecutive
frames 120–183 match exactly: 9,646,749 indices and 3,211,328 cell offsets.
Both paths receive fresh index arrays and equivalently sized offset storage;
call order alternates. Mean CPU publication time:

| Group | Original ms | Partitioned ms | Faster pairs |
| --- | ---: | ---: | ---: |
| All | 0.384391 | 0.168537 | 64/64 |
| Original first | 0.393656 | 0.156159 | 32/32 |
| Candidate first | 0.375125 | 0.180915 | 32/32 |

Strict pair report: `tmp/south-fork-crest-topology-pair-v1-20260917.json`,
SHA256 `b751a167f20f6191f6208b720e5d9e6bb7662438e6df2e5583020fc4efa32470`.
Its source log SHA256 is
`79653987e40ed4d4798a96f5a425522539d28b9b99144c0fb3dc64ea7f55c7a1`.

Final native report: `tmp/crest-topology-publish-native-v2-20260917/index.json`,
SHA256 `10e974cb87d54ee70f7b757c2f057db108fb4f42776008263c2773daf3f65605`.
Final isolated gameplay DLL:
`tmp/crest-topology-publish-v2-20260917/UnrealEditor-RaftSimRaft.dll`,
SHA256 `e64b290fa2f57c312d29bc7fad67edd9c79230e6e76ad1c62f7fb069e9c2ce08`.
All outputs remain local and ignored; no installed DLL was replaced.

## Ordinary-play result: still fails 30 FPS

The separate default-enabled 300-frame capture is 1280x720 D3D12, ordinary
South Fork gameplay at station 8330 using the isolated module override. It has
no paired timing diagnostic or topology-selection override. The unchanged
inclusive sample window 60–240 contains 181 rows:

- Elapsed-frame rate: **28.057157 FPS**.
- Mean frame: **35.641530 ms**; p95: **41.2354 ms**.
- Required p95 budget: **33.333333 ms**. **FAIL**.
- Mean game thread 35.428940 ms; GPU 12.233090 ms.
- Water tick 21.419625 ms; Cartesian publication 11.121440 ms;
  SetMesh 9.824797 ms; crest update 7.843654 ms;
  selection 3.602291 ms; solver StepWater 5.953484 ms.

These scopes are nested; do not sum them. The earlier separate capture was
27.068531 FPS / p95 43.391 ms. This is not a controlled whole-frame comparison,
so do not attribute its entire difference to this 0.216 ms local saving.

CSV: `unreal/Saved/Profiling/CSV/south-fork-crest-topology-default-v2-20260917.csv`,
SHA256 `168695681ef5759343ac58aea1d82ecff05c7d3843698b37a708bde8b1eddb5c`.
Strict audit: `tmp/south-fork-crest-topology-default-v2-20260917-audit.json`,
SHA256 `cba23a9c08426d8ca7cd83f5652e7a8f8a3bd5c473bc71f5efdbc04bc4a4c042`.
Both capture runners exited 0 and resumed every explicitly owned paused
process. Their process witnesses are retained under `unreal/Saved/RaftSimValidation/`.
All 63 original SM5 shader-input hashes were checked unchanged before and
after both captures. Shader editor 9976 and worker 31736 remain live; the
other original worker completed its batch. No restart or new shader inputs.

## Exact hydraulic continuation, not settled

The original 600–1800s cook is terminal, not waiting. Its completed frame
24000 passed both state and 86,720 dry-bank checks but was not settled.
The new independent native restart audit passes all 5,382,400 original cells
bit-exactly, preserving grids, beds, roughness, boundaries, and checkpoint time.
Added cells and added water are both zero. No physical input was retuned.

New input: `tmp/control-ablation-1800to3600s-input-v1-20260917/manifest.json`,
SHA256 `9787d3de361006f2b912c2f2519782489cd47d056e66084dad5967074f1c7bcb`.
Restart audit: `tmp/control-ablation-1800s-restart-v1-20260917.json`,
SHA256 `6a2590b7efeb611f16e640829b7e493bcea7e80f2438bcc0559d1980cf0d22a3`.
The same solver executable hash remains
`b2e2834f2dadd347c0ff89d86e4a90859ee316a563f779b82a6b02767cdc2cfa`.

Continuation session 51728 / PID 36872 started
`2026-09-17T03:10:30.0811512Z`, with 36,000 steps at the unchanged 0.05s and
snapshots every 1,000 steps. Output:
`tmp/control-ablation-1800to3600s-v1-20260917`.
Latest observed progress was 1835.5s/local710; next complete snapshot is
1850s/local1000 and requires both state and dry-bank audits. Preserve the live
process. No snapshot is promoted; settling and normal-map integration remain false.

Nonlinear wet-front pressure/full RK2, convincing moving waves/froth, source-
consistent terrain/boulders/collision, safe installation, 30 FPS, normalization,
Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene review, crew, and release
remain open. Troublemaker is only a rapid within South Fork, never a menu scenario.
