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

## Current shared foam and colour paths

Later September 17: two additional stale Chilko/shared-water source contracts
are reproduced before edits: 12 PASS / 2 FAIL, report
`tmp/chilko-contract-before-v1-20260917.xml`. One requires the former spelling
of the unchanged 220 ms exponential attack; the other expects three duplicated
volume-core uploads where the current publisher has one shared fallback and
a separate packed/clipped Cartesian carrier.

The repaired checks preserve the attack constant and additionally require its
actual Resolve call, final red-channel write, held-clock preservation and
attack interpolation in the extracted helper. Linear-colour checks still
inspect every explicit procedural upload and now also follow the actual
source packer into the clipped carrier. They require non-sRGB colour packing;
merely lowering the expected call count would leave that path unguarded.

Ten new in-memory mutation controls reject changed/bypassed attack, lost final
foam, regenerated held foam, wrong interpolation, sRGB/erased packed colours,
bypassed packing/clipping and a gamma-converted fallback upload. Together with
the earlier controls, the focused suite now passes 78 tests, no skips:
`tmp/current-water-contracts-v2-20260917.xml`, SHA256
`dc0b147b9a84dcb99629ae3c878cc87a543dbd84f39bf7c2e6b3ad68d407cd9b`.
This test repair changes no runtime behaviour and is not a Chilko visual review.
The restored ordinary native D3D12 run also passes SurfaceSourcePacking and
FoamCommittedEvolution alongside eight mesh/contact regressions, ten total,
zero warnings/failures/not-run tests. Report:
`tmp/crest-root-workset-restored-native-v1-20260917/index.json`.
