# Flow-direction-aware South Fork foam onset

2026-09-17. Installed in the normal South Fork FullReach single-surface runtime,
not an opt-in material or separate rapid scenario. This is a localized optical
source correction, not completed breaking-water, terrain, or scene acceptance.

## Change and physical limits

The generic generator previously added absolute gradient components. A smooth
descending chute, cross-current bank slope, or mutually cancelling relief could
therefore generate foam as if it were a rising wave. South Fork now projects the
combined signed surface gradient onto the current and uses only positive rise.
Both hydraulic axes participate; rotation, reflection, and current speed scaling
do not change the resulting slope. Stationary or nonfinite inputs return zero.

Existing onset thresholds and Froude ramp remain unchanged. Explicit standing
crests, hydraulic features, boulder wakes, accepted spilling crests, pockets and
boils still contribute. Previously transported foam is not removed by this rule.
Foam advection, lifetime, committed clock, geometry, raft support, collision,
material, and solver state/timestep are unchanged. Other maps retain the exact
legacy onset expression. Positive rise is an optical onset proxy, NOT a measured
air-entrainment rate or a dissipative turbulence model.

The normal path is Cartesian single-surface water on
`L_SouthForkAmerican_FullReach`, shared by the South Fork launch entries.
`-RaftSimLegacyGenericFoamSource` is a non-shipping comparison control only.
Troublemaker remains a rapid within South Fork, never a menu scenario.

## Actual source and installed evidence

At committed water time 7.800000407 s, the ordinary run audited the same 10,821
wet vertices with both generic expressions. The generic source sum changed from
263.615591 to 20.453188: 776 vertices decreased and 38 increased (the new rule
also handles the previously omitted base lateral slope). The final source sum,
including other source mechanisms, was 311.103102; the legacy final sum lies
between 489.541330 and 492.023333. These are unitless vertex-source sums, not
foam mass, entrained-air volume, or rendered area. The bound retains ambiguity
when an increased candidate background masks a smaller independent source.

The separately captured legacy control reports identical old/new generic and
final sums, with exactly equal lower/upper bounds, at its own 8.600000449 s
water time. Do not compare these differing-time runs as identical fluid states.
Reports are `tmp/directional-foam-source-{default,legacy}-audit-v1-20260917.json`.
Default SHA256:
`16b1b75f5905194f97fcbeb60ada3d3a4ff8d6b31b9f4a7a41b6265da95d08f9`.

All five gameplay translation units were rebuilt. The first actor build failed
on an incorrect JSON shared-reference call; that error was corrected. One
subsequent invocation used the wrong include working directory and was rerun
from the engine source root. The existing C4701 warning in the full-route
footprint test remains recorded, not treated as a new foam failure.

Native candidate suite: **37 PASS**, zero failures/warnings/not-run tests.
Ordinary installed module without bootstrap: **8 PASS**, covering four clock
tests, directional source, committed foam evolution, native mean smoothing,
and terrain probes. Full focused Python coverage remains 72 PASS. Expanding to
the three older foam-contract files gives **79 PASS / 7 FAIL**; replaying those
files against committed HEAD in memory reproduces the same seven failures
(7 PASS / 7 FAIL). Those older source wiring/hash guards remain open; their
expectations and hashes were not weakened or rewritten here. The thirteen
previously recorded physical-suite failures were not rerun or waived.

Installed DLL SHA256:
`09a1dc5804bdd57a119d8f074af0191282c77f162ddcaecd37ffc6d7110285ef`.
Installed PDB SHA256:
`e74ff5166378b664e9970770e25e188020df84cebe30cbfb8a91dbabdf8a2691`.
Verified original backup: `tmp/directional-foam-installed-backup-v1-20260917/`.
The production water material retains SHA256
`7e0f29aa41787954ef5d2156345a66c4f5d4d507f79985ae0f6a8311c6fb9038`.

## Motion and frame cost

Both ordinary installed default and legacy-rule captures completed with 24
1280x720 PNGs and finalized recordings. Each capture/profile verified exact cook
17516 suspension and successful resumption. No candidate plugin was used.
Capture labels: `south-fork-directional-foam-{default,legacy}-motion-v1-20260917`.

