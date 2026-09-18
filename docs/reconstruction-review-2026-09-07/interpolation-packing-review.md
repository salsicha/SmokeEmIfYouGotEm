# Water interpolation/packing trial: not promoted

2026-09-18. Commit `88b6f9fe5` combined the evolving rendered-field blend and
source-vertex packing into one opt-in pass. It retained the original arithmetic,
normal normalization, color conversion, all UVs/tangents, foam-transport fallback,
rendered history and publication cadence. No fidelity, physics or acceptance
threshold was changed. The default path was never switched to this candidate.

## Actual gameplay evidence

Two independent FullReach captures at the normal South Fork review launch each
collected 64 alternating same-input pairs after two warmups. Both compare all
five floating-point rendered fields and every packed attribute, then compare
against the actual published attributes. All 128 pairs are exact, covering
6,480,000 source vertices. The first capture uses ordinary separate production;
the second explicitly enables the fused candidate. Diagnostic output is never
published; input copies and equality checks are outside the timed regions.

Mean component times in milliseconds:

| Capture / order | Separate | Fused |
| --- | ---: | ---: |
| A / separate first | 3.136687 | 2.870287 |
| A / fused first | 3.021382 | 3.290625 |
| B / separate first | 3.366362 | 2.747616 |
| B / fused first | 2.958409 | 2.903078 |

Capture A loses the fused-first order. Capture B passes both order means, but
does not erase A. This is an inconsistent/order-dependent result, not a qualified
repeatable improvement. The trial implementation, its opt-in flag and its native
test are removed; the original actor source is restored exactly to `cfc513150`.
The experiment remains recoverable in Git. The strict report reader and its
negative controls remain to verify preserved evidence, not as gameplay code.

Paired reports:

- `tmp/south-fork-interpolation-pair-a-v1-20260918-pairs.json`, SHA256
  `361f21858b2bfe27d96ea19d9878deb3852ce288ce138e5f867e951afa37728c`.
- `tmp/south-fork-interpolation-pair-b-v1-20260918-pairs.json`, SHA256
  `3fec4631054ec6e1f0316825c4bae660927e1281f5b1132449e762dda8f1281f`.
- Analysis: `tmp/interpolation-packing-pair-{a,b}-analysis-v1-20260918.json`.

The exact owned cook32728 and pressure audit17228 were suspended by retained
handles during each measurement, with executable/start-time identity checked
and successful resume in finally blocks. Their CPU totals did not advance while
suspended. Isolation records are the two capture process reports under
`unreal/Saved/RaftSimValidation/` and matching `tmp/*-pressure-isolation.json`.
No job was restarted. Diagnostic CSV timings include paired audit overhead and
are not ordinary FPS evidence.

## Validation and limits

The candidate editor build and two native tests passed before its commit.
The independent original-arithmetic native test covered carried histories,
50,625-vertex arrays, supplied/fallback transport and invalid-input rejection.
37 initial report-reader tests passed; expanded report/shoreline/runtime-contract
and frame-auditor checks pass 94 tests with no skips or waived gates. Record:
`tmp/interpolation-packing-restored-python-v1-20260918.xml`.

The restored editor build succeeds and eight native D3D12 checks pass: source
packing, exact/moving shoreline caches, fine crests, shoreline geometry and actor
surface, committed foam evolution and directional foam sourcing. Records:
`tmp/interpolation-packing-restored-build-v1-20260918.log` and
`tmp/interpolation-packing-restored-native-v1-20260918/index.json`.
The final ordinary, audit-free capture averages28.171491 FPS, with frame
p9543.1591ms: FAIL30. This is1280x720 D3D12,300 CSV rows and the unchanged
inclusive60..240 measurement interval. The cook was suspended/resumed correctly;
the original pressure audit and independent verifier had already finished.
Record: `tmp/interpolation-packing-restored-profile-v1-20260918.json`; CSV SHA256
`28b320d1b026e14a05866d536cb9ed5f2136babeccf081d7c0a39d9934f39ce7`.
This is not a controlled comparison against earlier ordinary runs, nor sustained,
packaged or full-traversal qualification. No new visual or physical acceptance.
The unchanged target remains 30 FPS with frame p95 at most33.333333ms, alongside
the full geometry/physics/appearance gates. Troublemaker remains a rapid within
South Fork, not a scenario. The source-driven smooth faces and unconvincing froth
still require the coupled water/geometry work; this failed optimization does not
resolve them. Continue the ordered full scene, crew and release scope.
