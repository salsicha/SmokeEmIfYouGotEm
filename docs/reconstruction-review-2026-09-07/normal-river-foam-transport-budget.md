# Effective surface transport and spilling budget — September 12

Still incremental implementation and verification, not finished realism,
traversal, performance or release acceptance. South Fork is the scenario;
Troublemaker is only a rapid inside it, never a menu entry.

## Optical detail now follows the existing foam backtrace

The CPU foam field already adds local roller return and boulder-eddy flow to
the sampled bulk velocity before its semi-Lagrangian backtrace. The previous
local optical shaders read smoothed bulk UV1 only, so small froth detail could
move through a returning/collecting foam patch in the wrong direction.

The exact effective velocity is now retained after those contributions and
packed into **UV3** on the Cartesian carrier. UV1 bulk current, UV2 wake data,
vertex foam amount, positions and normals retain their original inputs.
Dry entries are cleared each refresh; the initial field uses sampled bulk
velocity until there is history to backtrace. This does not alter the existing
transport equation, roller/eddy calibration, momentum solver or raft forces.
Surface return remains a presentation approximation, not measured fluid flow.

Only the two local optical custom nodes are rebound from UV1 to UV3. Their
one-second renewal and numerical shader bodies are unchanged. The guarded
installer checks all other graph code (ignoring comments only), links and
values; WPO and shoreline coverage graphs match exactly and did not read UV3.
No material nodes are added. Refresh remains idempotent at691 expressions.
Map,456 external actors, ground asset and user save are hash-preserved.

Initial build fails because the new audit referenced a refresh-local array
outside its scope (log retained). Corrected build
`south-fork-surface-transport-build-v2-20260912.log` succeeds in48.35s.
Initial transport Raft DLL SHA256:
`99d7fad88c0c9799b012ddbb9685faf472152b8adf869edc7b54b0de36cac19e`.
Main game DLL rebuilt because of the actor header dependency, SHA256:
`40f149a155ccfd829a288961e6c5bd9c46bbc183c883d7c1123dbaf54db1b708`.

Installer and fresh read-only graph assertions pass in validation reports
`south-fork-surface-transport-integration-v1-20260912.json` and
`south-fork-surface-transport-fresh-v1-20260912.json`. Both editor command
sessions12424/54685 exit1 without Python tracebacks or compilation errors;
the assertion evidence is not described as a clean process-exit pass.
Separate native/D3D12 session9817 exits0:36 successes, zero warnings,
failures or unrun tests in `south-fork-surface-transport-regressions-v1-20260912/index.json`.
Packing tests now explicitly cover exact UV3 transfer, unchanged bulk/wake/
geometry/foam values, serial/parallel paths and rejection of partial fields.
Existing clipped-edge/refinement/compact-upload tests preserve all four UVs.

Material SHA256:
`094123c76f078c905e2eff67101a48aeb27788599e902cb345b4f7c46cff95f5`.
Foam shader SHA256:
`c0b05fe8b5b640f8244a62afa86cf34945a4c3ad671a41fd587d177bca4e6ec1`.
Normal shader SHA256:
`f5dacae8716300b775ee1415fe8c3b97d041418dc1dd463c35182504532e8cbe`.
Historical UV1 one-shot installers cannot be rerun against these hashes.

## Actual transport capture before source-budget correction

Normal game session58837 exits0. Audit
`tmp/south-fork-surface-transport-audit-v1-20260912.json` checks all50,625
submitted source vertices: maximum UV3 versus CPU transport error0m/s and
maximum UV1 versus supplied bulk-channel error0m/s. Of8,754 wet vertices,
8,402 differ from the published bulk flow; max difference5.586633m/s.
That difference includes bulk smoothing as well as roller/eddy adjustment;
it is NOT an isolated measurement of return velocity or GPU pixel flow.

Actual crest audit `tmp/south-fork-surface-transport-crest-v1-20260912.json.cartesian-mesh.json`:
712,440 samples, maximum1.426740832cm <= unchanged2cm; source-vertex change0,
tracking0.003492594cm. Its stated exclusions of macro temporal lag, other
base relief and GPU perturbations remain. The separate site record has9 sites,
including2 with zero estimated spilling fraction.

