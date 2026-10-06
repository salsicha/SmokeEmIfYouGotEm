# First named human visual review — 2026-08-06

Reviewer: repo owner (salsicha / alex moran). Reviewed on the Linux machine
from the committed capture evidence (all captures dated 2026-08-03/04, i.e.
current with the latest water milestones — these verdicts are real gaps, not
stale imagery). This record supplies the named-human decisions the
fail-closed review chain has been waiting on; per-review JSON transcription
happens as each area is re-worked and re-captured.

## Verdicts

**South Fork canonical five** (`docs/environment-captures/south_fork_full_reach/`:
chili_bar_launch_downstream, meat_grinder_guide_eye, troublemaker_approach,
coloma_bridge_context, salmon_falls_takeout):
- Water surface: acceptable.
- **Rejected: waves carry no white froth.** Wave crests read as clean water;
  no broad aerated foam anywhere breaking would produce it.

**Six-river guide-seat views**
(`docs/environment-captures/photoreal_river_previews/landscape_candidates/`):
- South Fork: water reads as water (blue). Accepted as baseline.
- **Colorado (Hance) and Chilko (Lava Canyon): rejected — water reads as
  absent or as brown/no-water.** The transmitting-water response lets the
  bed dominate; there is no convincing air/water interface.
- **Futaleufú (Terminator): rejected — surface reads as a solid, not a
  liquid.**
- **All six: rejected for absent white water / frothy splashing.**

**Character/crew set** (MetaHuman roster wrap scene, folded splash jacket
v3, CC0 crew grip captures):
- **Rejected: hands do not grab the paddle T-grip** (fingers not closed on
  the cross-handle).
- **Rejected: boots do not read as connected to the legs** (ankle gap /
  skinning discontinuity).
- **Rejected: helmets are off-center or do not read as helmets.**

These confirm, with concrete named blockers, the standing
photoreal-promotion rejections recorded across the M9 and landscape-candidate
review chain. Playtesting is deferred by the reviewer until visuals pass.

## Root-cause notes (code-grounded)

- Foam: current whitewater presentation is localized (per-site rapid-foam
  meshes, solver-gated breaking lip, bounded spray) — there is no broad
  Froude/aeration-driven froth layer in the water surface material family,
  and no foam albedo/normal texture set exists in-repo. Materials are
  code-built in `RaftSimEditor/Private/Materials/*.cpp`.
- Colorado/Chilko/Futaleufú: per-river water materials
  (`RaftSimEditorColoradoMaterial.cpp`, `RaftSimEditorChilkoWaterMaterial.cpp`,
  Futaleufú equivalents) expose scalar params (roughness/specular/opacity/
  transmission tint); the sediment/clarity tuning currently sacrifices the
  visible interface (reflection, sparkle, normal detail) that makes water
  read as water.
- Gear: helmet/boot/paddle are project-owned procedural meshes attached in
  `RaftSimCrewAvatarActor.cpp` / `RaftSimMetaHumanCrewVisualActor.cpp` /
  `RaftSimCC0CrewVisualActor.cpp`; grip closure is a pose/socket alignment
  problem, boot connection a skinning/attachment seam, helmet fit a socket
  transform + silhouette problem.

## Fix plan (ranked)

1. Broad aerated-froth layer in the shared water material family, driven by
   the solver's existing Froude/aeration fields (all six rivers + flagship),
   plus denser crest spray. Needs foam surface textures (see unlock list) or
   a procedural fallback.
2. Colorado/Chilko/Futaleufú interface response: restore reflection/spec/
   normal sparkle over the transmitting base so water reads as liquid before
   tuning sediment tints.
3. Gear pass: palm-conforming T-grip closure poses, boot/leg seam closure
   (cuff overlap), helmet socket refit + silhouette rework — or replacement
   with higher-fidelity sourced meshes (see unlock list).

## Gated asset sources (reviewer to unlock before use)

