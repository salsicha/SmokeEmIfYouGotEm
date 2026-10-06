# Integrated exact arithmetic and corrected hydraulic continuation

September 16, 2026. Production shader integration; NOT visual, physical-history,
full-package, SM5 runtime or 30 FPS acceptance.

## Arithmetic integration and actual GPU verification

The original editor rebuild completed successfully:160 actions, exit0,
1990.52s. Editor binaries now link the current solver library. The separate
candidate GPU test then passed all64,078 input pairs against both the exact
Fraction oracle and original wide accumulator, with zero input-bit errors.
Report `tmp/portable-add-native-v1-20260916/index.json`, SHA256
`5430baad11316bbe97f251c626854154aeca68234404e7fb529e6be00b93951d`.

Production `RaftSimPortableFloat.ush` now includes the compact two-operand
helper. Euler/RK2 wide accumulation remains unchanged. The GPU test explicitly
calls `RaftSimPortableEuler(a,1,b)` as its independent original control; it
does not compare the new helper with itself. Fixed2/3/4-iteration loops in
preparation, pressure and transport now state their unroll counts explicitly.
No equations, rounding policy, iteration budget, tolerances, shader targets or
geometry resolution were weakened. The candidate helper itself is unchanged.

Full WaterDetail plus prescribed-normal GPU suite:

- First integrated run:82 PASS,1 setup FAIL. The isolated reconstructed-CG test
  required a fresh output-path argument omitted by the invocation. Preserve
  `tmp/portable-add-integrated-native-v1-20260916/index.json`; process exit0
  did NOT mean all tests passed.
- Corrected complete run:83 PASS,0 warnings/failures/not-run,21.638510s total
  test duration, actual D3D12/SM6. Includes production pressure, acceleration,
  transport, shoreline, temporal evolution, breaking, foam, polynomial and CG
  controls. The same original fixtures and gates were retained; no synthetic
  CG control was substituted. Report
  `tmp/portable-add-integrated-native-v2-20260916/index.json`, SHA256
  `2d4ef78241123d7df6f0c4adc006b89a4f98fb1d0f279aaa46f952527a1556dc`.
-44 Python arithmetic/restart tests PASS. These results do not qualify the
  outstanding actual captured-history/physical regressions or normal gameplay.

## SM5 compilation and fresh package

All retained failing preparation/pressure/transport inputs now compile with
the corrected private copies using unchanged FXC cs_5_0/O3/Zpr/Gec/Ni settings.
Pressure2/4/9/11 pass. Transport distinct3/4/9/10/14/15/16/21/22 pass;
byte-identical original groups3/27,4/28,9/33,10/34,14/20 share input coverage.
The earlier barrier and prescribed-normal corrections remain in production.
All listed successful probes are TERMINAL0, not live. The earlier compact-add-
only preparation probe remains a preserved failure; explicit bounds were needed.

Transport21 took6410.546s; the other inputs took80–2769s. Slow compilation was
not a reason to stop or restart them. Potentially-uninitialized warnings in
exact/scaled polynomial helpers and register-pressure warnings remain retained.
Source inspection finds initialization of returned fields, but this does not
waive actual SM5 runtime validation. No ForceDXC/platform removal workaround.

- Transport21 report SHA256:
  `0fd59d7a5ddc5d86f56b4d5c8f95e9fded9eb8bbeb946e6c57afbda39dd446e4`.
- Other transport report SHA256:
  `69637674e1f7d4a3173d6dfcc5a36084d1191077b9ce37d40ccebb4ff7e23884`.

Fresh full package session83678 / cook PID5852 started07:55:46 local; shader
workers are active. Log `tmp/ground-cpu-package-v2-20260916.log`; target archive
`unreal/Packaged/GroundCPU-Development-v2-20260916`. Includes Boot, actual South
Fork FullReach and the explicit retained local rock package. Original failed
package evidence is preserved. No package success yet. Game SHA remains
`18d9e4b24bc845192a26ca5f50212111ff6d4d2a8cf29d1bf23fd6576ef785d1`.
After completion verify all444 non-editor ground identities and2,405 staged
runtime payloads before packaged play/contact and uncontended performance.
Do not rebuild editor/game DLLs or edit shader inputs during this cook.

## Failed domain and source-exact correction

Old hydraulic session69416/PID18716 completed1800s, exit0.1700/1750/1800s cell
audits pass but dry artificial-bank audits FAIL. At1700s,13 southern face cells
of context_0836 wet, max0.138596786m. At1800s that edge has22 wet cells,
max0.633022777m; core_0602 north also has one wet cell at0.020810138m. No later
state is accepted or transferred. Outflow also continues to reject settling.
Failed bank reports remain under `tmp/south-fork-context3-*-banks-v1-20260916.json`.

Restart from the last clean1650s state. Both necessary80x80 source tiles are
copied without interpolation at UTM(675280,4295040) and(682960,4297360).
All839 retained geometry records, rock union, bed, roughness and physical
boundary definitions stay exact;12,800 added source cells, zero added water.
Applying the existing rock union changes zero added samples. The earlier
one-edge v1 preparation is retained unused; v2 uses both observed edges.

One-second pilot passes all5,382,400 cells and all86,720 exact-dry bank faces.
Independent pilot AND actual restart audits prove all5,369,600 retained h/u/v
cells bit-exact and the clock unchanged; inventory error9.313225746e-10m3.
Input `tmp/south-fork-landward-dry1650-context-input-v2-20260916/manifest.json`,
SHA256`d6dd8efcc0f43805d8954a066e5f5f84d590543c93086b10320e68dcbc215a8d`.
Actual restart report SHA256
`efb8fa8ec22239e5de26c0177a631400c018334f04d835a9a70bb737c7c85892`.
Union proof SHA256
`e59bd3952cd4f1339f3547c4d83fba14578bfe7d771ba6d8cddb3f75980bf39e`.

LIVE corrected continuation session72710 / PID4608, start07:58:24 local,
output `tmp/south-fork-landward-context1650to1800s-v2-20260916`,3000 steps at
unchanged0.05s, snapshots1000. Historical solver SHA7d7c3be0... unchanged.
NEXT local1000 / absolute1700s needs BOTH state and bank audits. No settling or
runtime-field promotion follows from restart correctness. Never restart on an
observation timeout; the preceding job was independently proven terminal.

Visible breaking/froth, source-supported rock flanks, sustained playable
integration and physical-history regressions remain open. Last uncontended
normal play17.819710FPS/p9581.6343ms still fails30FPS/33.333333ms. Colorado then
Pacuare then Futaleufu, other-scene water, crew, normalization and release remain
open. Troublemaker is a rapid inside South Fork, never a separate menu scenario.
