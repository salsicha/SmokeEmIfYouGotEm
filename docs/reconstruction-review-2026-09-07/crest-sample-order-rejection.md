# Exact crest sample order: rejected timing candidate

Recorded 2026-09-17 UTC. This pass does not accept scene realism or 30 FPS.

## Experiment and decision

Adaptive selection is the larger measured crest cost: the last ordinary
capture spends 3.602291 ms per frame, 7.326008 ms per active selection frame.
This experiment tried the three interior quarter-barycentric samples before
the nine edge samples. It retained all twelve positions, arithmetic, strict
0.5 cm threshold, three refinement levels, current profile epochs and canonical
memo bindings. It changed neither heights nor detail resolution. The previously
rejected range-limit candidate was inspected and not repeated.

The isolated gameplay module compiles and links. Eight renderer-backed native
tests pass with zero test warnings/errors, including the sample-order fixture.
That fixture covers changing XY/profile/detail windows, serial and parallel
evaluation, memo reuse and alternating evaluation order. Every quarter sample
is also tested as the only failing sample, below/at/above the original threshold.
The build retains the existing C4701 warning in DetailSourceFootprintTest.cpp;
this is not a warning-clean compilation.

Actual South Fork comparison: all 64 alternating-order pairs, frames124-190,
preserve ordered parents, triangles, cell ownership, expanded coordinates and
production topology across 4,296,459 vertices and 3,110,396 triangles.

| Execution order | Reference mean ms | Candidate mean ms | Candidate faster |
| --- | ---: | ---: | ---: |
| All | 8.154605 | 8.071669 | 40/64 |
| Reference first | 8.205100 | 8.384544 | 13/32 |
| Candidate first | 8.104109 | 7.758794 | 27/32 |

The candidate fails the unchanged both-orders-faster requirement. It is
**rejected**, not promoted on the slightly better combined mean. Candidate
runtime code, opt-in flag, audit hook and native candidate test are archived in
`tmp/crest-sample-order-v1-20260917/RejectedSources` and removed from production.
The two edited production files have zero diff against the previous commit.
Do not rerun the same candidate merely to find favorable noise.

The retained Python report validator requires64 original numbered pairs,
strictly increasing post-warmup frame numbers, alternating boolean call-order
flags, positive integer mesh counts and finite positive timings. Missing,
duplicate, malformed, mismatching and order-sensitive evidence cannot pass.
New and existing audit/process checks: **37 PASS**. The initial invocation
lacked the repository's test-dependency PYTHONPATH and did not run; the reported
pass uses the existing dependency directories, without installing packages.

## Reproducible evidence and isolation

- Candidate DLL: `tmp/crest-sample-order-v1-20260917/UnrealEditor-RaftSimRaft.dll`,
  SHA256 `8f8b57889e6ec7cbdedd4609bab7db2e2d75a9fe475bea85513e50f388b90d79`.
- Native report: `tmp/crest-sample-order-native-v1-20260917/index.json`,
  SHA256 `ab8e4d3a855610c5dedde972a95c9798ff55dfad0da13b0388bad956b2096d75`.
- Actual pairs: `tmp/south-fork-crest-sample-order-pair-v1-20260917-pairs.json`,
  SHA256 `198ac39fafb7e410a53f0d229ca59a3fcd354cfe282ccecf3c0d9ebc21a11ccb`.
- Strict summary: same prefix with `-summary.json`; exact=true,
  measured_both_orders_faster=false, release_accepted=false.
- Python report: `tmp/crest-sample-order-audit-tests-v1-20260917.xml`,
  SHA256 `c7e088208936ddc287313770e253ef12c372c1272e27dae3f4f15d185508565c`.

Native session16681 and actual-play session27979 terminate successfully. Before
the timing capture, exact PID/start/executable/command-line identities and all63
frozen shader hashes were checked. Original cook36872, editor36412, workers32072
and37836, and standalone compiler37212 were suspended with retained handles.
All suspend/resume status codes are zero, all five CPU counters stay unchanged
during capture, and subsequent live CPU advancement confirms resumption.
The original shader sources and installed gameplay/project DLL hashes remain
unchanged. No asset/map regeneration, installation, lower-detail default or
ordinary FPS claim accompanies this diagnostic capture.

