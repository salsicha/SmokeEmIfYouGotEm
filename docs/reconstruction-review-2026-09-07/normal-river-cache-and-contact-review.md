# Retained cache, completed control cook, and newly observed stranding

September 15 local / September 16 UTC, 2026. South Fork is still incomplete.
Troublemaker remains a rapid within South Fork, never a separate scenario.

## Cache experiments: default remains OFF

The initial coordinate-binding candidate duplicated its sample maps at three
refinement levels. The revised implementation shares one bounded sample table
per worker, with distinct level/triangle bindings. Full-coordinate checks and
per-build profile epochs remain mandatory. A reset invalidates every binding.
The final implementation uses an explicit `TSparseSet` so the sample position
also serves as its hash key, removing the second stored copy. Only insertion,
rehashing and full reset are used; no individual removal or compaction can
invalidate surviving handles. The existing 4096-coordinate cap is unchanged.

Actual changing-input audits retain all 64 pairs and alternate execution order:

| Local report | Control mean ms | Candidate mean ms | Candidate maximum retained bytes | Faster in both orders |
| --- | ---: | ---: | ---: | --- |
| `bound-memo-shared-live-summary-v2-20260915.json` | 13.081679 | 12.861374 | 77,754,172 | Yes |
| `bound-memo-shared-live-summary-v3-20260915.json` | 13.221930 | 13.021010 | 77,778,068 | Yes |
| `bound-memo-sparse-live-summary-v1-20260915.json` | 12.521327 | 12.298927 | 52,785,100 | **No** |

Reports are under ignored `tmp/`. In the final sparse comparison, control-first
means are 12.184406 / 12.366622 ms: the candidate loses that order. Do not use
the favorable overall mean to waive this failure. It stays opt-in through
`-RaftSimBoundCrestMemo`, DISABLED in ordinary play. Retained memory is lower
than the first experiment's 119,255,060 bytes, but still above the final paired
control's 45,105,404 bytes. No ordinary FPS or release acceptance is claimed.

All three comparisons preserve exact ordered parents, triangles, ownership and
expanded coordinates. The candidate-enabled shared v3 run also matches actual
published topology. Capture SHA256 values, in table order:

- `db8f21e800c19a75ec8c05c9ea2b178a163c9a9f2c6ef9316149ef09c70c0a30`
- `2d8497b6d97252943d0796696aa30be04a798244f25748108bd3c6dbf19ea557`
- `5fa685338a953be50527d9f83da72581e1cf0b940d00588130f9f37d01b443ad`

Shared v1 never reached gameplay: an unquoted PowerShell descriptor argument
was split before `.json`. Its refusal log is retained; it is not counted as a
comparison. Correctly quoted v2/v3 and sparse v1 use the unchanged source-matched
50-second descriptor and complete the requested captures. Engine exit 0 alone
was not accepted as evidence. Both editor builds pass (existing D6 double-to-float
warnings remain). Final `tmp/bound-memo-sparse-native-v1-20260915/index.json`:
nine passed, zero failed/skipped/warnings. New checks cover shared-level sample
reuse, changing level counts, stale epochs, growth/rehashing and reset handles.

## Actual playable contact failure: not repaired yet

Inspected the original `bound-memo-shared-live-v3-20260915_001.png` screenshot.
Broad white froth, smooth green faces and jagged inferred rock flanks remain.
The capture is not visual acceptance. The source trace confirms that the moving
detail window receives flow-convergence entrainment combined by max with the
accepted physical spilling-crest source, not the legacy height-only fallback.
No source amount, material, water geometry or contact response was changed.

The longer v3 run reveals more than an appearance problem. At about 20 seconds,
raft speed is 3.335 m/s with no grounded points. Near 30 seconds it is 0.023 m/s
while water speed is 3.725 m/s, with one grounded and one dry support point.
Floor freeboard is 2.210 m. All three subsequent screenshots report station
8363.825 m / lateral -7.814 m, essentially unchanged. The original-control v2
also stalls near the same station, so this is not evidence of a cache regression.
The capture callback changes the camera and requests screenshots; it does not
freeze the raft.