Per repo policy (free/first-party first; Fab Standard License usable in
packaged builds only, never committed), the quality gaps above now justify:
1. **Epic account sign-in inside the UE editor for Fab + Quixel Megascans**
   — foam/whitewater surface textures, water detail normals, and candidate
   helmet/boot/paddle meshes (many free/CC0 items; license recorded per item
   at intake).
2. **MetaHuman Creator cloud access** (same Epic account) — refit avatars
   and grip poses at source rather than patching attachments.

No sign-in or download happens until the reviewer approves each source.

## Remediation session addendum (same day, Linux machine)

Reviewer approved CC0 sources (ambientCG) in lieu of Fab; intake landed as
`/Game/RaftSim/Rendering/CC0WaterDetail` (16 textures, manifest committed).

Landed in code (assets regenerate via the sanctioned builders):
- Two-scale CC0 froth (open lace clotting to dense froth on the solver foam
  mask) in the authored river-water material and the live-window surface
  material; froth colour corrected from 48% gray to aerated white; a
  `RaftSim.CreateSouthForkTransmissionWater` command so the shared
  transmission parent — a one-time duplicate — can be recreated from the
  updated source without a full map rebuild.
- Interface restoration for the three rejected rivers (fresnel/sky/normal
  energy to a bounded midpoint of the accepted South Fork values; the
  near-zero values were an earlier over-correction against a clipped-white
  sheet and are documented as such in the builders).
- Crew helmet round 1: full dome with ear/nape coverage, seated lower and
  centred, safety colours replacing the hair-black default.

Headless-pipeline defects found by regenerating on Linux (all latent on the
Mac, where interactive viewports masked them):
1. Candidate captures fired with no settle frames (Lumen/TSR never
   converged offscreen) — the settled-capture 12-frame loop is now shared.
2. The preview light rig spawned via `GEditor->AddActor` with silent
   per-actor null guards — now falls back to a plain world spawn.
3. The rig SkyLight baked its cubemap at build time; headless sessions bake
   an unrendered (black) sky into the SAVED map, so regenerated maps read as
   unlit even in gameplay — the rig skylight now uses real-time capture.

First interactive playtest findings (2026-08-07, Training Eddy via PIE,
correct GPU/SM6 confirmed from the session log):
- The dev-tank map's calm water overlay ran at its designed coverage 0.0 and
  read as **no water at all** — fixed the same day: the tank (no river
  config) now forces a visible calm surface; river maps keep their authored
  coverage handoff.
- The guide's own stroke (W/S) plays audio and applies impulse but has **no
  first-person paddle model** — queued with the T-grip/boot round.
- Terrain/trees/sky absent in the tank is authored (bare diorama), not a
  defect; the reviewer should judge environments on the river maps.

Second interactive playtest finding (2026-08-07, boot menu): clicking
through the mode/run selector crashed the game during the map switch —
Array RangeCheck inside `USoundWaveProcedural::GeneratePCMData` on an audio
render worker (crashinfo pid-358247). Root cause: every menu button played
the one shared procedural confirm-tone wave through `PlaySound2D`; each
play spawns a never-finishing mixer source over the same wave (procedural
waves report indefinite duration), and the audio mixer renders sources on
parallel task workers, so stacked sources raced the wave's single-consumer
`AudioBuffer` — the window opens right after any click and widens when
level travel stops all leaked sources at once. Fixed the same day: the menu
now owns one persistent `UAudioComponent` playing the wave for the widget's
whole life (silence between cues) and clicks only `QueueAudio` — never a
second consumer. The playtest guide's menu paths were also corrected to the
M6 selector flow (Change Mode / Next Run / Start Selected Run; Free Run
unlocks every river).

Third playtest findings (2026-08-07, Training Eddy): all crew heads faced
right, helmets and PFDs clipped through the bodies, and seated crew bobbed
on flat water. All four traced and fixed the same day on the CC0
production-visual path:
- Heads/PFD: the CC0 bodies are exported facing Unreal +Y and the
  swing-only bone driver preserved that rest yaw in the whole axial chain;
  a −90° about-shaft twist now turns pelvis→head to the pose's forward.
