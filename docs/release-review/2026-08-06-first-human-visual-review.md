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

Open at session end: headless candidate captures still render the
SkyAtmosphere as if the sun sat at the horizon despite a correctly bound
−50° atmosphere sun (verified by direct map probing); regenerated-asset
churn from the dusk sessions was restored to the committed Mac-canonical
state, so no defective evidence was committed. Next step is an interactive
editor session on this machine (lighting is expected to behave as on the
Mac) to validate the froth/interface changes visually and re-capture; the
South Fork committed-capture parity question (builder state vs evolved
assets) is queued behind that.
