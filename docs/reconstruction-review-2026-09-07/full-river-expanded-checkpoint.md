# Source-exact expanded-domain continuation — September 12, 10:38 UTC

## Latest: 2300 s state and artificial-bank checks pass

Continuation96057/PID29104 remains live; no restart. Local6000 passes BOTH
independent audits `tmp/south-fork-expanded-2300s-state-v1-20260912.json`
and `tmp/south-fork-expanded-2300s-banks-v1-20260912.json`.
All5,382,400 cells finite; maxdepth4.183992580m, speed7.176383560m/s,
volume2,971,933.830200126m3, drivererror-9.313225746e-10m3,
maximumstepresidual1.425201424e-8m3. All86,720artificial-facecells exactlydry.
hSHA2a70de63d614c2d9d7cb493386bd7cf02bc1a2898a4cf15dd7d2aabf29327c5b.
Outlet96.663279395 versus inlet45.306954547m3/s STILL SETTLING. Runtime600s
unchanged. Next2400/local8000 requires BOTH audits after complete snapshot.

The following entries are retained process history, not current-state overrides.

## Previous: 2200 s state and artificial-bank checks pass

Continuation96057/PID29104 remains live; no restart. Local4000 passes BOTH
independent audits: `tmp/south-fork-expanded-2200s-state-v1-20260912.json`
and `tmp/south-fork-expanded-2200s-banks-v1-20260912.json`.
All5,382,400 cells finite, maxdepth4.241424593m, speed7.260071969m/s,
volume2,977,041.14241628m3; driver error-4.656612873e-10m3 and maximum step
residual1.357466406e-8m3. All86,720 artificial-face cells remain exactly dry.
hSHA22565246c83902d1f6830b740d9a66928e905257c1c57738df7ce3f56269411a.
Outlet96.598629044 versus inlet45.306954547m3/s is STILL SETTLING. Runtime600s
unchanged. Next2300/local6000 requires both independent audits after completion.

The following entries are retained process history, not current-state overrides.

## Previous: 2100 s state and artificial-bank checks pass

Continuation96057/PID29104 remains live; no restart. The completed local2000
snapshot is2100 simulated seconds. Independent state and bank reports:
`tmp/south-fork-expanded-2100s-state-v1-20260912.json`,
`tmp/south-fork-expanded-2100s-banks-v1-20260912.json`.
All5,382,400 cells finite; maxdepth4.295685668m, speed7.255200577m/s,
volume2,982,139.080397612m3. Driver volume error-2.793968e-9m3,
maximum step residual1.3574664e-8m3. All86,720 artificial face cells exactlydry.
hSHA61c6fe44a7ae9680c57c5843ef8340e36e12e9550bfea78347052c31c42fcd38.
Outlet96.158801482 versus inlet45.306954547m3/s is still settling; runtime600s
unchanged. Next2200/local4000 needs BOTH independent audits after completion.

The following entries are retained process history, not current-state overrides.

## Latest: 2000 s state/banks pass; exact continuation to4000 s active

Old v3 session37336/PID29308 completed its requested6000steps normally, exit0.
Independent2000s state AND bank audits pass:
`tmp/south-fork-expanded-2000s-state-v3-20260912.json` and
`tmp/south-fork-expanded-2000s-banks-v3-20260912.json`.5,382,400 finite cells,
maxdepth4.346785185m, speed7.214308144m/s, volume2,987,177.960751385m3,
drivererror9.313226e-10m3, maximumstepresidual1.424969431e-8m3.
All86,720 artificial-facecells exactly dry. hSHA256
`58a706d50d49f3713a321cd7fe455b444e1b02dbe12ceef4cb54f0802cee6004`.
Outlet95.235026411 versus inlet45.306954547m3/s: STILL SETTLING, no promotion.

Prepared exact2000s restart, no added cells/water, grid/bed/roughness/boundaries
unchanged: `tmp/south-fork-expanded-checkpoint-2000s-v1-20260912/manifest.json`,
SHA256 `22e1cce67b4049ee6f8727a3fd2ca05a4b648f0f8d2c9c34f904092fef35b4bc`.
Preparation87361 exits0.20-step pilot86605 exits0; independent restart and bank
audits pass (`tmp/south-fork-expanded-2000s-pilot-{restart,banks}-v1-20260912.json`).
All5,382,400 retained state cells bit-exact; zero added water.

NEW LIVE continuation session96057/PID29104, exact start
`2026-09-12T23:20:51.6847346Z`, same verified executable
`tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`.
Output `tmp/south-fork-expanded-flow-2000-to4000s-v1-20260912`.
40,000steps at.05s; complete snapshots every2000steps/100s. This longer target
avoids repeated short job restarts, not intermediate validation: audit every
completed checkpoint's state AND artificial banks. Next2100s/local2000.
Long-run framezero independent restart audit passes:
`tmp/south-fork-expanded-2000s-long-restart-v1-20260912.json`.
Runtime stays audited600s; full-river settling/closure/traversal remain open.

## Latest: repaired v3 passes 1900 s state AND banks

Complete v3 local4000 passes independent state and artificial-bank audits:
`tmp/south-fork-expanded-1900s-state-v3-20260912.json` and
`tmp/south-fork-expanded-1900s-banks-v3-20260912.json`. All5,382,400 cells finite,
max depth4.394079721m, speed7.222233074m/s, volume2992110.795741257m3,
driver-volume error1.862645149e-9m3, max step residual1.276216066e-8m3.
All86,720 artificial-boundary cells remain exactly dry. Input660d3280…,
heightdf0be69f… hashes match. Both audit commands exit0. Outlet93.953066244
versus inlet45.306954547m3/s remains unsettled; no runtime promotion.
Same process29308 live, observed1904.5/local4090. Next2000/local6000 requires
both complete-snapshot audits; the playable600s baseline is unchanged.

