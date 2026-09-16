# Actual detail-water handoff replay and exact hydraulic continuation

This is a continuation of the source-coverage fix committed as `48c161868`.
The whole-scene visual, normal-menu delivery and 30FPS gates remain open.

## Actual gameplay, not a direct helper call

The three affected RaftSimRaft unity units were recompiled with the normal
module definitions, generated classes and exports. The complete gameplay DLL
was linked separately, reusing unchanged remaining objects and dependencies.
An early, Core-only temporary loader changes this process's module filename;
it does not replace any project binary or shader consumed by the live cook.
The process module inventory confirms the candidate DLL is actually loaded:

`tmp/detail-game-module-v1-20260916/UnrealEditor-RaftSimRaft.dll`

SHA256 `5ec1b5cdec5e652ad2f5038c9ee50d4b357985a0acbb89dadfbab9ac887f113b`.
This exercises real reflected components, Initialize and TickComponent, not
only direct nonvirtual coverage calls on an otherwise old gameplay component.

The opt-in `RaftSimDetailStreamingPlayProbe` observes actual post-actor ticks,
one live water detail component and one streaming controller. It checks ready
state, complete finite presented GPU frames and monotonic sequence/time. It
does not move the raft, request crops, advance physics, re-enable failed detail
or override time. It retains actual 1280x720 screenshots at selected handoffs.
Acceptance requires all of: at least120 world seconds, eight handoffs AFTER
the first ready frame,100 fresh presented frames and60 detail-simulation seconds.
The observation deadline is900 wall seconds; this is not an FPS test.

The first run terminated after120 world seconds with668 observed ticks/fresh
frames, two post-ready handoffs and44.466669 detail seconds. Its report is
**false/incomplete coverage**, despite the engine returning process exit0.
Always inspect the result JSON; do not equate shutdown success with acceptance.
The longer probe retains every gate and waits until all are met or times out.
The first report is retained at `tmp/detail-game-module-v1-20260916/result-v1.json`,
SHA256 `ccd6d050f9114b7db627be278b04b846962bb0ec1995664f52f69a558014bc36`.

The second replay session70833/PID28200 is now TERMINAL exit0, with its report
also **passed=true**:5,593 observed ticks,5,593 fresh presented frames, eight
post-ready handoffs, and372.800019 detail-simulation seconds. Handoff10 at
20:08:52 UTC completes the eight-post-start gate. Handoff5 now occurs
before the previously missing source observation: at(-5602.096,3633.939)m,
then the next window(-5634,3602)m continues presenting advancing detail frames.
The previous permanent shutdown is not reproduced at that transition.
This passes the bounded actual-game handoff/progression regression, not scene
realism or performance acceptance. Completed evidence under
`tmp/detail-game-module-v1-20260916/`:

- `result-v2.json`: `4d35a0e5d5dbdad037000a65cc1a8a3332c07e1ee03ef6b734ae8ea705866753`.
- `play-v2.log`: `40131d959a2febcb9270399b58d0fed01fc066bee477e46ee6d865360e08e2f2`.

Do not continue polling the completed session or restart it.

The first screenshot is a startup view and is unsuitable for visual acceptance.
The fifth-handoff image shows sustained water in a later downstream view, not
a camera-matched view of the rapid. It does not prove breaking/froth realism:
`result-v2-handoff-005.png`, SHA256
`ed1de9119c104b84aae941da07337df1d296ec8f694aad98b42afe303478a65f`.
Engine toolset Python startup errors remain in the log; no clean-log claim.

## Normal project entry points now running

The probe is now registered by normal non-shipping project module startup only
when `-RaftSimDetailStreamingReport=<new absolute JSON path>` is supplied.
It requires `-RaftSimEphemeralProfile` and unregisters on module shutdown.
Ordinary gameplay without the flag does not register an observer; Shipping
does not include it. The normal project unity compiled and linked separately,
including the existing GameMode pre-BeginPlay paired-terrain implementation:

`tmp/detail-game-module-v1-20260916/UnrealEditor-SmokeEmIfYouGotEm.dll`, SHA256
`71d2c54d4dcc03262456e09fc744b33c5aa5bcee5da34751008d2c9c5f8a3878`.