- Face frame: the published head frame read head-local −Z as the face —
  measured 180° off against the front-authored vest in an instrumented
  roster session; corrected to +Z. Every asymmetric headgear placement had
  been presenting its rear bowl forward.
- PFD: now seated on the rendered spine (solved chest frame, spine plus
  9 cm chest-depth) instead of the host waist-pivot abstraction.
- Bob: SeatedIdle carried an ungated ±1.5/±2.0 cm torso/head oscillation at
  paddle cadence over a fixed pelvis; resting crew now sit still. Renderer
  invariants (clavicle span, anchor errors) verified unchanged.
Queued from the same roster review: per-identity helmet trim angle (the
anchor-drop constants were calibrated against the flipped face frame — the
guide's shell rides high-back, crew04's dips forward) and the vest rear
panel stack standing a few cm off the upper back in profile.

First South Fork I playtest (2026-08-08): two defects traced same day.
The map's sun sat at pitch −88 (near-zenith) while the bootstrap authors
−42/−128 Sierra daylight — a leftover from a `sunpitch=` capture override
saved into the map; a near-vertical sun disk whirls around the screen top
with every raft/camera yaw, which read as "the sun is spinning quickly
around the sky." Restored to the authored rotation (external-actor package
only; the .umap and its integrity pins are untouched). The guide's occiput
protruded behind the helmet rim: the shell centre offset and the 0.96
recommended scale were both tuned while the shell was worn backwards —
re-tuned under the corrected face frame (rear bias −2 cm, scale 1.02) and
re-verified on the roster renders. Also reported, queued next: gameplay
camera defaults to the chase view (guide POV requested), no visible guide
stroke/paddle on W, and a looping squeak in the South Fork soundscape.

Same-day round 2 (2026-08-08): the three remaining SF I reports fixed.
The "first-person" seat anchor sat 1.8 m behind the guide's eyes (an
over-shoulder framing) — moved into the eye socket, with the guide
avatar's head/helmet hidden only while the first-person camera is live
(chase toggle is C, Free Run only). The guide's own W/S/turn strokes now
hold the matching stroke pose on the stern avatar for a beat, so player
inputs are visible on the body and paddle (they previously fired audio
and impulse only). The looping squeak was the ambience layer's fixed
1250 Hz bird chirp recurring every second in a 2 s PCM loop — replaced
with sparse, deterministically pitch/time-varied chirps over a 16 s
buffer at lower level.

Round 3 corrections (2026-08-09, after the playtest re-reported both):
the spinning sun's true root cause is the weather director, not the map —
its StormDusk preset targets yaw −205, which actor-rotation normalization
can never return, so the frame-rate interpolation chased the wrap around
the full circle forever (weather cycles on T / left-stick click, adjacent
to the steering keys). The −88 pitch previously found saved in the map
was a mid-orbit snapshot of this chase, not the cause. Fixed by
interpolating along the shortest arc to the normalized-equivalent goal.
The first-person camera's fixed eye offset landed inside the chest on the
real seated pose ("all that can be seen is the inside of the life vest");
the view now seats on the guide avatar's posed head every frame. This
round also exposed that the previous round had never compiled: the build
wrapper piped Build.sh through tail and swallowed the failing exit code,
so its verification ran against stale binaries — output piping on gating
commands is now banned in session memory, with module-timestamp checks
required before claiming a build happened.

