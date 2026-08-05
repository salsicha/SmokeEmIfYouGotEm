# Production character integration

RaftSim's runtime character host prefers production skeletal-character wrappers and
keeps the existing project-owned procedural avatar only as a deterministic fallback.
This prevents missing optional art from breaking gameplay while making the release-art
state directly queryable through `ARaftSimCrewAvatarActor::IsUsingProductionVisual()`.

## Production asset contract

The first-party UE 5.8 authoring pipeline creates editable source characters under
`/Game/RaftSim/Characters/Authoring/MetaHumans` and optimized cookable actors at:

- `/Game/RaftSim/Characters/Production/MetaHumans/MHC_RaftSim_Guide/BP_MHC_RaftSim_Guide`
- `/Game/RaftSim/Characters/Production/MetaHumans/MHC_RaftSim_Crew_01/BP_MHC_RaftSim_Crew_01`
- `/Game/RaftSim/Characters/Production/MetaHumans/MHC_RaftSim_Crew_02/BP_MHC_RaftSim_Crew_02`
- `/Game/RaftSim/Characters/Production/MetaHumans/MHC_RaftSim_Crew_03/BP_MHC_RaftSim_Crew_03`
- `/Game/RaftSim/Characters/Production/MetaHumans/MHC_RaftSim_Crew_04/BP_MHC_RaftSim_Crew_04`

Both MetaHuman asset trees are intentionally local-only. Epic licenses downloaded/generated
characters for distribution inside a cooked project, while source-format Licensed Content
may not be publicly redistributed. This public repository therefore commits the deterministic
builders, integration code, sanitized manifests, hashes, and rendered evidence, but ignores
the editable and optimized `.uasset` binaries. Release cooks are made from a validated local
roster and distributed as packaged game artifacts.

The native `ARaftSimMetaHumanCrewVisualActor` instantiates each optimized Blueprint and
uses its exact assembled body, face, eyes, teeth, identity textures, wardrobe and groom
assets. A hidden poseable body with the same production skeleton remains authoritative for
the deterministic rafting solve. The assembled anatomical body follows it under the
project-owned fitted wetsuit, while the generated garment is retained for audit but hidden
behind rafting PPE. The assembled face is rigidly aligned to the driven head and uses the
project-owned `MetaHumanFaceCropV2` material-instance hierarchy to remove only the
conventional shoulder/chest apron below the neoprene collar. Groom assets and their reviewed
card/mesh LODs remain audited but are suppressed beneath the mandatory helmet; the baked
face representation owns eyebrows and eyelashes in gameplay. Runtime never calls Epic
services.

The roster gate is all-or-nothing. All five packages must exist before any of them is
selected; corrupt classes or missing body, face, wardrobe, hair, eyebrow, or eyelash assets
restore the complete CC0 fallback. The adapter's blank MetaHuman archetype remains available
only when instantiated directly for offline diagnostics; it cannot mask an invalid declared
production roster in the shipping host.
`/Game/RaftSim/Characters/Production` is an always-cook directory so string-selected
production actors cannot disappear from packaged builds.

Custom licensed-character Blueprints remain supported at the older conventional paths or
through `ProductionCrewVisualClassPaths` and `ProductionGuideVisualClassPath`. Such a wrapper
must implement `RaftSimCrewProductionVisual`. The host calls:

- `Configure Crew Appearance` when the guide/crew identity or seat changes;
- `Apply Crew Pose` every active frame with the authoritative rafting action,
  normalized phase, intensity, and seat side.

Custom wrappers must not move the parent raft, write physics state, or replace rescue or
gameplay authority. An absent class, load failure, or wrapper without the interface fails
closed to the packaged CC0 character, then Manny only if that rights-tracked set is absent.

## MetaHuman UE 5.8 path

The installed base MetaHuman plugin can create and preview a character asset, but the
preview body/face meshes and materials are transient editor objects. The current local
release workstation has completed the required production setup:

1. Install **MetaHuman Creator Core Data** from the UE 5.8 installation options in the
   Epic Games Launcher.
2. Sign in to the Epic services used by MetaHuman Creator.
3. Auto-rig each final character and download its high-resolution texture sources.
4. Assemble with the Optimized pipeline at a reviewed quality level.
5. Run the reproducible roster build and retain its provenance/validation report.

From the repository root:

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash \
  -ExecutePythonScript="$PWD/unreal/Scripts/build_metahuman_production_characters.py"
```

The script authors five distinct body measurements, face proportions, complexions,
freckling, short/helmet-compatible hair preferences, brows, lashes, and dark river wardrobe;
requests `JOINTS_AND_BLEND_SHAPES` auto-rigging and high-resolution texture sources; and
assembles the Optimized pipeline at High quality into a shared Common directory. It emits
`Saved/RaftSimValidation/m9/metahuman-production-roster.json`. It never records Epic account
or service tokens. Existing valid output is reused; destructive replacement of a complete
roster requires the explicit `RAFTSIM_METAHUMAN_REBUILD=1` environment variable.

Interrupted runs are retry-safe: each new source asset is marked as owned by the roster
schema before cloud or build work begins. A retry may replace only that schema-owned partial
character and its matching partial build directory. An unmarked or differently marked asset
fails closed and requires an explicitly reviewed `RAFTSIM_METAHUMAN_REBUILD=1` run.

Wardrobe, groom, and instance-parameter edits use UE 5.8's live preview collection and are
explicitly propagated back to the source character both before preview assembly and after
parameter changes. This is required for those edits to survive the production build; a
visible editor preview by itself is not persistence evidence.

Preflight requires the installed texture-synthesis model, default garment, and nonempty
hair/brow/lash inventories. MetaHuman Creator Core Data is installed and the current report
records 1,783 loadable optional assets, the texture-synthesis model, and a complete five-
character optimized roster. The CC0 set remains a packaged fail-closed fallback, not the
accepted production presentation.

Epic's editor subsystem rejects assembly when the character is not rigged or lacks
downloaded texture sources. Duplicating the gray preview meshes is not an acceptable
release workaround because it discards the production textures, stable build output,
and packaging contract.

After a successful roster build, render the matched full-body and helmet-turntable evidence set:

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash \
  -ExecutePythonScript="$PWD/unreal/Scripts/capture_metahuman_production_roster.py"
```

The capture harness requires all five optimized Blueprint classes, fixed turntable lighting
and camera geometry, finite assembled bounds, the cropped baked face shader, wetsuit body,
suppressed garment/groom layers, helmet-compatible reviewed hair representation, complete
PPE and paddle, and thirty nonempty full-body/portrait front/profile/rear renderer outputs.
It fail-closes on helmet-to-head error, rendered-face forward alignment, identity-fit scale,
visible seated waist/hip volume, and hip-centre error, then records paths, bounds, crop planes,
presentation flags, and SHA-256 hashes in
`Saved/RaftSimValidation/m9/metahuman-production-captures.json`; pixel-level photoreal,
hair/PPE, clipping, and identity review remains a human release decision.

For the guide, the same run also records matched close-torso dry and forced-swimmer-wet PFD
frames, material-instance availability, and before/after presentation wetness. This proves
that Cloth/fuzz and live wet response are wired to the production roster; it does not replace
named character-art or whitewater-safety review.

The same assembled-roster capture now fail-closes on the complete upper paddle grip. The
retained upper T-grip Contact V1 solver preserves the imported palm, metacarpal, proximal
joint, and middle pad, then corrects only each terminal finger segment to a 2.95 cm pad-centre
radius around the modeled 2.2 cm transverse handle. Axial contact is clamped to plus or minus
5.65 cm inside the rounded ends, and the distal thumb pad must oppose the middle-finger pad at
`dot <= -0.95`. All five identities pass with effectively zero upper contact error and
`dot = -1.0`, while the lower-shaft grip and palm anchors remain unchanged. Exact close views,
runtime metrics, M5, six-river map-load evidence, hashes, and the still-open topology/motion
and human approvals are recorded in
`docs/environment-captures/south_fork_full_reach/m9_upper_t_grip_contact_v1_review.json`.
This is a deterministic terminal-pad correction, not motion-captured grip deformation or
photoreal hand approval.

