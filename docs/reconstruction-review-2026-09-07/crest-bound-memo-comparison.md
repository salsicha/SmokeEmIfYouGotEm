# Exact-coordinate binding cache: not promoted

September 15, 2026. This is an opt-in diagnostic candidate, not a gameplay
performance or visual acceptance result. Default gameplay is unchanged.

`-RaftSimBoundCrestMemo` enables per-triangle exact-coordinate lookup bindings.
Every reused binding checks the full coordinate; sampled heights expire every
profile epoch. The existing 4096-coordinate cap invalidates all bindings before
indices are recycled. Mesh detail, selection tolerance and update cadence are
unchanged. `-RaftSimCrestBoundMemoAudit=<fresh report path>` compares isolated
candidate/control builds on actual changed inputs without publishing either.

The 64-pair live audit used the source-matched landward 50-second preview in the
existing South Fork scenario. Ordered topology and expanded coordinates match
exactly across 4,114,511 compared vertices and 2,673,532 triangles, frames
122 through 185. Two warmups precede the alternating execution orders.

| Execution order | Control mean ms | Candidate mean ms |
| --- | ---: | ---: |
| All 64 pairs | 12.848494 | 13.287992 |
| Control first, 32 pairs | 12.704425 | 13.193391 |
| Candidate first, 32 pairs | 12.992562 | 13.382594 |

The candidate is slower in BOTH orders and wins only 20 of 64 individual pairs.
Maximum retained allocation rises from 45,100,304 to 119,255,060 bytes. It remains
DISABLED by default. The summarizer intentionally returns exit code 1 because
performance qualification failed; this is not a parser or infrastructure error.
The concurrent hydraulic cook also precludes ordinary gameplay FPS acceptance.

Local regenerable evidence (already excluded by `.gitignore`):

- Capture: `tmp/bound-memo-live-pairs-v1-20260915.json`, SHA256
  `cff45070a3ea5ce3baddbc3417da7bc68ca35c2568fcbaf946e2d3ade8c537cf`.
- Summary: `tmp/bound-memo-live-summary-v1-20260915.json`.
- Native report: `tmp/bound-memo-native-v1-20260915/index.json`, nine passed,
  zero failed or skipped. Coverage includes epoch freshness, exact coordinates,
  capacity reset, batch changes, moving windows, holes and ordered refinement.
- Targeted bound/range/inline audit Python tests: 39 passed on commit review.

Last uncontended gameplay remains 24.225877 FPS / p95 47.78 ms, failing the
30 FPS / 33.333333 ms target. No terrain, breaking-wave, froth, traversal or
release acceptance is implied by these exactness tests.