## Previous: repaired v3 passes 1800 s state AND banks

Complete v3 local2000 independently audited in
`tmp/south-fork-expanded-1800s-state-v3-20260912.json` and
`tmp/south-fork-expanded-1800s-banks-v3-20260912.json`: finite/nonnegative state,
5,382,400 cells, max depth4.437210175332066m, speed7.226217050088561m/s,
volume2996893.3562401785m3, driver-volume error-9.313225746e-10m3,
max step residual1.085239054e-8m3. All86,720 artificial boundary cells are
exactly dry, including the previously leaking edge. Input660d3280… and
height9d909e93… hashes match the complete snapshot. Both commands exit0.
Outlet92.233295329 versus inlet45.306954547m3/s still fails settling acceptance.
Same process29308 confirmed live; next complete1900/local4000 needs both audits.
No runtime promotion; the playable600s baseline remains unchanged.

## Previous: 1800 s v2 artificial-bank failure; source-exact repair prepared

Complete local4000 v2 state passes finite/depth/speed/mass checks, but banks
FAIL: one wet cell on `core_0602` north edge, depth0.021391496407m. Reports
`tmp/south-fork-expanded-1800s-{state,banks}-v2-20260912.json`. This is not a
clean checkpoint and must not be promoted. Outlet92.233295329 versus
inlet45.306954547m3/s remains unsettled. The existing runtime600s is unchanged.

Prepared `tmp/south-fork-expanded-checkpoint-1700s-context-v3-20260912/manifest.json`
from the independently verified clean1700s/local2000 state, using the later
1800s audit only to identify missing terrain coverage. All5,376,000 retained
state cells remain exact; one source-exact tile adds6400 cells and ZERO water.
No invented barrier, changed bed, discharge, tolerance or mass gate. Preparation
session17214 exits0. Input SHA256
`660d328074fa65a6310a12a427a33e4a974e1a4d498ee57aaa783f8146003293`.
Added `context_0840`, UTM centre[682960,4297360], copied without interpolation
from retained region0220, slice[row200,col40], source SHAb4304d78….

Pilot74173 exits0 at1701s. Independent restart and bank reports
`tmp/south-fork-expanded-context1700s-pilot-{audit,banks}-v3-20260912.json`
pass: all5,376,000 original cells bit-exact,6400 added source-exact cells,
zero added water, unchanged original grid/bed/roughness/boundaries/clock,
volume error-4.656612874e-10m3, all86,720 artificial-bank face cells exactlydry.
Old v2 PID35952 explicitly killed only after executable/start-time checks;
session68098 terminal exit1, last logged1813s. All snapshots retained. This
retirement is due to the verified domain failure, not an observation timeout.

**CURRENT LIVE session37336/PID29308**, exact start
`2026-09-12T21:31:45.4507047Z`, unchanged solverSHA7d7c3be0….
Output `tmp/south-fork-expanded-flow-1700-to2000s-v3-20260912`;
6000steps×.05s, snapshots every2000:1800/1900/2000s.
Long-run framezero independent restart audit also passes:
`tmp/south-fork-expanded-context1700s-long-restart-v3-20260912.json`.
Latest observed1702.5s/local50. Next complete1800s/local2000 needs BOTH state
and bank checks; future closure/settling are not established by a one-second
pilot. Never reuse old process pause templates. Runtime600s unchanged.

## Latest: expanded clean restart passes 1700 s (20:47 UTC)

Same live session68098/PID35952/start20:09:56.4973049UTC, no restart or
duplication. Complete local2000 checkpoint independently audited across
5,376,000 cells. Reports `tmp/south-fork-expanded-1700s-{state,banks}-v2-20260912.json`
both pass their checks. All86,720 artificial-bank face cells are exactly dry,
unlike the retired v1 checkpoint's13wet cells. The source-exact context addition
resolved that failure at this checkpoint; later checks remain necessary.

Depth max4.474719809m, speed max7.223276883m/s, volume3,001,488.712603m3;
snapshot/driver volume error-2.793967724e-9m3, maxstep residual1.303670549e-8m3.
Outlet90.210308325 versus inlet45.306954547m3/s remains unsettled: no runtime
promotion, no settling/visual acceptance. Runtime still uses audited600s.
Next complete1800s/local4000, then1900/2000s; audit complete files only.

1700s h/u/v SHA256 respectively:
`a3d4fdef5d3581cfcce6d86f6cb863fdc4f5f0e23a5951166efc068c0b8b570f`,
`675482c8ed1946784f67337b54e6b512b65d73e6cb569bbfc6c110f94e8df0c8`,
`76c9955db4b1caa3bf98c50a3ee8e5d8951e2a708ff634fe21d0d51f6b23b956`.
Input manifest remains53a0db1c… (840tiles, source-exact1600s+one dry tile).

## Current: clean 1600 s plus one dry source tile (20:12 UTC)

The previous 1600-to2000 v1 cook reached a complete1700 s checkpoint. Its state
and mass audit pass, but artificial-bank audit FAILS:13 wet cells on
`context_0836` south edge, max0.138589886 m. Outlet90.210308325 versus inlet
45.306954547 m3/s is still unsettled. Reports:
`tmp/south-fork-expanded-1700s-{state,banks}-v1-20260912.json`.
Do not promote this checkpoint or later v1 states into playable flow.

Prepared a new restart from that cook's frameZERO, which is the independently
verified clean1600 s state, using the later1700 s audit **only** to select missing
terrain context. New explicit `--allow-later-bank-observation` validates the same
immutable input and later complete-frame depth hash; default still requires the
same step. Two tests reject mismatched input/state and older observations.

