# Normal-river wet-edge distance sweep — September 15

The normal Cartesian surface now selects an exact two-pass wet-edge distance
transform instead of its queue traversal. This is a CPU implementation change,
not new wave/foam geometry or physical/visual acceptance. South Fork remains
the scenario; Troublemaker remains a rapid within the full descent.

## Actual-input qualification

Normal entry: `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`,
`-RaftSimScenario=south_fork_full_descent`, review station 8330.
Both actual consumers use the same helper: shore displacement damping and
rendered-terrain probe-band selection. No distance threshold, wet mask,
terrain-probe budget, refinement tolerance, solver step or source is changed.
The old queue remains available with `-RaftSimReferenceWetEdges`.

The original seeds are all dry cells, wet cells touching dry cells in any of
eight directions, and all four grid boundaries. Propagation is through every
cell, not an obstacle-restricted route. Both algorithms compute the minimum
integer Chebyshev distance to that identical seed set. The sweep removes the
queue, repeated queue-index division and full neighbor expansion; it does not
truncate distances to a narrow band or retain results across wet-mask changes.

Actual paired report:
`tmp/south-fork-wet-edge-sweep-pair-v2-20260915.json`,
SHA256 `1ec76cd084fa4540d6d79a60e910e12b7e3097580967294c320c7f72dd6cc9e0`.
Analysis: `tmp/south-fork-wet-edge-sweep-analysis-v2-20260915.json`.
The 720-frame process completed with exit 0. Four warm calls precede 64
comparisons sampled every 16 engine frames, frames 152–648. It compares
3,240,000 integer distances exactly across 19 distinct input-mask checksums.
Both consumers get both call orders; all 64 comparisons favor the sweep.

| Actual consumer / order | Queue mean ms | Sweep mean ms |
| --- | ---: | ---: |
| All | 2.030311 | 0.747100 |
| Shore damping, queue first | 1.906931 | 0.772093 |
| Shore damping, sweep first | 2.055306 | 0.683794 |
| Terrain band, queue first | 2.043243 | 0.720075 |
| Terrain band, sweep first | 2.115763 | 0.812437 |

These are per-call CPU costs, not whole-frame gains. The paired CSV contains
additional diagnostic work and must not be reported as ordinary game FPS.

Retained insufficient first capture:
`tmp/south-fork-wet-edge-sweep-pair-v1-20260915.json`.
Its 64 exact comparisons covered frames 122–153 but just one mask. Mean queue
1.941052 ms versus sweep 0.718533 ms did not qualify it: the strict validator
rejected the unchanged input. The subsequent longer capture, not a relaxed
validator, supplies the changing-mask evidence.

## Other candidates rejected

Two previously committed candidates remain disabled by default:

- Strong edge hash: actual 64 pairs / 4,299,553 compared vertices and
  3,116,398 triangles exact, but 10.548775 ms original versus 10.659535 ms
  candidate. It also loses when called first. Assembly alone is
  1.435647 versus 1.522197 ms. Report
  `tmp/south-fork-crest-edge-hash-pair-v1-20260915.json`,
  SHA256 `617a0b671dae565f63c88f5f13f0cccc1fde93abfb4e41e95586b03a6e0fe10d`.
- Level-local sampling maps: actual 64 pairs / 4,299,525 compared vertices and
  3,116,344 triangles exact, but 11.852867 ms shared versus 12.258292 ms
  level-local. Called first, the candidate averages 12.996881 ms versus
  11.958862 ms shared. Peak retained allocation grows from 51,836,416 to
  85,790,256 bytes. Report
  `tmp/south-fork-crest-level-memo-pair-v1-20260915.json`,
  SHA256 `c2462f98a20d612893715b77bd49132ea87a79d9fc26f03e767b6f0da466eea4`.

No promotion or whole-frame gain is claimed for either rejected candidate.

## Verification and remaining work