At that stalled sample the logged position is approximately
(-544836, -361565, 942.6) cm; the exact entering tube position and hit owner
are not present in the existing drift log and must be captured before repair.

The current reduced-runtime ground constraint samples six tube points and
translates the WHOLE raft vertically by the largest penetration, then clips
velocity against that one normal. It does not sweep the intervening side face.
This is a plausible mechanism for climbing onto a steep obstacle rather than
responding to its side, not yet proof of the exact contacted triangle. NEXT
capture the entering support point, prior/predicted positions and original
component/triangle/normal; test continuous side contact using the SAME terrain
authority; then replay this descent and verify clearance, energy/motion and
actual traversal. Do not reduce friction, move the rock, disable collision or
declare the stalled raft a traversal pass.

## Original-geometry cook completed; not settled

Session45187/PID32276 finished normally: 12,000 steps, 600 seconds. This remains
the older rock-union geometry, NOT the landward geometry used above. Independent
550- and 600-second audits pass all 5,350,400 cells and keep all 86,720 artificial
bank cells exactly dry. At 600 seconds maximum depth is 4.777406207 m, speed
11.952985593 m/s, and maximum step conservation residual 1.644163272e-8 m3.
Volume is 3,030,834.959811481 m3, 8,756.123494943 m3 above the initial state.
Instantaneous net boundary flow is approximately -8.395445136 m3/s; completion
is NOT settling. No old-state transfer into the landward bed is permitted.

Audits: `tmp/south-fork-rock-union-600s-snapshot-v1-20260915.json` and
`tmp/south-fork-rock-union-600s-banks-v1-20260915.json`. Final h/u/v SHA256:

- `919b2e5670303598066402709c093b43b53c4e7968dc3a93f872048071310f46`
- `216d0cd0c076641a24c0efca33f01a1f4f6a3714b6977ead0b8c4f5bc9cd1624`
- `a29cac3f5e8237068f17db090624ad947fdb7de0264149fa9af629477ee0829a`

Checkpoint preparation now explicitly clears the inherited cold-start claim,
old restart record and old initial extrema while preserving physical inputs.
Focused Python suite: 47 passed (`tmp/shared-memo-restart-tests-v1-20260915.xml`).
An initial invocation omitted the existing local pytest dependency directory;
it executed no tests, and is not counted as a pass.

The newer landward geometry now continues from its OWN 50-second checkpoint:
input `tmp/south-fork-landward-restart50s-input-v1-20260915/manifest.json`, SHA256
`c7b1f796a76b9944abe3725f0d2648bfe6b757a1a33109a2869c9c6bdf71fe73`.
No context, bed, or water inventory is added. The unchanged solver executable
runs 11,000 additional steps toward 600 seconds, saving every 1,000 steps.
Output `tmp/south-fork-landward-cook50to600s-v1-20260915`, LIVE session75302 /
PID2344, started September 15 at 17:29:39 local. The initial native restart
audit `tmp/south-fork-landward-restart50s-native-v1-20260915.json` passes:
5,350,400 h/u/v cells bit-exact, grid/bed/roughness/boundaries unchanged,
clock 49.9999999999993 s unchanged, volume error 1.862645149e-9 m3.
Last observed step 60 / 53 seconds remains finite and within the unchanged
gates. NEXT audit local step 1000 (absolute 100 seconds) only after its complete
marker exists. Do not restart this live process because observation times out.

All 464 protected source/map/save/actor hashes match after the native runs.
Generated inputs, captures, logs, binaries and audit reports remain ignored.

The last uncontended ordinary gameplay result remains 24.225877 FPS / p95
47.78 ms, FAIL against 30 FPS / 33.333333 ms. Terrain/contact/breaking/froth,
settling, 13 physical regressions, Colorado then Pacuare then Futaleufu,
other-scene water, crew, normalization and release remain OPEN.