Round 4 (2026-08-10) — "the water isn't flowing": the deepest finding of
the playtest series, in three parts. (1) The reported dead water was a
diagnosis trap: the live-window log printed 0-1 presentation normals
under SI-looking names (speed_mean=0.1017 is 0.81 m/s), which briefly
mis-read a healthy Chili Bar pool as a quiescent film — the cooked
hydraulics, streaming manifest, config actor, and window solver were all
correct and running (streaming handoff to chili_bar_hole confirmed at
station 120 once the streamer got logs). Telemetry now prints both
normalized and SI fields, and the streamer's four silent death paths log.
(2) The raft truly was not carried: the rigid support stage's quadratic
drag opposed ABSOLUTE velocity, not velocity relative to the current —
identical in still water (every tank test passed), structurally unable
to transport the raft in a river (measured: water 0.63-0.79 m/s at the
hull, raft 0.001 m/s after two minutes). Drag now acts on the relative
velocity via the flex water sampler; measured free drift reaches
0.44 m/s in two minutes and tracks the local current downstream. First
verified river transport in the project. (3) Still open from the same
report: calm-water rendering on SF is the static authored band meshes
(the animated live surface only fades in with hydraulic coverage), so
pools read as frozen; and the first-person paddle rig (pawn anchors,
never populated) so strokes read in view. Both queued next.

Round 5 (2026-08-10) — "a hole opened in the water and the boat sank":
instrumented free-drift telemetry (raft vs water speed, draft, wet state,
retained water, tube pressure, fabric integrity, dry support points, and
river position every 10 s) convicted the exact mechanism at station ~235:
the cooked wet mask carries dry cells over boulder patches, those cells
have no collision actor, and every buoyancy point sampling a dry cell
contributed zero support — the hull fell through the hole in the mask
(1.2 m under at three dry points; 2.3 m once the raft centre crossed the
patch), then the run recovery teleported it back to the put-in. Damage
and overwash were cleared by the same telemetry (pressure 1.0, retained
water transient). Fix: dry-celled support points now ground at the
current (or last) wet centre waterline, so the raft rides onto bars and
boulder patches instead of submarining; verified by re-running the same
drift — minimum draft stayed normal through the patch and the raft
beached gently. Also in this round: the first-person paddle rig (the
pawn's hand/paddle anchors, empty since creation, now carry the shared
commercial blade on a stroke-swept shaft) and the standing drift
telemetry line. Note for pilots: unpiloted rafts now ground on
mid-channel bars — paddle off or steer around.

Round 6 (2026-08-10) — "the surface isn't flowing / waves should break
white". Two findings. First, the elevation report was re-verified against
the cooked data: the full 337 m of real grade is present and correctly
datum-mapped into the world (world Z = cooked Z − 120 m, exact at the
put-in); the reach played so far is the genuinely-flat Chili Bar dam pool,
with the 19 m first-kilometre cascade starting past the bar at ~station
400. Second, the South Fork band-water material asset on disk predated
the entire CC0 froth round — the builder gained white aerated breaks on
2026-08-07, but the one-time-duplicated transmission parent the river
actually renders with was never regenerated. Recreated in-session (the
recreation command's shader validation cannot pass under -nullrhi and
needs a fully initialized editor on Linux; it also needs the pinned
NVIDIA environment offscreen — one attempt lost the GPU under the shader
compile burst). The froth-review capture now shows white breaking lace
on Meat Grinder where the committed water was previously clean. Open
tuning: froth density/breadth on big rapids, capture-path exposure
(renders darker than gameplay), and calm-pool surface-motion
perceptibility (CalmRippleStrength 0.035 is a documented anti-groove
floor; raising it needs a proper visual round).

Open at session end: headless candidate captures still render the
SkyAtmosphere as if the sun sat at the horizon despite a correctly bound
−50° atmosphere sun (verified by direct map probing); regenerated-asset
churn from the dusk sessions was restored to the committed Mac-canonical
state, so no defective evidence was committed. Next step is an interactive
editor session on this machine (lighting is expected to behave as on the
Mac) to validate the froth/interface changes visually and re-capture; the
South Fork committed-capture parity question (builder state vs evolved
assets) is queued behind that.