## Fresh production transport compilation: qualified standalone

Original session26355 is now terminal0. Its compiler37212 completed all six
transport phases from the unchanged frozen production shaders, using model3
read directly from the original fixture header. The immediately following
combined suite passes **54 tests, zero failures/errors/skips**, in102.43s:
transport, coupled pressure, portable represented-float arithmetic and resource
bindings. The original18-case fixtures pass on actual hardware and WARP, using
the previously qualified production pressure bytecode. Force, residual,
diagnostic, iteration and dispatch-order gates are unchanged. No CPU pressure
injection or changed expected values were introduced.

This independently closes the fresh-transport rebuild check that the preceding
wrong-model run failed. It does not convert standalone coupled fixtures into a
full RK2, native-engine, physical wet-front, scene or performance pass.

- JUnit: `tmp/sm5-production-unscaled-regression-v2-20260917.xml`,
  SHA256 `7d27cae5e5ce30642ff7864a13467fc11a699e271ce009ac5dc6c99bfdeb7330`.
- Original fixture: `tmp/south-fork-unscaled-transport-fixtures-v1-20260914.bin`,
  unchanged SHA256 `4c81f24988e743529033eae53cb74252c49040ccf3e2c52d5f6686d994702d9e`.
- Fresh six-phase output: `tmp/sm5-transport-production-unscaled-v2-20260917`.
- Compile process witness: same prefix with `-process.json`, preserves fixture
  version3,18 cases and63 frozen shader inputs; its accepted=false field describes
  the pre-test launch witness, not a substituted test outcome.

| Phase | Fresh CSO SHA256 |
| --- | --- |
| 0 | `e2f92a28b396e37515d9e149e002093c4151bc8085302767c805394ac4991e02` |
| 1 | `ab9cfb3daa9fb0c9207194a8b6a3c711fc36ed13d1ddae3350b06eb6c50cddf0` |
| 2 | `e79e187eaaa16330cadcdd1739d05f654cd5b5f81605afc4969050170d5ea68d` |
| 3 | `d1dd88ed1160cb00822071fef90b6285b8aadec9f493c85958ff999a84ea4251` |
| 4 | `4d1e7f3cf288510c026df815c9537f76c40672f82d83fa50a70b21005da769ef` |
| 5 | `a117f06a68e686bb00119781e9d13f9c49e485a1d593f80d556f8bfaf7b7a3f4` |

Original native33-test replay55459/editor36412 and workers32072/37836 are still
LIVE with advancing CPU and unchanged start identities. All63 shader input
hashes match. Its long FXC compilation is not a terminal failure; preserve that
run. Future capture wrappers must no longer expect compiler37212 to be live.

## Hydraulic continuation

Same original continuation51728/PID36872 reaches2100s/local6000. Both state and
86,720 exact-dry artificial-bank audits PASS on all5,382,400 cells. Maximum
depth4.2956862140m, speed7.3053801942m/s, volume2,982,099.352960332m3 and maximum
step conservation residual1.5158152511e-8m3. Outflow96.1588226602m3/s still exceeds
inflow45.3069545472m3/s. **Not settled**, calibrated, promoted or map-integrated.

- State: `tmp/control-ablation-2100s-state-v1-20260917.json`,
  SHA256 `f5486f5c71729bc71e441ff71b191a084ca3c2c59dc0d34416768202d231b1f1`.
- Banks: `tmp/control-ablation-2100s-banks-v1-20260917.json`,
  SHA256 `fe7b828136cc97d523d8d0b08ab17105d6532864559d2db170399e79bc8cdfd6`.

Next2150/local7000 needs BOTH audits after its complete marker. Preserve the
same run. Full physical wet-front coupling, terrain/boulder/collision fidelity,
convincing crest/froth motion, ordinary30FPS, later river sequence, all-scene
water, crew and release acceptance remain open. Troublemaker remains a rapid
inside South Fork, never its own menu scenario.
