# Playable crest midpoint dependency scheduling — September 14

Desktop target remains 30 FPS / p95 33.333 ms. Physics stays at 120 Hz.
This is an exact-attribute scheduling optimization, not new crest geometry,
wave physics, froth detail, or a visual acceptance result.

## Implementation and checks

`FRaftSimCrestMidpointExpansion` partitions the existing ordered midpoint parents
into contiguous independent bands. Each band joins before its descendants read
it. The actual South Fork workloads below contain three bands. Every node uses
the original arithmetic, including normal/tangent normalization and color
quantization. Cache invalidation compares source count and the complete parent
array; no evolving coordinates/heights are cached. History and reconstruction
selection remain unchanged. Invalid parent indices fail rather than inventing
geometry.

Build 35118 succeeded (286.61 s). Native test process 83195 exited successfully:
all five tests passed in 0.687349 s, including CrestMidpointExpansion,
CrestHistory, ShorelineCompactUpload, ShorelineCrestTargetCache, ShorelineFineCrest.
The new test independently checks 112,212 complete vertex attribute sets over
20 changing, dependent, regrouped, cropped, empty and reset frames. Comparison
is bit-exact for each attribute, excluding unobservable struct padding.
Timing-parser and desktop-budget suite: 19 passed in 0.64 s.

## Paired actual South Fork inputs

Direct offscreen Unreal game runs use the full playable South Fork map, scenario
`south_fork_full_descent`, review station 8330, 1280x720, 300 CSV frames.
The original five long research/cook jobs remain running; no profiler-wrapper
suspension or restart. These are shared-load measurements. Audit runs execute
both implementations and therefore cannot establish ordinary-game FPS.

The audit retains every engine frame 120–250 inclusive, including additional
calls in the same frame. It alternates which implementation executes first,
includes candidate plan lookup/rebuild and joins, and compares all output
attributes. Source-prefix copying and the audit comparison are outside the
timed region for both variants. No missing-frame or zero-work acceptance.

First run, process 77394, terminal exit 0:

- Report: `tmp/south-fork-crest-midpoint-paired-v1-20260914.json`.
- Log SHA-256: `a7a40d9d31f931f6213d14794b945bccbb7c54b6c5036c05e08daa543ac6fb8e`.
- 131 frames / 132 calls; 8,870,623 exact vertex attribute sets;
  2,000,173 midpoint evaluations per variant.
- Mean serial 1.115468 ms; parallel 0.390729 ms; benefit 0.724739 ms/call.
- Per-call p95: serial 1.362398 ms; parallel 0.539102 ms.
- Mean benefit by serial-first / parallel-first: 0.719934 / 0.729691 ms.
- Mean per-frame serial 1.123983 ms; parallel 0.393712 ms.

Repeat run, process 47389, terminal exit 0, with candidate vertices supplied to
the playable mesh:

- Report: `tmp/south-fork-crest-midpoint-paired-v2-20260914.json`.
- Log SHA-256: `9beade64d2f7e92115a572c54aefd92d772986370ffccfa2e89172253a2c5f57`.
- 131 frames / 132 calls; 8,871,203 exact vertex attribute sets;
  2,000,671 midpoint evaluations per variant.
- Mean serial 1.107748 ms; parallel 0.398329 ms; benefit 0.709419 ms/call.
- Per-call p95: serial 1.332700 ms; parallel 0.563800 ms.
- Mean benefit by serial-first / parallel-first: 0.692276 / 0.726563 ms.
- Mean per-frame serial 1.116204 ms; parallel 0.401369 ms.

Both CSVs have all 300 samples and valid completed footers, independently
audited in `tmp/south-fork-crest-midpoint-paired-csv-v1-20260914.json`.
Their doubled expansion and attribute-comparison overhead must not be labeled
ordinary-play performance.

Decision: enable parallel midpoint scheduling by default. Both full repeats
show substantial benefit in both call orders and better p95 and maximum costs,
without changing rendered attributes. `-RaftSimSerialCrestMidpoints` retains
the original path for regression comparison. The audit now allocates its
candidate output and copies only the initialized source prefix, rather than
copying the not-yet-expanded suffix; both timers still exclude this copy.
Default-path build 25566 succeeded in 258.90 s. Native process 67503 exited 0:
all seven requested tests passed in 0.815935 s (the same five crest tests plus
M6.CareerCatalog and M6.ProgressionMigration). Thus the rebuilt ordinary path
retains the catalog rule excluding Troublemaker as a standalone scenario and
the old-selection migration to South Fork. Final Python suite includes release
checks: 36 passed in 1.20 s.

## Ordinary default-path result

Process 58264 exited 0. No midpoint audit or explicit parallel flag was used.
All 300 CSV samples and footer pass the strict audit; analysis retains rows
120–250 inclusive. Report:
`tmp/south-fork-crest-midpoint-default-normal-v1-20260914.json`.
CSV SHA-256: `8c9f94e8d751f4b360d262f99d5031f577a03b547d33caf3deea5761344fbed0`.

Measured 9.345596 FPS, frame p95 128.5814 ms: **30 FPS target FAIL**.
Mean game thread 106.273352 ms; GPU 36.666179 ms. Inclusive water tick
70.561233 ms, crest update 27.299807 ms, selection 14.422872 ms. These nested
scopes must not be added. This remains a shared-load development capture,
not an isolated or sustained release qualification. It does not replace the
earlier isolated 18.899245 FPS / p95 70.33 ms failure or establish an aggregate
frame-rate improvement from the midpoint change alone. The paired evidence
above establishes the local scheduling gain.

All five original long jobs remain directly LIVE. Frozen observer/candidate
dependencies remain exact (417/422 hashes). COMPLETE8600/local12000 cook
passed both state and artificial-bank audits; still unsettled. Next completed
8700/local14000 requires both audits. No solver candidate is promoted here.

Next performance work should address the larger remaining crest selection and
water-refresh/publish costs, with exact same-input comparisons and full-frame
measurement. Wave/froth/contact visual failures and physical qualification
remain separate open work. No 30 FPS, appearance, physics, full-river traversal
or project acceptance is implied.