Candidate build and 24 targeted native tests passed. The new distance test
compares 1,417,368 exact integer distances: exhaustive masks on grids up to
4×4, independent nearest-seed geometric distances, changing asymmetric
larger grids, internal holes, and full-size all-wet/all-dry controls.
The tests also retain current-oriented relief, Cartesian boulder/surface,
shoreline, crest, conforming-carrier and GPU-bound coverage.
Report: `tmp/wet-edge-sweep-native-v1-20260915/index.json`.
After promotion, the final Development Editor build succeeded (13 actions,
53.64 seconds) and the same 24 native tests passed again, now also testing
default/control selection on every distance case. Final report:
`tmp/wet-edge-sweep-default-native-v1-20260915/index.json`,
SHA256 `048142e42633b1a52c65f285eb470c4837fd18bec5f16db081beeda20f25144b`.
The rebuilt Raft module SHA256 is
`544c92734696fb7b8d515b59f65688d32e19eca8022707989f742c33b851e64a`;
Water module:
`9c2e0743fa3fe9f90d02902532b82c561ceda2fbda0a8cb47b8da0cc6f342935`.
Strict Python report suites: 44 PASS, zero failures
(`tmp/wet-edge-and-crest-parser-v1-20260915.xml`).

Fresh protected-file verification reads all 464 original source/actor hashes:
zero mismatches. The water material remains the restored original
`44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.
An initial hash-check command mishandled absolute paths and was invalid; its
printed counter was not accepted. A fail-fast rooted-path-aware rerun read
and verified every file. No assets or source geometry were edited.

The earlier stage-instrumented baseline
`tmp/south-fork-surface-stage-v1-20260915.log` identifies refresh mean
26.015096 ms (frames 120–250), including foam/core publication 7.439334 ms,
shore/wake preparation 2.913792 ms and base vertices 2.840036 ms. These
non-overlapping marks within refresh are not additive with inclusive CSV
parents or other threads. The new sweep addresses two calls inside that work;
large crest-selection, surface publication and solver costs remain.

## Ordinary default frame check

Fresh 300-frame game run, no paired audit or stage-logging flags:
`tmp/south-fork-wet-edge-sweep-default-performance-v1-20260915.json`.
Original CSV:
`unreal/Saved/Profiling/CSV/south-fork-wet-edge-sweep-default-v1-20260915.csv`,
SHA256 `bf5f7e1c46525db61fd0a5b91f3172915cb28feb145fa0891f91b1a5f412f113`.
Rows 120–250 inclusive, 1280×720 D3D12, Development WindowsEditor:
13.420531 FPS, mean frame 74.512698 ms, p95 89.9936 ms.
**FAILS 30 FPS / p95 33.333333 ms.**
Inclusive mean surface tick 46.519217 ms contains refresh 20.062835 ms;
crest selection 9.666710 ms belongs inside publication, and solver step
17.112569 ms is separate. Do not sum nested or overlapping thread scopes.
This short run is not sustained or packaged acceptance, and comparison to an
older build/trajectory is not a controlled attribution of whole-frame gains.

## Fresh actual motion inspection

Normal default `RaftSim.CaptureSeries 12 3 1
south-fork-wet-edge-sweep-motion-v1-20260915 shore_left record` completed.
The game, capture and all owned build/test processes are terminal.
Recording: `unreal/Saved/VideoCaptures/RaftSim_20260915-093525.mp4`,
SHA256 `fdb2e5ad2b35dd3612a23cef99ce5568211d9fd37cae03a817fd7f214431ca76`.
Engine reports 64 source frames over 6.150 seconds; the complete clip decodes
184 frames through PTS 6.1 seconds. The encoder's 30 Hz timestamps may repeat
source frames and are NOT game FPS. Analysis and unmodified extracted frames:
`tmp/wet-edge-sweep-motion-decode-v1-20260915/`.

Inspected the original still
`unreal/Saved/Screenshots/south-fork-wet-edge-sweep-motion-v1-20260915_001.png`
(SHA256 `26040b498152e2d4e4197257805442f850a0cd9f4a24aea15fbb5529938a25bc`)
and the actual decoded 3 s / 5 s frames. The raft moves downstream and leaves
the foreground; broad white froth bands and excessively smooth green water
faces persist around the rocky drop. They are not visually accepted. This
turn's CPU change supplies no new geometric/optical detail and no claim of a
fresh calibrated reference match. Complete decoding is not watching every
frame; image-change metrics do not measure physical velocity or amplitudes.
Final post-capture hash check again verifies all 464 protected files unchanged.

Breaking-surface/froth deformation, source-front forces/transport, consistent
ground contact, actual sustained 30 FPS, full reference-motion acceptance,
Colorado → Pacuare → Futaleufu, remaining all-scene water, crew,
normalization, the retained regressions and release checks remain OPEN.
No physics gate or visual criterion is waived by this exact CPU change.