New input `tmp/south-fork-expanded-checkpoint-1600s-context-v2-20260912/manifest.json`,
SHA256`53a0db1c1063722e5ca9bcb0ca2483e013473a2d29b601fa768afcd729045aa8`.
840 tiles/5,376,000 cells. Added `context_0839`, UTM centre[675280,4295040],
6400 cells copied without interpolation from retained region0614, slice[40,40].
Source SHA9cc5b3ef…; original5,369,600 cells/bed/roughness/boundaries/clock remain
exact. Added initial water volume is **zero**. Geometry is source-backed, not an
invented wall or modified riverbed. No threshold, discharge or mass gate changed.

20-step native pilot40819 exits0 at1601 s. Independent restart audit passes all
retained cells bit-exact plus6400 source-exact cells; volume error-9.313225746e-10m3.
All86,720 artificial-edge cells are exactly dry at1601 s. Reports:
`tmp/south-fork-expanded-context1600s-pilot-{audit,banks}-v2-20260912.json`.

Old session71400/PID30636 was explicitly retired for the diagnosed boundary
failure, not for a timeout. The first PowerShell Stop-Process call failed; a
subsequent start-time/executable-verified Process.Kill/WaitForExit succeeded.
Old handle is terminal(exit1), last logged1739.5 s; completed snapshots retained.
The new process briefly overlapped the old after the first stop failure. No
performance measurement uses this interval. Do not poll or reuse the old PID.

**CURRENT LIVE session68098 / PID35952**, start
`2026-09-12T20:09:56.4973049Z`, unchanged solver executableSHA7d7c3be0….
Output `tmp/south-fork-expanded-flow-1600-to2000s-v2-20260912`.
8000 steps×.05 s, snapshots every2000:1700/1800/1900/2000 s. New long-run frameZERO
independent audit passes (`tmp/south-fork-expanded-context1600s-long-restart-v2-20260912.json`).
Latest observed1605.5 s/local110. Next complete1700 s/local2000, with full state
AND dry-bank audit required. No runtime promotion; normal scenario still uses
audited600 s. Prior process-pause templates invalidated again.

## Current continuation: 1600 to 2000 s (19:31 UTC)

Old cook79428/PID37256 completed its requested6000 steps normally (exit0),
and the process disappeared. Its complete1600s snapshot passes independent
state/mass and artificial-bank audits on5,369,600 cells. Reports:
`tmp/south-fork-expanded-1600s-{state,banks}-v1-20260912.json`.
Depth max4.505364428m, speed max7.215402835m/s, volume3,005,865.295292834m3;
driver volume error-1.862645149e-9m3, maxstep residual1.274183448e-8m3.
All86,720 artificial-bank face cells are exactly dry. Outlet87.916530779 versus
inlet45.306954547m3/s remains unsettled: **no runtime promotion**.

1600s SHA256:
h`6bab0cff94a9379eb72f21d6216de22b46ee1032e635cc56cd7980ebf533c08e`,
u`9c30af3dfcf5a88bdd92f1dc6a1f272e49f721aff7d5b906fae3bc9e20ee6f64`,
v`76e81907a211127faa596c5b2049dbca5eacf05f6148bce898b652e577965ca8`.

Prepared an exact-state continuation with NO added terrain or water:
`tmp/south-fork-expanded-checkpoint-1600s-input-v1-20260912/manifest.json`,
SHA`d3b2d831758426610a9807184e013aa56f6d48b4552f0b0fc01c8d1b5a884095`.
20-step pilot to1601s exits0; all original5,369,600 state cells are bit-exact
at restart, bed/grid/roughness/boundaries/clock unchanged, restart volume
error-9.313225746e-10m3. Pilot banks exactly dry. Reports:
`tmp/south-fork-expanded-checkpoint-1600s-pilot-{audit,banks}-v1-20260912.json`.

**CURRENT LIVE session71400 / PID30636**, start
`2026-09-12T19:22:36.6708003Z`, same checkpoint solver executable SHA7d7c3be0…
(full path/hash retained below). Output
`tmp/south-fork-expanded-flow-1600-to2000s-v1-20260912`.
8000 steps at0.05s; complete snapshots every2000:1700/1800/1900/2000s.
Actual long-run frame-zero independent audit also passes all5,369,600 retained
cells (`tmp/south-fork-expanded-1600s-long-run-restart-v1-20260912.json`).
Latest process identity rechecked19:31UTC; do not duplicate/restart it.
The stored performance-capture pause template was invalidated because it
contained the OLD PID/starttime. Reconstruct any future pause/resume against
the new verified process identity; never reuse the old template.

September12 19:09UTC: same executable path/starttime, cook79428/PID37256 verified
live at1574s/local5480. Max step residual remains1.274183448e-8m3. Next complete
1600s/local6000. No new completed checkpoint, restart or runtime promotion.
Normal-map line/planning work uses the existing600s atlas and does not edit
this cook or source geometry.

## Latest complete checkpoint: 1500 s passes state and dry banks (18:44 UTC)

Same cook79428/PID37256 remains live; next complete1600s/local6000.
Reports `tmp/south-fork-expanded-1500s-{state,banks}-v1-20260912.json`.
All5,369,600 state cells pass. Depth max4.528780818m, speed max7.191082831m/s,
volume3,009,994.373712418m3; snapshot/driver error-1.397e-9m3. Maximum step
residual1.274183448e-8m3. All86,720 artificial-bank cells are exactly dry.
Flow remains unsettled: outlet85.2756632970 versus inlet45.3069545472m3/s.
No runtime promotion; normal map still uses audited600s data. No restart needed
for this checkpoint, and no source/proof files were removed.

1500s SHA256: h`ba747cff7408f81703e7e86a3c02faeffe3e481a9419d06374f9504f57d9345e`,
u`da5982fe79466506fd0b33ec25ec73250db75da103cebb4c8abeb1b031c19e49`,
v`6060598c4bda5097f9abcfd334bef1ed2772eac06a79ca9907f6e20273c5a15e`.