Default recording `RaftSim_20260917-115845.mp4`: 224 source frames / 15.814 s;
all 474 encoded frames decoded through PTS 15.766667 s. SHA256
`13809f49ca881cff9de46aad7a65fd9cb814e91b7a51cdf9ff3a28f76d19974d`.
Legacy recording `RaftSim_20260917-115953.mp4`: 243 source frames / 15.711 s;
all 471 encoded frames decoded through PTS 15.666667 s. SHA256
`0d5d821b978cc2a70945e63c75ab5354b19ad2106a4159a636d5b6c2e46081e6`.
Inspected both original PNG22 captures, default decoded 6/11 s and legacy
decoded 11 s. Broad smooth froth, the abrupt mean face, and rough crew/scene
appearance remain visible. Different trajectories preclude an exact pixel
comparison. Full decoding is not calibrated reference-motion acceptance, and
the encoder's repeated 30 Hz timeline is NOT game FPS.

The previously pending decode of the rejected inline-crest installed trial was
also completed this pass: `RaftSim_20260917-111125.mp4`, all 466 encoded frames
through PTS 15.5 s. Its original SHA256 remains
`806407c002097afa71b9e86c41b88f36f79357e882d070ea2887ebb6f48ff260`;
report: `tmp/inline-physical-installed-decoded-v1-20260917/report.json`.
That trial remains rejected; completing its decode does not alter acceptance.

Recording-free installed ABBA, unchanged 300-frame D3D12 captures, 1280x720,
inclusive CSV rows 60–240 (181 samples):

| Run | Mean FPS | Mean frame ms | p95 frame ms |
| --- | ---: | ---: | ---: |
| Legacy A | 26.978155 | 37.067027 | 46.2135 |
| Default A | 28.287908 | 35.350794 | 39.8540 |
| Default B | 27.489729 | 36.377223 | 41.6582 |
| Legacy B | 29.098613 | 34.365899 | 40.0340 |

The two orders disagree about performance benefit. No repeatable speedup or
absence of overhead is established. ALL runs fail the unchanged 30 FPS /
33.333333 ms p95 target. The source correction remains installed as incremental
normal-play work; this is not an optimization or full visual/FPS acceptance.

## Evidence and remaining work

Local generated reports stay ignored:

- `tmp/directional-foam-native-v1-20260917/index.json`, SHA256
  `6d3266df9899d34e808cc6827c128ed0dec5e43481957a33a79ce43c814a209f`.
- `tmp/directional-foam-installed-native-v1-20260917/index.json`, SHA256
  `c965602ab5baf7aea5a4172233b004763556067714dc7ba028ca9d01b8295004`.
- `tmp/directional-foam-installed-abba-v1-20260917.json`, SHA256
  `2f005e9f1c739af00a0b5dfd9f0eaa2fd0db9bfd8535bb2849b1b8fb4ff6225a`.
- `tmp/directional-foam-python-v1-20260917.xml`, SHA256
  `59f50f6a1731b6591427fcdc573364e19b74e74ce3419f4864bf2fe843a3af10`.
- `tmp/directional-foam-baseline-guards-v1-20260917.xml` retains the baseline
  failure replay. Decoded evidence lives under
  `tmp/directional-foam-{default,legacy}-decoded-v1-20260917/`.

The same live hydraulic cook's 4700, 4750 and 4800 s snapshots pass BOTH state
and artificial-bank audits; all 86,720 bank cells are exactly dry. At 4800 s:
maximum depth 3.766961483 m, speed 6.218043024 m/s, volume 2,850,155.798833 m3,
maximum step residual 1.521822357e-8 m3. Outflow 111.692445498 versus inflow
45.306954547 m3/s remains unsettled. No candidate bed/flow promotion follows.
Depth SHA256 `ba1b9730dfe45098df9be79a9aa9707b0ded431a41183ad53604ce930441bd25`.
Next 4850/local25000 requires its completion marker and both audits.

Next physical priority remains source-consistent mean water shape and localized
breaking/froth on the shared rendered/contact surface, not further optical
whitening or interpreting a source diagnostic as completion. The full South
Fork -> Colorado -> Pacuare -> Futaleufu sequence, Chilko/Zambezi, crew,
normalization, outstanding regressions, reference-motion review and release
acceptance remain open. Captured geometry and inferred bed provenance are
unchanged; no new reference-video measurement is claimed in this pass.