Round 7 (2026-08-10) — stroke-feel series. Three reports in quick
succession, all in the guide-input path. (a) "one turn command gives two
strokes": ApplyTurnStroke fired its own yaw impulse and also started a
crew cadence that immediately took a stroke of its own; restructured so
whichever path owns the stroke is the only one that impulses
(bCadenceTookStroke), one tap = one stroke everywhere. (b) "can't look
around while holding a paddle key": not reproducible in the input map on
inspection; per-second look-axis instrumentation ("RaftSim look:" log
line) shipped so the next session localizes it to either the Enhanced
Input layer (no lines while key held) or the view pipeline (lines
present, view fixed). (c) "the boat turns before the paddle animation":
the crew-cadence path already phase-locked its impulse to the pose catch
(PowerImpulsePhase 0.29 of the 0.8 s cycle), but the direct branch —
used whenever no crew avatar owns the stroke — kicked the hull the same
frame the pose began, ~0.23 s before the blade visually reached water.
Direct impulses now queue through the same catch delay
(QueueDirectStrokeImpulse, fired from Tick), so blade-in-water precedes
hull response on every input path.

Round 8 (2026-08-11) — "when the paddle command is given to the crew the
guide should not also paddle; the guide needs separate controls since
the guide is using his paddle to steer". Control-scheme split, and the
right end state for a stern-guided paddle raft. Until now W/S/A/D did
double duty: they issued crew cadence commands AND animated/impulsed the
guide, a leftover from when the guide's blade was the boat's only
propulsion. Now the channels are fully separate: the number keys /
D-pad are the only crew-propulsion channel (All Forward / All Back /
Turn Left / Turn Right / Stop — and a called command now holds its
cadence until Stop or a new call, like a real standing order), while
W/S/A/D drive only the guide's own paddle. The guide's W/S power stroke
is scaled to one stern paddler (GuideSoloStrokeScale 0.35 of the old
full-boat impulse, still governed by the propulsion shortfall); A/D
stern draw/pry steering keeps full un-scaled yaw authority — stern
leverage is precisely the guide's job — and works over a standing crew
order, so "call all-forward, steer with your own blade" is now the
actual technique. Guide-paddle cadence ownership
(bCrewCommandFromGuidePaddle, the 0.75 s expiry) is deleted outright.
All guide impulses still queue through the pose-catch delay from Round
7. Controls table updated in the playtest setup doc.

Round 9 (2026-08-11) — "the crew are still not sitting on the boat,
their butts float above the boat" (second report; the 2026-08-10 8 cm
seat drop was not enough). Root cause of the recurrence: seat heights
were hand-tuned guesses layered over two hidden offsets — the RaftVisual
component rides 15.4 cm BELOW the hull frame (-TubeRadius*0.55), and the
seated pelvis's underside rides ~25 cm ABOVE the avatar origin (solved
hip centre at local Z=40, pelvis half-height 15 x stature). Net effect:
paddler glutes hovered ~35 cm over the rendered tube crown. Fix removes
the guesswork permanently: at attach time the raft scans the actual
uploaded visual mesh sections in a glute-sized column under each seat
station (production extraction and procedural fallback both covered,
component offset folded in), and places the avatar so the pelvis
underside rests on the measured tube top with a 1.5 cm compression
sink. Per-seat "RaftSim seat:" log lines record measured tube top and
final seat Z for session-log verification. Guide camera follows
automatically (it already rides the posed head).

Also this round: finally running the P1 tank gate against the new
controls caught a latent regression from the wave-coupling round — the
presentation travelling wave was being added to EVERY live water field,
so the dead-flat test tank sloshed 0.52 kg of water aboard a surface it
renders as glass (the same render/physics divergence class the coupling
exists to close, inverted). The live window now carries an explicit
travelling-wave-presentation flag: cooked river bands couple, tanks
never do.