## Latest complete checkpoint: 1400 s passes state and dry banks (18:15 UTC)

Same 839-core cook 79428/PID 37256 remains live; no restart or promotion.
Local frame 2000 independently audited across all 5,369,600 cells:
`tmp/south-fork-expanded-1400s-state-v1-20260912.json` and
`tmp/south-fork-expanded-1400s-banks-v1-20260912.json`.
Depth max 4.545992511 m; speed max 7.150320074 m/s; volume
3,013,843.05252563 m3, exact snapshot/driver agreement. Maximum step mass
residual 1.274183448e-8 m3. All 86,720 artificial-bank face cells exactly dry,
1,084 bank faces and 2,268 directed shared faces. This repairs the prior
1300 s failed boundary, but flow remains unsettled: outlet 82.2385822412
versus inlet 45.3069545472 m3/s. Normal runtime stays on audited 600 s.
Next complete checkpoint local 4000 / 1500 s; do not duplicate the live cook.

1400 s array SHA256:
- h: `bc705eed8d3d54332cabe2758a920982ae5548772e6493edc3bc87ef3a2726b2`
- u: `6c06765434dda47638258a0d012e71be006da9001ce6cfdb6f1a31fa56c1a4b9`
- v: `4e8426425c185c7f3b0f95d7eb89bfffd2b4818ba4db502d5e02c2406b4a1550`

September 12 18:01 UTC observation: the same replacement cook 79428/PID 37256
continues, local step 1620 / 1381 s, maximum step residual 1.274183448e-8 m3.
Next complete checkpoint remains local 2000 / 1400 s. No new checkpoint or
runtime promotion claimed. No source/proof cleanup was performed.

## CURRENT: 1300 s bank repair, 839 cores (September 12, 17:32 UTC)

The complete 838-core 1300 s snapshot passes finite/state/mass checks on
5,363,200 cells, but fails the unchanged exactly-dry artificial-bank gate:
one core_0229 east face cell is 0.111736131932 m deep. Maximum depth 4.559991931 m,
speed 7.143598970 m/s, volume 3,017,366.779715144 m3; maximum step residual
1.3921307884e-8 m3. Outlet 78.7687406175 versus inlet 45.3069545472 m3/s is
unsettled. No runtime promotion. Audits
`tmp/south-fork-expanded-1300s-{state,banks}-v1-20260912.json`.
Snapshot H SHA256 `f566dc0b59055fd6e9485d49ff6bb50f25eedf7efeb81cdba459f627bc9ba294`,
U `446fd558d5caf70099b4ab6ec6348f186aa2c7a06cac62cbdca15cf2fa9e7c6e`,
V `3e3aca13e985d37d8957525b6b6b1b68939c048f5ef2744f7cb31e13cee0e26c`.

Added one captured-source tile with zero added water. New input
`tmp/south-fork-expanded-checkpoint-1300s-input-v1-20260912/manifest.json`, SHA256
`5a8e8a7c5e2fae342972d8dbaafc018866f505f63a044769cc9eb14746643059`.
Pilot session 21635 exits 0 after 20 steps to 1301 s (26.07 s wall time).
`tmp/south-fork-expanded-checkpoint-1300s-pilot-v1-20260912/restart_audit.json`
independently proves 5,363,200 retained cells bit-exact, 6,400 added bed cells
source-exact, unchanged bed/roughness/physical boundaries/clock, and inventory
error 1.396983862e-9 m3. Pilot bank audit: 86,720 face cells exactly dry,
1084 artificial faces and 2268 directed shared faces. Bank audit SHA256
`bfaac4374e0e75efd35f60d7e28d74fa074b8fe66a0e5e1852f23c2393c7f389`.

CURRENT LIVE: session 79428 / PID 37256, start 2026-09-12T17:30:21.3825864Z.
Same native executable `tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`
SHA256 `7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
Output `tmp/south-fork-expanded-flow-1300-to1600s-v1-20260912`, 839 cores,
5,369,600 cells, 6000 steps at 0.05 s, snapshots every 2000 steps
(1400/1500/1600 s). Actual replacement frame-zero `restart_audit.json` also
passes, SHA256 `2c03ae227d3aa94e56e78271b0173aa813c528e5633a1f4180bae87388887cf7`.
Only after this proof and live-process identity checks, the superseded
session 66046/PID 37616 was intentionally stopped (terminal exit 1 from stop,
not a solver failure). Its checkpoints and artifacts remain intact.
New process reverified at local 110/1305.5 s, CPU 439.21875 s and unchanged
start identity. Next complete 1400 s; a progress row is not a bank audit.
Normal runtime remains the independently audited 600 s source. Free disk about
1.43 GB; budget the remaining three snapshots before additional input copies.

## Current continuation: 1200 s bank repair, 838 cores (September 12)

The previous 837-core cook (session 49780/PID 32032) is TERMINAL, exit 0.
Its complete 1200 s state passes finite/mass checks over 5,356,800 cells, but
fails the unchanged exactly-dry artificial-bank gate: one core_0229 west face
cell has 0.007963794110 m depth. Outlet 74.6290237194 versus inlet
45.3069545472 m3/s is unsettled. Do not promote this snapshot. Audit files:
`tmp/south-fork-expanded-1200s-{state,banks}-v1-20260912.json`.

Added one captured-source context tile (6,400 cells), zero added water. Input
`tmp/south-fork-expanded-checkpoint-1200s-input-v1-20260912/manifest.json`, SHA256
`c3036bbc83822c80cc8cd57770d79c6c7760478ca5413bdef619d530f5034a40`.
Pilot `tmp/south-fork-expanded-checkpoint-1200s-pilot-v1-20260912` exits 0 after
20 steps to 1201 s. Independent native restart audit proves all 5,356,800 retained
cells bit-exact and all 6,400 new bed cells source-exact; original physical
boundaries, bed, roughness and simulation clock unchanged. Inventory error
4.656612873e-10 m3. All 86,560 artificial face cells are exactly dry at 1201 s.

CURRENT LIVE: session 66046 / PID 37616, started 2026-09-12T16:48:40.9062638Z.
Executable `tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`,
SHA256 `7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
Output `tmp/south-fork-expanded-flow-1200-to1600s-v1-20260912`; 838 cores,
5,363,200 cells, 8,000 steps at 0.05 s, complete snapshots every 2,000 steps
(1300/1400/1500/1600 s). Actual long-run frame-zero `restart_audit.json` also
passes independently; do not substitute the pilot for this proof. Brief owned
process pauses for isolated engine benchmarks resume this same process; never
restart it or change its numerical state. Normal runtime remains audited 600 s.
Same live session reverified at local step 1360 / 1268 s after all benchmark
pauses, maximum cumulative step residual 1.3921307884e-8 m3. PID/start identity
unchanged and CPU time advanced to 4713.84375 s. Next complete snapshot is
1300 s / local step 2000; the progress row is not a new independent bank audit.