Frames000/039 inspected: normal terrain/canopy/water/raft render, but dense
white bands, dark upstream banding and raft/water contact appearance remain
unaccepted. `tmp/south-fork-surface-transport-motion-audit-v1-20260912.json`:
40 unique PNGs/11.654s sampled game time, fixed camera. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260912-140446.mp4`,112 sourceframes/16.301s,
SHA256`3efcd5b54e2bc62e8b5250ef44e0ae9493c4b8e60351b42dd63cb1b4f949b718`.
No continuous-reference or FPS claim from screenshots/encoder cadence.

## Spilling budget correction

The shared physical crest already scales fresh foam by the site's estimated
spilling fraction. But the pocket function remapped every positive detection
to a minimum0.62 foam strength, and pocket/boil generation bypassed that
spilling budget. Thus a zero-spill site could still continually generate a
bright return patch. The actual nine-site record corroborates the existence
of zero-spill sites; source inspection establishes the bypass.

For the Cartesian physical-crest path, pocket and boil **new-source** weights
now use the same eased site weight times estimated spilling fraction. Full
spilling retains the prior envelope; zero spilling creates no new pocket/boil
foam. The source helper clamps invalid inputs, has no positive minimum and
preserves unmigrated legacy scene calibration. Transported existing foam is
not multiplied by this gate, so it can still enter a nonspilling wave.

Shared crest, pocket and boil displacement formulas, roller/eddy velocities,
attack/release, optical density and terrain are unchanged. Lower foam amount
can change the existing foam-driven GPU micro-ripple modulation; this is not
a claim that every shaded or GPU-displaced pixel remains geometrically equal.

Build `south-fork-spilling-budget-build-v1-20260912.log` succeeds in46.28s.
New Raft DLL SHA256:
`1ec2517ee94b22b7f61b85980838591cc0539740ab674bb4f12c62012cfd9d61`.
The material and main game DLL above are unchanged. Three source-wiring tests
plus ten existing phase tests pass. Native/D3D12 session22740 exits0 with
**37 successes, zero warnings/failures/unrun**, including the new monotonic
source-budget test and all previous tests. Report
`south-fork-spilling-budget-regressions-v1-20260912/index.json` under validation.

## Final current-build gameplay and cost

Actual normal-game session26899 exits0. Final transport audit checks50,625
source vertices, complete prefix, UV3 error0m/s and preserved bulk UV1 error0m/s.
8,389 of8,754 wet vertices differ from the published smoothed bulk field,
max5.586952m/s; the same smoothing/return interpretation limits apply.
Report `tmp/south-fork-spilling-budget-transport-audit-v1-20260912.json`.

Actual crest audit `tmp/south-fork-spilling-budget-crest-v1-20260912.json.cartesian-mesh.json`:
712,152 samples, max1.427386888cm <= unchanged2cm, original-vertex change0,
tracking0.000262856cm. Original audit exclusions retained; not whole shaded
surface or raft-contact acceptance. Frames000/039 inspected: the water and
raft render, but broad white breaking cores and dark upstream banding remain
visually unaccepted. Do not call the logical source correction photorealism.

Final sampled-motion audit `tmp/south-fork-spilling-budget-motion-audit-v1-20260912.json`:
40 unique PNGs/11.626s sampled game time, fixed camera. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260912-141028.mp4`,96 sourceframes/16.181s,
SHA256`f1b6df36abc043440ed0ebcea0bfe4dddad0098840bca4c60908063fa3ec1dc9`.

Isolated profiling session93958 exits0, no timeout, exact cook suspend/resume0.
Strict completed300-row CSV audit passes:
`tmp/south-fork-spilling-budget-performance-v1-20260912.json`.
Current CSV SHA256`df5271caf3fa3bf3223c1b56950016dbb99f290aeb3b9e07f63a64571f7f9a89`.
Samples100–250, Development/D3D12/WindowsEditor,1280x720,RT off:
mean44.824275ms,p9553.2544ms,**22.309340FPS: STILL FAIL60**, GPU12.920076ms.
No causal or sustained speedup claimed. Compiler response-file check shows
`/Ox /Ot /Ob2 /fp:precise` already active for the surface/crest source files;
the frame cost is not explained by an accidental unoptimized debug build.

Mapdb3080cc…, material094123c7…, profile181d1e57… rehash unchanged after game.
No editor/game/build remains live. Same clean expanded cook68098/PID35952
continues, observed1770.5s/local3410, next complete1800s/local4000. Last complete
1700s state and banks pass; flow is unsettled and normal runtime remains600s.
NEXT physical breaking/crest-trough fidelity, remaining white-core coverage
and temporal behavior, CPU publish/refresh cost, guide/rejoin, whole-river
scenery and all later rivers/crew/release/commit. Full goal remains active.
