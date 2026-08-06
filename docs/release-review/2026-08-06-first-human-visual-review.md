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
