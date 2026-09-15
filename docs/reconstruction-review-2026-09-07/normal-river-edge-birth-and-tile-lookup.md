# Edge wetting and playable crest lookup — September 15

This increment separates a physics prerequisite from a playable runtime
optimization. Neither is full water realism, 30 FPS, or release acceptance.

## Edge-birth pressure prerequisite

`subcell_edge_birth_pressure.py` implements the one-source edge limit of the
original two-pole pressure Hamiltonian. An edge first wets with `V=c*e^2`,
whereas a point wets with `V=c*e^3`. Consequently the old-row normalized
newborn column is **order one**, not order `sqrt(e)`. Both its contribution
to the newborn diagonal and its coupling to all old unknowns must survive.
The previous point limit cannot be substituted here.

The positive augmented factor acts as follows:

```
old factor rows: F_old * J_old(q_old) + F_old[:,0] * B * q_new
new factor rows: F_edge * [d_self; I] * q_new
F_edge.T * F_edge = [[1/2, -b_x, -b_y],
                    [-b_x, 3*b_x^2, 3*b_x*b_y],
                    [-b_y, 3*b_x*b_y, 3*b_y^2]]
```

Each original minimum-edge triangle supplies its own positive factor with
weight `(projected_area / opposite_height) / c`. Point triangles in an
edge-containing polygon are higher order, not discarded from finite geometry.
All original old factors, old source-block preconditioning, both pressure poles,
40-CG limit, 2e-5 residual and 1e-10 contraction/work checks remain. Unit weights
inside the limiting solver provide vector coordinates only; they are not water
volumes or physical-error weights. No minimum depth, dense inverse, eigenvalue
repair, stage update, front force or invented dissipation is introduced.

At fixed old volume/momentum and bounded new physical velocity, the normalized
new momentum tends to zero. The augmented pressure solution nevertheless has a
nonzero new auxiliary component. For each pole, with original old response `z`,
old/new operator block `Q_on`, and augmented response `z_plus`, the stable jump
identity is `Delta E = alpha/2 * (Q_no*z) dot z_plus_new`.
Independent positive-factor energy and contraction verify this identity.

In the manufactured bed-x fixture the limiting jump is
`-0.018383710213832682`, not a height slope. Positive-water calculations converge
to this finite value for zero and nonzero bounded newborn velocity. This makes
energy continuity a distinct front-law requirement: a negative jump alone does
not authorize treating it as physical breaking dissipation.

12 new tests pass, including two axes, two slopes, finite-water energy and
**every** pressure-operator column, old and new auxiliary response, original
positive-factor adjointness, independent small dense test-only solve, zero old
momentum, copy-free original state and invalid/stale/owned/wrong-cone rejection.
Full source and retained energy suite: **451 PASS / 13 retained FAIL**, 158.27 s,
terminal exit 1. Reports:
`tmp/edge-birth-pressure-unit-v1-20260915.xml` and
`tmp/edge-birth-pressure-full-suite-v1-20260915.xml`.
The thirteen failures remain one legacy face/storage representation mismatch,
eight paired-stress nonlinear energy cases and four nonbreaking constant-velocity
energy cases. No gate is relaxed. These edge fixtures are manufactured geometry,
not a new measurement of South Fork. The actual bank's previously recorded 24
immediate receiving regions are point births; this result does not replace that
bank evidence or resolve its activation guard.

## Playable crest tile lookup

Normal entry point remains **South Fork full descent** on
`L_SouthForkAmerican_FullReach`. Troublemaker remains a rapid, not a menu scenario.

The immutable `FRaftSimIndexedBreakingProfile` now also owns a bounded direct
tile table of the same ordered source records used by the existing hash lookup.
It changes lookup only, not the crest evaluator, source order, local/global
height caps, foam, continuous coordinates, tessellation tolerance, cadence,
collision or hydraulic geometry. Sparse rectangles over 65,536 slots retain
the hash path; unsupported profiles retain the original full scan. Owned arrays
remain correct after ordinary copy/move; there are no pointers into another
profile's hash table. The table is rebuilt with each current profile, not a cache
of historical heights.

Native build PASS (59.98 s); the two existing D6 double-to-float warnings remain.
18 native tests PASS / 0 FAIL / 0 not run. The extended full-scan comparison
checks height and foam at 166,388 points, including negative tile boundaries,
nonunit directions, source-order changes, mixed caps, copied profiles and sparse
fallback. Native report: `tmp/dense-breaking-tiles-native-v1-20260915/index.json`.
The strict actual-pair parser has nine passing tests; incomplete, malformed,
repeated-frame, order-sensitive and mismatch evidence cannot promote a result.

Actual South Fork comparison: **64/64 pairs faster**, with exactly matching
height and foam at 3,240,000 source-grid points (206,049 nonzero heights), frames
122–185 after two warm calls. Each pair uses the same current immutable sites.

