# South Fork editor split and rejected range optimization

September 16, 2026. This continuation makes source-normalization progress and
extends hydraulic evidence. It does not qualify the displayed water model,
terrain/crew appearance, default-map integration or 30 FPS.

## Behavior-preserving editor split

The FullReach editor implementation exceeded the existing 3,000-line gate at
4,077 lines. Its builder/capture entry points now remain in the main source,
with shared helpers in `RaftSimEditorSouthForkFullReachHelpers.cpp`, declarations
and the actor-spawn template in `RaftSimEditorSouthForkFullReachInternal.h`, and
the support-field exporter in `RaftSimEditorSouthForkSupportExport.cpp`.
Each member is below the original limit. The 8,897-line LandscapeFoliage source
still fails the wider layout gate; no new exception or limit increase was added.

Direct comparison with the original Git source verifies unchanged helper,
template, builder/capture/wrapper and exporter implementation blocks. Defaults
move from helper definitions to their declarations. Internal helpers now have
a dedicated nested namespace so the separate translation units can share them.
No geometry, constant, material, terrain source, mesh asset, map, scenario or
runtime solver was regenerated or changed.

All three translation units compile independently, and the complete editor DLL
links with the new objects. Final build/link session93500 exits0. These outputs
are isolated under `tmp/south-fork-editor-split-v1-20260916`; the installed editor
DLL was not replaced. This is compile/link qualification, not a fresh scene
rebuild, deployed module test or packaged release.

Static contract readers now enumerate the four specific FullReach members;
unrelated river code cannot satisfy those checks and a missing member raises.
All **1,133 existing assertion ASTs are unchanged**. The inventory is regenerated
from the actual sources. Six new tests cover member inclusion, missing-member
rejection and the unchanged per-file line budget.

Verification:

- Focused parser/source-set suite: **38 PASS** in1.78s.
- Original75-test release/layout/Zambezi selection plus the six new tests:
  **69 PASS / 12 FAIL**, session12479 terminal1. The original failure identities
  remain, but the oversized-source failure now names only LandscapeFoliage.
- Additional source/visual-history selection: **43 PASS / 13 FAIL**. Existing
  capture hashes, absent historical external actors and legacy runtime-source
  assertions remain failures; none was rewritten to match current output.
- Initial post-split run exposed four moved-source reader failures and stale
  inventory. Updating locations and regenerating inventory resolves those,
  without changing the assertions. Both failed and final reports are retained.

Isolated editor DLL SHA256:
`926202bcfbfb43b653045dc5884e0dcc051d72d43940212f6e44b858d87ea04d`.
Installed editor DLL remains
`384fad9943690d1bc36a5977037fd4df9ead7db117431ad701bc334e5fb3ff32`.
Implementation-preservation report SHA256:
`2f6ab830dcefe889d71514264d380573cab2cdfd82bbd334350f7c45b8952b2c`.

## Crest range early-out: rejected, not a speedup

The preceding experiment attempted to stop nonnegative range accumulation once
it exceeded the original half-centimetre refinement threshold. It returned an
unbounded sentinel, never a partial sum presented as a complete range. V3 also
checked before toe/tail exponentials and preserved reference addition grouping.

V1 and correctedV3 each compare64 alternating-order actual-input refinement
builds. Parents, expanded coordinates, triangle order and ownership are exact;
neither candidate is faster in both execution orders. Mean milliseconds:

| Candidate | Reference first: original / candidate | Candidate first: original / candidate |
| --- | ---: | ---: |
| V1 | 8.109575 / 7.766494 | 7.646875 / 7.895722 |
| V3 | 8.473313 / 8.231578 | 8.049069 / 8.189556 |

The unchanged audit charges preparation to every candidate build. Both audits
correctly fail their speed gate. Native correctness alone does not override
that result. V2 was superseded before actual-game qualification after its
arithmetic grouping was corrected; do not cite it as gameplay evidence.

The candidate code/test was archived and removed from production source before
this continuation; files and binaries remain recoverable in ignored `tmp/crest-
range-limit-v{1,2,3}-20260916` directories. No gameplay optimization is promoted.
Do not repeat this candidate merely to seek a favorable noisy timing result.
The actual paired captures are diagnostic, not ordinary FPS measurements.

- V1 capture SHA256: `841a2bf450881cd1cca1ebacadf2ce3c7e74454c73b69fa45daf5eabd1d8d734`.
- V3 capture SHA256: `9fa5f8c01b6d154d000b8aaa699fbc43cfcf83bb3d3a9739fc6208b7bd255901`.

## Hydraulic checkpoints and live SM5 job

The same hydraulic process11316 continues the exact600s restart toward1800s.
New1050/local9000 and1100/local10000 checkpoints pass BOTH original audits:
5,382,400 finite/nonnegative cells and86,720 exactly dry artificial-bank cells.
At1100s maximum depth4.5996528753m, speed6.9163813566m/s, volume3,023,178.115412m3,
maximum step mass residual1.287374e-8m3. Outflow70.0281003007m3/s still exceeds
inflow45.3069545472m3/s: **not settled**, not calibrated or promoted to gameplay.
Next complete1150/local11000 checkpoint needs BOTH audits.

- 1050s state SHA256: `ffe5946978c2fcbd6016bd83f5e5e5ad4e8d378b27c548a249fd54147a6fb545`.
- 1050s banks SHA256: `36c96bb111f6af3fb8dbc1fda036bb4d4da0a53c7424eb1a1f22a3e8f599df41`.
- 1100s state SHA256: `ed96c061064d30663a3b27e0001e25d4b3993ed36a20f615efb16eadd12fdbe2`.
- 1100s banks SHA256: `c22f6b1509872a9b8e93b50d81c2e908e73586a7da69a9fde169fac8c6de5357`.

SM5 session47178 remains live when directly polled; editor35584 and workers
31820/34968 have advancing CPU time. Worker31104 previously exited; the owned
workload manifestv2 excludes it. At22:41:40 UTC the log records a hung-shader-map
error after7200s, with15 pending/141 finished jobs. This is an adverse result,
not success or proof of process termination. Preserve the same job and its
inputs until its terminal report; do not restart from an observation timeout.

The last ordinary installed-module result remains22.560934FPS/p9553.9323ms,
failing30FPS. Reinspection confirms the first-ready gameplay image has no visible
water despite technical detail readiness. Full streaming replay is not initial
render, nonlinear-water or visual acceptance. Continue that integration and
physical/source-consistent rapid review, then Colorado, Pacuare, Futaleufu,
other-scene water, crew and remaining release gates. Troublemaker remains only
a rapid in South Fork, never a separate menu scenario.