Session8661 waited for PID28200 to finish and now runs a distinct v3 replay,
PID32124, confirmed LIVE. It uses both separately linked modules, the normal
`-RaftSimJointReconstructionPreview=tmp/control-ablation-350s-joint-preview-v1-20260916.json`
entry point and the project-owned probe. It does NOT load the temporary
terrain/observer harness. The early loader is in `BootstrapV2` under the same
temporary directory. The normal GameMode logs verified terrain residency and
replacement on the original actor before BeginPlay at20:09:19–20 UTC. Actual
detail frames then advance (sequence78 at16.492 world seconds). The full v3
replay remains pending. Its eventual `play-v3.log` and `result-v3.json` must be
checked, together with actual loaded module paths and terrain activation.
The wrapper explicitly fails when the report is false even if engine exit is0.
This is active validation, not a claimed pass or deployment of the normal
on-disk project DLL. The active package cook's inputs remain untouched.

Three existing compatibility tests also pass against both separately linked
modules (session70860 TERMINAL exit0): `CartesianStreamingActorFollowsBothAxes`,
`CartesianWaterRegions` and `DetailSampleGrid`. These cover ordinary two-axis
handoffs/state transfer, the unchanged raft-only selector contract and source
lattice registration; they do not substitute for graphical playback.
`compatibility-tests/index.json` SHA256:
`c226b48189bcb1157970ef821b0f916c92af6529a24910f641e347c2c3366cbc`.

## Clean600s endpoint; unchanged continuation to1800s

The original full-domain solve46094/PID22940 is TERMINAL exit0 at600s.
Do not poll/restart it. All5,382,400 cells pass the state/conservation audit;
all86,720 artificial-bank faces are exactly dry. Max depth4.777406m, max
speed11.952986m/s, volume3,030,798.415241m3. Outflow53.702400m3/s versus
prescribed inflow45.306955m3/s is still not a settled state.

The new immutable restart input is
`tmp/control-ablation-600to1800s-input-v1-20260916/manifest.json`, SHA256
`c45d92e00aaf7fa98e363e17c85f7190b665754468a72c9ee56d956ca5b7de02`.
Native frame0 independently preserves all5,382,400 original cells bit-exactly,
the600s clock, original grid/bed/roughness/boundaries and zero added water.
No domain extension or changed hydraulic forcing was needed.

Continuation session40601/PID11316 is LIVE, output
`tmp/control-ablation-600to1800s-v1-20260916`,24,000 steps at0.05s with snapshots
every1,000 steps. Its absolute650s snapshot passes state AND exact-dry banks;
outflow55.873774m3/s still exceeds inflow45.306955m3/s. NEXT completed local2000
/ absolute700s must receive BOTH audits. Preserve the same process and input.

Report hashes (all under ignored `tmp/`):

| Report | SHA256 |
| --- | --- |
| `control-ablation-600s-state-v1-20260916.json` | `3d9dfdf2143c5b4b7634be89c37de85c7a74a43d919c166f0a4172249d06fcfb` |
| `control-ablation-600s-banks-v1-20260916.json` | `f69bd5d165e96e4a8f020c3b510f6d791d49ba44923c7145de2f9c83144798b8` |
| `control-ablation-600s-restart-v1-20260916.json` | `23894a404f435121537d942e5da99d181da627e77a17fd5448eef43a46cf0a47` |
| `control-ablation-650s-state-v1-20260916.json` | `552f1daaa464ee7d56212a44ff90f2a9248ef0165b7aa08446ddab707902e03d` |
| `control-ablation-650s-banks-v1-20260916.json` | `473ce609add3aca80b6f4894928332b714b0676f356ab5fecb113102a1f2a8e6` |

## Reference access, protection and remaining gates

The existing [Qweniden Troublemaker video](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
successfully replays in the browser on this turn, observed from0:00 through0:29.
Visible angular fractured banks and rock-controlled drops break into irregular
foam patches with darker translucent water between them. This is a qualitative
motion/appearance reference, not calibrated bathymetry, camera or discharge.
No remote video download or source-data promotion was performed.

All464 protected identities still comprise462 unchanged files and two previously
verified CPU-retention-only revisions. All22 original binary/manifest identities
remain unchanged. `tmp/detail-game-module-v1-20260916/protected-v1.json` SHA256:
`5b8858a67183671f27df0a2f5f0776d0809b1ec8d851ff87e86c4b556b93b188`.

Package83678/cook5852/shader5104 is still LIVE with advancing CPU on transport
permutation21. Preserve its inputs; terminal completion, archive coherence,
444 non-editor ground sources and2,405 staged runtime payload checks are pending.
Actual settled-water/camera-matched breaking/froth, normal-menu delivery, broad
contact/traversal and30FPS/p95<=33.333ms remain open. Last uncontended17.819710FPS
/ p9581.6343ms still FAILS. Colorado then Pacuare then Futaleufu, other-scene
water, crew, normalization/regressions and release remain open. Troublemaker
remains a rapid within South Fork, never a separate scenario/menu entry.