| Call order | Hash mean | Direct mean |
| --- | ---: | ---: |
| All 64 pairs | 2.067817 ms | 1.535808 ms |
| Hash first | 2.050231 ms | 1.512397 ms |
| Direct first | 2.085403 ms | 1.559219 ms |

The direct path is retained as the normal default. This is approximately 25.7%
less time for the measured grid evaluation, **not** an overall FPS improvement.
Paired timing excludes table construction/copy costs; the ordinary run below
includes those costs. The unchanged hash path remains independently selectable
in `Sample`; `-RaftSimHashedBreakingTiles` selects it for the fine-crest callback.
`-RaftSimBreakingTileAudit=...` is diagnostic only and publishes no sampled arrays.

Pair report: `tmp/south-fork-breaking-tile-pair-v1-20260915.json`, SHA256
`2575f6a699ca0a469290974090b2e04a3fa93e5d41d592318ddce2970c413885`.
Strict analysis: `tmp/south-fork-breaking-tile-analysis-v1-20260915.json`, SHA256
`7adfc5277456fa53284ce8aeb8ffa4b7680d460c89a894128d36adb7b8c8ca9d`.

Fresh ordinary 300-frame capture, no audit switches, 1280×720 D3D12,
Development WindowsEditor, sample rows 120–250: **11.447123 FPS**, mean
87.358194 ms, **p95 98.7482 ms — FAIL** against 30 FPS / 33.333333 ms.
Crest selection averages 11.468687 ms/frame, crest update 21.240092 ms,
surface Tick 56.741892 ms, Refresh 26.120599 ms. These scopes are inclusive and
nested; do not sum them. This short run is slower than the preceding historical
capture and does not establish a causal whole-frame benefit or regression.
It is not sustained, packaged or traversal acceptance.

CSV: `unreal/Saved/Profiling/CSV/south-fork-dense-breaking-default-v1-20260915.csv`,
SHA256 `d017605009457c2125ee5968c7104a71c5e8e4a588140ff02a7f57233317db63`.
Frame report: `tmp/south-fork-dense-breaking-default-performance-v1-20260915.json`,
SHA256 `d0e961aaabf5e5612ca8b4357c9b441fa3a759b4bb672c3cf2988efa4b580e48`.
The frame parser exits successfully when it records a valid report; its explicit
`frame_p95_within_target_budget=false` is the performance verdict.

Fresh normal-scenario capture:
`unreal/Saved/VideoCaptures/RaftSim_20260915-022258.mp4`, 60 source frames over
6.109 seconds. The encoder's 30 Hz output/repeats are not measured game FPS.
The three actual screenshots
`unreal/Saved/Screenshots/south-fork-dense-breaking-motion-v1-20260915_000.png`
through `_002.png` were inspected in sequence. The raft advances across the
foreground; water remains a broad smooth green face with merged white bands and
large rounded froth patches, beside visibly angular/blocky rock flanks. The
first frame also shows transient dark foliage patches absent in later frames.
This is **not convincing breaking/froth/reference acceptance**. The optimization
was not intended to change those visuals. This turn inspected the still sequence,
not the full encoded motion against newly reopened reference videos; that
qualification remains open.

Capture SHA256: video
`96bf48d3db3c4ecc223dc14fa4a3fabe951316d085f589a94fa2d2240dd2a506`;
screenshots 000/001/002 respectively
`1cbab3b7469c4af2a32fbc9c267f17ab44cc36a9444ecef56e6c80c4a2a45283`,
`c07f7fb34ab301c1350840758e1b4f29d127b9d731bc3854a083ab6111a9e151`,
`de931a3debb4adf3d3fd3b041eb75e1383631c82877836ee94c01a63dd990ff5`.

All 464 protected source/terrain/capture/actor hashes remain unchanged. Tested
Raft DLL SHA256:
`e932e71532c9160980a6b514a81024700cbc2ef9087b370b87a657136cb4a401`.
Native report SHA256:
`a69a6f176fea0c3b41050bc371e2b1a297028c7595dc0f4b687d17eae80b8050`.
Build, Python tests, native tests, paired run, ordinary run and recording jobs
are terminal. Generated captures/reports/build outputs remain ignored.

## Remaining work

Edge/point limits are not full front force/impulse laws. Complete flat and coupled
mixed births, one-sided/unequal front transport, compatible physical work and
finite time/open-boundary evolution before native solver promotion. Continue
actual single-surface shape/froth/reference and 30 FPS qualification, then
Colorado, Pacuare, Futaleufu, Chilko/Zambezi/all-scene water, crew fit/animation,
normalization, outstanding regressions and release. No diagnostic pass closes
these requirements.
