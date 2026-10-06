# Displayed-frame froth phase — September 13, 2026

Previous goal turn only reconfirmed the30FPS target and eight budget tests:
no gameplay progress. This turn implements the optical clock mismatch found
by the preceding source/knockout observations, not another density/color tweak.

The production clump and local lace both use a one-second two-phase backtrace.
Their material inputs were MaterialExpressionTime, although transported foam
already uses committed water duration. A held GPU frame could therefore keep
animating on wall time. The new helper reads the clock belonging to the actual
displayed texture. Legacy readback attaches its captured simulation timestamp
to unused registration-row texel1 (marker3); GPU-owned marker2 is preserved.
Data texels and origin/cell registration texel0 remain unchanged. The whole
immutable payload is still uploaded together and sampled for raft support.

Outside the detail window, the optical clock comes from the committed CPU foam
field's elapsed duration. Inside it, phase comes directly from the displayed
GPU frame. The existing4m boundary weight interpolates full clocks before phase
wrapping. High/low float pairs retain phase at long durations; no wall-time
fallback, density/source/velocity changes, timestep cuts or geometry edits.
Each solver retains its existing initialization epoch; this does not change
the physical clock or promote the experimental total-depth solver.

The editor builder and guarded saved-material installer are updated together.
Only the registered Cartesian material parent gets the new path; historical
non-Cartesian variants are not silently frozen. The installer preserves and
hashes the prior material backup, map, external actors, captured ground and
save; WPO, normals and wet mask graphs remain exact. Completed tests and
installation are recorded below; no visual/performance acceptance.

Initial build56582 failed on explicit TObjectPtr-to-auto pointer deduction in
the editor builder; corrected to UMaterialExpression*. Rebuild45290 succeeds
in34.32s. The initial rebuild also emits two pre-existing C4305 double-to-float
warnings in RaftSimD6ChaosMeasuredRunner, unrelated to this edit.

First native61028:86 existing passes, new long-duration clock test fails by
.00999999046 cycles. Added precise split-clock intermediates to prevent
floating arithmetic reassociation; no tolerance change. Diagnostic build72713
succeeds12.76s. Full rerun91439 CLOSED0:87 clean passes, no warning/failure/
unrun tests,19.627378s. New test exercises56 actual GPU queries with held and
completed frames, moved registration, edge blends across integer seconds,
disabled and legacy fallback, GPU-owned clocks and100-million-second time.
Maximum circular phase error2.74553895e-6 against independent double reference
(unchanged2e-5 gate). Completed-frame support test also verifies timestamp
insertion retains every water-data texel and the candidate-overwrite guarantee.
Neither these tests nor the older filtered-froth fixture proves visual realism.

Normal saved-material installation26489 CLOSED0. Material SHA256 now
`e0c9613bc16125c0f991dc29c6421359cd0fbd6903ab0481657ed544bca55f2c`;
previous material26aa50... is preserved in the verified backup zip, SHA256
`387bb750555aaae70fe03d2253f766d1c57d23dff2cff2b5c751137e10e9aaf7`.
All459 protected files unchanged. Only the two optical time connections and
their two new nodes changed; four coverage consumers, all other nodes and
WPO/normal/wet-mask graphs remain exact. Fresh read-only commandlet1969 CLOSED0
verifies the saved six graphs, helper include and clock connections without
resaving. Both commandlets report zero errors and four existing startup warnings.
Reports: `unreal/Saved/RaftSimValidation/south-fork-committed-froth-{install,fresh}-v1-20260913.json`.
Raft DLL SHA256 `6e0941a9ead4cbd5f3c0313387718156431f4094c094118e7fc7dd1d95be0028`.

Playable paired capture72471 CLOSED0: game0, no timeout, cook suspend/resume0.
Carrier2020 wet points and GPU4226 queries share sequence112. Maximum contact
error4.765453673e-5cm; maximum GPU RGBA error5.960464478e-8, passed unchanged
gates. Reports `tmp/south-fork-committed-froth-{carrier,gpu}-v1-20260913.json`.
The inspected screenshot `unreal/Saved/Screenshots/south-fork-committed-froth-contact-v1-20260913.png`
(SHA00da636b318e72cf67d38dbea8bb49518d0f750812771dc085fe871863dea6d9)
still shows broad white coverage, rounded crests and unfinished terrain/crew.
A still image cannot establish motion acceptance. This is a clock correctness
integration, not an accepted visual transformation. Runtime log records both
CPU/detail origins0, CPU foam28.400001481s versus detail28.533334821s and
wall34.018165313s; separate completed presentation may lag both current clocks.
Map, installed material and save hashes remain exact. Do not treat the opt-in
paired capture as a performance baseline.

Ordinary no-audit capture34532 CLOSED0: game0, no timeout, cook suspend/resume0.
Current30FPS audit:18.899245FPS, mean52.912166ms, p9570.33ms, FAIL. Actual
1280x720/D3D12/Development/WindowsEditor, rows60–240 (181 rows) of300. Surface
Tick32.260021ms inclusive; Refresh11.25ms and crest selection6.24ms activate
on99/181 rows rather than prior181/181. That different actual cadence/trajectory
prevents attributing the whole FPS difference to this clock change. No cap,
resolution, timestep, source or quality adjustment. Report
`tmp/south-fork-committed-froth-frame-v1-20260913.json`, CSV SHA256
`92c50eb84ae4c10eb8c5c2fcc30eb3b3aef689a7c539baf9f31221f483f2d3ce`.
Ordinary screenshot inspected; same unresolved broad white foam/rounded crests
and unfinished crew/terrain. Screenshot SHA256
`efa17a81bbcaf6f96633f6bb9de59890804442426b510e517b102f444ed0dcba`.
Both CPU/detail epochs0; at teardown CPU foam32.800001711s, detail32.933335051s,
wall34.082868133s. Protected map/material/save hashes remain exact. No fresh
native gate in this optical pass; previous native frame/FV budgets still fail.

This turn is progress: committed-clock motion is integrated into the saved
normal material and verified against GPU, saved graph and actual playable
contact evidence. It is NOT full physical or visual acceptance. Continue
persistent surface deformation/breaking and foam motion against references;
do not repeat the rejected threshold/affine/dielectric appearance candidates.
Same cook84534/PID32144 verified live5026.5s/local20530 after both captures;
5000 state/banks pass but remain settling. Next5100/local22000 BOTH audits.

Latest ordinary measurement is18.899245FPS/p9570.33ms, FAIL30. The full
physical breaking/entrainment, convincing motion, terrain/crew, remaining
rivers, release checks and final commit are still unfinished.