## Latest complete snapshot — September12 16:10UTC

The837-core1100s snapshot (`frame_002000`) passes independent state/mass checks
over5,356,800 cells. All86,720 artificial-bank face cells are exactly dry;
1084 bank faces and2260 directed shared faces checked. Maximum depth4.599654078m,
speed7.149926868m/s, volume3,023,217.8431676514m3; maximum step residual
1.2523322157065309e-8m3. Outlet70.0281015067 versus inlet45.3069545472m3/s
still contradicts settled-flow acceptance. No runtime-source promotion.

Audits: `tmp/south-fork-expanded-1100s-state-v1-20260912.json` and
`tmp/south-fork-expanded-1100s-banks-v1-20260912.json`. Exact snapshot hashes:
H `845d73075f5c7c303ae2fc07310975df9223cc52f11a112aabd7201a05cf3a84`,
U `4934f194fdb1fef75ab91a2239f4521246209355500cbfac263dba46833c3de3`,
V `698254ac1185d32c7429add4e7050c373c2e5d6ca1164d6326bec0cb71b661a7`.
Same session49780/PID32032 continues toward1200s/local4000; do not restart.
Reverified via that live session16:31UTC: local3310/1165.5s, maximum cumulative
step residual1.425222717621466e-8m3. This is not a new completed snapshot audit.

## Current continuation — September 12, 15:36 UTC

The complete 1000 s snapshot from the 836-core run passes finite/state/mass
checks but fails the unchanged artificial-bank gate: three cells on core_0201
south are wet (maximum 6.515260167e-6 m). Outlet 65.2957371420 versus inlet
45.3069545472 m3/s is still unsettled. Do not promote that snapshot. Audits:
`tmp/south-fork-expanded-1000s-state-v1-20260912.json` and
`tmp/south-fork-expanded-1000s-banks-v1-20260912.json`.

Added one captured-source tile, with **zero added water**. Immutable input:
`tmp/south-fork-expanded-checkpoint-1000s-input-v1-20260912/manifest.json`, SHA256
`be9c1f9f0f19488a6c4beea3ec3def2484e2e6537d0b7637e4b3877e3d72559c`.
Pilot `tmp/south-fork-expanded-checkpoint-1000s-pilot-v1-20260912`, session25883,
exit0, 20 steps to1001s in26.77s. Independent native restart audit proves all
5,350,400 retained cells bit-exact,6,400 new source-exact bed cells, unchanged
physical boundaries/bed/roughness, and inventory error -4.656612873e-10m3.
All86,720 artificial face cells are exactly dry at1001s. Restart audit SHA256
`16e55b7e7d3820fdcd540b1b7d506939078ca2a1b38a0bf666d12886381b43e2`;
bank audit `8470bf5799ab7fefd09faf52d03f680a94d728e05bca72b13df7f0c773ed0623`.

**CURRENT LIVE: session49780 / PID32032, started15:34:41.2881188UTC.**
Same live handle reverified16:07UTC atlocal1910/1095.5s, maximum cumulative
step residual1.2523322157065309e-8m3; next complete1100s/local2000. No new
snapshot acceptance is implied. The runtime map/profile hashes remain unchanged.
Output `tmp/south-fork-expanded-flow-1000-to1200s-v1-20260912`,837 cores,
5,356,800 cells.4000 additional.05s steps,2000-step snapshots: local0=1000s,
local2000=1100s,local4000=1200s. Executable remains the unchanged verified
`tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`.
Actual replacement frame0 independently passes the same full-cell restart audit.

Only after pilot AND actual replacement verification, retired PID31752/session1541
using its exact executable path and original13:10:13.2119965UTC start time.
Session1541 is terminal exit1. All old inputs/outputs retained; later elapsed
steps under the affected boundary were not transferred. Normal map still uses
the previously audited600s runtime atlas; no source promotion or settling claim.
Previous sections below are historical process checkpoints, not current jobs.

## Current continuation — September 12, 13:11 UTC

The 836-core run to 600 s completed successfully (session51161 exit0; PID38888
no longer exists). Its 5,350,400 cells pass state/mass checks; all 86,720
artificial bank-face cells remain exactly dry. Maximum depth 4.777402375 m,
speed 11.952985593 m/s, volume 3,030,838.1431382014 m3, maximum step residual
1.236987668e-8 m3. Outlet 53.7023996832 versus inlet 45.3069545472 m3/s still
does not support settled-flow acceptance. Audits:
`tmp/south-fork-expanded-600s-state-v4-20260912.json` and
`tmp/south-fork-expanded-600s-banks-v4-20260912.json`.

