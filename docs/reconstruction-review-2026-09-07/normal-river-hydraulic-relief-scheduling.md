# Normal playable hydraulic-relief scheduling — September 15

This is a qualified CPU scheduling change to the existing playable water, not
new waves, source physics, visual acceptance, or achievement of 30 FPS.

## Implementation and actual-state comparison

The flow-aligned four-sample hydraulic-relief loop now executes independently
per vertex, joining before shoreline weighting and subsequent surface work.
The original direction, sample coordinates, wet-neighbor rejection, arithmetic,
and relief function are unchanged. Inputs are immutable during the parallel
pass; each worker writes only its own output. There is no shared accumulation,
memoization, stale state, smaller stencil, or reduced frequency. Non-Cartesian
water keeps its original implementation. `RaftSimSerialHydraulicRelief` selects
serial scheduling for diagnosis; normal play uses the verified parallel path.

The original-loop native oracle compares 35,916 float values over changing
directions, zero currents, dry holes, boundaries, strides and invalid neighbor
samples, with bit-exact serial and parallel results. The helper also rejects
invalid input dimensions without modifying output.

On the actual South Fork full-descent scenario, station 8330, the opt-in
`RaftSimHydraulicReliefAudit` recorded 64 distinct post-warmup refreshes from
world time 10.05449456 to 15.48923618 seconds. All 3,240,000 vertex comparisons
match bit-for-bit, including the production result. Every refresh has nonzero
relief. Input/output geometry and clocks are not advanced between paired calls.
The audit alternates call order, includes output initialization, and never
substitutes its diagnostic arrays into gameplay.

| Call order | Pairs | Serial mean ms | Parallel mean ms |
| --- | ---: | ---: | ---: |
| All | 64 | 2.004799 | 1.501256 |
| Serial first | 32 | 1.975475 | 1.563509 |
| Parallel first | 32 | 2.034122 | 1.439003 |

Parallel is faster in 53/64 pairs and in both order-group means. This supports
the scheduling default, not a general CPU/platform benchmark or total FPS gain.
`audit_hydraulic_relief_pair.py` rejects missing pairs, invalid or empty counts,
nonfinite timings, nonalternating order, and repeated/pre-warmup refreshes. It
reports exactness and timing separately and never grants release acceptance.

## Final verification and retained failures

- Final editor build succeeded. The first build caught an unsupported Unreal
  numeric-limits infinity API in the new test; standard C++ limits fixed it.
- Final rendered `RaftSim.M4.Cartesian` group: **5 PASS, 0 FAIL**, including
  boulder surface, scheduling, shoreline geometry, shoreline surface and grid.
  An earlier NullRHI invocation was **4 PASS, 1 FAIL**: the shoreline-surface
  test requires a real rendering proxy. That failed run remains recorded;
  the test and its rendering assertion were not weakened or skipped.
- Python paired-evidence and CSV regressions: **11 PASS**. The added relief CSV
  scope is optional in historical captures; absence is not zero cost. The
  original frame-time and duplicate-header gates remain intact.
- All **464 protected scene/source/capture/profile/actor hashes unchanged**.
  No terrain, material, geometry, contact tolerance, water state, or physics
  timestep was changed. Captured versus inferred geometry remains as before.

Ordinary final-default gameplay, with no paired audit or stage-log diagnostic,
recorded 300 frames at 1280×720, D3D12, Development/WindowsEditor. Rows 120–250:
**12.257837 FPS**, mean frame **81.580464 ms**, p95 **98.2909 ms** — **FAIL 30 FPS**.
The relief scope averages 1.454073 ms on active refreshes. Larger inclusive
costs remain: crest selection 11.130556 ms/frame, water step 16.909922 ms/frame,
and refresh 25.176972 ms/frame. These overlap/nest; do not sum them.

The fresh pre-change stage-logging run is diagnostic, not an ordinary paired
frame comparison. A subsequent same-build serial control completed, but its
CSV has duplicate `LightCount/UpdatedShadowMaps` and `ShadowCacheUsageMB`
headers. The strict parser rejected it; no accepted serial frame summary was
created. No overall FPS improvement or regression is inferred from these
different captures or from the older 20.80 FPS measurement.

## Evidence locations

All temporary/generated output stays ignored, not committed:

- `tmp/south-fork-hydraulic-relief-pair-v1-20260915.json`, SHA256
  `fa1ac30fc6db39346a54f9000399cce617896ba70fa911343daa80afa03784f1`.
- `tmp/south-fork-hydraulic-relief-analysis-v1-20260915.json`, SHA256
  `aca0569d7a1b2f2a38f6c124f381c196b8f31b75bc50eaf94c39a2f64e7a45c2`.
- `tmp/hydraulic-relief-native-v1-20260915/index.json`: initial isolated native PASS.
- `tmp/hydraulic-relief-cartesian-v1-20260915/index.json`: retained NullRHI failure.
- `tmp/hydraulic-relief-cartesian-rendered-v1-20260915/index.json`: final rendered group.
- `tmp/hydraulic-relief-audits-v1-20260915.xml`: 11 Python tests.
- `unreal/Saved/Profiling/CSV/south-fork-hydraulic-relief-default-v1-20260915.csv`,
  SHA256 `7a420e806b26bcb1afb6816ed0c303871fa71a133b7fe21c785226f9b2a170a9`.
- `tmp/south-fork-hydraulic-relief-performance-v1-20260915.json`, SHA256
  `92342fc8745089403c60fff3e719cb9936deb0a5c904064a2fce1171e44b923c`.
- `unreal/Saved/Profiling/CSV/south-fork-hydraulic-relief-serial-v1-20260915.csv`:
  completed but rejected duplicate-header control, not accepted measurements.
- Final `unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll`,
  SHA256 `3f3d414f26d1a533081fff2abf52d265cf6fdcb172652848bd7011e8eea78878`.

All owned build, test, and profiling processes finished. The full nonlinear
source stage still rejects unowned wet-front activation; its closed time
candidate is not promoted. Next work remains full-metric wet/front/open/native
coupling and the larger playable crest/solver costs, followed by actual motion
and reference comparison. South Fork realism/30 FPS, Colorado, Pacuare,
Futaleufu, Chilko/Zambezi reviews, crew, normalization, regressions and release
remain open. Troublemaker remains a rapid within South Fork, not a menu scenario.
