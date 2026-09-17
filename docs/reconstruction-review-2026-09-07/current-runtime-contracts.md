# Current South Fork runtime contracts

Reviewed 2026-09-17 UTC. This change repairs five stale source-contract tests;
it changes no runtime code, installed binaries, terrain, or material assets.

The launch checks now compare all five South Fork sessions to the registered
session contract and verify its coordinate-map hash. Troublemaker remains a
rapid within South Fork, never a separate menu scenario. Terrain checks follow
the extracted source classifier, including actor- and component-tagged ground,
while preserving the ray budget. Clock checks require retained simulation debt,
at most four completed ticks per frame, failure handling, and coupled MUSCL2;
they reject the old elapsed-time-discard behavior. Near-bank checks cover both
shared and single-surface breaking with unchanged coverage/clearance thresholds.
Smoothing checks follow the shared helper and preserve independent hydraulic
passes, wet-neighbor guards, native mean restoration, and other-river optics.

Eighteen in-memory negative controls verify that these checks reject concrete
regressions without modifying runtime files. The first run had 68 passes and
two failures: controls exposed checks that could match unrelated source blocks.
Scoping those checks to the actual classifier and coupled solver corrected the
tests; neither the controls nor the runtime requirements were relaxed.

## Validation

- Focused Python suite: 70 passed, no skips; repeated before commit: 70 passed.
- Ordinary installed Unreal module, no candidate override: six native tests
  passed, zero failures, warnings, or not-run tests: Clock.CommittedDetail,
  Clock.FixedQueue, Clock.NativeBridge, Clock.RaftFailureLatch,
  M4.NativeMeanSmoothingElision, and M4.ShorelineTerrainProbe (RaftSim prefix).
- `git diff --check` passed. Generated reports, captures, caches, and Unreal
  binaries remain excluded by the existing `.gitignore` rules.

Local evidence (ignored, not packaged into Git):

- `tmp/south-fork-current-contracts-v2-20260917.xml`, SHA256
  `2e4cc59cc885108e9913d3a9502001faf366c8e0f836b0b40712c2a68f27c8a7`.
- `tmp/south-fork-current-contracts-native-v1-20260917/index.json`, SHA256
  `11179fc4dbd60cb9632b09104c9f25e2d81c364f0153c7075d474f0ed656a9e7`.

These checks do not establish convincing breaking/froth, settled hydraulics,
full playable integration, or sustained 30 FPS. The previously recorded thirteen
physical-suite failures remain open and were not reclassified or waived here.
The complete scene, crew, regression, and release queue remains open.