Prepared a source/terrain/boundary-identical restart, with no additional tiles
or water: `tmp/south-fork-checkpoint-600s-input-v1-20260912/manifest.json`, SHA256
`00eeda5554c6e423ece07c022077609364f6e177df58dff07134afe0b2ba7f18`.
Independent audit of the actual new native frame zero verifies all 5,350,400
cells bit-exact, identical clock, unchanged bed/roughness/physical boundaries,
and inventory error -9.313225746e-10 m3.

**CURRENT LIVE: session1541, PID31752, started 13:10:13.2119965 UTC.**
Latest revalidation13:45UTC: same live session, local2160/708s, maximum step
residual1.328721511e-8m3. Next complete snapshot is still800s. Latest600s state
has now passed shared native runtime export/dense comparison; see
[normal scene assembly preflight](full-scene-assembly.md). No map promotion or
settling acceptance is implied.
Reverified via the same session and native PID at 13:27 UTC: local step1060,
653 simulated seconds, maximum cumulative step residual1.131258665e-8m3.
This progress line is not a complete snapshot or an artificial-bank audit.
Output `tmp/south-fork-flow-600-to1200s-v1-20260912`; 12,000 additional 0.05 s
steps, snapshots every 4,000: local0=600 s, local4000=800 s, local8000=1000 s,
local12000=1200 s. Executable remains the same verified checkpoint solver.
No predecessor was killed for this continuation: the 600 s run was already
terminal. All previous files are retained. This is continuing transient flow,
not a steady-state or playable visual acceptance. Inspect future complete
snapshots for artificial banks, section discharge and settling before accepting.

Entries below describe earlier checkpoints and historical process handles.

### 550-second verification — September 12, 12:52 UTC

Current 836-core run, session51161/PID38888, remains live toward 600 s.
At local1000 / 550 s all 86,720 artificial bank-face cells are exactly dry.
All 5,350,400 state cells pass finite/depth/speed checks, with maximum depth
4.8127829131 m, speed 11.9665725562 m/s, volume 3,031,219.2463062 m3 and
maximum step residual 1.236987668e-8 m3. Driver/snapshot volume difference
-2.328306437e-9 m3. Outlet 51.19337922995 versus inlet 45.3069545472 m3/s:
steady-flow acceptance remains open. No source extension/restart is needed
at this checkpoint. Reports: `tmp/south-fork-expanded-550s-state-v4-20260912.json`
and `tmp/south-fork-expanded-550s-banks-v4-20260912.json`. Next complete snapshot
is local2000 /600 s; terminal completion alone is not settling acceptance.

## Latest process update — September 12, 12:36 UTC

500 s / 835-core state passes finite/depth/speed/mass checks: 5,344,000 cells,
maximum depth 4.8544685846 m, speed 12.0461476332 m/s, volume
3,031,455.505084867 m3, maximum step residual 1.158564392e-8 m3. Outlet
48.1760077184 versus inlet 45.3069545472 m3/s; settling is not accepted.
Ten artificial face cells on core_0210 west became wet (maximum 0.101747104 m).
The state and bank audits are `tmp/south-fork-expanded-500s-state-v3-20260912.json`
and `tmp/south-fork-expanded-500s-banks-v3-20260912.json`.

Added one captured-source 80 x 80 tile, with zero additional water. New immutable
input `tmp/south-fork-expanded-checkpoint-input-v4-20260912/manifest.json`, SHA256
`11be13dbec19a6040b392bb07776e820e5169f074efd0b6170e7ed8adb7938dc`, 836 cores.
Pilot `tmp/south-fork-expanded-checkpoint-pilot-v4-20260912`, session8938 exit0,
20 steps to 501 s in 25.13 s. Independent native audit verifies all 5,344,000
original cells bit-exact, 6,400 new source-exact terrain cells, unchanged physical
boundaries and original bed/roughness, inventory error 4.656612873e-10 m3.
All 86,720 artificial face cells are dry at 501 s. Restart audit SHA256
`e9747af19c3fd7e80db603743ae0a56d00e365c95ec640295509686ebb0c0dc6`;
bank audit `a4ddfb587540b1e754d961bbc1e5a434e56aa0050656baff4e0e275c14934b71`.

**CURRENT LIVE: session51161, PID38888, started 12:34:07.9994988 UTC.**
Output `tmp/south-fork-expanded-flow-to600s-v4-20260912`; 2,000 additional
0.05 s steps, snapshots every 1,000: local0=500 s, local1000=550 s,
local2000=600 s. Actual new frame zero also passes the independent restart audit.
Executable is unchanged (`7d7c3be0…`, path below). Do not overwrite live files.

Superseded PID13424/session2578 was stopped after pilot AND actual restart
verification, with executable and exact start time checked. First PowerShell
stop failed; explicit `-InputObject -Force` succeeded. Terminal exit1, last
ledger 525 s. Files are retained; the last 25 s under the affected boundary
topology were not transferred. Normal map integration remains unfinished.

The entries below are historical, not current live handles.

## Latest process update — September 12, 11:56 UTC

The 400 s snapshot of the 833-core run passes finite/depth/speed/mass checks
but wets 17 artificial bank-face cells on core_0676 south, core_0677 west and
core_0681 north (maximum 0.4655954368 m). Its outlet is 30.24762008 m3/s versus
45.3069545472 m3/s inlet: conservation is sound, but settling is not accepted.
Added two existing captured-source 80 x 80 terrain tiles, with zero added water.