The current project-owned rescue-PFD source is generator V12. Its tapered soft-cell revision
uses a 33.345 x 34.22 x 42.8 cm collisionless mesh, thinner torso-wrapped front/rear foam,
zero shoulder flotation pads, and curved front/side adjustment webbing. The retained fixed-view
review and exact hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_tapered_soft_cell_pfd_v5_review.json`;
photoreal character-art and whitewater-safety acceptance remain open.

The packaged CC0 fallback has a separate renderer-backed grip regression harness:

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash -RenderOffscreen \
  -ExecutePythonScript="$PWD/unreal/Scripts/capture_cc0_production_roster.py"
```

It captures full, profile, rear, face, grip, and grip-profile views for all five identities
(30 images total) and fails closed unless both hands expose complete three-joint finger and
thumb chains. The retained palm-aligned grip V1 evidence measures at most
`5.809241088172712e-9` cm palm-anchor error, at least `134.3199920654297` degrees of upper
finger-chain closure, `230.6800079345703` degrees of lower closure, and
`55.20000076293945` degrees of thumb closure. The runtime swimmer check also requires the
grip to release when the paddle is released. Exact reports, images, hashes, rejected
iterations, and open gates are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_palm_aligned_grip_v1_review.json`.
This is a technical regression pass only: coarse hand topology, weak thumb opposition,
material compression, motion biomechanics, and named character-art and guide approval keep
photoreal and production fallback acceptance open.

The same capture now fail-closes on seated head-to-shoulder clearance. The retained V1
presentation moves only the rendered head and neck target 5 cm along solved torso-up and
reports a 21.9315 cm minimum across the five seated identities, above the 19.5 cm roster
threshold. M5 enforces a separate 9.5 cm lower envelope across its dynamic and swimmer poses.
Helmet-to-eye alignment, hands, paddle, collision, mass, raft physics, and rescue authority
are unchanged. Matched baseline/candidate frames, runtime measurements, source and evidence
hashes, and the still-open human gates are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_head_shoulder_clearance_v1_review.json`.
This is not a photoreal character approval: the broad angular collar/PFD envelope, final
anatomy and materials, and named character-art and guide review remain open.

The CC0 clavicle-span V1 follow-up corrects a smaller rig defect inside that still-open
envelope. The adapter previously translated both imported clavicle roots to the same
upper-spine point. It now retains 32 percent of each solved shoulder half-span at the inner
clavicle while leaving both upper-arm joints on their authoritative pose anchors. All five
captured identities report a 10.88 cm inner span, at most `4.6645e-9` cm shoulder-anchor
error, and unchanged paddle and head clearance. A procedural torso/sleeve cover was visually
rejected and is not present in runtime. Exact matched images, metrics, hashes, M5, and six-map
P4 evidence are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_clavicle_span_v1_review.json`.
The correction is intentionally fail-closed: its pixel change is subtle, and production cloth
skinning, neckline topology, tailoring, compression, motion review, and named approvals remain
open.

Official setup references:

- <https://dev.epicgames.com/documentation/en-us/metahuman/getting-started-with-metahuman-creator>
- <https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine>

## Release acceptance

Production character acceptance requires all five spawned avatars to report the
production path, retain finite transforms for every guide command and rescue state, and
pass the rendered rescue capture without fallback geometry. Review must also confirm
commercial rafting PPE, paddle grip/socket alignment, no raft or seat clipping, useful
LOD transitions at the gameplay camera, and the M8 frame/memory budgets.

The procedural fallback remains valuable for headless physics tests and missing-asset
diagnostics, but any fallback in representative media or a release candidate is a
fail-closed M9 visual gate.