Round 9 verification addendum: seat measurement vindicated the approach
immediately — the production raft's real tube top sits at Z=39.7 cm in
the hull frame where the derivation-from-constants chain predicted ~11,
so paddlers dropped ~9 cm onto the tubes and the guide's hand-tuned 30
was already correct (measured 29.8). P1 after the coupling gate:
retained splash load at the 4 s settle check fell 0.52 -> 0.39 kg (the
wave-slosh share is gone) and drains to zero by test end, so the
remaining red is a drain-rate-vs-contract question. The same run also
exposed a genuine open defect: drift telemetry shows the hull at
2.57 m/s on dead-still water before the test's two strokes fire
(stroke-time shortfall 0.26 proves ~2.2 m/s pre-stroke). Something in
the water/support stack self-propels the hull on flat water; the river
current has been masking it. Logged as the next physics round, with P1
as its tripwire. M5.CrewAvatarPoseProduction's failures are all
texture-platform-data reads that return size 0 under -nullrhi (asset
gate needs a real RHI on Linux); no pose or seating assert failed.

Round 9 resolution (2026-08-11, supersedes the addendum's "open physics
defect"): the still-water self-propulsion was not real, and neither was
the drain-rate question. A standalone 150 s tank run shows the raft
parked at origin the whole time (speed 0.000, retained 0 kg, draft
-21.5 cm constant), and P1 run alone in a fresh session passes as-is.
The P1 reds were STALE TEST STATE, in two layers. First, P1's P1-era
GetActiveGameWorld() took the first live game world instead of its own
(every newer test in the module already resolves its own world; the
tank test now resolves by map identity with newest-world fallback).
Second — the actual mechanism in these runs — M7.ProductionAudio drives
the SAME tank map: it strokes the raft and issues AllForward to open
the callout envelope, and never rests it; AutomationOpenMap skips
reloading an already-current map, so P1 inherited M7's raft still
driving at the propulsion-governor cap (2.44-2.57 m/s, shortfall 0.26
against the 3 m/s ceiling) and shipping 0.32-0.39 kg of its own
bow-wave overwash. Both layers fixed: P1 force-reloads the tank map
(bForceReload), and M7 issues Rest after its audio assert so it leaves
a calm world for whoever follows. Calm-water physics is clean: no
phantom forces, no slosh, no slow drain.

Round 10 (2026-08-11) — "crew animation no longer fires when paddle
command given." Round 8's split read the request backwards. The
request: W IS the crew's paddle command ("when the paddle command is
given to the crew..."), and the defect was the GUIDE stroking along
with it — his paddle is for steering, on separate controls. Round 8
instead moved the crew off W/S/A/D onto the number keys and gave
W/S/A/D to the guide's blade, so a W press showed no crew response at
all. Corrected split: W/S/A/D are crew calls again (tap = one cadence
stroke, hold = cadence, tap overrides a standing order and expires to
Rest; the guide never animates on a call), the number keys remain
standing orders, and the guide's own stern draw/pry moves to the mouse
buttons (LMB draw left / RMB pry right, gamepad left trigger for left)
with full yaw authority over any crew order, catch-delayed like every
stroke. The steer action is runtime-transient (created and mapped into
the loaded IMC in code, the rescue-fallback pattern) because
GActionSpecs mirrors the Milestone 23 input contract. Seat measuring,
tank coupling gate, and the P1/M7 test hygiene from Rounds 9's
verification all carry forward unchanged.

Round 10 addendum — "panning camera doesn't work when pressing paddle
command key." The Round 7 look instrumentation paid off: the playtest
session log shows IA_Look silent for the full duration of every held
paddle key (11 s of held-W strokes with zero look events) and firing
again the frame the key lifts, with control rotation applying correctly
whenever the action does fire (yaw moved -148 -> 208 -> 204 across the
look bursts). Verdict: Enhanced Input action-layer starvation, not the
view pipeline. Shipped a deterministic fallback: the pawn reads the
controller's raw mouse delta every frame IA_Look stays silent and
applies the identical controller rotation, flag-guarded against
double-application, with a once-per-second "RaftSim look fallback" log
line so the next session shows which path drove the camera. EI root
cause stays open as a polish item.