New input `tmp/south-fork-expanded-checkpoint-input-v3-20260912`, 835 cores,
SHA256 `852726456041457b8b1ade715480e61ff0b2fd692f1bd870290af5f7513355f4`.
Pilot `tmp/south-fork-expanded-checkpoint-pilot-v3-20260912`, session37502,
terminal exit0: 20 steps from 400 s to 401 s in 26.03 s. All 5,331,200 previous
cells are bit-exact, 12,800 new terrain cells are source-exact, physical
boundaries/bed/roughness unchanged, water inventory error 4.65661e-10 m3.
At 401 s all 86,720 artificial boundary cells are dry; maximum step mass
residual 5.27184e-9 m3. No hydraulic or visual acceptance is inferred.

- Pilot and actual new live frame-zero restart audit SHA256:
  `e08b86cdd97bd6d470497e3bfbe3073443d9c691f0ef6fd1eb3d8c295701db4b`.
- Pilot exterior audit SHA256:
  `52e074a0b848d98e47e554ee669eb6928a8140c7fa398570c25d58072948182f`.

**CURRENT LIVE: session2578, PID13424, started 11:54:30.8857905 UTC.**
Output `tmp/south-fork-expanded-flow-to600s-v3-20260912`; 4,000 additional
0.05 s steps, snapshots every 2,000. Local step0=400 s, step2000=500 s,
step4000=600 s. Verified live at local step60 / 403 s. Executable remains
`tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`,
SHA256 `7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
Do not rebuild or overwrite that live executable/input/output.

The superseded PID8116/session48811 was stopped only after the replacement's
actual frame-zero state passed the independent audit. Its executable and exact
start time were checked. The initial scoped stop was denied by the sandbox;
the elevated scoped stop succeeded. Terminal exit1, final ledger step2420 /
421 s. All outputs, including the complete 400 s snapshot, are retained. Its
last 21 s under the affected boundary topology were not used as restart state.

The following 11:17 entry is historical and its process is no longer live.

## Latest process update — September 12, 11:17 UTC

The832-core continuation's300s complete snapshot passed all field/mass checks
but wetted14 artificial bank-face cells on core_0682 south and core_0683 west
(maximum0.5041050896840754m). The previous repaired faces remained dry. One
additional source-exact80x80 tile fills the shared missing neighbor. It adds
no initial water volume and changes no original terrain or physical inlet/outlet.

New input `tmp/south-fork-expanded-checkpoint-input-v2-20260912`, SHA256
`73feaa2244f6d6c468030d0457b1809e7e4fc4581ca2633046ee9b077fce197b`,833 cores.
The input generator now correctly labels exact checkpoint initialization rather
than inheriting the older warm-start description.

Pilot `tmp/south-fork-expanded-checkpoint-pilot-v2-20260912`,session39612 terminal
exit0,20 steps from300s to301s,23.41s wall. Independent native output audit proves
all5,324,800 previous cells bit-exact plus6,400 added source-exact cells. Clock
preserved at300.00000000003394s; volume inventory error-9.313225746154785e-10m3;
added water0m3. At301s all86,720 artificial bank-face cells are exactly dry.
Maximum step conservation residual7.4662163118688341e-9m3.

- Restart audit SHA256
  `0d5b17224089be72bac3616e4aaa299e09abb10890bd98abd665042c1c18e1cb`.
- Pilot exterior audit SHA256
  `9dd11de3372ccdf4db15d1db7b3a02ef82f0d9f9bdb8e889d6e33dd5d3e4be23`.

The affected832-core process PID37312/session54194 was deliberately stopped
only after this verification, with executable path AND start time checked.
Terminal session result exit1; final recorded local step2480/324s. All outputs
are retained. The additional24s after its complete300s checkpoint is diagnostic
history under the affected boundary topology, not transferred state.

**Current LIVE handle: session48811,PID8116,started11:15:55UTC.**
Executable remains `tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`
(SHA7d7c3be0..., unchanged). Output
`tmp/south-fork-expanded-flow-to600s-v2-20260912`;6000 additional0.05s steps,
2000-step snapshots. Local step0=300s,2000=400s,4000=500s,6000=600s.
Its actual frame0 has independently passed `restart_audit.json`, not only the
pilot. Do not confuse this live handle with either stopped predecessor.

The native shared-atlas runtime loader is now implemented and tested using the
separate valid201s/832-core snapshot; see
[Shared atlas](full-river-shared-atlas.md). A later833-core export must use the
new snapshot/geometry and recheck physical-edge coverage. This new cook is still
transient, not accepted steady water; native mass correctness does not imply
settling, visual/cost acceptance or normal-map integration.

This is a repaired offline flow-domain prerequisite, not normal-scene delivery
or settled-flow acceptance. Troublemaker remains a rapid within South Fork and
stays off the scenario menu. The entire active goal remains unfinished.

## Evidence and repair

The original826-core run's200s complete snapshot passes the independent full-
field finite/depth/speed/volume audit, but wets71 artificial exterior bank-face
cells (62 over1cm), maximum0.3756411377600755m. This confirms the100s issue is
growing, not a tiny roundoff film. The4 actual physical inlet/outlet faces are
excluded from this diagnostic. Shared tile faces are never counted as banks.

- Source snapshot `tmp/south-fork-coupled-flow-600s-v2-20260912/frame_004000`.
- Full audit `frame_004000_audit.json`:5,286,400 float64 cells, maximum depth
  4.347481432046968m,speed12.11185647716171m/s,volume3026369.9869786436m3,
  maximum step mass residual1.3275345156493756e-8m3. Still transient: outlet
  20.06205456065112m3/s versus inlet45.3069545472m3/s.
- Bank audit `frame_004000_exterior_bank_audit.json`, SHA256
  `83f871813fe0f6a20dd5fc519241a9e66e7635ea92f50f2bf8ac2780d6f38778`.

Added6 source-exact80x80 context tiles,38,400 cells, to cover all currently wet
artificial faces. Each complete tile copies all four retained geometry arrays
from one hash-verified321x321 source packet, with an explicit integer slice and
no interpolation/extrapolation. Several affected faces share the same added
neighbor. Existing tile identities, grid, bed, Manning roughness and authored
physical boundaries remain unchanged. The coupled solver naturally replaces
newly shared banks with actual neighbor ghost states at both RK stages.

All6 added tiles are captured-dry, so added initial water volume is exactly0m3.
The preparation tool explicitly supports/reports inferred captured-surface
depth and initially resting water in newly included context, rather than
pretending such water was evolved; this case needs none. No uniform rescaling,
height edit, removed wet probe or global mass correction was used.

## Implementation and checks

- `physics/cpp/include/raftsim_water/cartesian_domain.hpp` and implementation:
  an additional constructor preserves a finite nonnegative checkpoint clock.
  The original constructor symbol/signature remains available; no class layout
  change. Scenario initial arrays carry the checkpoint state. Native cook reads
  optional `initial_time_seconds`, preserving absolute simulated time while
  starting a new local step/mass ledger.
- `physics/cpp/tests/cartesian_domain_tests.cpp`:16-tile moving wet/dry and lake
  cases restart after37 steps. State h/u/v/hu/hv/eta/wet, clock, numerical face
  fluxes and volume are bit-exact initially and for50 further steps versus the
  uninterrupted run. Invalid negative/infinite/NaN clocks fail closed.
- `physics/scripts/prepare_cartesian_snapshot_restart.py`: verifies original
  input hashes, complete source snapshot, finite bounded arrays and volume;
  preserves original cell state and physical boundaries; adds only complete
  source-exact tiles; verifies serialized state and reports inventory.
- `physics/scripts/audit_cartesian_snapshot_restart.py`: independently checks
  actual native frame0 against all original cells and added captured arrays,
  including source hash, bed, roughness, grids, boundaries, clock and inventory.

Separate build `tmp/south-fork-checkpoint-solver-v1-20260912`, session91234,
terminal exit0,28 actions. Four CTests PASS in3.69s; native test output in
`Testing/Temporary/LastTest.log` includes the exact-continuation comparison.
The native executable SHA256 is
`7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
Candidate library SHA256
`18ecf827f5f81f0396de60c5a89fbc2ee077a3bc23a8a47e11b9cefd5375a5fe`.
It is NOT installed in Unreal. Installed archive remains
`e69772d2c856054f6bb37035486e6828c47d3ee3eebdbf9b0261dec6fb9a678c`.

Prepared immutable input `tmp/south-fork-expanded-checkpoint-input-v1-20260912`,
manifest SHA256
`cec8bb0168c4da25f5ff57905154ae2da354c87b758e34521b8baead015818b7`.
Its explicit `restart` block is authoritative. Its inherited top-level
`initial_velocity_method` still describes the original warm-start lineage;
the preparation script now labels checkpoint initialization correctly for
future generations. Do not mutate this input while its cook is running.

One-second native pilot `tmp/south-fork-expanded-checkpoint-pilot-v1-20260912`,
session67185 terminal exit0,20 steps from200s to201s,23.27s wall:

- All5,286,400 retained cells are bit-exact. All38,400 added cells match captured
  terrain. Native clock is200.00000000001123s at restart, not0. Inventory error
  versus the prior native ledger is4.656612873077393e-10m3.
- `restart_audit.json`, SHA256
  `8626c1c0f76ba9dbc7748104dbd0f41829978009b7156a006f1ede74453f660f`.
- After1s all86,720 artificial bank-face cells are exactly dry. Physical inlet
  and outlet faces remain unchanged; max step mass residual9.8444112861528765e-9m3.
- `frame_000020_exterior_bank_audit.json`, SHA256
  `b1bf8286bb1e230b6acc59312f64df6721e7da2899ae6ff6f6d84c510ededbfb`.

These checks prove checkpoint fidelity and removal of the currently affected
artificial boundaries. They do NOT prove the new domain remains dry at every
artificial edge indefinitely or that flow has settled.

## Historical process transition — superseded at11:15UTC

The old solve was deliberately superseded after the verified replacement pilot,
NOT restarted because of a poll timeout. Exact executable path and PID36216
were checked before stopping it. Session63136 is terminal exit-1. Its final
ledger entry is step4590/229.5s; no old files were deleted or overwritten.
The new solve resumes the last complete200s checkpoint. The old additional
29.5s under the affected artificial-bank topology is retained as diagnostic
ledger output, not claimed as transferred checkpoint state.

**Superseded832-core solve:** session54194,PID37312,started10:35:51UTC:

`tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`

Input above; output `tmp/south-fork-expanded-flow-to600s-v1-20260912`;
8000 additional steps of0.05s,2000-step frame interval. Local step0 is200s;
step2000 will be300s; step8000 will be600s. Do not overwrite its executable or
inputs. Verify this process/handle directly before future actions. Actual-run
`restart_audit.json` independently passes the same full-cell fidelity check.
At10:36:37 it was live at local step40/202s, all state/mass gates passing.

## Next work recorded at10:38UTC (see latest update above)

Inspect every later COMPLETE snapshot for wet artificial banks, settling and
section discharge. If additional edges become wet, use evidence-driven source-
exact expansion and the verified checkpoint path; do not mask them or silently
pretend reflecting walls are physical banks. Do not repeatedly recook from the
original inferred warm start.

Update gameplay shared-atlas mapping/availability for the832-core domain rather
than reusing the old826-core slice index. The799 geometry source packets and
route do not move. Shared immutable h/u/v atlas loading, exact packet bed and
availability checks still need implementation. Remaining Cartesian boulder-
height/baseline paths, scene/route/terrain/collision integration, full actual
motion/visual/cost acceptance, later rivers and the rest of the goal remain open.
