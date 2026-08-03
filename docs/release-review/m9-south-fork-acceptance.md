# M9 South Fork Release Acceptance Packet

Status: `awaiting_named_human_reviewers_not_approved`

This is the review handoff for the current editor technical baseline: post-v510 shoreline,
v516 renderer policy, allocation-free overwash lookup, paired Lumen probes, the v552
project-owned procedural-boulder correction, the v559 coordinated high-side pose, and
the v579 rights-tracked hair, parent-shaft head orientation, and measured helmet-fit
technical correction, plus the v587 source-restored boulder verification after rejecting
the v584-v585 texture-transfer regressions, and the v595 bounded low-discrepancy spray
distribution after rejecting and restoring the v594 broad-water roughness regression,
plus the v600 source-equivalent boulder-material restoration after rejecting the v599
generated world-aligned granodiorite branch, the v601 skeletal-neoprene body-material
override, the v606 captured-scene skylight fill correction, the v610 static-mesh
raft-material/wet-film correction, the v613 preintegrated CC0 skin response, the rejected
v616-v618 offline MetaHuman pilot, the v624 exact contact-water restoration after
rejecting all v621-v623 dedicated-shoulder brackets, the v632 retained high-side
paddle-readability correction after rejecting the oversized v629 bracket, and the
v642 retained live-surface standing-wave parity correction after fully removing the
v638-v640 contact-pillow experiment, v675 solver-resolved hydraulic relief, the v695-v705
isolated water-material review safety lane, the v709-v730 experiments-only reviewed-rock
diagnostic lane, and v735's retained soft contact-water breakup after rejecting and fully
removing the v733-v734 static chin-tuck experiment, plus the M9B.2 five-character
Optimized/High MetaHuman roster, the M9B.3 v9 project-owned production whitewater helmet,
the M9B.3 v12 project-owned flexible production paddle raft, and the M9B.3 v13
project-owned production whitewater rescue PFD, plus the M9B.3 v20 project-owned
production river boulder, the v24 flow-aligned foam, v25 microdroplet water VFX, v29
bounded local exposure, and the M9B.3 v34 project-owned production river boot with
dedicated dark-neoprene/rubber PBR materials, plus the M9B.3 v35 articulated production
paddle grip across both hands on all five avatars and the v36 palm-centred visible-paddle
contact correction, followed by the M9B.3 v42 bounded D4-aware chamber compression and
deformation-gradient tangent-frame response on the project-owned production raft, and the
M9B.3 v48 solver-gated multi-valued breaking-water lip. v48 adds a separate, non-colliding
curled sheet only at existing supercritical-to-subcritical hydraulic-jump sites; it changes
no water sampling, D3, D4, collision, buoyancy, flip, wrap, pin, damage, or rescue authority.
The current technical baseline also includes raft-and-crew foam-occlusion V1, which removes
duplicate raised foam from the raft/crew footprint without changing hydraulic or gameplay
authority. The canonical fixed-camera files now carry the current shoreline, ground, and
presentation hashes recorded in the machine-readable packet. The v269/v270 repeat is retained
as historical determinism evidence and is explicitly `exact_current: false`; it does not qualify
the changed captures. In that earlier run, independent v269 and v270 editor processes loaded
the same saved World Partition map without regeneration.
Three views are byte-identical; Meat Grinder changes 3 pixels with maximum channel delta
1, and Troublemaker changes 7 pixels with maximum channel delta 4. Every view passes the
locked per-image limits of 32 changed pixels, 0.00005 changed fraction, 0.0001 mean
absolute channel error, and maximum channel delta 8. The machine-readable evidence is
`docs/environment-captures/south_fork_full_reach/capture_repeat_evidence.json`; it records
`all_byte_identical: false` rather than overstating renderer determinism. The environment
preserves 97.2670% of strong source-backed canopy on the visible bank band, widens the
fold-free detailed terrain ribbon to 112 m, and erosion-conditions the transition to the
globally stitched v24 valley. The dominant planar walls and Salmon Falls endpoint gap are
removed; a disclosed visual-only reservoir continuation has no collision or hydraulic
authority. Solver-conditioned water normals and bounded sky-reflection modulation remain
unchanged. Fixed evidence freezes editor-only material time and disables temporal/Lumen
history plus final tonemapper grain quantization without changing runtime rendering. The
settled v255 HLOD repeat evaluates all 24 actors with zero modified packages. Five
independently morphed, game-engine-rigged MakeHuman/MPFB bodies now replace the Manny
fallback while retaining project-owned rafting equipment. All five bodies now include
weighted Hair02 geometry by Elvaerwyn with item-level CC BY 4.0 attribution. The v306 safety-gear upgrade
adds tapered PFD cells, fitted webbing and buckles, calibrated ripstop response, and
open-shell river helmets. The latest v642 source-true Meat Grinder capture records four D4
contacts, three wrapping segments, one pinned contact, one recovering contact, 0.220 m
maximum tube indentation, 0.999 final-frame wetness, and active solver-conditioned spray/mist/sheet
response. The capture command does not write raft deformation state. Its retained
gameplay-camera response uses Lumen irradiance-volume diffuse GI, preserves opaque Lumen
reflections, and limits the water itself to sky/reflection captures plus half-resolution
refraction. The bounded contact-water path drives a 63-vertex/96-triangle local water
shoulder, 39 low-discrepancy fine-spray, one mist, nine contact-foam, and 68 droplet
instances. The retained spray pass varies phase, rate, source width, arc, and card shape
without changing D4 or water authority. The v515
scene-wide reflection experiment is retained as a rejection because it turned the
boulder's upper response black. The v517 Shipping package cleanly cooked 1,082 eligible
packages and passed its functional gates. Its first cooled rendered minute passed at
15.649 ms workload p95 with zero hitches, but the confirmation run crashed after 55.057
seconds in the game-thread D3 overwash response-map rehash and wrote no report. v517 is
therefore superseded rather than qualified. The allocation-free bounded response lookup
passes a 20,000-evaluation native regression. The corrected v527 package pairs the Lumen
irradiance and occlusion probes at resolution 8, fully cooks 1,082 eligible packages from
1,089 discovered with seven platform skips, and passes 60/60 rapid cases, 39/39 full-reach
cases, all 14 keyboard/gamepad actions, save/future-version protection, and fresh-profile
persistence. Two independently launched, cooled normal-window Metal minutes passed at
13.278 and 13.747 ms workload p95 with zero hitches. Six additional `-RenderOffScreen`
diagnostics are retained as negative evidence because three passed and three failed on
wall-clock hitches; that tooling path is not used to qualify release performance. Because
the v527 package predates the v552 source/material, v559 pose, v579 character-source,
adapter, and helmet-fit corrections, the v587 restored material path, the v595
spray runtime/material change, the v600 boulder-package restoration, the v601
production-body material override, the v606 captured-sky fill, the v610 raft-material
correction, the v613 CC0 skin response, the v624 material/package restoration, the v632
crew-equipment runtime correction, and the v642 live-surface standing-wave correction,
all v527 package,
performance, and archive results are now historical rather than exact-current and must be
regenerated. This packet is intentionally fail-closed.
These images are not approved as photoreal, production art, marketing material, or
navigational guidance.
Procedural terrain and geography are used where authoritative detail is incomplete.

The v200-v202 Meat Grinder hero review is the latest isolated environment-art bracket.
The hash-gated Poly Haven `Boulder 01` intake is CC0 and imports at publisher scale with
Nanite, but it is not production-promoted. v200 and v201 are rejected for detached orange
ribbons and nearly black artificial shelves. v202 removes those generated bank surfaces and
grounds all transient boulder/pine dressing through 1,760 direct samples of the settled
DEM-derived terrain mesh, with zero procedural height fallback and no map, collision,
hydraulic, navigation, buoyancy, raft, rescue, or gameplay change. The source-grounded review
infrastructure is retained; the image is still rejected for photoreal, marketing, store,
press, trailer, and navigational use because rock repetition, smooth banks, card vegetation,
flat water volume, and synthetic lighting remain obvious. The exact record is
`docs/environment-captures/south_fork_full_reach/m9_meat_grinder_hero_v202_review.json`.
The follow-up v203 multi-donor bracket is also rejected and removed from the active seam:
six additional scan-rock variants reduce repetition, but 142 detailed small-tree analogs
resolve as pale speckles and the Meat Grinder frame changes only 0.386719% of pixels above
eight RGB levels from v202. Its capture remains negative evidence in the same review record.

The v204-v207 River Small Rocks sequence adds a second, distinct material-and-geometry
hypothesis without
changing production authority. Three official 2K Poly Haven payloads match publisher API MD5
values and pinned SHA-256 values; Unreal imports the base-color, OpenGL-normal, and packed ARM
maps with the correct color-space, compression, and green-channel settings. v204 binds the
2.9 m surface transiently to all thirteen detailed terrain components, but the production
aerial-macro blend hides it: fixed-view mean RGB deltas from v202 are only 0.03-0.58 levels.
v205 lowers that review-only macro influence and disables its edge override so the scan can be
judged. It becomes visible as a broad beige corridor sheet while pebble-scale relief still does
not resolve at guide-eye distance. v206 then imports the official displacement field and uses
1,672 reconstructed shoreline rows, 21,736 detailed-DEM terrain traces, and 39,648
non-colliding triangles to isolate source-driven geometry to station 768-1164 m. Low values
intersect the underlying terrain as pale contour ribbons. v207 narrows and lifts the band and
darkens its review tone; the fragments reduce but the result still reads as artificial shoreline
strips with seams. All four versions are rejected and geometry tuning is stopped. The hash-gated
importer, provenance, four isolated textures, opt-in review seams, coverage gates, and captures
are retained; no map, material, collision, hydraulic, navigation, water, raft, or gameplay
package is promoted. Exact evidence is in
`docs/environment-captures/south_fork_full_reach/m9_river_small_rocks_v207_review.json`.
The result confirms that texture substitution and unart-directed displacement ribbons cannot
replace coherent bank modules, sediment/rock strata, wet-edge transitions, roots/understory,
turbulent water volume, and art-directed lighting. v184 remains authoritative and every M9 gate
remains open.

The v208-v209 interior-live-oak branch-atlas sequence tests a project-owned canopy source and a
separate representation bracket without changing production ecology, placement, collision,
hydraulics, navigation, map packages, or runtime mesh references. The built-in image-generation
source contains twelve isolated `Quercus wislizeni` branch studies with no supplied reference
images. Deterministic processing produces alpha-safe 2048-square albedo/opacity, normal, and
AO/roughness/subsurface maps, with all four reserved bottom-row atlas cells transparent. v208 uses
the production oak billboard as a core plus thirty-six review branches. Its five views change only
0.16-0.92% of pixels by more than eight RGB levels from v202, and the core continues to dominate as
a dark flat crown. v209 uses a brighter isolated core and forty-eight larger cards. It changes
1.17-2.74% of pixels above eight levels but visibly regresses into pale leaf speckles and thin card
silhouettes while preserving the same billboard-like crown mass. Both variants are rejected and
card count, radius, scale, and tint tuning is stopped. Exact provenance, prompt location, source
and package hashes, pixel deltas, captures, and the superseded-v208-mesh reproducibility boundary
are recorded in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_branch_atlas_v2_v209_review.json`.
The retained source and review seam are negative evidence only and are not approved for runtime,
photoreal, trailer, store, press, marketing, or navigational use. A production attempt now requires
species-appropriate woody topology, multiple crown-age/health variants, branch-aligned leaf
clusters, controlled near/mid/far transitions, integrated roots and understory, calibrated
lighting, and named art plus ecology review. v184 remains authoritative and every M9 gate remains
open.

v210 supplies the missing true-woody prototype but still fails the visual gate. A new project-owned
2048-square bark source deterministically yields seamless albedo, normal, and packed PBR maps. The
isolated two-section mesh removes the billboard core and contains 72 tapered woody segments, 45
terminal branches, and 90 branch-aligned V2 leaf cards (1,196 triangles total). Three Python
commandlet authoring attempts correctly fail closed because commandlet mode cannot build running-
platform texture data; normal offscreen editor startup validates all six 2048-square textures at
12 mips before saving the two materials and mesh. The five-view transient pass swaps 21 HISM
components / 24,830 instances without saving the map or changing ecology, placement, collision,
hydraulics, navigation, or gameplay authority.

The topology and bark pipeline are retained as technical infrastructure, but visual promotion is
rejected. Dark, sparse leaf-card fragments expose repetitive geometric limbs instead of forming a
continuous evergreen crown; the five views change an average 3.91% of pixels by more than eight
RGB levels from v202 yet remain plainly synthetic. Exact hashes, per-view deltas, failed and
accepted authoring modes, captures, and the decision are recorded in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_true_woody_v210_review.json`. The next
canopy input must be a dense leaf-dominant cluster source with multiple crown forms and controlled
representation transitions, followed by named art/ecology review. v184 remains authoritative and
every M9 gate remains open.

v211 replaces the twig-heavy V2 leaf source with four dense, leaf-dominant terminal sprays from a
new built-in image-generation pass. The exact prompt is pinned in the deterministic generator;
the untouched keyed source, soft alpha/despill output, largest-component quadrant cleanup, 4x4
runtime atlas, tile-bounded mip padding, normal, and packed maps are hash-gated. Only tiles 0-3 are
occupied (399,118 pixels above alpha 8); all twelve reserve tiles contain zero opaque pixels. The
separate dense-woody V2 package reuses the v210 bark and 72-segment scaffold, selects the four V3
tiles across 90 cards at 1.12x scale, validates all six 2048-square textures at 12 mips, and builds
in three editor actions. The transient capture again swaps 21 components / 24,830 instances and
saves no map or gameplay-authority package.

This is a clear technical improvement over v210: continuous leaf mass replaces sparse black card
fragments, changing an average 2.04% of pixels above eight RGB levels from v210. It still fails the
photoreal gate. Four silhouettes repeat as dark rounded clumps on one visibly regular scaffold,
and near/mid/far lighting and representation transitions do not preserve believable foliage volume
or color. v211 is therefore not promoted, but V3 is retained as the strongest current technical
leaf source. Exact source/package/capture hashes and deltas are in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_dense_woody_v211_review.json`. The
next canopy candidate needs several irregular crown-age/form variants, calibrated two-sided
foliage lighting, variant selection, and controlled transitions followed by named art/ecology
review. v184 remains authoritative and every M9 gate remains open.

v212 implements that technical bracket without changing production ecology or gameplay authority.
One isolated authoring pass produces three true-woody forms: a 1,426-triangle spreading mature
crown, a 966-triangle compact river-edge crown, and a 1,196-triangle asymmetric competition crown.
Their seed, scaffold count, width, height, and directional bias are distinct. Each asset also has
real reduced render LODs at 1.00/0.34/0.12 screen size; the resulting triangle chains are
1,426/828/457, 966/561/310, and 1,196/694/383. The shared lit masked material bounds baked AO at
0.62, retains 64% of the tangent normal, uses no emissive compensation, and enables dithered LOD
transitions. The alpha-bearing leaf texture now receives the same mip alpha-coverage preservation
as the project canopy billboards.

The transient five-view capture deterministically distributes the forms by stable actor/component
identity: 8 components / 8,535 instances use spreading, 5 / 8,421 compact, and 8 / 7,874 asymmetric.
No map, source transform, ecology, collision, hydraulic, navigation, or gameplay package is saved.
This closes the prior candidate's authoring, component-distribution, lighting-bracket, and explicit
LOD-infrastructure gaps, but it does not close the visual gate. Sparse planar clusters remain
detached from exposed geometric limbs, Troublemaker and Coloma still show procedural forks and
card silhouettes, and Salmon Falls fragments into dark bars and clumps. Fixed frames also cannot
approve temporal transitions. v212 is therefore rejected; exact package/capture hashes,
distribution counts, deltas, and the full decision are pinned in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_crown_family_v212_review.json`.
Further tuning of this scaffold is stopped. The next credible canopy input is rights-reviewed
production tree geometry or an art-authored botanical trunk/branch/twig/volumetric-shoot set with
per-instance variation, roots and understory integration, moving-camera transition evidence, and
named art plus ecology approval. v184 remains authoritative and every M9 gate remains open.

v213 consumes that distinct external-art input without relaxing the same authority boundary. The
already imported Poly Haven Island Tree 01/02/03 set has a complete CC0 source manifest, 33
verified source files, three grounded Nanite meshes, thirty textures, and nine explicit
trunk/leaf/branch materials. The assets remain in `ExternalReview`; they are disclosed as generic
wind-sculpted broadleaf morphology donors, not surveyed `Quercus wislizeni` or a California
ecology claim. The capture path normalizes each donor to the existing 12.5 m × 9.2 m broadleaf
proxy envelope, preserves its source materials, and uses the same stable actor/component key to
distribute all three forms across the exact 21-component / 24,830-instance review population.
Every original world transform and mesh is restored after capture, and the saved map's timestamp
and SHA-256 remain unchanged.

The external geometry removes the generated scaffold as the primary defect, but the unmodified-
material baseline still fails the visual gate. Near and mid-field crowns resolve as very dark,
narrow masses; several branch/leaf clusters create bright, empty, or sparse artifacts; and far
views collapse back into repeated vertical black marks rather than a continuous riparian canopy.
The forms also lack approved California-live-oak species and age identity, per-instance variation,
roots, understory, and temporal transition evidence. The native editor build, exact population
gate, five fixed captures, restoration, hashes, and rejection are pinned in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_cc0_island_tree_morphology_v213_review.json`.
The rights-reviewed intake and reversible scale-normalized seam are retained, but no donor package,
map, visual baseline, release media, or gameplay authority is promoted. The next bounded bracket
must fix masked leaf/branch behavior and near/mid/far lit-material transitions on real geometry;
production still requires reviewed California live-oak forms plus named art/ecology approval.
v184 remains authoritative and every M9 gate remains open.

v214 isolates the remaining leaf-material hypothesis on the same real geometry. One review-only
material reads the four unchanged 1K CC0 leaf textures after a running-platform ten-mip gate and
uses lit masked TwoSidedFoliage with 2.0 opacity coverage, a 0.30 clip, bounded 0.45-0.85
roughness, 0.55 tangent-normal detail, 0.78 AO, modest per-instance energy variation, and no
emissive or unlit compensation. Only imported mesh slot 1 is transiently overridden; trunk and
branch materials stay fixed. The shared restoration state now preserves and restores the complete
original material-override array in addition to every mesh and world transform. The donor texture
and mesh packages remain byte-identical, the native editor rebuild passes all 46 actions, and the
map timestamp/hash remains unchanged after the five-view capture.

The result is visually ineffective. Chili Bar, Meat Grinder, and Troublemaker are byte-identical
to v213; across all five views the candidate changes only 0.021596 mean RGB and 0.089062% of pixels
above eight levels. Dark narrow crowns, bright/sparse branch sections, repeated silhouettes, and
unstable far marks remain. This closes the leaf-only scalar/material hypothesis and ends Island
Tree tuning. Exact material/source/capture hashes and the fail-closed decision are recorded in
`docs/environment-captures/south_fork_full_reach/m9_live_oak_cc0_island_tree_material_v214_review.json`.
The material and override-restoration infrastructure is retained, but the donor geometry,
material, captures, species identity, and release media are not promoted. Production canopy now
requires new reviewed California interior-live-oak geometry or equivalent authored art with
multiple age forms, per-instance variation, explicit distance transitions, roots/understory, and
named art/ecology approval. v184 remains authoritative and every M9 gate remains open.

The exact-current v214 full Python/data/source matrix reports 1,137 passes, three expected
installed-dependency-path skips, and one intentional fail-closed release-packet failure in
1,062.31 seconds. The sole failure is the existing contract that refuses to equate the current
post-v317 flexible-raft source with the historical v42 review hash; D6 and M9 evidence explicitly
require that mismatch to remain unreconciled until an accepted M9 candidate is assembled. The
JUnit SHA-256 is `133861e50b3475aba344cd3b47c3c1df1dcbe445e0011324ad0e880ea5d92fbd`.

A project-owned generated-textile pass now supplies deterministic 1024×1024 albedo,
normal, and packed AO/roughness/height maps for the raft coating, PFD ripstop, and wetsuit.
The v280 renderer-backed rescue close-up accepts the coated-fabric result only as a
technical fallback. The later v287 CC0 close-up materially improves anatomy and individual
morphology. The v306 close-up improves the Type-V PFD, webbing, buckles, helmet coverage,
retention, and guide/crew material differentiation while removing the earlier
sub-millimetre ripstop shimmer. It still rejects limited faces, generic wardrobe,
procedural PPE/body integration, and the procedural raft geometry as photoreal production
art. The source and derived hashes live in their source manifests; the explicit rejection records are
`m9_equipment_textile_fallback_v280_review.json` and
`m9_cc0_production_character_fallback_v287_review.json`, with the latest equipment result
in `m9_safety_gear_fallback_v306_review.json`.

The exact-current V10 local technical chain is green. Renderer-backed M4 v431 passes 4/4,
M5 v432 passes 5/5, renderer-backed M7 v433 passes 4/4, headless M8 v434 passes 4/4, and
reconciled manifest-sensitive fail-closed M9 v437 passes 5/5. M4, M5, and M7 contain only the
known successful-with-warning UE 5.8 `r.MotionVectorSimulation` read; M8 and M9 are clean.
The v436 Python/data/source matrix reports 1,146 passes, three expected installed-dependency-
path skips, one intentional fail-closed historical-V42 visual-source hash mismatch, and zero
unexpected failures in 466.945 seconds. V10 promotes no runtime asset, map, or gameplay authority;
the settled HLOD evidence remains content-current. All reports are stored in the repository and
locked by hash in the machine-readable acceptance packet and V10 review record.

This refresh establishes current local technical continuity only. V8 remains disabled and
rejected, direct V9 stock-template reuse is rejected and removed, and V10 is a separate opt-in,
default-off, presentation-only technical candidate. It remains photoreal-rejected and lacks named
water-VFX art and South Fork guide approval. The most recent Shipping/package/performance/archive
evidence still predates the current source and is a dirty-worktree diagnostic. A fresh clean
rebuild, package, normal-window soak, archive, and qualification remain required after a candidate
passes photoreal and named-human review.

The historical v527 Shipping package passed two normal-window measurements totalling 9,807 frames.
The worse run is 13.747 ms workload p95, 16.619 ms wall-clock p95, 1.026 ms maximum solver
time, 5,291.1 MB peak memory, and zero hitches. Its five-report, 1,272,361,448-byte archive
has SHA-256
`4f92bc38bec8cac643c656fd547b9ee79b7843d732b2132fe0d6328fd0812d53`.
Independent artifact verification passes with the dirty-worktree and nondistribution
exceptions explicitly enabled. The bundle is adhoc-signed, not Developer-ID-signed or
notarizable, so this remains same-machine engineering evidence rather than a promotable
release. It does not contain the v552 boulder, v559 pose, v579 hair/adapter/helmet-fit
correction, v587 restored material path, v595 spray state, v600 restored package, v601
skeletal-neoprene presentation, v606 captured-sky fill, v610 raft wet-film correction, or
v613 CC0 skin response, v632 crew-equipment correction, or v642 live-surface standing-wave
correction and cannot qualify the
current worktree.

The v317 flexible-raft construction pass retains the D4-authoritative deforming mesh and
adds tube-conforming chafe fabric, bonded D-ring and grab-line pads, thwart collars, and
five-crown inflated floor relief. Its isolated renderer review accepts the construction
upgrade technically after rejecting and correcting an initial clipping implementation,
but it still rejects the parametric craft, simplified wear and fastening, test-tank
presentation, and missing in-river representative evidence as final photoreal raft art.

Reviewers record identities, dated evidence, decisions, and follow-up work in
`docs/release-review/m9-south-fork-acceptance.json`. Approval requires evidence; changing
a checkbox or Boolean alone is not sufficient.

## Current fixed-camera evidence

### Chili Bar launch — downstream

![Chili Bar launch downstream](../environment-captures/south_fork_full_reach/chili_bar_launch_downstream.png)

Station 120 m; SHA-256
`8e4ca025b33404188ac1862c4ad1f4455f52a9306007714801f7179db057986c`.

### Meat Grinder — guide eye

![Meat Grinder guide eye](../environment-captures/south_fork_full_reach/meat_grinder_guide_eye.png)

Station 920 m; SHA-256
`a8ec4585afd1e41fdcc0abbcfce6cea2295fd12e4134e52a4048de5d81c6d42a`.

### Coloma bridge context

![Coloma bridge context](../environment-captures/south_fork_full_reach/coloma_bridge_context.png)

Station 5,100 m; SHA-256
`052dc8c60e59c7f03c78978fe51a9a15160ee209c1dfabddd0a2a7f52b74eb68`.

### Troublemaker approach

![Troublemaker approach](../environment-captures/south_fork_full_reach/troublemaker_approach.png)

Station 8,280 m; SHA-256
`9087825dccb34db7d0c6862876e4551e78f4364c06e9abd395201c3e15790027`.

### Salmon Falls takeout

![Salmon Falls takeout](../environment-captures/south_fork_full_reach/salmon_falls_takeout.png)

Station 48,940 m, looking upstream from the takeout; SHA-256
`fd52fcf46046e91004639946ac4e3f39043f235ea1ba4f3bf31d9b2355722d8f`.

### CC0 production-character fallback — rejected photoreal diagnostic

![Rejected v287 CC0 character diagnostic](../environment-captures/south_fork_full_reach/m9_cc0_production_character_fallback_v287_rejected.png)

Renderer-backed `RaftSim.M5.RuntimeRescueLoop` close-up; SHA-256
`98d7316037b98891bcd09511460ad1d3fe528eecf16c2f1d244da4aec149ad7e`.
Five packaged rigged bodies and zero Manny fallbacks pass functionally, but this frame is
retained specifically as evidence that character, gear, raft, and marketing presentation
remain below the photoreal gate.

### Equipment textile fallback — rejected photoreal diagnostic

![Rejected v280 raft and crew textile diagnostic](../environment-captures/south_fork_full_reach/m9_equipment_textile_fallback_v280_rejected.png)

Renderer-backed `RaftSim.M5.RuntimeRescueLoop` close-up; SHA-256
`1601ba4fba7940c5b78f325776f3c7021dc3c6827d3449d13208caf4a961d29b`.
The scenario passes functionally, but this frame is retained specifically as evidence
that the current character, PFD, and raft presentation does not pass the photoreal gate.

### Safety-gear fallback v306 — improved, still rejected as photoreal art

![Rejected v306 safety-gear diagnostic](../environment-captures/south_fork_full_reach/m9_safety_gear_fallback_v306_rejected.png)

Renderer-backed `RaftSim.M5.RuntimeRescueLoop` close-up; SHA-256
`bbb1adffc53b6bca8a8d69b53abbf3fec199f65040b6e2eb3450aa59ac1fc790`.
Exact-current M5 passes 4/4. Tapered flotation cells, a high back, side wings, shoulder
foam, centre closure, two buckle rows, lash tab, physically rescaled ripstop, and layered
open-shell helmets are present. The frame remains rejected because the parametric PPE,
generic wardrobe and faces, procedural raft, and test-tank presentation are not final
photoreal production art.

### Production whitewater helmet v9 — technical upgrade, still rejected as photoreal art

![Retained v9 production-helmet diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v9_production_helmet_technical_retained_photoreal_rejected.png)

Renderer-backed Meat Grinder D4 evidence; SHA-256
`fa581077fc3d61dd2348eb839eed705fc6d1e84c017d7c9beed7af6a7d8dedf2`.
The project-owned 24,508-triangle helmet provides a continuous asymmetric molded shell,
six separated cut-through vents, dark EPP liner, lower gasket, four-point retention,
ear pads, adjusters, fasteners, and buckle. All five production MetaHuman wrappers select
it with a maximum measured solved-head error of `1.154e-9` cm, and exact-current M5 passes
4/4. v8's merged openings were rejected as a broken-crown silhouette; v9 is retained as
the corrected production-geometry boundary. The smooth shell finish and surrounding PPE,
body/hand/paddle/pose, raft, rock, water, aerosol, shoreline, terrain, and lighting still
fail photoreal review. This image has no named human approval and is not approved for
marketing, store, trailer, press-kit, or release-media use.

### Flexible raft construction v317 — improved, still rejected as photoreal art

![Rejected v317 flexible raft diagnostic](../environment-captures/south_fork_full_reach/m9_flexible_raft_upgrade_v317_rejected.png)

Renderer-backed `RaftSim.M5.RuntimeRescueLoop -RaftSimRaftArtReview` isolated frame;
SHA-256 `e1adced1a8085b28f1f844e485caba0c310a3d8f6738546bf89dcb7d15342f11`.
The surface-projected workboat detail is accepted as the strongest project-owned flexible
raft fallback. The frame remains rejected for photoreal, marketing, store, or release-media
use, and it has no named human approval.

### Production paddle raft v12 — authored flexible geometry, still rejected as photoreal art

![Retained v12 production-raft diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v12_production_raft_v2_technical_retained_photoreal_rejected.png)

Renderer-backed `RaftSim.CaptureRapidWrapTest` evidence; SHA-256
`a9842655d33bbf61e99f33d1e7cf615ba8a882a459cd6e50a175fd659ff5b142`.
The project-owned 38,344-triangle rest mesh replaces the smooth parametric silhouette with
a 14-foot-class self-bailer: kicked ends, four chamber seams, two thwarts, inflated floor,
perimeter line, bonded reinforcement, twelve D-rings, four quarter handles, five valves,
and eight drain recesses. The cooked CPU-readable topology is copied into the collisionless
procedural presentation component and moved by the ordinary D4 field; the hidden hull,
collision, buoyancy, flip, wrap, pin, damage, and rescue remain authoritative. v2 corrects
v1's oversized rings/pads and crossed handles. Exact-current M5 passes 4/4, while the frame
retains four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
wetness, and 40/1/9/68 spray/mist/contact-foam/droplet instances. The broad wet-film
highlight, crew contact/pose, boulder, water/aerosol, shoreline, terrain, foliage, and
lighting remain photoreal-rejected. No named guide or art reviewer has approved it, and
the image is not approved for marketing or release-media use.

### Production whitewater rescue PFD v13 — authored safety gear, still rejected as photoreal art

![Retained v13 production-PFD diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v13_production_pfd_technical_retained_photoreal_rejected.png)

Renderer-backed `RaftSim.CaptureRapidWrapTest` evidence; SHA-256
`bd5e4f66c958e65240d1af20e45e3f8300b3fc5e41811d573186f906277e6e74`.
The project-owned 42.2×44.9×44.9 cm rescue-PFD asset has 21,180 authored triangles, a
2,168-triangle Nanite fallback, and five material sections. Four front foam panels, thin
back, fitted side wings, continuous shoulder bands, pockets, front entry, backup buckles
and webbing, eight adjustment points, quick-release rescue belt, tether ring, reflective
zones, placard, and lash tabs replace the four-layer procedural vest. Project-owned 1K
PfdRipstop albedo, normal, and AO/roughness maps drive the shell response. All five
production MetaHuman wrappers select it with 0.0 cm maximum measured torso-origin error;
exact-current M5 passes 4/4 and the focused source/runtime suite passes 22/22. The frame
retains four D4 contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
wetness, a 96-triangle contact patch, and 40/1/9/68 spray/mist/contact-foam/droplet
instances. The swept shoulders and broad front panels remain visibly procedural at hero
distance, and the surrounding crew, raft, boulder, water/aerosol, shoreline, terrain,
foliage, and lighting remain below the requested photoreal bar. No named guide or art
reviewer has approved it; the image is not approved for marketing or release-media use.

### Production river boulder v20 — authored Nanite geometry, still rejected as photoreal art

![Retained v20 production-boulder diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v20_production_boulder_technical_retained_photoreal_rejected.png)

Renderer-backed `RaftSim.CaptureRapidWrapTest` evidence; SHA-256
`1e78ccac76d83060bf6f84312f237c82c2265c2cbe0dea271170b6abe53ecdfd`.
The project-owned 235.8×214.5×141.9 cm closed shell has 81,920 authored triangles, a
1,766-triangle Nanite fallback, three localized physical fracture bands, two water-worn
facet fields, and one dedicated dark wet-mineral material. It is collisionless and fitted
to 96% of the existing D4 radius; the production component is visible while the legacy
procedural shell and quarantined reviewed scan are hidden. Exact-current M5 passes 4/4.
The frame retains four D4 contacts, three wraps, one pin, one recovery, 0.220 m indentation,
0.999 wetness, a 96-triangle contact patch, and 40/1/9/68 spray/mist/contact-foam/droplet
instances. v14-v19 are rejected setup/art diagnostics; v20 is the retained cached-shader
frame. Large-scale mottling and residual broad facets still read as procedural, and the
mesh is an appearance analog rather than measured site-specific Meat Grinder geology.
No named guide, art, or geology reviewer has approved it, and the image is not approved
for marketing or release-media use.

![Rejected v318 in-river flexible raft diagnostic](../environment-captures/south_fork_full_reach/m9_flexible_raft_in_river_v318_rejected.png)

The normal `RaftSim.M7.ZFullReachPresentation` chase-camera frame proves that the upgraded
raft and five crew render in the authored full-reach South Fork world. It is still a calm
Chili Bar start view, not representative rapid-scale wrap, pin, flip, spray, or convincing
dynamic-wetness evidence, and remains rejected for release-media use.

### Meat Grinder D4 wrap v460 — bounded contact-water upgrade, still rejected as photoreal art

![Rejected v460 source-true wrap diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v460_rejected.png)

Renderer-backed `RaftSim.CaptureRapidWrapTest M9_MeatGrinderD4Wrap_v460 960` evidence;
SHA-256 `e83d3675a7a3b60af8db68f6a8967a1613b94246425c39fe88ec1afd27029ed7`.
The live D4 path reports four contacts, three wrapping segments, one pinned and one
recovering contact, 0.220 m indentation, 0.998 wetness, and active spray/mist/sheet/
droplet response against a non-colliding generated closed boulder. This is the strongest
representative rapid-scale deformation evidence. The maximum-indentation segment at local
(-53.75, -100.0) cm drives a bounded immediate-instancing path with 40 fine-spray cards,
one mist card, nine horizontal contact-foam cards, and 68 small droplet cards. The soft-card
material compiles cleanly for Metal SM6 without the checker/default fallback. The deterministic manual exposure,
1.75 EV bias, restrained color contrast, sharpening, and vignette are shared by the real
guide/chase cameras rather than capture-only code. The new contact cue is a technical
improvement over v426's nearly absent response, but the procedural crew, rock, raft and
foam, calm surrounding water, limited aerosol volume, and simplified pose/gear integration
remain below the photoreal and release-media gates.

### Meat Grinder D4 wrap v482 — blended water shoulder, still rejected as photoreal art

![Rejected v482 source-true wrap diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v482_rejected.png)

Renderer-backed `RaftSim.CaptureRapidWrapTest M9_MeatGrinderD4Wrap_v482 960` evidence;
SHA-256 `178602f2817b24fe407bcdda1846ff283e88de933dd4564c0584e7cf053b3c2b`.
The exact-current frame preserves the same source-true four-contact state, with three
wrapping segments, one pinned and one recovering contact, 0.220 m indentation, and 0.998
wetness. A bounded non-colliding 9×7 procedural mesh samples the live surface at all 63
vertices, uses D4 indentation only for its local pile-up amplitude, produces 96 triangles,
and fades both height and opacity back to the live surface at every edge. The v469 shoulder
read as a separate green patch; v482 blends into the surrounding surface. Its spray
material uses cheap crossed triangular UV waves and `TLM_VolumetricNonDirectional`, compiles
cleanly for Metal SM5/SM6 without fallback, and passes the exact-current v481 Shipping soak.
The distant terrain/water seam, calm broader water, card-like spray, generated boulder,
parametric raft, crew, poses, and gear remain visibly synthetic, so this is technical
evidence only and is rejected for photoreal, marketing, store, press, and human approval.

### Meat Grinder D4 wrap v514-v516 — shoreline and renderer qualification sequence

![Rejected v514 shoreline diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v514_rejected.png)

v514 records the solver-bounded shoreline completion and retained High-preset renderer as
technical evidence; SHA-256
`9f4845fa135edd4accdeaf18606d8d742d775c6a1f1c9891b8a4667230fab84b`.
The source-true D4 state remains valid, but the synthetic people, boulder, raft, spray,
broad water, shoreline, and terrain keep the frame below the photoreal gate.

![Rejected v515 scene-wide reflection regression](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v515_rejected.png)

v515 is an explicit renderer rejection; SHA-256
`f8bc311580ee0922dd5f97e709a4bc11882e848588fab2a9e0cc5784542d2b68`.
Disabling opaque Lumen reflections collapsed the boulder's upper response to black, so the
scene-wide optimization was removed rather than accepted for its measured speed.

![Rejected v516 water-only renderer baseline](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v516_rejected.png)

v516 is the corrected renderer-backed technical baseline; SHA-256
`47dbf8d2fe047d86e0848823092f66b9f81bdde177132d420bfc3c7e333d9594`.
Opaque Lumen reflections restore the boulder response while water alone uses reflection
captures, half-resolution refraction, and no redundant distance-field shadow. The result is
still rejected for photoreal, marketing, store, press, and human approval.

### Meat Grinder D4 wrap v552 — procedural boulder correction, still rejected as photoreal art

![Rejected v552 procedural boulder correction](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v552_procedural_rejected.png)

v552 records a bounded, production-safe correction to the project-owned fallback boulder;
SHA-256 `81d3bd9ae183cbb918e406a6d0f229f271dc0b52f9959b156ea89b801650aec3`.
The deterministic mesh now has a multiharmonic radial profile, shouldered crown, corrected
tangent handedness, and a dedicated procedural mineral branch in the shared material.
The optional CC0 scan was evaluated only as a diagnostic, produced no visible pixels despite
valid component state and bounds, and remains disabled behind the existing rights/geology/
guide/art/performance review gate. D4 remains the only collision and hydraulic authority:
the matched frame retains four contacts, three wrapping nodes, one pin, one recovering node,
and 0.220 m maximum indentation. The silhouette is materially better than the earlier sphere,
but the rock is still too dark and synthetic, and the people, equipment, raft, broad water,
lighting, shoreline, and VFX still fail photoreal and release-media review.

### Meat Grinder D4 wrap v559 — coordinated high-side pose, still rejected as photoreal art

![Rejected v559 coordinated high-side pose](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v559_coordinated_highside_rejected.png)

v559 records a bounded crew-pose correction; SHA-256
`ba2be3aaaaeb1e22bf8bbe3c815745421d0e00e61b5a3520f86ea7297cf5216d`.
The high-side response now carries the shoulders, hips, knees, and progressively planted
feet with the torso and head, removing the torn/intersecting body silhouettes visible in
v552. Crew commands, reaction timing, D4 weight action, contact state, and rescue authority
are unchanged. The matched frame retains four contacts, three wrapping nodes, one pin, one
recovering node, 0.220 m maximum indentation, and 0.998 wetness. The resulting figures are
coherent technical stand-ins, but the CC0 faces and hands, helmet/PFD fit, clothing, raft,
boulder, broad water, lighting, shoreline, spray, and terrain remain below photoreal,
marketing, store, press, and human-approval standards.

### Meat Grinder D4 wrap v570 — head/helmet alignment, still rejected as photoreal art

![Rejected v570 head/helmet alignment](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v570_head_helmet_alignment_rejected.png)

v570 records a second bounded production-character correction; SHA-256
`bb3004464979dc1c36fb9e42fc433aa173ef3d6e7d979d1fb023d44fdac8d37a`.
The CC0 adapter now resolves a terminal `head → head` bone segment from the reference
bone's up axis, allowing the visible head to follow the same high-side orientation as the
helmet. A CC0-only 1.18 outer-shell allowance reduces scalp intersection without changing
the procedural fallback. The matched frame retains four contacts, three wrapping nodes,
one pin, one recovering node, 0.220 m maximum indentation, and 0.998 wetness; command,
weight-action, D4 contact, and rescue authority are unchanged. Head/helmet motion is now
coherent, but facial anatomy, hands, residual helmet/PFD fit, clothing, raft, boulder,
broad water, lighting, shoreline, spray, and terrain remain below photoreal, marketing,
store, press, and human-approval standards.

### Meat Grinder D4 wrap v579 — rights-tracked hair and parent-shaft head correction, still rejected as photoreal art

![Rejected v579 rights-tracked hair technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v579_rights_hair_technical_rejected.png)

v579 records a third bounded production-character correction; SHA-256
`4b4c7f160ef5dfbd1a12b1b5a98a819477e64da1747201f992fb08481ffad9bc`.
All five independently morphed MakeHuman/MPFB bodies now carry weighted Hair02 geometry
from three helmet-compatible styles, with item-level CC BY 4.0 provenance and attribution
to Elvaerwyn. Variant-specific hair textures, materials, skeletal-mesh slots, and usage are
validated by the 4/4 renderer-backed M5 suite. The adapter now derives terminal-head
orientation from the authored parent-to-head shaft instead of MakeHuman's unsuitable local
`+Z` axis, eliminating the approximately 90-degree backward head regression exposed by
the first hair import. Measured 18.4 cm maximum crown clearance informs the production-only
1.22 helmet shell and `[3, 0, 1]` cm center offset. The matched frame retains four contacts,
three wrapping nodes, one pin, one recovering node, 0.220 m maximum indentation, and 0.998
wetness; command, weight-action, D4 contact, and rescue authority are unchanged. This is a
real technical and rights/provenance improvement, but facial anatomy and silhouettes,
fallback hair/helmet integration, hands and poses, PFD/clothing, raft, boulder, broad water,
lighting, shoreline, spray, and terrain remain below photoreal, marketing, store, press,
and human-approval standards.

### Meat Grinder D4 wrap v587 — boulder source restored after rejected texture experiments

![Rejected v587 boulder source-restored verification](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v587_boulder_source_restored_rejected.png)

v587 is the restored pre-spray baseline; SHA-256
`7b74f0d5d71aceaca5a0e44ec10cc8a8f38be7df48b89cb6e16ae99a7c18e182`.
The v584 tangent-normal transfer and v585 scan-albedo/roughness transfer were explicitly
rejected because the reviewed scan inputs collapsed the procedural shell toward black.
Those branches were removed, and v587 restores the proven project-owned mineral-noise
source while retaining non-colliding presentation geometry and D4 as the sole collision
and hydraulic authority. The frame records four contacts, three wrapping nodes, one pin,
one recovering node, 0.220 m maximum indentation, 0.999 wetness, a 63-vertex/96-triangle
contact-water shoulder, 39 fine-spray cards, one mist card, nine contact-foam cards, and
68 droplet cards. The v579 rights-tracked hair and parent-shaft head correction remain
active. This resolves the experiment's visual regression but does not improve or approve
the boulder: it remains too dark and synthetic, and the full frame remains rejected for
photoreal, marketing, store, press, and human approval.

### Meat Grinder D4 wrap v595 — spray distribution improved, still rejected as photoreal art

![Rejected v595 spray-distribution technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v595_spray_distribution_water_restored_rejected.png)

v595 is the retained spray-upgrade comparison frame; SHA-256
`865e380c520ea078bc4a6fd77a95b66e3d2aafc6bb6a26775337615e59d214f8`.
The retained presentation pass replaces the evenly spaced single-parabola spray-card
pattern with deterministic low-discrepancy phase, rate, source-width, arc, and card-shape
variation, softens the radial card edge, and lowers spray opacity to 0.20. The v594 attempt
to vary broad-water roughness is explicitly rejected because it exposed the riverbed across
most of the hero frame; the prior broad-water source is restored. The v587 boulder asset is
byte-identical, and D4 remains the only collision and hydraulic authority. v595 records four
contacts, three wrapping nodes, one pin, one recovering node, 0.220 m maximum indentation,
0.998 wetness, a 63-vertex/96-triangle contact-water shoulder, 40 spray cards, one mist card,
nine contact-foam cards, and 68 droplet cards. The uniform spray necklace is materially
reduced, but the broad water remains planar, aerosol is still procedural, and the people,
gear, raft, boulder, lighting, shoreline, and terrain remain below photoreal, marketing,
store, press, and human-approval standards.

### Meat Grinder D4 wrap v600 — boulder material restored, still rejected as photoreal art

![Rejected v600 restored technical baseline](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v600_boulder_material_restored_rejected.png)

v600 is the retained boulder-restoration comparison frame; SHA-256
`7f3b581fee244855305dd984fe2b5da7a0345ec46f31b86f517cdfdda6ff5931`.
The v599 generated world-aligned granodiorite branch compiled, but rendered the procedural
contact boulder nearly black and emphasized its coarse facets, so it is rejected. v600
removes that runtime texture reference and regenerates the source-equivalent project-owned
mineral-noise path. The generated PNG and provenance remain unpromoted source art for a
future offline asset workflow; byte identity with v587 is not claimed because Unreal
reserialized the package. The retained v595 spray distribution remains active, and the
final frame records four contacts, three wrapping nodes, one pin, one recovering node,
0.220 m maximum indentation, 0.998 wetness, a 63-vertex/96-triangle contact-water shoulder,
40 spray cards, one mist card, nine contact-foam cards, and 68 droplet cards. This resolves
the v599 regression but does not pass photoreal, marketing, store, press, or human review.

### Meat Grinder D4 wrap v601 — skeletal neoprene improved, still rejected as photoreal art

![Rejected v601 skeletal-neoprene technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v601_skeletal_neoprene_rejected.png)

v601 is the retained skeletal-neoprene comparison frame; SHA-256
`81e00d08f52b32962ed108bfcb8aeab28e9ac169e08a72a91fdb0c7a2b16e666`.
The runtime keeps each imported variant's rights-tracked skin, eye, and hair materials, but
routes the wetsuit slot to the existing generated-neoprene material with a skeletal-mesh
shader permutation. Its 0.76 dry roughness center and restrained specular/normal response
remove much of the chrome-gray mannequin read from exposed arms and legs. The renderer
comparison accepts that as a narrow material improvement without changing pose, rescue,
D4, collision, hydraulics, or character identity. The final frame records four contacts,
three wrapping nodes, one pin, one recovering node, 0.220 m maximum indentation, 0.999
wetness, a 63-vertex/96-triangle contact-water shoulder, 39 spray cards, one mist card,
nine contact-foam cards, and 68 droplet cards. The body meshes, hands, faces, hair/helmet
fit, wardrobe construction, poses, broad water, aerosol, raft, boulder, shoreline, terrain,
and lighting remain below photoreal, marketing, store, press, and human-approval standards.

### Meat Grinder D4 wrap v606 — captured-sky fill improved, still rejected as photoreal art

![Rejected v606 captured-sky fill technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v606_captured_sky_fill_rejected.png)

v606 is the retained captured-sky lighting baseline; SHA-256
`1836536904aa943a4ee10ba56f4758953bcf129832f47b969461f4cef4ccd5d0`.
The clear-weather runtime previously reduced the map-authored captured-scene skylight to a
0.9 dry ceiling. The retained change restores the dry endpoint to 1.25 and the wet endpoint
to 0.62, applying 1.2185 at the clear-morning preset's 0.05 weather wetness. Mean frame RGB
rises from `[61.652, 70.477, 73.165]` in v601 to `[66.819, 77.720, 82.921]`, preserving
more information on backlit crew, raft, and wet rock without real-time sky recapture or any
change to D4, rescue, collision, hydraulics, or character identity. The v603 live-surface
coverage experiment and v605 lifted-mineral/roughness experiment were both rejected and
exactly restored. The frame records four contacts, three wrapping nodes, one pin, one
recovering node, 0.220 m maximum indentation, 0.999 wetness, a 63-vertex/96-triangle
contact-water shoulder, 39 spray cards, one mist card, nine contact-foam cards, and 68
droplet cards. M7 v607 passes 4/4. This is only a bounded lighting improvement: character
anatomy and integration, PPE, raft, boulder, water, aerosol, shoreline, terrain, and the
overall lighting remain below photoreal, marketing, store, press, and human-approval
standards.

### Meat Grinder D4 wrap v610 — raft wet-film response corrected, still rejected as photoreal art

![Rejected v610 raft wet-film technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v610_raft_wet_film_rejected.png)

v610 is the retained raft wet-film/material-usage baseline; SHA-256
`5ed88387977ec984f6c5438a251e9cb8aee5e1b2e740f4cb840fa8678a56b13b`.
The focused raft authoring path now emits explicit static-mesh shader usage. A v609 frame
without that usage rendered the craft as a white/default fallback and was rejected. The
corrected v610 packages preserve the authored red raft and raise only the saturated
wet-film roughness scale/maximum from 0.34/0.32 to 0.46/0.40. Tube and floor package
SHA-256 values are
`860a0c7b819b255cf9caf8b26ffdeedca64560732254d3fb830e5a2d3fce7629` and
`b24d1b19980c025bd5bd241913d2d24a8c46093a9dd13fc33c2e9940d4c8077d`.
The change slightly softens the saturated mirror-like response without changing raft
geometry, D4, rescue, collision, hydraulics, or crew identity. The matched frame preserves
four contacts, three wrapping nodes, one pin, one recovering node, 0.220 m indentation,
0.999 wetness, a 63-vertex/96-triangle contact-water shoulder, 39 spray cards, one mist,
nine contact-foam cards, and 68 droplets. Exact-current M7 v611 passes 4/4. This remains a
bounded technical material improvement: the parametric raft construction and broad
highlight, character anatomy and integration, PPE, boulder, water, aerosol, shoreline,
terrain, and overall lighting remain below photoreal, marketing, store, press, and
human-approval standards.

### Meat Grinder D4 wrap v613 — preintegrated CC0 skin response, still rejected as photoreal art

![Rejected v613 preintegrated CC0 skin technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v613_cc0_preintegrated_skin_rejected.png)

v613 is the current source-true technical verification frame; SHA-256
`03924874afa330d0d23810e69096f3f96461f27631a078f75a97ed680ce75f5f`.
The focused authoring path keeps every rights-tracked MakeHuman 2K skin atlas, skeletal
mesh, rig, and material slot. It replaces the prior Base-Color-plus-constant-roughness
response with restrained preintegrated skin, 36× neutral microdetail, 0.46–0.58 roughness,
0.16 micro-normal strength, and a 0.94 near-opaque scatter width. A first v612 broad
subsurface branch pushed hands toward orange and was rejected. The corrected v613 frame
preserves four contacts, three wrapping nodes, one pin, one recovering node, 0.220 m
indentation, 0.999 wetness, a 63-vertex/96-triangle contact-water shoulder, 40 spray cards,
one mist, nine contact-foam cards, and 68 droplets. Exact-current M5 v614 and M7 v615 pass
4/4 each. This is only a material-layer improvement: low-detail character topology,
facial expression/animation, hands, hair and PPE integration, poses, plus the raft, boulder,
water, aerosol, shoreline, terrain, and lighting remain below photoreal, marketing, store,
press, and human-approval standards.

### Offline MetaHuman guide pilot v616-v618 — adapter retained, production promotion rejected

The v616 investigation proves a bounded offline integration path without treating a blank
template as finished character art. Unreal Engine 5.8's installed MetaHuman Character core
contains the identity-template body/face skeletal meshes, DNA, skeleton, eyes, teeth, skin
material functions, region masks, and microdetail. The installed payload does not contain an
authored guide identity, groom, brows, wardrobe, or high-resolution facial albedo. Epic's
current workflow documents auto-rigging and high-resolution texture synthesis as service-backed
operations; RaftSim did not submit geometry, authenticate, accept new service terms, or call
either cloud operation during this pilot.

RaftSim now retains a dormant `ARaftSimMetaHumanCrewVisualActor` diagnostic adapter and a
self-contained `M_RaftSim_MetaHuman_Skin` technical material. The adapter uses only soft asset
paths, allocates both poseable-mesh transform buffers before the first bone write, rotates the
MetaHuman +Y reference basis into RaftSim's +X avatar contract, mirrors the deterministic rafting
pose into the shared body/face chains, and refreshes both meshes immediately. The corrected
isolated seated probe measured matching body and face head pivots at
`(6.000, 0.000, 92.618)` cm and actor bounds centered at
`(19.875, -4.871, 55.146)` cm with extent `(37.714, 29.436, 57.066)` cm. This closes the
initialization and framing defect that had left the first diagnostic in its standing reference
pose.

The visual result is explicitly rejected for production: the blank archetype is bald, lacks
brows and authored facial albedo, has placeholder-looking eyes/skin, and exposes poor
neck/shoulder deformation under the generic direct-bone solve. The installed unified sample
skin was also tested locally and remained a neutral/placeholder presentation rather than a
finished identity. Consequently the runtime guide selector does not reference the MetaHuman
class, the `MetaHumanCharacter` plugin is not enabled in the shipping project, and the complete
rights-tracked CC0 guide remains active. Exact-current M5 v618 passes 4/4 with five CC0 guide and
passenger bodies, zero Manny fallbacks, and zero auto-promoted MetaHuman pilots. The adapter and
material builder are retained only to shorten a future authored-asset intake after identity,
groom, clothing, rights, performance, and named art review are available.

### Contact-water v621-v624 — dedicated shoulder rejected and exact baseline restored

![Rejected v624 restored contact-water baseline](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v624_contact_water_restored_rejected.png)

The v621-v623 bracket tested a bounded 13×9 split-flow shoulder and a dedicated surface-lit
contact-water material without changing D4, collision, the live free surface, or any raft
state. v621 removed the old radial blob but made the hero response optically absent. v622
raised visibility and the lower `contact_port` probe exposed a transparent glass shell around
the boulder. v623 removed clear-water opacity and underside rendering, but the remaining foam
read as a pale triangular sail. All three branches are rejected. Their temporary material
asset and every repository reference were removed.

v624 restores the prior shared-card material, 9×7 grid, 63 vertices, and 96 triangles. Its
SHA-256 is `d68a387bb553fd827616f81ca66bac396e77c5bd70efec6d8d5a8475c9ec18a5`.
The matched frame records four contacts, three wrapping nodes, one pin, one recovery, 0.220 m
indentation, 0.998 wetness, 40 spray cards, one mist, nine contact-foam cards, and 68 droplets.
The UE 5.8 editor target builds, focused source/acceptance checks pass 25/25, restored
water-VFX automation passes 2/2, and exact-current rendered M7 v626 passes 4/4. v624 is
accepted only as proof that the experiment was fully restored; it is still rejected as
photoreal water and release media.

### Crew paddles v627-v632 — disappearing equipment corrected, photoreal gate still open

![Rejected v632 paddle-readability technical upgrade](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v632_paddle_readability_rejected.png)

The production adapter was not dropping equipment: the shared high-side pose explicitly hid
every paddle for all five avatars. v627 removes that impossible disappearance, places both
hands on each shaft, and carries the blade toward the commanded tube. v629 adds a modeled
convex whitewater blade and transverse T-grip, but its first full-scale outside extension
dominates the close camera and is rejected. v631 compacts the shaft and blade to the frame,
but arbitrary roll leaves most blades edge-on. Retained v632 controls the blade feather angle,
uses a 3.3 cm shaft diameter, keeps a compact modeled blade and T-grip, and preserves all five
pose-coupled paddles without adding collision.

The v632 SHA-256 is
`d7694a761ee15e83a06f4ea9b6d436a9bda9bbf4ad2ef75fed4a5008ef1db705`. The matched
frame preserves four contacts, three wraps, one pin, one recovery, 0.220 m indentation,
0.998 wetness, 40 spray cards, one mist, nine contact-foam cards, 68 droplets, and the
restored 96-triangle contact-water patch. UE 5.8 builds, exact-current M5 v634 passes 4/4,
and exact-current rendered M7 v633 passes 4/4. This is accepted only as a technical action-
readability correction; the characters, equipment integration, and scene remain rejected as
photoreal art and release media.

### Live-surface standing-wave parity v635-v642 — authored detail preserved, photoreal water gate still open

![Rejected v642 live-surface standing-wave parity frame](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v642_standing_wave_retained_rejected.png)

The moving live-water overlay previously followed the D3 surface height but omitted the
deterministic sub-grid displacement already authored into the seasonal river. Around the
raft, the overlay could therefore flatten the standing-wave shoulders it covered. Retained
v642 applies the same bounded, time-independent authored formula to the presentation mesh
and combines its analytic slopes with the sampled D3 surface normal. It keeps the existing
3 m grid, 15 Hz refresh, no-collision policy, and stricter runtime foam threshold. It does
not change a D3 sample, D4 contact, raft state, or rescue behavior.

The focused v641 automation passes 1/1, exact-current M5 v644 passes 4/4, and exact-current
rendered M7 v643 passes 4/4. The calm-water diagnostic reaches only the authored
1.8 cm base ripple; the initial South Fork patch reaches 3.19 cm. The v642 SHA-256 is
`6df6f4e16a7881d9e015760ba7137dcda0cd8e72de04c8dd523fa01614699312`.
The matched frame remains source-true with four contacts, three wraps, one pin, one
recovery, 0.220 m indentation, 0.999 final-frame wetness, 39 spray cards, one mist, nine
contact-foam cards, 68 droplets, and the restored 96-triangle contact-water patch.

An adjacent v638-v640 bracket attempted to add a bounded D4-conditioned contact pillow to
that same mesh. At 3 m spacing it reached 0.1738 m, and the isolated v639 contact-port frame
proved that the geometry formed a tan triangular sail between the raft and boulder. A 1.5 m
v640 grid still formed the sail while reaching 0.1922 m, so the representation was rejected
rather than tuned further. The entire contact-pillow API, implementation, diagnostics, and
tests were removed, and the 3 m grid was restored. The durable negative evidence is
`m9_meat_grinder_d4_wrap_v638_contact_pillow_rejected.png`,
`m9_meat_grinder_d4_wrap_v639_contact_pillow_isolated_rejected.png`, and
`m9_meat_grinder_d4_wrap_v640_contact_pillow_1_5m_isolated_rejected.png`.

v642 is accepted only as technical live-surface parity. The broad water still reads too
calm and synthetic, so this frame remains rejected as photoreal art and release media.

### Named-rapid visual parity and hitch-safe audio v647-v663 — hydraulic mismatch closed, art gate still open

![Rejected v663 named-rapid parity and thin-foam frame](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v663_named_parity_thin_foam_retained_rejected.png)

The seasonal full-reach water previously came only from the continuous transit seed while
runtime physics swapped to the cooked named-rapid D3 field. At Meat Grinder station 960 m,
the median transit surface was 446.005981 m and the cooked named-rapid surface was
446.568919 m: a 0.562938 m presentation/physics mismatch. Environment v25 now composites
all 20 validated rapid windows and all three flow bands into the continuous full-reach
products with the same 64 m smooth handoffs used by runtime streaming. A focused regression
test proves the saved station-960 surface, wet mask, depth, speed, and foam channels match
the cooked Meat Grinder field. The correction does not change D3 sampling, D4 collision,
raft state, or rescue behavior.

v648 proves that parity but exposes a broad low-frequency foam carpet. v650 attempted to
apply sparse breakup to foam, roughness, and ripple normals together; it made the authored
river surface effectively disappear and was removed. The retained v663 material uses a
finer, lower-energy deterministic breakup only for foam color and opacity while the complete
solver mask continues to drive roughness and ripple normals. This is a bounded improvement
over the cloud carpet, not final water art: convincing crest, offset-hole, breaking-wave,
and wave-train geometry is still absent.

The first exact-current M7 run also exposed a hitch-sensitive production-audio defect:
`FInterpTo` could clamp one long-frame decay step to 100% and erase a paddle transient.
The retained runtime uses frame-rate-independent exponential decay. Focused production
audio v660 passes 1/1, exact-current rendered M7 v661 passes 4/4, exact-current rendered M5
v662 passes 4/4, M4 v666 passes 3/3, M8 v667 passes 4/4, the v670 settled HLOD
repeat evaluates 24/24 actors with zero modified packages, the v671 Python/data/source
matrix passes 1,092 tests with three expected skips, and exact-current fail-closed M9 v672
passes 5/5. The final source-true
v663 frame records four contacts, three wraps,
one pin, one recovery, 0.220 m indentation, 0.999 wetness, 40 spray cards, one mist, nine
contact-foam cards, 68 droplets, and the 96-triangle contact-water patch.

The v648, v650, and v663 hashes and decisions are recorded in
`m9_meat_grinder_d4_wrap_v663_review.json`. v663 remains rejected for photoreal art and
release-media acceptance because water-scale geometry, characters, PPE, boulder, raft,
aerosol, shoreline, terrain, and lighting remain below the requested production bar.

The retained v675 follow-up sharpens only large-scale relief already present in the sampled
cooked surface. A symmetric five-sample, 12 m station stencil removes linear river grade;
depth-, speed-, and Froude-bounded activation then adds zero relief on planar or calm water
and up to 0.2624 m in the source-true Meat Grinder window. The v675 frame retains four
contacts, three wraps, one pin, one recovery, 0.220 m indentation, and unchanged D3/D4,
raft, and rescue authority. Focused water-surface v673 passes 1/1, M4 v676 passes 3/3, M5
v677 passes 4/4, M7 v678 passes 4/4, M8 v679 passes 4/4, the v680 matrix passes 1,092
tests with three expected skips, and fail-closed M9 v681 passes 5/5. The capture and metrics
are recorded in `m9_meat_grinder_d4_wrap_v675_review.json`. This remains photoreal-rejected:
the heightfield cannot overturn into a breaking lip, and foam, aerosol, people, PPE, raft,
boulder, shoreline, terrain, and lighting remain visibly synthetic.

### Isolated water-material review lane v682-v705 — retained tooling, art rejected

Two later water-art branches were evaluated without changing the accepted v675 candidate.
The v682-v685 non-heightfield breaking-lip mesh produced triangular white sheets and was
fully removed. The v687-v692 panned-noise and packed-mask foam experiments removed the
reviewed aeration field and were also rejected. The exact v675 material package was restored
from its content-addressed local object and remains SHA-256
`dd615ad20fd70cea6f5b492ae65dbe998729107fc92d90d1be703cdedea468d1`.
Focused source/release checks, native compilation, water-surface v693, and source-true v694
confirm recovery.

The retained implementation authors future material experiments only under
`/Game/RaftSim/Experiments`, can apply one explicitly named preview material to the authored
water during a diagnostic capture, and performs a read-only canonical graph audit. The
override is loaded before the evidence timers begin so shader loading cannot silently shorten
the solver and render settling interval. v698 matches the production presentation, and v699
reports 93 expressions in each package with identical canonical graph hashes and material
properties. A v700-v704 physically scaled river-UV noise attempt was then contained in this
lane: its first build exposed a float2/float3 shader error; the corrected version rendered
long straight bands and incurred multi-second frame stalls. It is rejected and quarantined.
The restored source builds, focused source/release checks pass 19/19, water-surface v705
passes 1/1, and the full v707 Python/data/source matrix passes 1,093 tests with three expected
dependency-path skips in 871.79 seconds. The final manifest-aware fail-closed M9 v708 pass is
5/5. This tooling is retained safety infrastructure, not photoreal acceptance; the v675 foam,
water-scale geometry, aerosol, people, PPE, raft, boulder, shoreline, terrain, and lighting
blockers remain open.

### Isolated reviewed-rock lane v709-v730 — render-path defect isolated, art rejected

The existing CC0 Poly Haven Rock Moss Set 01 review meshes did not render when selected by
the diagnostic actor. Raising the mesh, reversing culling, and forcing the Nanite fallback
did not change that result and were fully reverted. The exact official 1K source bundle was
then reacquired and matched all four recorded source hashes: FBX
`8fa2a2666ecc4591f59e1d45db05d86857115b55492c8522917f3de5e650e6f9`, base color
`40cea65d8aa4ee73a93b04af19963834d061eee9779c3fc2c1cba76eef812ccc`, normal
`d86555deabb910ed82b2b770d852ba5aa931d373689ff7ae028574c7b310be99`, and roughness
`4d6ec46623abd8e2cdb855f59c7ce31873ad61b36b60e4de579e9e776a497c6b`.

A clean import under `/Game/RaftSim/Experiments/RockMossSet01_BakedScale` renders all six
source meshes when LOD0 build scale remains 1× and the capture-only actor normalizes the
source-sized bounds into its existing 1.2 m contact envelope. It does not alter D4 contact,
collision, raft physics, rescue state, or ordinary gameplay selection. A capture-only
`rockmesh=` override and read-only asset audit verify rock 04 at 10,588 triangles, one UV
channel, 31,764 valid vertex instances, the expected atlas range, the three active PBR
textures, and the live Base Color/Normal/Roughness graph inputs. Exporting the base-color
uasset returns a 1024×1024 image within four code values per channel of the decoded JPEG
source. This closes the invisible-review-mesh diagnosis: the old 100× LOD build-scale render
resource was the failing path, not missing geometry, corrupt source pixels, UVs, or material
connections.

The v714-v727 frames remain rejected. The scan improves silhouette and microgeometry, but
its sunward face clips toward pale gray under the fixed South Fork camera/light response;
the normal rapid frame is additionally covered by the intended contact-water patch. The
candidate stays experimental and `production_promoted: false`. Geology, qualified-guide,
art-direction, and performance review are still required, so no CC0 scan replaces the
project-owned procedural production boulder and no photoreal or release-media gate closes.
The v731 Python/data/source matrix passed 1,095 tests with three expected dependency-path
skips in 634.60 seconds but became historical after the v735 source delta. Its exact-current
replacement, v741, passes the same 1,095 tests with three expected installed-dependency-path
skips and zero failures in 1,224.66 seconds; the JUnit report SHA-256 is
`4bd6156fd7b7c4d5445b337a27fab222ceb6f6e9250c107648ba7e68254f4b51`.

### Meat Grinder D4 wrap v735 — softer contact-water breakup, still rejected as photoreal art

The retained `m9_meat_grinder_d4_wrap_v735_contact_breakup_retained_rejected.png` frame
keeps the existing 9x7, 63-vertex, 96-triangle solver-driven contact patch and shared spray
material. Only its dynamic opacity and crossed-wave contrast change: opacity 0.38 to 0.30,
breakup gain 0.82 to 0.24, and breakup floor 0.18 to 0.66 at the existing 11x scale. This
replaces the bright cellular quilt with a softer continuous aerated fan without changing
the material package, live-water samples, D3, D4, collision, raft, or rescue authority.
The source-true final frame retains four contacts, three wraps, one pin, one recovery,
0.220 m indentation, full wetness, and 41/1/9/68 spray/mist/contact-foam/droplet instances.
The UE 5.8 target builds; focused guards pass 7/7; M4 v735 passes 3/3; M5 v736, M7 v737,
and M8 v738 each pass 4/4; the full v741 Python/data/source matrix passes 1,095 tests with
three expected skips; and fail-closed M9 v742 passes 5/5. The full scene remains rejected for photoreal and release-media
use because the water is still a non-overturning heightfield with analytic foam/aerosol and
the people, PPE, raft, boulder, shoreline, terrain, and lighting remain visibly synthetic.

### Production-character authoring/runtime bridge v744-v753 — architecture accepted, Core Data gate open

An authenticated disposable UE 5.8 pilot now proves the real MetaHuman production path:
`JOINTS_AND_BLEND_SHAPES` auto-rigging completed, high-resolution texture sources downloaded,
and an Optimized/Medium actor assembled with 184 build assets. Its matched full-body and
portrait captures are valid 1280x900 renderer output, but both show checkerboard skin and no
hair or brows because the installed engine lacks MetaHuman Creator Core Data. The pilot is
therefore retained only as negative evidence and is not copied into the game.

The shipping integration no longer needs hand-authored wrapper Blueprints. The native
MetaHuman adapter instantiates each final assembled actor, preserves its face animation,
RigLogic, grooms, eyelashes, wardrobe, and baked materials, and makes its body follow the
existing deterministic whitewater pose driver. Selection is fail-closed across the complete
five-person roster; a partial or malformed build leaves all five CC0 characters active.
Production characters are now always cooked, while Python and MetaHuman authoring services
remain editor-only and never run in a packaged game.

The reproducible authoring script performs explicit Core Data inventory checks, authors five
distinct identities, records MetaHuman licensing/provenance without credentials, requests the
production rig and texture services, builds the five optimized Blueprints, and verifies the
exact runtime class paths. v750 executed that preflight in the shipping project and correctly
reported zero Optional assets plus the missing texture-synthesis model, default garment,
hair, brows, and eyelashes without creating partial assets; its JSON report SHA-256 is
`c33644404d2fa2a3b73f4e96727d62a5bafae7bb677f9b87e0f643b15a0de5ab` and the final
authoring-script SHA-256 is
`8776bc45cde0fad12ae3c1f8c75ce288b6e1a0727022c5888411a606a90db665`.

The adapter compiles under UE 5.8. A cold v751 run also exposed that the M5 rescue test's
fixed wall-clock wait could contain too few simulation ticks during shader/screenshot stalls;
an isolated v752 rerun reached re-entry but was failed only by UE 5.8's nondeterministic
offscreen macOS IME-window teardown error. The retained test now waits for the authoritative
rescue phase with a bounded 30-second timeout and suppresses only that known engine log on
Mac. Exact-current renderer-backed v753 passes all four `RaftSim.M5` tests with zero failures;
its log/index SHA-256 values are
`6aa202a24cfda979e05269367e04dc62c3f553f4b607f76efdda2c2a0de4bf4a` and
`95670a1d9e1cf08f8f9392986ce5689c317332cfc3e466cb9049da5710c87416`.

This accepts the production replacement architecture, not the art. Core Data installation,
five successful final builds, matched in-raft captures, face/hair/helmet/PFD/hand/seat review,
and photoreal acceptance remain mandatory before the character blocker can close.

### Meat Grinder D4 wrap v24 — flow-aligned broad-water foam, still rejected as photoreal art

The retained
`m9_meat_grinder_d4_wrap_v24_flow_aligned_foam_technical_retained_photoreal_rejected.png`
frame replaces the broad-water material's generic cellular world-space noise with a
project-owned deterministic 1024×1024 grayscale mask. The v3 source contains 168 sparse,
curved, softened fragments no longer than 108 pixels. In Unreal, one tile covers about
7.1 m downstream by 3.2 m across the channel, pans downstream at 0.018 UV units per second,
and uses mirrored addressing. The breakup source remains multiplied by conditioned solver
foam, and foam roughness now follows the broken result rather than the full broad mask.
It cannot create whitewater on calm or unmasked water and does not change live sampling,
surface geometry, D3, D4, collision, raft, or rescue authority.

v21 was rejected because continuous source seams traded the former cracked-cell carpet for
dense ruler bands. v22 shortened the source fragments but still merged into parallel speed
lines at guide-eye scale. v23 is a warm-up frame only. The cached v24 repeat removes both
dominant artifacts and retains four contacts, three wraps, one pin, one recovery, 0.220 m
indentation, 0.999 wetness, the 96-triangle contact patch, and 40/1/9/68 spray/mist/contact-
foam/droplet instances. The UE 5.8 editor target builds; source/layout checks pass 20/20;
`RaftSim.P2.WaterSurfaceRenders` passes 1/1 with known headless warnings; and exact-current
M5 passes 4/4 with zero failures.

This is a technical presentation acceptance only. The sparse laces remain too clean and
linear, the free surface remains non-overturning with insufficient crest/hole/pile/wave-
train volume, and spray/mist remain card-like. No named guide or art reviewer has approved
the scale, motion, shape, or rapid fidelity, and the capture remains rejected for marketing,
store, trailer, press-kit, and release-media use.

### Meat Grinder D4 wrap v25 — finer microdroplet water VFX, still rejected as photoreal art

The retained
`m9_meat_grinder_d4_wrap_v25_microdroplet_vfx_technical_retained_photoreal_rejected.png`
matched frame keeps the v24 broad-water material and the existing solver/contact-derived
VFX classifier, trajectories, and bounded instance pools. It changes presentation only:
fine spray, mist, rapid aerosol, and droplets use lower opacity and emissive response;
their cards are substantially smaller; and the bounded fine-spray, mist, droplet, and
rapid-aerosol populations are denser. At the captured state (`spray=0.932`, `mist=0.318`,
`impact_sheet=1`, `droplets=1`) the deterministic visible populations are 91 fine-spray,
five mist, nine unchanged contact-foam, and 144 droplet cards. The right-side spray now
reads as a faint microdroplet cloud instead of the former necklace of large white cards.

The 63-vertex/96-triangle contact-water patch, contact foam, material packages, water
sampling, free-surface geometry, D3, D4, collision, raft, and rescue authority are
unchanged. The UE 5.8 editor target builds; focused source guards pass 32/32; exact-current
renderer-backed M4 passes 3/3; and M5 passes 4/4 with zero failures. This remains a bounded
soft-card implementation rather than production volumetric spray. Individual analytic
planes remain visible at hero distance, the improvement is subtle, and no named guide or
art reviewer has approved scale, opacity, motion, lighting, or rapid fidelity. v25 is
accepted as a technical VFX upgrade and rejected for photoreal, marketing, store, trailer,
press-kit, and release-media use.

### Meat Grinder D4 wrap v29 — bounded local exposure, still rejected as photoreal art

The retained
`m9_meat_grinder_d4_wrap_v29_local_exposure_technical_retained_photoreal_rejected.png`
cached repeat replaces the shared guide/chase/evidence camera's +1.75 EV response with
+1.25 EV and bounded bilateral local exposure. Highlight contrast is 0.78, shadow contrast
is 0.72, detail strength remains 1.0, and a 50% blurred-luminance blend with a 50% screen
kernel limits local ringing. The matched frame preserves more coated-fabric microtexture,
reduces the clipped white band across the wet raft, and recovers face, PFD, and wetsuit
shadow detail. No scene light, material, weather, water, D3, D4, collision, raft, or rescue
state changes.

v26 was a non-mutating +1.00 EV diagnostic and was too dark for consistent crew
readability. v27 established the +1.25 EV response without local exposure. v28 was the
first rebuilt shader-warm-up frame; v29 is the cached retained repeat. The UE 5.8 editor
target builds; focused source guards pass 33/33; and exact-current renderer-backed M4, M5,
and M7 pass 3/3, 4/4, and 4/4 with zero failures. This is a technical cinematography
improvement only. Manual non-physical exposure remains a compromise, the raft still has a
broad synthetic highlight, and character, water, rock, terrain, foliage, and lighting art
remain below the photoreal bar. No named guide or art reviewer has approved highlight
rolloff, shadow recovery, skin response, or rapid fidelity, and the frame remains rejected
for marketing, store, trailer, press-kit, and release-media use.

### Meat Grinder D4 wrap v34 — production river boot and dark PBR, still rejected as photoreal art

The retained
`m9_meat_grinder_d4_wrap_v34_production_river_boot_dark_pbr_technical_retained_photoreal_rejected.png`
frame replaces each of the ten blunt rounded procedural boot overlays with the same
project-owned, ankle-centred whitewater river-boot asset. The editable deterministic source
contains a lasted foot shell, cuff, outsole, toe and heel rands, pull tab, twelve outsole
lugs, and three vamp bands. Unreal audits 9,708 authored triangles, three material sections,
33.34×13.5×23.575 cm bounds, Nanite enablement, and a 1,704-triangle fallback. The two
collisionless components on each avatar follow the existing solved foot positions and
roster profile scale; they do not change animation, crew mass, D3, D4, collision, raft,
rescue, or progression authority. The procedural rounded footwear remains available only
for missing-asset or procedural-body fallback.

Dedicated project-owned materials now separate a textured-neoprene upper from rubber sole
and rand sections. The retained dark tuning uses the existing rights-tracked 1K
WetsuitNeoprene maps for the upper and a bounded rough rubber graph for the contact parts.
A clean FBX reimport temporarily disables the prior Nanite state so its topology audit
measures the authored LOD0, then reproducibly restores Nanite and all three material slots.

The UE 5.8 editor target builds and exact-current M5 passes 4/4 after correcting a
superseded test that confused the Nanite fallback count with the authored FBX count. The
source/import audit still requires the detailed authored topology, while runtime M5 checks
the nontrivial representation Unreal exposes after Nanite conversion. The mesh removes the
former cylinder silhouette and adds a recognizable toe, cuff and sole. v31 and v33 were
rejected for an over-gray plastic read; v32 was shadow-biased; v34 retains the darker PBR
tuning. It remains a technical upgrade rather than final character art: the generated
material cannot replace scanned or artist-authored wet-footwear response, yaw-only
placement is not skeletal ankle/toe deformation, and the surrounding body, hands, paddle
contact, and seated poses remain synthetic. M4, M7, M8, the full Python/data/source matrix,
M9, packaging, and release evidence are stale or pending after v34; water-surface and HLOD evidence remain
content-current. No named guide or art reviewer has approved the footwear or frame, which
remains rejected for marketing, store, trailer, press-kit, and release-media use.

### Upright fitted production river boot V1 — inverted read repaired, external review open

The authored boot was not rotated 180 degrees: its outsole and tread occupy negative local Z,
its cuff rises to positive Z, and its toe points along local +X. The visual inversion came from
using the full 23.575 cm source height on a deeply flexed seated pose whose solved knee is only
13 cm above the foot. The oversized cuff could rise through or above the knee and made the leg
appear to enter the sole end of the boot.

V1 explicitly constructs a +X toe-forward, +Z cuff-up basis and applies a bounded
0.88×0.92×0.68 footwear fit before the existing identity profile. The runtime reads the source
mesh's actual minimum-Z sole bound and offsets the fitted component so the tread remains at the
exact previous support height. Solved foot points remain animation authority; collision, crew
mass, raft contact, water, D3/D4, rescue, scoring, and progression are unchanged.

![Upright fitted boot guide front](../environment-captures/south_fork_full_reach/m9_upright_fitted_boot_v1_guide_full.png)

![Upright fitted boot guide profile](../environment-captures/south_fork_full_reach/m9_upright_fitted_boot_v1_guide_profile.png)

![Upright fitted boot guide rear](../environment-captures/south_fork_full_reach/m9_upright_fitted_boot_v1_guide_rear.png)

All ten boots across the five production identities pass the fitted-upright runtime invariant
with 1.0 minimum cuff-up and toe-forward alignment. The editor target builds; 36 focused source
contracts pass; M4 v556 passes 4/4, renderer-backed M5 v555 passes 5/5, rendered M7 v557
passes 4/4, and rendered M8 v558 passes 4/4. The exact-current full matrix passes 1,148 tests
with three expected dependency-path skips and zero failures in 433.05 seconds. Reconciled M9
v560 and its independent-profile confirmation v561 each pass 6/6. Rigid ankle/toe deformation
and procedural wet-footwear materials remain below final photoreal character quality, and named
character-art and guide approval are still required.

### Meat Grinder D4 wrap v35 — articulated production paddle grip, still rejected as photoreal art

The retained matched
`m9_meat_grinder_d4_wrap_v35_articulated_paddle_grip_technical_retained_photoreal_rejected.png`
frame and contact-side diagnostic exercise the complete five-avatar production roster.
The production MetaHuman adapter now caches the complete body reference skeleton and
articulates both hands through standard thumb, index, middle, ring, and pinky chains;
non-thumb metacarpals receive a small palm curl. Visible-paddle actions apply a firm,
deterministic grip, while rescue and swim states retain a light relaxed curl instead of
the flat imported reference palm.

This is a bounded visual adapter change. Existing `FRaftSimCrewAvatarPose` hand and paddle
points remain authoritative, and crew mass, water, raft, D3/D4 contact, collision, rescue,
progression, and command selection are unchanged. The UE 5.8 editor target builds, focused
character/raft contracts pass 21/21, and exact-current M5 passes 4/4. Both renderer views
show stable attached digit chains with no exploded or detached fingers, and the
paddle-bearing hands read more closed than v34.

The result remains below the requested photoreal bar. One generic curl profile does not
replace per-action grip targets, inverse kinematics, hand/shaft contact constraints, or a
motion-captured guide stroke. The coarse hand mesh, residual shaft spacing, broad seated
posture, and shoulder/elbow/torso biomechanics remain synthetic. M4, M7, M8, the complete
Python/data/source matrix, fail-closed M9, packaging, and release qualification are stale
or pending after v35; water-surface and HLOD evidence remain content-current. No named
guide or art reviewer has approved grip safety, hand placement, stroke biomechanics, or
the captures, which remain rejected for marketing, store, trailer, press-kit, and
release-media use.

### Meat Grinder D4 wrap v36 — palm-centred paddle contact, still rejected as photoreal art

The retained matched
`m9_meat_grinder_d4_wrap_v36_palm_centered_paddle_grip_technical_retained_photoreal_rejected.png`
frame and contact-side diagnostic supersede v35 as the current grip presentation. The
pose contract already described each hand point as the visible grip target, but the
production adapter had been placing the skeletal wrist pivot there. v36 derives the wrist
from the reference hand-to-`middle_metacarpal` offset for every visible-paddle state, then
solves the forearm to that wrist. The existing pose target therefore lands at the middle
palm without a detached after-the-fact correction. Rescue and swim hand targets remain
unchanged.

The UE 5.8 editor target builds, focused character/raft contracts pass 21/21, and
exact-current M5 passes 4/4. Its roster gate requires a maximum 0.25 cm middle-palm anchor
error on every rendered production avatar. Both renderer views retain stable wrists,
sleeves, and articulated digit chains while placing the shaft through the curled palm
region more credibly than v35. No command, crew-mass, water, raft, D3/D4 contact,
collision, rescue, or progression authority changes.

This remains a technical correction rather than final animation art. The wrist basis is
still shared rather than aligned to a per-action shaft/contact frame, and the generic curl,
coarse hand topology, residual blade/shaft biomechanics, broad seated posture, and
shoulder/elbow/torso motion remain synthetic. M4, M7, M8, the complete Python/data/source
matrix, fail-closed M9, packaging, and release qualification are stale or pending after
v36; water-surface and HLOD evidence remain content-current. No named guide or art reviewer
has approved grip safety, hand placement, stroke biomechanics, or the captures, which
remain rejected for marketing, store, trailer, press-kit, and release-media use.

Two follow-up orientation experiments are explicitly rejected. v37 aligned the palm-across
anatomy to the shaft or T-grip with a 65° cap but twisted foreground wrists into a mitten-
like silhouette. v38 reduced the cap to 28° and removed the worst twist, but the two review
angles did not show a clear improvement over v36. That branch was fully removed; current
grip source hashes and retained grip captures remain the exact v36 state.

A later v40 boulder experiment reused only the already rights-reviewed CC0 normal and
roughness as bounded microstructure while excluding its diffuse image. The hero renderer
produced a pale fallback-like boulder and did not improve the broad faceted silhouette, so
the candidate source was fully removed. Reauthoring the retained graph restored the matched
v36 renderer appearance, and its post-restoration M5 suite passed 4/4 with zero failures
before being superseded by v42. No v40 boulder shading change is part of the accepted
baseline.

### Meat Grinder D4 wrap v42 — D4-aware production raft, still rejected as photoreal art

The retained matched
`m9_meat_grinder_d4_wrap_v42_d4_aware_production_raft_technical_retained_photoreal_rejected.png`
frame and
`m9_meat_grinder_d4_wrap_v42_d4_aware_production_raft_contact_diagnostic.png`
make the production raft consume the D4 compression it already followed translationally.
On chamber section zero, v42 applies bounded area-preserving contact-axis squash and
reciprocal bulge using a 0.38 compression gain and 0.90 minimum compressed scale. Imported
tangent and bitangent directions also receive 52% of the analytic D4 offset gradient before
being re-orthonormalized. Topology, UVs, collision, D3/D4 authority, buoyancy, flip, wrap,
pin, damage, rescue, commands, crew mass, and progression remain unchanged.

The primary source-true frame records four contacts, three wrapping segments, one pinned
contact, one recovering contact, 0.220 m maximum indentation, 0.999 wetness, 89 fine-spray,
four mist, nine contact-foam, and 144 droplet instances, with the 96-triangle contact patch
visible. The contact diagnostic is a later runtime sample and is retained as a visual angle,
not as the source for those primary-frame counts. The UE 5.8 editor builds, focused M1
passes 1/1, and exact-current M5 passes 4/4 with zero warnings. The earlier v41 bracket used a
1.20 compression gain, 0.74 minimum scale, and full gradient response; its overinflated,
lacquered silhouette was rejected and is not part of the retained baseline.

v42 is accepted only as a bounded technical flexibility correction. The wet tube still has
a broad synthetic highlight, crew contact remains weak, and the source mesh lacks
artist-authored abrasion, repair history, manufacturing asymmetry, and fabric strain folds.
The surrounding water, foam, aerosol, boulder, people, PPE, shoreline, terrain, foliage,
and lighting remain below the requested photoreal bar. M4, M7, M8, the complete
Python/data/source matrix, fail-closed M9, packaging, and release qualification are stale or
pending after v42; water-surface and HLOD evidence remain content-current. No named guide
or art reviewer has approved the deformation, safety behavior, material response, or
captures, which remain rejected for marketing, store, trailer, press-kit, and release-media
use.

A later v43 wet-film bracket preserved the generated coating roughness at full runtime
wetness and raised the raft-only saturated roughness. The warmed frame retained the same
oversized white band and made the foreground coating read harsher, so the material change,
focused helper, and source-layout delta were fully removed. The original 2,999-line v42
material source and its 0.46 scale/0.40 cap were restored and reauthored; exact restoration
M5 passes 4/4 with zero warnings and focused M1 passes 1/1. No v43 material change is part
of the accepted baseline.

The subsequent v44 bracket added D4-gated sub-centimetre chamber creases and matching
normal slope. Neither the matched upstream-right frame nor the contact-port diagnostic
showed a material improvement, so the extra per-vertex math was fully removed. The runtime
deformer is byte-identical to retained v42, the editor rebuilds, exact restoration M5 passes
4/4 with zero warnings, and focused M1 passes 1/1. No v44 crease change is part of the
accepted baseline.

### Solver-breaking-water lip v48 — technical upgrade, photoreal rejected

![Retained v48 raft-centred breaking-water hero diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v48_flow_lace_breaking_lips_hero.png)

![Retained v48 strongest-site breaking-water diagnostic](../environment-captures/south_fork_full_reach/m9_meat_grinder_d4_wrap_v48_strongest_flow_lace_breaking_lip_review.png)

v48 closes one structural limitation of the live-water renderer: hydraulic jumps are no
longer limited to a single-valued heightfield. Each existing solver-detected
supercritical-to-subcritical transition can now drive an 8-by-8, 128-triangle curled sheet
that rises from the free surface, noses downstream, and curls upstream beneath itself. The
mesh is presentation-only, non-colliding, shadowless, and bounded to 24 sites and 3,072
triangles. It does not alter jump detection, water samples, foam-site generation, D3, D4,
buoyancy, flip, wrap, pin, damage, or rescue authority.

The exact Meat Grinder review window activates five sites and 640 triangles. The raft-centred
frame retains three wrapping contacts, one pin, 0.220 m maximum indentation, 0.998 wetness,
the 96-triangle contact-water patch, and 91/5/9/144 spray, mist, contact-foam, and droplet
instances. Its dedicated project-owned translucent material serializes the rights-tracked
foam-lace and flow-normal dependencies, compiles for Metal SM6, and does not fall back to the
default material. Exact-current water-surface, M4, and M5 automation pass 1/1, 3/3, and 4/4
with zero warnings; focused packet/source Python checks pass 34/34.

This is technical acceptance only. The strongest-site view exposes coarse riverbed and
terrain seams, hard water-patch boundaries, simplified wave shape, insufficient entrained-air
volume, limited collapsing-crest breakup, and analytic spray/mist. The full frame therefore
remains below the requested photoreal standard. No named guide or art reviewer has approved
the hydraulic scale, motion, material response, or captures, and neither image is approved
for marketing, store, trailer, press-kit, or release-media use.

### Full-reach photographic review v168 — capture path accepted, imagery rejected

![Rejected v168 Troublemaker photographic view](../environment-captures/south_fork_full_reach/photographic/troublemaker_approach.png)

The opt-in photographic capture mode enables temporal antialiasing, ambient occlusion,
Lumen GI/reflections, screen-space reflections, and twelve settle frames without changing
the deterministic evidence path or saving map packages. All five fixed views render, but
the added renderer features do not materially improve the scene: flat broad water, smooth
banks, sparse repeated canopy, limited shoreline dressing, and absent gameplay subjects
remain dominant. The capture path is retained as review infrastructure; all five images
remain rejected for photoreal, marketing, store, trailer, press-kit, and release-media use.

### Volumetric broadleaf review v169 — technical topology accepted, imagery rejected

![Rejected v169 Troublemaker photographic view](../environment-captures/south_fork_full_reach/photographic_v169_broadleaf/troublemaker_approach.png)

Interior live oak and white alder now use one coherent full-tree core plus thirty-six
smaller branch sprays in six layers, producing 148 vertices and 74 triangles per proxy.
The five fixed views show a modest reduction in obvious crossed full-tree silhouettes, but
still read as dark, repetitive card vegetation against synthetic water, terrain, banks,
and distant scenery. The renderer-backed M7 gate passes; all 30 HLOD actors rebuild and a
final repeat saves zero packages. The durable review is
`docs/environment-captures/south_fork_full_reach/m9_volumetric_broadleaf_v169_review.json`.
No named reviewer has approved it, and every photoreal and release-media gate remains open.

### Detailed terrain microrelief v170 — rejected and rolled back

![Rejected v170 Coloma terrain-relief view](../environment-captures/south_fork_full_reach/photographic_v170_terrain_relief/coloma_bridge_context.png)

v170 tested a two-metre visual terrain grid with deterministic bank-only microrelief while
keeping the four-metre source DEM as collision authority. It generated cleanly, remained
hydraulically inert, and stayed below its 28 cm displacement cap, but all five fixed views
showed no material realism gain at guide-eye distance. The cost was disproportionate:
detailed-terrain visual triangles rose from 1,467,648 to 5,870,592. The implementation and
thirteen orphaned candidate meshes were removed, while the captures and durable rejection
record remain in
`docs/environment-captures/south_fork_full_reach/m9_detailed_terrain_relief_v170_review.json`.
The accepted v169 terrain/map was regenerated with 200 stable actor identities; all 30 HLOD
actors rebuilt and a final repeat saved zero packages; renderer-backed M7 passes. v170 closes
no art, performance, named-review, media, or release gate.

The v171 shoreline-bank bracket was also rejected. It added 13 non-colliding median-edge
actors, 26,208 segments, and 157,248 triangles under a measured 94.50 cm maximum height,
without changing terrain, hydraulics, collision, or navigation. Although the editor build,
23/23 source-layout checks, native mesh contract, generation, and five-view capture passed,
the output read as a thin repeated brown shelf rather than varied natural bank morphology.
The largest fixed-view delta affected only 5.25% of pixels above eight RGB levels, and the
Meat Grinder/Troublemaker views gained a more obvious layered-plate shoreline. Candidate
source and 13 orphaned meshes were removed; captures and the durable rejection record remain
in `docs/environment-captures/south_fork_full_reach/m9_shoreline_bank_v171_review.json`.
The restored v169 map has 200 stable identities, 30/30 current HLOD actors, a zero-save final
repeat, and a passing renderer-backed M7 test. v171 closes no art, performance, named-review,
media, or release gate.

The v172 Forest Ground 03 material bracket was also rejected. It applied the existing
hash-locked, rights-reviewed CC0 4K albedo, normal, and roughness only to 13 transient
terrain components, leaving the map, collision, hydraulics, navigation, and packages
untouched. All five fixed views rendered, but the visible result was limited to isolated
bank patches; Coloma and Troublemaker gained bright tan islands and harder seams without
believable gravel, rock, root, soil, cutbank, or vegetation-transition structure. The
locked parent projects at 3.2 m while the publisher records a 2.0 m physical width, so the
direct substitution also fails source-scale fidelity. Candidate runtime and test paths
were removed; the captures and durable review remain in
`docs/environment-captures/south_fork_full_reach/m9_forest_ground_v172_review.json`.
The exact-current map and build-manifest hashes are unchanged, the rollback editor target
builds, focused source/rights suites pass 35/35, and renderer-backed M7 passes. v172 closes
no photoreal, named-review, media, or release gate.

The v173 procedural woody-debris bracket was also rejected. It used existing shore-cobble
samples to place three camera-forward log/root-wad clusters in every fixed view and reused
the rights-reviewed CC0 Pine Tree 01 bark. All five views rendered, but the straight cylinders
read as oversized poles, the five-branch root fans read as synthetic prongs, and multiple
pieces floated above or intersected the coarse bank, most visibly at Troublemaker, Coloma,
and Salmon Falls. Candidate source and tests were removed without changing the map, collision,
hydraulics, navigation, packages, or gameplay authority. Captures and the durable rejection
record remain in
`docs/environment-captures/south_fork_full_reach/m9_woody_debris_v173_review.json`.
The candidate and rollback editor targets build, focused suites pass 35/35 after removal,
the exact-current map and build-manifest hashes remain unchanged, and renderer-backed M7
passes. v173 closes no photoreal, named-review, media, or release gate.

The v174 reflective-water bracket was also rejected. It changed only transient material
parameters on fourteen median base-water components, increasing sky reflection and reducing
roughness without touching textures, meshes, packages, collision, solver channels, hydraulics,
or raft physics. All five fixed views changed enough for decisive review, but Meat Grinder,
Troublemaker, Coloma, and Salmon Falls expose large rectangular and polygonal light/dark patches
aligned with the water mesh/material interpolation. The brighter response turns the current
surface into visibly tiled plates and is worse than v169's flatter but continuous water. The
candidate path and tests were removed; captures and the durable rejection record remain in
`docs/environment-captures/south_fork_full_reach/m9_reflective_water_v174_review.json`.
The rollback editor target builds, source/rights suites pass 35/35, exact-current map and
build-manifest hashes are unchanged, and renderer-backed M7 passes. v174 proves that scalar
reflection/roughness tuning cannot close the underlying surface-fidelity gap and closes no
photoreal, named-review, media, or release gate.

The v175 crew-stroke slice is retained as a bounded technical animation and handling upgrade,
not as photoreal character acceptance. Forward/back strokes now use continuous catch, longer
power, and aerial recovery phases; blades lift 26 cm in recovery, both hand targets remain on
the visible shaft, and five deterministic crew offsets span only 56.8 ms at the production
cadence. The first reduced-model impulse is synchronized to the 0.29 visual power phase rather
than an unrelated timer that continued while resting. Per-stroke impulse, steady 0.8 s cadence,
reaction latency, mass, D3/D4, water, collision, rescue, terrain, maps, and packages are
unchanged. The UE 5.8 target builds, focused source/rights tests pass 35/35, renderer-backed M5
passes 5/5, P3 propulsion passes 1/1, and exact-current M7 passes 1/1. The dedicated side frame
still exposes rigid seated posture, tube-like arm deformation, coarse hands, imperfect helmet
fit, limited gaze/facial performance, and synthetic character/PPE response. It is technical
evidence only; authored motion capture plus named guide and art review remain required. The
capture, hashes, authority boundary, validation results, and open defects are recorded in
`docs/environment-captures/south_fork_full_reach/m9_crew_stroke_cadence_v175_review.json`.
v175 closes no photoreal, named-review, media, or release gate.

The v176 helmet-fit correction is also retained as a bounded technical improvement. It raises
the project-owned production shell 4 cm relative to the solved head pivot while keeping the
0.96 scale, mesh, materials, per-frame head tracking, skeleton, hair policy, and gameplay
authority unchanged. The matched front-starboard frame now exposes all five eye lines instead
of placing the shell rims across them. The UE 5.8 target builds, focused source/rights tests
pass 35/35, renderer-backed P3 passes 1/1, M5 passes 5/5, and exact-current M7 passes 1/1.
Photoreal acceptance remains rejected: the shared fit lacks per-character brow, ear, occipital,
and retention landmarks, while hair edges, shell/strap detail, anatomy, gaze, hands, motion,
and PPE shading remain synthetic. The capture, comparison, hashes, validation results, and
open defects are recorded in
`docs/environment-captures/south_fork_full_reach/m9_helmet_fit_v176_review.json`. v176 closes
no named-review, media, or release gate.

The v177 reference-length arm-IK bracket was rejected and fully removed. It preserved the
existing palm-on-shaft targets and used the MetaHuman reference upper/lower-arm lengths for an
analytic two-bone solve, but the matched frame exposed multiple elbows folding upward behind
shoulders and helmets plus hooked foreground arms. Passing source, build, and propulsion tests
did not override that visible anatomical regression. The exact v176 production adapter and
review-test hashes are restored; source/rights gates pass 35/35, the editor target builds, and
renderer-backed M7 passes 1/1. Negative evidence and rollback hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_arm_ik_v177_review.json`. Production arm
deformation still requires authored Control Rig/mocap, explicit elbow pole vectors, shoulder
mechanics, twist distribution, and paddle-contact constraints; v177 closes no gate.

The v178 production-helmet-liner revision is retained as another bounded technical character-
presentation improvement. It recesses the deterministic project-owned crown, occipital, and
ear padding beneath the unchanged shell envelope. In the matched frame, the large black shapes
that protruded above and behind all five v176 helmets are gone, while the v176 eye-line correction,
fit offset, shell bounds, six cut-through vents, four retention anchors, four material slots, and
visual-only authority remain intact. The UE 5.8 full-editor import audit records 24,485 authored
LOD0 triangles with Nanite enabled; focused character/source/rights tests pass 48/48, the editor
target builds, renderer-backed P3 and M7 pass 1/1, and M5 passes 5/5. Photoreal acceptance remains
rejected because small liner/webbing edges, shared fit, simplified construction/materials,
character anatomy, hands, gaze, PPE integration, paddle contact, and motion remain synthetic.
The capture, provenance, hashes, import audit, validation results, and open defects are recorded
in `docs/environment-captures/south_fork_full_reach/m9_helmet_liner_v178_review.json`. v178 closes
no named-review, media, or release gate.

The v179 continuous-surface-water diagnostic was rejected and fully removed. It transiently
applied the existing project-owned DefaultLit solver-surface parent to fourteen median base-water
actors, retained global station/lateral UVs and solver-foam overlays, disabled vertex tint and
solver-field sampling, and did not save the map. All five photographic views completed, but the
surface became visibly faceted into giant triangular and polygonal plates—most severely in the
Meat Grinder and Troublemaker foregrounds. This is worse than the flatter v169 Single Layer
baseline. The source hook is gone, focused gates pass 48/48, the rollback editor target builds,
and exact-current M7 passes 1/1. The captures, hashes, pixel deltas, rejection, and restored-source
proof are recorded in
`docs/environment-captures/south_fork_full_reach/m9_continuous_surface_water_v179_review.json`.
The initial review attributed the plates to geometric normals/tessellation. v180 below withdraws
that inference after isolating simultaneous source/HLOD rendering. v179 closes no gate, and its
removed material remains unaccepted because it lacked a valid exclusive review.

The retained v180 source/HLOD-exclusive capture correction supersedes that causal conclusion.
`WorldPartition->LoadAllActors` had loaded source actors and their instanced HLOD proxies into the
same editor world; v179 changed only the fourteen source materials, so the raw scene capture drew
two representations with different materials and produced the polygon mosaic. v180 suppresses
185 HLOD primitive components while fully loaded source truth is captured, mirrors the configured
`median_runnable` selector across 64 tagged components (41 inactive), and restores every previous
visibility state afterward. It does not save or alter the map, HLOD, water meshes, materials,
hydraulics, collision, navigation, or gameplay. The corrected five-view set is continuous and lies
within 0.73-1.14 mean RGB levels of v169; focused gates pass 48/48, the editor target builds, and
renderer-backed M7 passes 1/1. The ledger is
`docs/environment-captures/south_fork_full_reach/m9_source_hlod_exclusive_v180_review.json`.
v179 remains removed and unaccepted because its material was never reviewed through this corrected
path, but it no longer supports a geometric-normal or tessellation diagnosis. v180 improves review
validity only: the river remains too uniform, dark, low-volume, and under-aerated for photoreal
acceptance, and no named review or release gate closes.

The retained v181-v184 slice is the current technical water baseline. v181 adds named-rapid
surface-slope, acceleration, strain, and convergence aeration while preserving the global solver
Froude base. v182 converts positive aeration into bounded, non-colliding breaking relief. v183
adds presentation-only guide-feature infill for recorded holes, ledges, wave trains, laterals,
rocks, eddy lines, shallows, and strainers; its authority is explicitly
`procedural_infill_interpreted_from_guide_inventory_pending_human_review`. v184 refines only the
qualifying overlay to a one-metre grid, yielding 24 foam actors and 396,425 triangles. The result
changes no hydraulic, collision, buoyancy, navigation, raft-physics, rescue, or progression
authority.

The settled five-view v184 capture loads 201 World Partition references, uses the active median
flow band, and contains no simultaneous HLOD proxy rendering. The UE target and world build pass;
focused environment/source/HLOD/rights checks pass 65/65; post-HLOD M7 passes 1/1; M8 passes 4/4;
and the fail-closed M9 suite passes 5/5. The M8 rerun aligns a stale test-only canopy topology
expectation with the retained two-plane crossed-card generator; no runtime canopy asset or
generator changed. The M9 shoreline test enforces the documented 0.42 m micro-relief source cap,
while the refined overlay retains its separate 0.56 m displacement cap. The final 28 HLOD actors
rebuild with zero errors and immediately converge to a 28/28 zero-save repeat, with every package
hashed in current durable evidence. These checks accept the data lineage, procedural fallback
disclosure, capture correctness, streaming output, and technical readability only.

Manual review rejects v184 as photoreal or release media. Meat Grinder is more legible, but its
foam remains bright polygonal ribbons over a dark, flat reflective surface; Troublemaker remains
too calm and distant. Coherent breaking lips, pile/crest volume, entrained air, spray and mist,
shoreline transitions, production terrain/foliage, and lighting remain below the target. The
individual decisions are recorded in
`docs/environment-captures/south_fork_full_reach/m9_solver_derived_aeration_v181_review.json`,
`docs/environment-captures/south_fork_full_reach/m9_solver_gated_breaking_relief_v182_review.json`,
`docs/environment-captures/south_fork_full_reach/m9_guide_feature_breaking_relief_v183_review.json`,
and
`docs/environment-captures/south_fork_full_reach/m9_refined_guide_feature_foam_v184_review.json`.
No named reviewer has approved the guide interpretation or art, so M9 remains fail-closed.

The subsequent v185-v187 static aerated-volume bracket is also rejected. v185 added 19
presentation-only actors with 263 solver/guide-gated sites and 42,080 triangles. It gave Meat
Grinder more apparent depth, but the translucent carrier read as glass humps and created a broad
synthetic mound at Troublemaker. v186 removed the water carrier while retaining translucent foam
lace; the matched frames barely changed and preserved the artifact. v187 switched the same
geometry to the masked solver-field foam material; the glass disappeared, but the crest volume
collapsed into disconnected bright shards and chevrons rather than believable turbulent water.
The implementation, temporary test contracts, material instance, and nineteen generated meshes
were removed. Negative captures and review ledgers remain in
`photographic_v185_aerated_roller_volume`, `photographic_v186_aerated_roller_lace`,
`photographic_v187_masked_aerated_crest`, `m9_aerated_roller_volume_v185_review.json`,
`m9_aerated_roller_lace_v186_review.json`, and `m9_masked_aerated_crest_v187_review.json`.

The exact v184 world was then regenerated from source and restored to 200 stable actor identities,
24 foam actors, and 396,425 foam triangles. HLOD rebuilt 28/28; one setup-settling repeat resaved a
single actor despite rejecting every geometry rebuild, and the required final repeat then evaluated
28/28 with zero modified packages and zero errors. Source layout passes 23/23, durable HLOD evidence
passes 6/6, renderer-backed M7 passes 1/1, M8 passes 4/4, and manifest-sensitive fail-closed M9 passes
5/5. This restores technical currency only. The retained water, terrain, vegetation, rocks,
characters, raft, animation, VFX, and lighting remain below the requested photographic bar, and no
named or external release gate closes.

## Known blockers reviewers must address

- The global v25 valley retains the v24 erosion-conditioned relief and adds all 20 named-
  rapid visual fields, removing the former transit/runtime water mismatch, but smooth or
  under-authored landforms remain visible.
- Source-canopy preservation reaches 97.2670% in the visible strong-source band, but sparse/card vegetation and the
  simple tree assets remain below the requested photoreal bar.
- v25 aligns seasonal presentation water with every cooked named-rapid runtime field. The
  M9B.3 v24 water slice replaces v663's cellular breakup with solver-masked, flow-aligned
  project-owned foam fragments and broken-mask roughness, removing the cracked-sheet carpet
  and dense ruler bands. M9B.3 v25 makes the existing solver/contact-derived spray, mist,
  droplets, and rapid aerosol smaller, denser, and less opaque, removing the largest card
  necklace in the matched frame. M9B.3 v48 adds a genuine multi-valued curled sheet at each
  detected hydraulic jump; the exact Meat Grinder window uses five sites and 640 triangles
  under its 3,072-triangle cap. The surrounding riverbed/terrain seams, hard water-patch
  boundaries, simplified crest form, clean linear laces, flat broad reaches, limited
  pile/wave-train interaction, and analytic aerosol remain below the requested final
  live-water standard.
- The v287 body fallback replaces blank Manny anatomy with five independently morphed,
  rigged human bodies, v306 substantially improves the PFD/helmet equipment layers, and
  v579 adds rights-tracked weighted Hair02 geometry to every variant, but facial nuance,
  final groom quality, PPE/body integration, and generic wardrobe remain below
  production-grade photoreal character art.
- The generated coated-fabric and physically rescaled ripstop materials are useful
  reusable fallbacks, but neither the parametric PPE nor flexible raft is a scanned or
  artist-authored production visual asset. The v482 rapid frame proves representative
  deformation and D4-driven contact-water presentation technically. M9B.3 v42 additionally
  makes the project-owned production chamber consume the existing D4 compression and
  updates its tangent frame from the deformation gradient, but broad wet highlights,
  limited crew contact, and absent abrasion/repair/fabric-strain detail preserve the art
  rejection.
- The v552 procedural boulder has a stronger project-owned silhouette/material fallback,
  but remains too dark and synthetic. The v584-v585 texture-transfer attempts regressed
  toward black and were rejected; v587 restores the source baseline without claiming a
  visual improvement. The v599 world-aligned texture, v605 diffuse/roughness lift, and
  v608 diffuse-only lift also regressed toward black and were rejected. v709-v730 prove that
  a clean 1×-build-scale import of the hash-matched CC0 source can render and that its UV/PBR
  data are intact, but the fixed-light response remains pale and the gated scan has not
  passed geology, guide, art, or performance review, so it is not promoted.
- The v559 coordinated pose removes the worst high-side body tearing, but the remaining
  CC0 anatomy, faces, hands, helmet/PFD fit, clothing, and equipment integration are not
  production-grade photoreal character art. v632 prevents all five paddles from vanishing,
  keeps hands on modeled shafts/blades/T-grips, and improves action readability, but it does
  not supply production animation or character/equipment assets. M9B.3 v34 replaces the
  ten blunt procedural footwear overlays with a project-owned lasted river-boot mesh, but
  its dark shared material and rigid yaw-only placement still need production material and
  skeletal ankle/toe treatment.
- The v579 adapter uses the authored parent-to-head shaft, adds measured hair clearance,
  and removes the first import's backward-head regression, but residual hair/helmet fit and
  all underlying facial, hand, clothing, and PPE art limitations remain open.
- The v616-v618 offline MetaHuman pilot fixes transform-buffer initialization and proves local
  core-mesh compatibility, but the installed blank archetype has no authored guide identity,
  facial albedo, groom, brows, or wardrobe. It is deliberately not auto-promoted and does not
  close the production-character blocker.
- The v621-v623 contact-water redesign is rejected for absent hero response, a glass-shell
  regression, and a triangular foam-sail regression. v624 restores the known technical
  baseline. v735 reduces the restored patch's cellular quilt without changing its topology
  or authority. v48 adds solver-gated non-heightfield overhangs without changing that
  authority, but still does not close the production-water blocker.
- No current screenshot or trailer frame is approved for release media.

The v188 capture-only terrain diagnostic also rules out global orthophoto dominance as a
release fix. It transiently set all 21 detailed/far-field terrain components to 100%
registered macro colour with neutral tone, changing 58.44-63.10% of fixed-view pixels by
more than eight RGB levels. The map and packages were never mutated. The result is greener
and smoother, not more photographic: close banks still lack local gravel, soil, root,
embedded-rock, cutbank, wet-edge, and vegetation-transition structure, while distant slopes
retain broad source/procedural mosaic regions. The temporary implementation was removed and
the rejection is recorded in
`docs/environment-captures/south_fork_full_reach/m9_raw_registered_macro_v188_review.json`.
Production terrain therefore requires source-conditioned local morphology/material authoring;
the existing NAIP contribution cannot close the gate by scalar tuning alone.

The v189 riverbank-detail review establishes a reversible, versioned local-material path but
does not close that morphology gap. A project-owned built-in-image-generation source is retained
at `unreal/SourceArt/RaftSim/Environment/GeneratedTerrain/american_south_fork_terrain_bank_detail_source_v2.png`;
its exact prompt, original hash, deterministic derivation, physical-width intent, and review-only
policy are recorded in the adjacent v2 manifest. Unreal validates all three 1024-square maps with
eleven running-platform mips and transiently binds them to exactly thirteen detailed terrain
components. The corrected five-view set loses the checkerboard of the first unbuilt-texture
attempt and gives exposed banks a more plausible brown gravel/soil read, but source detail
mostly disappears at guide distance. More importantly, the bank remains a smooth ribbon with no
cutbank, gravel-bar relief, embedded-rock fabric, roots, or credible wet-edge transition. The
prompted 2.0 m source is also sampled by the locked parent at an unverified 3.2 m width. Production
promotion is therefore rejected; v184 remains authoritative. Captures and hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_riverbank_detail_v2_v189_review.json`.

The v190 scan-rock bank-morphology review tests whether mesh variety alone closes that gap. It
transiently replaces the static meshes on exactly 78 non-colliding scenic-rock and 39
non-colliding shore-cobble components with six already imported Poly Haven `Rock Moss Set 01`
CC0 scan donors. The v189 terrain-detail material remains active, while no map, mesh package,
collision setting, or runtime authority is saved. Unreal validates the three 1024-square review
textures at eleven mips, renders all five fixed views after loading 229 World Partition actor
references, and exits cleanly.

Production promotion is rejected. The varied scan silhouettes help only the large Meat Grinder
and Troublemaker rocks; existing cobble transforms make most shore instances too small to read.
Only 0.047960-0.160482% of each frame changes above eight RGB levels from v189. Chili Bar,
Coloma, and Salmon Falls still show broad flat painted banks, and none of the views gains a
credible cutbank, gravel bar, embedded-rock fabric, root system, undercut, or wet shoreline
transition. Vegetation, terrain, water, and lighting remain visibly synthetic. The donor is a
weathered-rock morphology analog, not an approved South Fork lithology match, and no named
reviewer approved the result. The review is retained as reversible negative evidence in
`docs/environment-captures/south_fork_full_reach/m9_scan_rock_bank_morphology_v190_review.json`;
v184 remains authoritative and all M9 acceptance gates remain open.

The v191-v194 embedded-bank sequence then isolates whether corrected physical sizing,
placement, and density can make the same rights-reviewed scans meaningful. v191 exposed an
import-unit error: dividing by the donors' raw pre-build bounds while ignoring their 100x LOD0
build scale produced landscape-scale occluders. v192 removed that regression but buried the
meshes because the donor bases sit 41-66 cm below their pivots. v193 accounts for both effective
bounds and pivot position, but retains only 2,446 candidates across approximately 49 km and is
visually absent. v194 increases this to 9,676 of 15,702 candidates, uses patch-varying 48-96%
retention, and sizes the donors to 0.25-1.90 m while preserving collision, hydraulics,
navigation, and all saved packages.

v194 is still rejected. Four fixed views are byte-identical to v190; Salmon Falls differs by
only 0.000012 mean RGB and no pixel in any view changes by more than eight levels. The existing
shore-cobble sample positions therefore cannot act as a production bank-morphology authority:
they remain mostly hidden, distant, or outside the guide-eye frusta even after their unit,
pivot, size, and density defects are corrected. The captures and ledgers
`m9_clustered_embedded_bank_rock_v191_review.json` through
`m9_dense_embedded_bank_rock_fabric_v194_review.json` are retained as negative evidence. The
next terrain attempt must derive longitudinal bank forms and camera-legible gravel, rock, root,
and wet-edge distributions from river edges, terrain elevation, and water level, using
deterministic procedural completion where source coverage is absent. v184 remains authoritative
and every M9 acceptance gate remains open.

The v195-v197 water-edge-derived sequence implements that missing placement seam but proves that
an unart-directed procedural strip is not sufficient production morphology. The opt-in review
path decodes station and lateral distance from fourteen saved median-water meshes, traces the
authoritative detailed terrain, and generates 4,521 longitudinal bank segments (27,126 triangles)
plus transient scan-rock instances. It never changes collision, hydraulics, navigation, or saved
packages and destroys its review actor after each capture. v195's 3,828-rock bracket is rejected
because reversed winding on one side produces a black knife edge and the wide planar faces read
as geometric wedges. v196 corrects the winding, submerges the toe, narrows the profile, and embeds
smaller rocks; this removes the artifact but makes the terrain-conforming overlay visually
ineffective. v197 tests one final bounded raised-toe bracket with 4,971 smaller rocks. It remains
nearly absent at Chili Bar and Salmon Falls and creates angular shoreline shelves at Coloma rather
than natural erosion/deposition structure.

All three candidates are rejected for production. They do not supply multi-scale sediment,
embedded-rock fabric, roots, undercuts, talus hierarchy, wet-edge transitions, or approved South
Fork lithology, and every view retains synthetic water, terrain, foliage, and lighting. The
reversible source seam, captures, and ledgers
`m9_water_edge_derived_bank_morphology_v195_review.json`,
`m9_corrected_derived_bank_morphology_v196_review.json`, and
`m9_raised_toe_bank_morphology_v197_review.json` remain as negative evidence for future authored
bank-module integration. Scalar/profile tuning of the strip is stopped. v184 remains authoritative;
no photoreal, named-review, rights, media, or release gate closes.

v198 then tests the next distinct hypothesis: discontinuous bend-classified erosion/deposition
modules rather than a continuous strip. It corrects a material defect that had marked every
v195-v197 bank vertex fully wet, derives 1,606 cutbank and 1,824 gravel-bar rows, and renders
2,220 connected segments (17,760 triangles), 3,675 multi-scale scan rocks, and 568 root segments
using the already rights-reviewed CC0 fir-bark material. The layer remains transient,
non-colliding, non-navigable, and no map or derived-bank package is saved; the combined review
command refreshes only the three isolated terrain-detail v2 Texture2D packages.

The candidate is rejected. Correct wetness makes the geometry legible but exposes pale pyramidal
berms and hard module seams at Chili Bar and Meat Grinder instead of eroded cutbanks or deposited
bars. Roots do not resolve in the guide-eye views, rocks remain disconnected from their sediment,
and Salmon Falls is unchanged. The fixed frames and exact hashes are recorded in
`m9_erosion_deposition_bank_modules_v198_review.json`. Further procedural cross-section tuning is
stopped: the next valid terrain-art input is a coherent scanned/authored bank-module set with
reviewed end caps, material layering, embedded sediment/rock, exposed roots, wetness, and
vegetation transitions. v184 remains authoritative and all M9 human, visual, rights, media, and
release gates remain open.

v199 performs the requested coherent-source intake rather than extending the generated strip.
Official Poly Haven metadata and CDN payloads supply Rock Face 01, Tree Stump 02, Roots, and
Rocky Gravel under CC0. All sixteen 2K files match the API-published MD5 values and locally pinned
SHA-256 values. Unreal imports two publisher-scale Nanite meshes, fourteen textures, and four
opaque PBR materials into an isolated `ExternalReview` package. The raw 68,002,452-byte source
bundle is not committed. A distinct opt-in review layer places 136 rock faces, 66 stump/root
scans, 117 roots patches, and 108 gravel patches from median-water station/lateral coordinates,
centerline curvature, deterministic masks, and 427 successful detailed-terrain traces near the
five fixed cameras. Every component is transient, non-colliding, non-navigable, unsaved, and
irrelevant to hydraulic and gameplay authority.

The rendered result is rejected. Rock Face 01's pale layered formation repeats as conspicuous
striped slabs and is not a credible South Fork lithology match. Tree Stump 02 becomes dark rounded
props at guide distance. The Roots and Rocky Gravel materials sit on opaque planar patches whose
rectangular orange/brown boundaries are obvious. The pieces remain detached from the smooth bank
ribbon instead of forming authored undercuts, strata, embedded talus, wet edges, and vegetation
transitions. Salmon Falls changes by only 0.008398 mean RGB from v198, and all five views retain
synthetic water, terrain, foliage, and lighting. The importer, provenance, isolated assets, and
transient integration seam remain useful infrastructure, but no v199 visual content or media is
promoted. Exact evidence is in `m9_scanned_bank_kit_v199_review.json`; v184 remains authoritative
and all named human, photoreal, rights, media, platform, signing, and release gates remain open.

## Production MetaHuman roster — technical acceptance, photoreal rejection

MetaHuman Creator Core Data is installed and the release path now resolves one guide and
four crew as five distinct Optimized/High builds. Each local build contains 84 validated
files; the runtime promotes only the complete five-character set and composes the exact
assembled face/body with cropped skin, wetsuit, PFD, helmet/retention gear, and paddle.
Hair assets remain provenance-checked but are suppressed beneath helmets. Production asset
sources stay out of the public repository and are distributed only through cooked builds.

The matched source-true Meat Grinder capture and review are recorded in
`docs/environment-captures/south_fork_full_reach/m9_metahuman_production_roster_v6_review.json`.
Technical character integration is accepted: helmets remain within the 1 cm solved-head
gate through seated, high-side, swimming, rescue, and re-entry transitions, and PPE/body
updates are atomic on action changes. Photoreal and release-media acceptance are rejected.
The crew still has visibly synthetic body/hand/paddle/gaze/facial performance and procedural
PPE, while the raft, boulder, water/foam/aerosol, shoreline, terrain, and lighting also remain
below the target photographic bar.

The UE 5.8 editor target builds; renderer-backed M4, M5, and M7 pass 3/3, 4/4, and 4/4;
M8 passes 4/4; the complete Python/data/source matrix passes 1,095 tests with three expected
skips; and the post-inventory fail-closed M9 suite passes 5/5. These gates establish technical
stability, not release acceptance.

## Exact-current renderer and performance investigation v220-v249

The cooked Development baseline profiles at 18.736 ms mean GPU and 20.709 ms p95 GPU,
with 47.901 ms workload p95 and 144 wall-clock hitches in the offscreen harness. Nanite
must remain enabled: disabling it regresses mean GPU to 29.130 ms. TAA/bloom/cloud and
shadow/GI reductions can lower GPU cost, but TAA visibly worsens production-character,
helmet, PFD, paddle, and raft edges; GI/shadow-off controls still hitch; and none of the
reduced-quality candidates is release acceptable. Keeping TSR and bloom while disabling
only clouds changes p95 GPU from 20.709 to 20.793 ms in the clear-morning workload, so
cloud support remains enabled. Body-only character shadows save approximately 0.25 ms
mean GPU in the matched reduced-quality bracket and remain diagnostic only.

Source-true close and broad captures also reject the renderer and water brackets. TAA is
sharper but noisier; cloud removal has no material clear-morning benefit; and disabling
authored foam, authored specular, live-overlay specular, or the breaking-lip mesh does not
produce a credible photoreal correction. Hiding the live-water actor is diagnostic only
because it removes required solver-resolved surface and hydraulic presentation. No
production renderer or water-material default is changed. The full machine-readable
ledger is `m9-current-render-performance-diagnostics-v249.json`.

Performance report schema v3 now records `render_offscreen`, `performance_protocol`,
`release_performance_qualification_eligible`, and `release_performance_qualified`.
Offscreen runs can pass raw engineering budgets but can never qualify a release artifact.
The artifact finalizer enforces that distinction, and the macOS RC workflow defaults to a
normal-window run. Fresh exact-current cooked Shipping normal-window evidence is still
required; the v220-v249 offscreen series is negative engineering evidence only.

Cooked v250 verifies that contract end to end. Its schema-v3 report identifies a Development
`-RenderOffScreen` run as `offscreen_engineering_diagnostic`, sets both release eligibility
and release qualification to false, and is parsed as failing by the artifact finalizer. The
short two-second sample also fails its raw engineering timing budget; its purpose is the
runtime qualification guard, not performance acceptance. Report SHA-256 is
`2f52d19421635bb15d56dbebf50e44fcc90d7ef5a212f590d2e45015c678e7e5`.

The exact-current v252 Python/data/source matrix reports 1,139 passes, three expected
installed-dependency-path skips, and one intentional fail-closed release-packet failure in
623.85 seconds. The sole failure is again the contract that refuses to equate the current
post-v317 flexible-raft runtime deformer with the historical v42 reviewed hash. There are zero
unexpected failures; JUnit SHA-256 is
`a84e1411efe02cc3acf84f1ccbfaefd60c73c9464d06ba45aafbec1ae9db88f7`.

Exact-current renderer-backed v252 native automation also passes M4 4/4, M5 5/5, M7 4/4,
M8 4/4, and fail-closed M9 5/5 with zero failures. The runtime now avoids rewriting
construction-only Niagara auto-activation state after BeginPlay, eliminating the prior pooled
warning burst without changing emission or simulation behavior. An intermediate cold M5 run
also exposed Unreal's documented 32-square placeholder while texture platform data compiled;
the gate now finishes each loaded production texture's compilation before preserving the same
1K/2K assertions, and the cold v252 M5 suite passes. M4, M5, and M7 each retain one
successful-with-warning case from an engine-owned UE 5.8 TSR read of
`r.MotionVectorSimulation`; the project never references that CVar. M8 and M9 are clean.
Report hashes and paths are recorded in `m9-current-render-performance-diagnostics-v249.json`.
These runs establish technical continuity only and do not satisfy Shipping/windowed
performance, photoreal art, named review, external hardware, input, signing, media, or
distribution gates.

## Exact-current local Shipping qualification v269-v273

The matched v269/v270 breaking-water capture retains the High profile with
`r.Lumen.TranslucencyReflections.RadianceCache=0`. Full-resolution inspection found no
material loss in water reflections, breaking foam, mist, shoreline, foliage, or boulder
presentation; the breaking-water structural-similarity score is 0.974. Opaque Lumen
reflections, Single Layer Water reflection captures, translucent-volume lighting, TSR,
bloom, Nanite, clouds, all authored water, and all nineteen production Niagara components
remain enabled. The separate translucent-reflection cache was redundant for this content.

The exact-current game/content/renderer v273 macOS arm64 Shipping package then passed 60/60
rapid/flow cases, release-candidate QA, a pristine save/profile disk round trip, and a
normal-window 1920x1080 High/60% Metal soak. Over 2,338 measured frames it recorded 13.094 ms
p95 frame/GPU, 13.547 ms p95 wall clock, zero >33 ms hitches, 0.275 ms average solver time,
and 5,560.5 MB peak physical memory. Its runtime report is release-performance eligible and
qualified. The complete machine-readable ledger is
`m9-v273-translucency-cache-shipping-performance.json`.

This closes the exact-current local technical performance gate, not M9. The package came
from the intentional dirty M9 worktree, is transient and ad-hoc signed, and was exercised
outside the canonical RC wrapper because a protected pre-existing sleeping Unreal
commandlet causes the wrapper's fail-closed isolation preflight to stop. Named photoreal,
guide, geospatial, legal, fresh-device input, Windows/Proton, distribution signing,
notarization, approved-media, account, clean-source, canonical-isolation, and immutable
promotion gates remain open.

Post-change native automation passes M4 4/4, M5 5/5, M7 4/4, M8 4/4, and fail-closed
M9 5/5. The exact-current Python/data/source matrix reports 1,140 passes, three expected
installed-dependency-path skips, one intentional fail-closed v42 visual-review hash mismatch,
and zero unexpected failures in 421.41 seconds. The JUnit SHA-256 is
`be5e767599f6c0c6d671ee9e4c28ab9e684a046549399a2b9f2f3b379c79f6cb`.

## Photographic whitewater SubUV V4 isolated review v280-v299

A new project-owned image-generation source provides sixteen high-speed whitewater studies.
Deterministic processing reorders them into the established spray, droplet, mist, and aerosol
frame ranges, emits a 2048-square grayscale atlas, preserves at least 77 pixels of black padding
on every cell edge, and records the exact prompt and hashes. A distinct review material, texture,
and five Niagara systems load only with `-RaftSimPhotographicWaterAtlasV4Review`; the selected
production atlas, production Niagara packages, maps, and solver/contact emission authority do
not change.

The candidate does not pass visual review. In matched wrap and contact captures, the unscaled
photographic cells are nearly invisible at the current physical sprite sizes and do not create
an obvious production-quality improvement. A separate 2.4x spray / 2.0x droplet scale bracket
makes the source legible but reveals vertically paired, repeated soft puffs beside the obstacle;
they read as smoke rather than torn ballistic sheets or suspended droplets. That scale experiment
was reverted. A second review-only BC4 grayscale-compression bracket preserves more intensity but
causes the low gameplay mips to expose rectangular/checkerboard billboard footprints over the
rock and downstream water. It proves compression alone cannot correct the mismatch between a
macro-plume source and particle-scale runtime sprites. BC4 was also reverted. The final unscaled
`TC_Masks` authoring pass saves all five systems, validates all seven review assets, and exits
cleanly.

Machine-readable evidence is
`docs/environment-captures/south_fork_full_reach/m9_photographic_water_subuv_v4_review.json`.
It retains the generated source, exact provenance, deterministic derivation, current isolated
asset hashes, matched production/review captures, rejected scale and BC4 captures, native log hashes,
and a fail-closed `promotion_allowed: false` decision. A future candidate must represent
individual particle-scale water events, demonstrate texture-compression and mip survival, and
show an unmistakable improvement in a close solver-authorized contact-spray camera without
repeated silhouettes or smoke-like density. No M9 approval or release gate closes.

Post-restore renderer-backed automation passes M5 v300 5/5 and M9 v301 5/5. M5 contains the
known successful-with-warning UE 5.8 `r.MotionVectorSimulation` read; M9 is clean. Production
Niagara remains selected in the runtime test, and the release manifest remains fail-closed.

## Connected contact-water and depth-bearing reviews V5-V9

The V5 photographic-particle review proves that particle-scale, mip-safe photographic cells can
produce sharp porous breakup at macro range, but not the connected body needed at contact and wrap
distance. V6 adds a solver-shaped 160-triangle connected sheet and proves physical attachment, but
reads as a smooth glass wall. V7 separates the candidate into a horizontal attachment, aerated
crest, and two-lobe breakup layer totaling 296 live triangles. A direction diagnostic corrected the
presentation volume from behind the obstacle to the exposed raft-rock pin, after which the real
material exposed the remaining failure: a translucent polygonal sail rather than turbulent water.
V8 replaces that shared vertical sheet with a sampled horizontal attachment and six closed,
independently phased, flow-aligned lobes. Its first 736-triangle native frame reads as six repeated
white teeth; widening, flattening, lowering, and reducing their foam density removes the teeth but
makes the bodies effectively disappear into the base surface. All four candidates are isolated,
default-off, non-authoritative, and rejected; production assets remain byte-identical. V6-V8 now
bound the current analytic translucent-mesh family between walls/fins and imperceptible geometry.

The exact-current post-V9-revert local chain passes M4 v364 4/4, M5 v365 5/5, M7 v366 4/4,
M8 v367 4/4, and reconciled fail-closed M9 v370 5/5. The editor source inventory remains
62 files and 68,492 lines. The v369 Python/data/source matrix reports 1,145 passes, three expected
installed-dependency-path skips, one intentional fail-closed historical-v42 source-hash mismatch,
and zero unexpected failures in 525.430 seconds. Repository-resident reports and SHA-256 hashes are
recorded in `m9_depth_bearing_contact_water_v9_review.json` and the machine-readable acceptance packet.
The next candidate must be a temporally evolving depth-bearing FLIP/VDB/mesh cache or bounded
Niagara Fluids volume, warped and emission-gated by the existing solver, with advected entrained air,
anisotropic spray, collision-aware breakup, and short-sequence review.
This closes the current local technical-validation refresh only; no photoreal, human-review,
external-platform, signing, media, clean-build, or promotion gate closes.

The subsequent V9 feasibility lane mounts UE 5.8's Niagara Fluids plugin only for review and tests
the stock Grid3D FLIP Splash and continuous Hose systems at the same solver-authorized contact.
Both warmed systems report active, visible, bounded components during a four-contact, three-wrap,
one-pin D4 state. Waterless isolation nevertheless shows no rendered liquid body from either
template. The Hose frame contains only the existing production spray puff. Direct engine-template
reuse is rejected, the experimental runtime and capture hooks are removed, Niagara Fluids remains
absent from the project descriptor, and production remains on the fail-closed V8 baseline. A future
candidate must be project-authored or deliberately duplicated with its renderer, materials,
emission volume, warm-up/cache, and temporal validation controlled by the project. Exact evidence
and hashes are recorded in `m9_depth_bearing_contact_water_v9_review.json`. This negative result
closes no M9 gate.

![Rejected V9 stock FLIP Splash in waterless isolation](../environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v9_splash_waterless_rejected.png)

![Rejected V9 stock FLIP Hose in waterless isolation](../environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v9_hose_waterless_rejected.png)

## Project-authored depth-bearing contact water V10

V10 replaces the rejected stock-template experiment with a first-party deterministic mesh
cache. Six closed implicit-volume frames are generated once at `BeginPlay` by marching
tetrahedra, then advanced at a fixed 0.12-second cadence. The candidate exposes 104.89 cm of
generated depth and 10,700-11,092 triangles per frame. Its transform and material response use
only the existing dominant D4 contact, live sampled surface height, flow/across frame, impact
energy, and contact scale. It is presentation-only: collision, navigation, shadows, water
sampling, forces, D4 authority, maps, scoring, rescue, and progression are unchanged.

![V10 forced frame 0](../environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v10_frame0_review.png)

![V10 forced frame 2](../environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v10_frame2_review.png)

![V10 forced frame 4](../environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v10_frame4_review.png)

The three forced frames prove temporal and topological change at the same four-contact,
three-wrap, one-pin, one-recovery fixture. An unforced run selects frame 1, and a waterless
isolation keeps the low rounded shoulder attached beside the D4 obstacle after broad water is
hidden. This is a technical pass over V9's invisible stock systems, not a production-art pass.
The full scene still falls below the requested photoreal bar, and no named water-VFX art
reviewer or qualified South Fork guide has approved the motion, breakup, translucency, hydraulic
read, or guide-seat visibility. The candidate remains opt-in and default-off behind
`-RaftSimDepthBearingContactWaterV10Review`; it is not promoted.

Exact-current validation passes M4 v431 4/4, M5 v432 5/5, M7 v433 4/4, M8 v434 4/4, and
reconciled fail-closed M9 v437 5/5. The v436 Python/data/source matrix contains 1,150 tests:
1,146 pass, three dependency-path cases skip as expected, and the sole failure is the intentional
historical V42 visual-review hash mismatch, leaving zero unexpected failures in 466.945 seconds.
Its JUnit SHA-256 is
`e726eab19d8e07c3bb9d5b646e569b4d60f2c3145f9f8632be11ad2171fe420f`.
The complete immutable capture, log, source, report, and reviewer ledger is
`docs/environment-captures/south_fork_full_reach/m9_depth_bearing_contact_water_v10_review.json`.
This closes the V10 local technical candidate gate only; it closes no photoreal, named-review,
external-platform, signing, media, clean-build, or promotion gate.

## Raft-and-crew foam occlusion V1 — technical repair retained, external review open

The raised solver-conditioned foam sheet previously duplicated foam already painted into the
opaque Single Layer Water base. Because the sheet can rise roughly 56 cm above the sampled
surface, that duplicate layer could render over raft tubes, PFDs, and crew lower bodies. V1
assigns visible hydraulic foam to the dedicated masked sheet, sets the base-water hydraulic-foam
contribution to zero, and feathers the sheet out inside a live raft-aligned 320-by-190 cm
half-extent ellipse. Contact spray and ordinary waterline intersection remain; water samples,
forces, collision, D3, D4, flip/wrap/pin behavior, rescue, scoring, and progression are unchanged.

![Foam-occlusion V1 contact-port review](../environment-captures/south_fork_full_reach/m9_raft_crew_foam_occlusion_v1_contact_port.png)

![Foam-occlusion V1 wrap-hero review](../environment-captures/south_fork_full_reach/m9_raft_crew_foam_occlusion_v1_wrap_hero.png)

The focused exact-current `RaftSim.P2.WaterSurfaceRenders` contract passes 1/1 in
`unreal/Saved/Automation/M9V443FoamOcclusionP2/index.json`. Both reviewed frames retain
surrounding flow and rock foam while keeping the masked foam sheet off the raft and crew. This
closes only the focused technical defect. A named water-VFX art reviewer must still approve the
feather, contact-water read, and motion in a short sequence, and a qualified South Fork guide
must approve Meat Grinder visibility and hydraulic readability.

The broad local technical qualification has now been refreshed after V1. M4 v445 passes 4/4,
renderer-enabled M5 v453 passes 5/5, M7 v454 passes 4/4, M8 v455 passes 4/4, and the manifest-sensitive M9 v452
passes 6/6. The locked Python 3.13 data/source matrix passes 1,148 tests with three expected
installed-dependency inverse-path skips and zero failures in 429.514 seconds; its JUnit SHA-256 is
`bb04809ff2e37337b6d564dbda34dd3d6e274e595a7ba326b474f30204e9f7b4`.

This closes the V1 local editor/source regression lanes only. The v273 package/performance evidence
remains historical, and no package, performance, human-review, external-platform, signing, media,
clean-source, or promotion gate is claimed.

The immutable source, asset, capture, log, and focused-report hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_raft_crew_foam_occlusion_v1_review.json`.

## Seat-side paddle orientation V1 — technical repair retained, external review open

The crew pose library previously reversed the ordinary paddle endpoints: the T-grip sat
outboard while the blade aimed toward the raft centre. The high-side pose separately aimed
every paddle toward the commanded tube. Perspective concealed much of the port-side error but
left the starboard passengers visibly crossing their paddles through the raft.

V1 keeps the T-grip inboard and the blade outboard for every assigned seat, mirrors the
anatomical T-grip/lower-shaft hand ownership, and uses opposing forward/back strokes for turns
without moving either blade through the boat. During a high-side command the existing
coordinated body translation remains unchanged, while each passenger's brace paddle stays
outside that passenger's tube and reaches the waterline.

![Seat-side paddle V1 port review](../environment-captures/south_fork_full_reach/m9_seat_side_paddle_v1_contact_port.png)

![Seat-side paddle V1 starboard review](../environment-captures/south_fork_full_reach/m9_seat_side_paddle_v1_contact_starboard.png)

The UE 5.8 editor target builds. The production-character/source checks pass 44/44; M4 v465
passes 4/4; renderer-enabled M5 v463 passes all five leaf tests; renderer-enabled M7 v464 passes
all four leaf tests; and renderer-enabled M8 v466 passes 4/4. Direct mirrored cameras show both
seat-side blades outside the raft and reaching the water during the same live four-contact D4
wrap. Physics forces, water samples, collision, crew mass, D3/D4, rescue, scoring, and
progression are unchanged. The locked Python 3.13 data/source matrix passes 1,148 tests with
three expected installed-dependency inverse-path skips and zero failures in 419.151 seconds;
its JUnit SHA-256 is
`0215934f5353a51c74b374ff556f5ea462b829f2768e609910558dfd1cdeb7a3`.
The reconciled fail-closed M9 v468 suite passes 6/6.

This closes the reported paddle-side defect as a local technical repair. A named
character-animation/art reviewer must still approve the grip and stroke silhouettes in motion,
and a qualified South Fork guide must approve high-side and brace readability. Package,
performance, clean-source, platform, signing, media, and promotion gates remain open. Immutable
source, capture, log, and report hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_seat_side_paddle_v1_review.json`.

## Raft-interior water transmission V1 — technical repair retained, external review open

The authored Single Layer Water surface previously applied its scattering and surface-opacity
response across the raft interior, creating an opaque blue-gray slab over the floor. Removing
that water in a diagnostic exposed a second contributor: the real floor was so dark and smooth
under the tube shadow that it still read as opaque water.

V1 gives the South Fork production water instance a derived, raft-aligned rounded-rectangle
transmission aperture. Inside the tubes it suppresses only surface opacity, scattering, and
absorption while retaining behind-water transmission; outside the aperture the authored river
is unchanged. The aperture follows the live raft transform. A dedicated warm rescue-orange
coated-fabric floor adds bounded shadow fill and textile relief so the actual I-beam floor stays
legible under passengers and tube shadows.

![Raft-interior water transmission V1 starboard review](../environment-captures/south_fork_full_reach/m9_raft_interior_water_transmission_v1_contact_starboard.png)

![Raft-interior water transmission V1 port review](../environment-captures/south_fork_full_reach/m9_raft_interior_water_transmission_v1_contact_port.png)

The UE 5.8 editor target builds. Focused source guards pass 58/58. The exact-current water-
surface contract passes 1/1 with zero warnings and errors; M4 v492 passes 4/4; renderer-enabled
M5 v493 passes 5/5; renderer-enabled M7 v494 passes 4/4; renderer-enabled M8 v491 passes 4/4;
and the post-evidence-reconciliation fail-closed M9 v497 passes 6/6. Collision, water sampling, forces, raft mass, buoyancy,
D3/D4, flip, wrap, pin, rescue, scoring, and progression are unchanged. The exact-current full
Python/data/source matrix passes 1,148 tests with three expected installed-dependency inverse-
path skips and zero failures in 425.518 seconds; its JUnit SHA-256 is
`1b0b8747d9992fa3cb6a075d33387f1dc2e66c3bc769454e3947e34ee562c1b0`.

This closes the reported opaque-water defect as a local technical repair only. A named water-
VFX/art reviewer must approve transmission and exterior continuity in motion, a qualified South
Fork guide must approve the presentation at Meat Grinder, and the product owner must accept the
candidate. Package, performance, clean-source, platform, signing, media, and promotion gates
remain open. Immutable source, asset, capture, log, and report hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_raft_interior_water_transmission_v1_review.json`.

## Identity-fitted helmet V1 — direction and seating repaired, external review open

The production helmet previously followed the avatar torso rotation instead of the rendered
face, used one shared fit scale for all five MetaHuman identities, and retained a 12 cm vertical
lift. Those three choices made the asymmetric shell read as backward in some poses and perched
above the head in close views.

V1 uses each rendered face's forward and up axes to orient the shell, guarantees that the
helmet's authored +X brow faces the same direction as the character, derives scale from the
identity's face bounds, and lowers the skull-centre lift to 9.5 cm. The runtime gate now checks
all five identities for no more than 1 cm solved-head error, at least 0.98 forward alignment,
and a bounded 0.90-1.02 fit scale. The captured roster records forward alignment of exactly
1.0 for every identity, a fit-scale range of 0.90-0.990621, and maximum solved-head error of
`1.877e-10` cm.

![Identity-fitted guide helmet front](../environment-captures/south_fork_full_reach/m9_identity_fitted_helmet_v1_guide_front.png)

![Identity-fitted guide helmet profile](../environment-captures/south_fork_full_reach/m9_identity_fitted_helmet_v1_guide_profile.png)

![Smallest-identity helmet profile](../environment-captures/south_fork_full_reach/m9_identity_fitted_helmet_v1_smallest_profile.png)

![Smallest-identity helmet rear](../environment-captures/south_fork_full_reach/m9_identity_fitted_helmet_v1_smallest_rear.png)

The editor target builds. Exact-current M4 v505 passes 4/4; renderer-backed M5 v502 records
five successful result entries; M7 v503 records four; and M8 v504 passes 4/4, all with zero
failures. The full Python/data/source matrix passes 1,148 tests with three expected dependency-
path skips and zero failures in 424.27 seconds; its JUnit SHA-256 is
`49beafd41f1beea6f7be631fc5da292707725a30865fef88b38a304ed5c4e075`.
The reconciled fail-closed M9 v507 acceptance suite passes 6/6.
Helmet mesh, materials, collision, crew mass, water, and physics authority are unchanged.

This closes the reported backward/shared-fit transform defect as a local technical repair. It
does not make the simplified first-party shell, retention hardware, materials, or character
lighting photoreal. A named character-art reviewer must approve or replace those assets, and a
qualified whitewater safety reviewer must approve the visible coverage and retention depiction;
this is not equipment certification. Immutable source, renderer, metric, and report hashes are
recorded in
`docs/environment-captures/south_fork_full_reach/m9_identity_fitted_helmet_v1_review.json`.

## Unpadded production PFD V1 — shoulder flotation removed, external review open

The production rescue PFD contained two swept shoulder foam bands, each 5.2 cm wide and
2.6 cm thick. Those bands created the reported shoulder-pad silhouette. V1 deletes both
foam objects and their source helper, terminates the front and back flotation cells below
the shoulders, and retains only two narrow shell-fitted webbing connectors. The first
diagnostic also exposed two protruding shoulder sliders; those were removed before the
retained capture.

![Unpadded PFD guide front](../environment-captures/south_fork_full_reach/m9_unpadded_pfd_v1_guide_front.png)

![Unpadded PFD guide profile](../environment-captures/south_fork_full_reach/m9_unpadded_pfd_v1_guide_profile.png)

![Unpadded PFD guide rear](../environment-captures/south_fork_full_reach/m9_unpadded_pfd_v1_guide_rear.png)

The deterministic source manifest now requires zero shoulder foam pads and two 2.0 cm-wide,
0.18 cm-thick webbing runs. The reimported asset has 19,948 authored triangles, a 2,058-
triangle Nanite fallback, five material sections, and plausible 42.2×44.9×43.3 cm bounds.
All five production MetaHuman wrappers select it with exactly 0.0 cm maximum torso-origin
error. The editor builds; focused source contracts pass 27/27; M4 v513 passes 4/4; renderer-
backed M5 v514 records all five results with zero failures; M7 v515 records all four results
with zero failures; and renderer-backed M8 v516 passes 4/4. Collision, crew mass, water,
D3/D4, flip/wrap/pin, rescue, scoring, and progression are unchanged.

The exact-current full Python/data/source matrix passes 1,148 tests with three expected
dependency-path skips and zero failures in 430.68 seconds; its immutable JUnit SHA-256 is
`0090fc5ab8fbddb23415027bb6f4d6f647cf1d74f988193a18ce016b81d7ac5d`.
The reconciled fail-closed M9 v518 acceptance suite passes 6/6.

This closes the reported padded-shoulder geometry defect as a local technical repair. It does
not make the simplified rigid front/back cells, hardware, fabric response, strap intersections,
character pose, or lighting photoreal. A named character-art reviewer and qualified whitewater
safety reviewer must approve or replace the current PFD; this is not equipment certification.
Immutable source, asset, renderer, roster, and automation hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_unpadded_pfd_v1_review.json`.

## Seated waist/hip V1 — missing body volume repaired, external review open

The production visibility path kept its tapered torso overlay but hid the pose-matched
pelvis. The PFD therefore ended above two visually disconnected thighs, making every
passenger appear to have no waist or hips. Simply restoring the former ellipsoid recovered
width from the front but looked like a hanging sphere in profile and rear views, so that
first repair was rejected.

V1 retains the collisionless pelvis layer and replaces its spherical source with a dedicated
14-ring by 24-side seated shell. It is shallow front-to-back, broad through the hips, and
keeps finite upper-waist and lower-thigh-root widths so it overlaps both the torso and legs.
The shell remains centred on the deterministic hip solve and scales with each identity.

![Seated waist and hip guide front](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v1_guide_full.png)

![Seated waist and hip guide profile](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v1_guide_profile.png)

![Seated waist and hip guide rear](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v1_guide_rear.png)

All five production identities pass the runtime silhouette gate with exactly 0.0 cm maximum
hip-centre error. The smallest measured half-extent is 9.025×16.56×7.99 cm, and the broadest
is 9.975×19.26×8.755 cm. M4 v526 passes 4/4; renderer-backed M5 v527 passes all five results,
including the new native anatomy checks; M7 v528 passes 4/4; and M8 v529 passes 4/4. The
full Python/data/source matrix passes 1,148 tests with three expected dependency-path skips
and zero failures in 430.43 seconds; its immutable JUnit SHA-256 is
`86c7c0e32d2fcf5ce68575947c8a9f11f85076cf546be6d20ca9fe6e83810057`.
The reconciled fail-closed M9 v531 acceptance suite passes 6/6.

This closes the reported missing-waist/hips defect as a local technical repair. It does not
make the procedural torso/pelvis integration, wetsuit response, body anatomy, or seated
deformation photoreal. A named character-art reviewer must approve or replace the retained
presentation. Collision, mass, animation authority, water, D3/D4, raft contact, rescue,
scoring, and progression are unchanged. Immutable source, renderer, roster, and automation
hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_seated_waist_hip_v1_review.json`.

## Seated waist/hip V2 — fuller pelvis silhouette retained, external review open

The V1 layer was present, but its 9.5×18×8.5 cm reference half-extent still read as a
pointed bridge under the PFD rather than a human seated pelvis. A first enlarged V2 bracket
restored width and depth but formed a skirt-like lower edge, so that shape was rejected.
The retained V2 uses an 18-ring by 32-side shell with rounded mid-volume shaping, a localized
seated glute bulge, and a central saddle between the thigh roots. Its reference half-extent is
15×23×15 cm, and the native visibility contract now also requires at least 500 mesh vertices.

![Fuller seated hips guide front](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v2_guide_full.png)

![Fuller seated hips guide profile](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v2_guide_profile.png)

![Fuller seated hips guide rear](../environment-captures/south_fork_full_reach/m9_seated_waist_hip_v2_guide_rear.png)

All five production identities pass with zero hip-centre error. The smallest measured V2
half-extent is 14.25×21.16×14.10 cm and the broadest is 15.75×24.61×15.45 cm. The editor
build and 36 focused Python contracts pass; M4 v549 passes 4/4, renderer-backed M5 v548
passes 5/5, offscreen-rendered M7 v550 passes 4/4, and offscreen-rendered M8 v551 passes
4/4. The exact-current v552 matrix reports 1,148 passes, three expected skips, and zero
failures in 434.82 seconds. Reconciled M9 v553 and its independent exact confirmation v554
both pass 6/6.

This V2 closes the specific missing-hip silhouette defect as a local technical repair. The
still-procedural anatomy, wetsuit surfacing, identity-specific deformation, and seated motion
remain below final photoreal character quality and require a named character-art reviewer.
Collision, mass, animation authority, water, D3/D4, raft contact, rescue, scoring, and
progression are unchanged. Exact source, capture, roster, and validation hashes are in
`docs/environment-captures/south_fork_full_reach/m9_seated_waist_hip_v2_review.json`.

## Soft rounded production PFD V1 — rigid panel silhouette repaired, external review open

The production rescue PFD still built its visible foam from broad planar extrusions. Edge
bevels softened only the rim, leaving the chest cells and back plate rigid-looking and the
side wings rectangular in profile. V1 replaces every visible flotation face with a
multi-ring loft: four-pass rounded outlines, rolled edge transitions, shallow convex crowns,
and smooth normals. The same treatment is applied to the flank wings and low front pockets.
Zero shoulder foam pads and the two narrow webbing-only shoulder connectors remain unchanged.

![Soft rounded PFD guide front](../environment-captures/south_fork_full_reach/m9_soft_rounded_pfd_v1_guide_full.png)

![Soft rounded PFD guide profile](../environment-captures/south_fork_full_reach/m9_soft_rounded_pfd_v1_guide_profile.png)

![Soft rounded PFD guide rear](../environment-captures/south_fork_full_reach/m9_soft_rounded_pfd_v1_guide_rear.png)

The reimported project-owned asset has 25,320 authored triangles, a 2,260-triangle Nanite
fallback, five material sections, and plausible 42.295×44.897×42.29 cm bounds. All five
production identities select it with exactly 0.0 cm maximum torso-origin error. M4 v532
passes 4/4; renderer-backed M5 v533 records five successful results; renderer-backed M7
v534 records four successful results; and renderer-backed M8 v535 passes 4/4. Collision,
crew mass, water, D3/D4, flip/wrap/pin, rescue, scoring, and progression are unchanged.

The exact-current full Python/data/source matrix passes 1,148 tests with three expected
dependency-path skips and zero failures in 416.60 seconds; its immutable JUnit SHA-256 is
`56b4dab37713fd6d4a004922a84d06ee5535859f0ac39a6d130ddca340d2b167`.
The reconciled fail-closed M9 v537 acceptance suite passes 6/6.

This closes the reported hard-edged PFD silhouette as a local technical repair. It does not
approve the simplified first-party hardware, fabric shader, webbing intersections,
identity-specific deformation, seated pose, or review lighting as photoreal. A named
character-art reviewer and qualified whitewater safety reviewer must still approve or
replace the retained PFD; this geometry review is not equipment certification. Immutable
source, asset, renderer, roster, and automation hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_soft_rounded_pfd_v1_review.json`.

## Torso-wrapped production PFD V2 — rear plate removed, external review open

The V1 cell lofts rounded the visible faces, but the single rear cell still presented one
broad plane to the guide camera. V2 changes the source mesh itself. All four chest cells
now follow a 2.0 cm lateral torso arc, and the rear is two independently rounded upper and
lumbar cells with a narrow flex break and 3.2 cm of lateral wrap. Rear foam thickness drops
from 4.8 to 4.0 cm and its crown from 1.65 to 1.35 cm. The vest still terminates below the
shoulders: two thin webbing connectors remain and flotation shoulder-pad count stays zero.

![Torso-wrapped PFD guide front](../environment-captures/south_fork_full_reach/m9_torso_wrapped_pfd_v2_guide_full.png)

![Torso-wrapped PFD guide profile](../environment-captures/south_fork_full_reach/m9_torso_wrapped_pfd_v2_guide_profile.png)

![Torso-wrapped PFD guide rear](../environment-captures/south_fork_full_reach/m9_torso_wrapped_pfd_v2_guide_rear.png)

The reimported project-owned asset has 26,664 authored triangles, a 2,416-triangle Nanite
fallback, five material sections, and unchanged plausible 42.295×44.897×42.29 cm bounds.
All five production identities select it with 0.0 cm maximum torso-origin error. The five
focused PFD/safety contracts and the focused renderer-enabled M5 production-crew gate pass.
Collision, crew mass, animation authority, water, D3/D4, raft contact, rescue, scoring, and
progression are unchanged.

This is a retained technical candidate, not photoreal or safety approval. The simplified
first-party fabric shader, hardware, webbing intersections, identity-specific deformation,
seated pose, and review lighting still require replacement or named character-art review;
a qualified whitewater safety reviewer must also approve the form independently. Exact
source, asset, roster, renderer, and validation hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_torso_wrapped_pfd_v2_review.json`.

## Organic bank mosaic V2 — broader low cover, external review open

The five canonical views still exposed large bare, tessellated bank areas. Organic bank
mosaic V2 replaces the sparse broad tuft with 52 narrower grass blades and ten low forb
leaves, expands the source-conditioned ground-cover band to 22–118 m, and uses bounded
multi-scale patch noise plus shoreline and outer-bank fades for both grass and understory.
The regenerated settled map contains 220,759 collisionless ground-cover instances, 82,609
near-corridor foliage instances, and 15,702 non-colliding shore-cobble instances.

![Organic bank mosaic at Meat Grinder](../environment-captures/south_fork_full_reach/meat_grinder_guide_eye.png)

![Organic bank mosaic at Troublemaker](../environment-captures/south_fork_full_reach/troublemaker_approach.png)

![Organic bank mosaic at Coloma Bridge](../environment-captures/south_fork_full_reach/coloma_bridge_context.png)

The Unreal 5.8 editor target builds. The focused native ground-cover contract passes 1/1;
the source-layout set passes 35/35; exact-current M4 lists 4/4 successful results, M5 lists
5/5, M7 lists 4/4, and M8 passes 4/4. The final HLOD repeat evaluates 28/28 actors and saves
zero packages. The full Python/data/source matrix passes 1,148 tests with three expected
dependency-path skips and zero failures in 426.20 seconds. Reconciled and frozen-ledger M9
runs both pass 6/6.

This is a material organic-ground improvement, not photoreal acceptance. Procedural tuft
forms, coarse terrain materials, simple repeated trees, sparse mid-story vegetation,
distant cards, and synthetic lighting remain visible. Collision, navigation, terrain and
water geometry, sampling, hydraulics, D3/D4, raft/crew physics, rescue, scoring, and
progression are unchanged. Named environment-art, geospatial, and South Fork guide review
remain open. Exact hashes and the fail-closed verdict are recorded in
`docs/environment-captures/south_fork_full_reach/m9_organic_bank_mosaic_v2_review.json`.

## CC0 scanned ground-cover V216 — layered bank breakup retained, external review open

The organic-bank mosaic still exposed broad bare tan shelves between one repeated synthetic
tuft family. V216 retains all 220,759 project-owned tufts and adds 442,938 non-colliding
instances from eight selected forms in the CC0 Poly Haven Grass Bermuda 01 family. The
publisher morphology is generic only: the registered vegetation-density raster, deterministic
patch field, bank distance, slope screen, and solver/VFX wet mask retain placement authority.
Interleaved four-metre samples are permitted only for scanned cover below 34 m; every legacy
ecology, cobble, rock, collision, and gameplay layer remains on its prior eight-metre lattice.

![Scanned ground-cover candidate at Meat Grinder](../environment-captures/south_fork_full_reach/photographic_v216_cc0_scanned_ground_cover/meat_grinder_guide_eye.png)

![Scanned ground-cover candidate at Coloma Bridge](../environment-captures/south_fork_full_reach/photographic_v216_cc0_scanned_ground_cover/coloma_bridge_context.png)

The exact-camera baseline hides only the scanned layer. The retained candidate keeps the
upright procedural grass silhouette and adds lower scanned litter/grass breakup, with the
largest greater-than-eight RGB change fraction at Meat Grinder (0.004341). No grass-on-water,
black wall, or neon-card artifact was observed in the five fixed frames. Collision, terrain,
water, hydraulics, navigation, raft, and crew authority are unchanged.

This remains a technical environment improvement, not photoreal acceptance. The terrain,
trees, water, lighting, mid-story, and exact local-species match remain inadequate; named
environment-art, ecology, geospatial, and South Fork guide approval plus final desktop/VR
performance evidence remain open. A matched 1920×1080 local offscreen diagnostic hides all
16 currently streamed scanned components (40,436 instances) for its baseline: baseline and
candidate measure 18.687 ms and 19.105 ms p95, respectively. The 0.418 ms candidate delta
stays below the milestone's 0.5 ms regression allowance with no hitches and passing solver,
memory, and GPU-timing checks, but both runs miss the 16.667 ms full-map budget. This is not
packaged-window or VR qualification. Source hashes, rejected experiments, exact capture hashes,
the A/B performance record, and the fail-closed verdict are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_scanned_ground_cover_v216_review.json`.

## Closed-finger paddle grip V1 — shaft-aware wrap retained, external review open

The V36 grip put the middle-palm anchor on the solved paddle point, but that metric did not
prove that the shaft was inside the fingers. Closed-finger V1 keeps the existing shoulder,
elbow, wrist, palm, paddle, physics, and gameplay authority. For visible-paddle poses only,
it resolves the lower hand against the shaft axis and the upper hand against the transverse
T-grip, then places all four visible non-thumb finger chains on a deterministic three-segment
arc around that real grip axis.

![Closed-finger guide full view](../environment-captures/south_fork_full_reach/m9_closed_finger_paddle_grip_v1_guide_full.png)

![Closed-finger guide profile](../environment-captures/south_fork_full_reach/m9_closed_finger_paddle_grip_v1_guide_profile.png)

![Closed-finger guide rear view](../environment-captures/south_fork_full_reach/m9_closed_finger_paddle_grip_v1_guide_rear.png)

All five production identities retain the articulated two-hand pose. Their maximum measured
palm-anchor error is `1.880034572465661e-9` cm and their maximum eight-distal-joint grip-contact
error is `0.0` cm, both below the 0.25 cm runtime gates. The Unreal 5.8 editor target builds;
M4 V563 passes 4/4, renderer-backed M5 V562 passes all five results including the new anchor
and contact assertions, M7 V564 passes 4/4, and M8 V565 passes 4/4. The full V566 matrix
passes 1,148 tests with three expected skips and zero failures in 426.06 seconds. Reconciled
M9 V567 and its independent-profile confirmation V568 both pass 6/6.

This closes the reported open-finger/edge-contact defect as a local technical repair. It does
not make the procedural hand mesh, knuckles, thumb contact, skin deformation, wet response,
or synchronized paddle stroke photoreal. A named character-art reviewer and qualified
whitewater guide must approve or replace the retained hand placement and biomechanics; the
captures are not approved release media. Exact source, roster, image, and validation hashes
are recorded in
`docs/environment-captures/south_fork_full_reach/m9_closed_finger_paddle_grip_v1_review.json`.

## Visible shoulders V1 — continuous garment sleeves retained, external review open

The production visibility layer previously hid both procedural upper arms after assembling
the MetaHuman body. The PFD, neck, torso and arms therefore lacked a reliable visible
deltoid transition. Three isolated shoulder-cap attempts were rejected because they read as
rigid balls or flotation shoulder pads. The retained repair instead adds a splash-jacket
sleeve from each authoritative solved shoulder to its live elbow target.

![Visible shoulders guide full view](../environment-captures/south_fork_full_reach/m9_visible_shoulders_v1_guide_full.png)

![Visible shoulders guide profile](../environment-captures/south_fork_full_reach/m9_visible_shoulders_v1_guide_profile.png)

![Visible shoulders guide rear view](../environment-captures/south_fork_full_reach/m9_visible_shoulders_v1_guide_rear.png)

All five production identities pass the visible-silhouette contract. The smallest measured
sleeve radius is 4.861 cm, the smallest turntable half-length is 7.411 cm, and the maximum
shoulder-anchor error is `1.3605050241949357e-7` cm. The live M5 rescue pose additionally
proves that each sleeve remains elongated at its shorter 5.87 cm half-length. The PFD still
contains zero flotation shoulder pads and retains only its narrow webbing connectors.

The Unreal 5.8 editor target builds; M4 V571 passes 4/4, renderer-backed M5 V570 passes all
five results, M7 V572 passes 4/4, and M8 V573 passes 4/4. The full V574 matrix passes 1,148
tests with three expected skips and zero failures in 426.11 seconds. Reconciled M9 V575 and
the independent fresh-profile confirmation V576 both pass 6/6.

This closes the reported missing-shoulder silhouette as a local technical repair without
changing animation, mass, collision, raft, water, rescue, or gameplay forces. The sleeves,
seams, deformation, wet response, and torso integration remain simplified procedural art.
A named character-art reviewer and qualified guide must approve or replace them before any
photoreal or release-media claim. Exact source, roster, image, and validation hashes are in
`docs/environment-captures/south_fork_full_reach/m9_visible_shoulders_v1_review.json`.

## Tapered shoulder sleeves V2 — anatomical garment profile retained, photoreal review open

The uniformly scaled V1 sleeves closed the missing-shoulder gap but still read as cyan balls
in front and profile views. V2 replaces each sphere-derived section with a closed procedural
garment mesh. Eighteen axial rings and twenty-eight radial sides form a broad deltoid that
tapers continuously toward the elbow, with a restrained cuff roll at the assembled-arm
transition. The authoritative live shoulder and elbow targets do not move.

![Tapered sleeves guide full view](../environment-captures/south_fork_full_reach/m9_tapered_shoulder_sleeves_v2_guide_full.png)

![Tapered sleeves guide profile](../environment-captures/south_fork_full_reach/m9_tapered_shoulder_sleeves_v2_guide_profile.png)

![Tapered sleeves guide rear view](../environment-captures/south_fork_full_reach/m9_tapered_shoulder_sleeves_v2_guide_rear.png)

All five production identities pass the fail-closed silhouette gate with 553 authored vertices
per sleeve. The smallest measured radius is 4.861 cm, the shortest turntable half-length is
7.411 cm, and maximum shoulder-anchor error is `1.3605050241949357e-7` cm. The Unreal 5.8
editor target builds, the five-identity renderer roster completes, and renderer-enabled M5
passes 1/1 with zero warnings and zero errors.

The new taper is a clear technical improvement, not final character art. The sleeve still has
simplified topology and shading, an abrupt cuff transition, no production cloth folds or
identity-specific tailoring, and no convincing wet deformation. No named character-art reviewer
or qualified whitewater guide has approved the captures. Photoreal acceptance and promotion
therefore remain false. Exact source, roster, capture, and M5 hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_tapered_shoulder_sleeves_v2_review.json`.

## Folded wet splash sleeves V3 — Cloth response retained, photoreal review open

V2 closed the missing-shoulder gap and fixed the uniform diameter, but its smooth circular
surface and generic wet shader still read as rigid cyan tubes. V3 preserves every solved
shoulder and elbow target while replacing only the visible garment shell and its focused
material. Twenty-eight axial rings and thirty-six radial sides carry two bounded diagonal
fold fields, localized cuff gathering, restrained underarm seam relief, axial drape, and a
softly elliptical profile with finite-difference surface normals.

![Folded wet sleeves guide full view](../environment-captures/south_fork_full_reach/m9_folded_wet_splash_sleeves_v3_guide_full.png)

![Folded wet sleeves guide profile](../environment-captures/south_fork_full_reach/m9_folded_wet_splash_sleeves_v3_guide_profile.png)

![Folded wet sleeves guide rear view](../environment-captures/south_fork_full_reach/m9_folded_wet_splash_sleeves_v3_guide_rear.png)

The isolated opaque splash-jacket parent uses Cloth shading and exactly the project-owned
PFD-ripstop albedo, normal, and packed AO/roughness/height textures. It shares the PFD's
bounded presentation-only `Wetness` signal; it has no collision, mass, rescue, water, raft,
paddle-force, or gameplay authority. All five production identities report live material
response, a visible shoulder silhouette, 1,075 authored vertices per sleeve, and maximum
shoulder-anchor error of `1.3605050241949357e-7` cm.

The Unreal 5.8 editor target builds, the isolated material authoring audit completes, all 16
focused source/review contracts pass, the five-identity roster capture completes, and the
renderer-enabled M5 gate passes 1/1 with zero warnings and zero errors. Compared with V2,
front, profile, and rear views show visible garment breakup and less hard-plastic gloss.

This remains a fail-closed technical candidate, not final character art. The folds are still
regular and exaggerated, the torso and cuff transitions remain abrupt, and the overlay lacks
production skinning, compression deformation, authored seam construction, and identity-specific
tailoring. No named character-art reviewer or qualified whitewater guide has approved it.
Photoreal acceptance and promotion therefore remain false. Exact source, material, roster,
capture, and M5 hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_folded_wet_splash_sleeves_v3_review.json`.

### Opaque profile hips V1 technical candidate

The character profile exposed the turntable background between the retained seated pelvis
and the assembled production legs. Inspection confirmed that the wetsuit shader was already
opaque: the apparent transparency was missing junction geometry. Retaining the full fallback
thighs closed the hole with oversized spherical hip pads, and shorter stretched spheres still
read as detached round joints. Both candidates were rejected.

The retained repair uses two closed, tapered wetsuit bridges. Each begins 15% above its solved
hip inside the pelvis and ends 58% along the live hip-to-knee segment, so its caps stay hidden
inside overlapping anatomy. The guide and all four crew identities now preserve a continuous
opaque waist-to-upper-leg profile.

![Opaque hips guide profile](../environment-captures/south_fork_full_reach/m9_opaque_profile_hips_v1_guide_profile.png)

![Opaque hips guide rear view](../environment-captures/south_fork_full_reach/m9_opaque_profile_hips_v1_guide_rear.png)

All five turntables report opaque pelvis and thigh-root materials. The smallest measured
bridge radius is 6.357 cm, the smallest turntable half-length is 11.844 cm, and the maximum
solved-hip centreline error is `2.7414336045694654e-7` cm. Renderer-backed M5 also passes the
shorter 9.82 cm live rescue-pose bridge after a rejected diagnostic exposed an overstrict
turntable-only 10.5 cm threshold.

The Unreal 5.8 editor target builds; M5 V578 passes 5/5, M4 V579 passes 4/4, M7 V580 passes
4/4, and M8 V581 passes 4/4. The full V582 matrix passes 1,148 tests with three expected skips
and zero failures in 425.75 seconds. Reconciled M9 V583 and independent fresh-profile M9 V584
both pass 6/6.

This closes the reported transparent profile hip as a local technical repair without changing
animation, mass, collision, raft, water, rescue, or gameplay forces. The procedural
pelvis/thigh anatomy, seams, deformation, and wet response remain below final photoreal
character-art acceptance. A named character-art reviewer and qualified guide must approve or
replace them before release-media use. Exact source, roster, image, and validation hashes are
in `docs/environment-captures/south_fork_full_reach/m9_opaque_profile_hips_v1_review.json`.

### Continuous thigh/knee V1 technical candidate

The retained opaque hip bridge ended at 58% of the solved hip-to-knee segment. In profile,
that left a diagonal separation before the assembled knee; because the retained thigh was
also narrower, the knee read as a detached mass larger than the upper leg. The replacement
keeps the same closed tapered mesh but extends it from -0.15 to 1.06 of the solved segment,
raises its maximum reference radius to 8.0 cm, and narrows the analytic profile toward the
knee. Its caps stay buried in the overlapping pelvis and assembled lower-leg geometry.

![Continuous thigh and knee guide profile](../environment-captures/south_fork_full_reach/m9_continuous_thigh_knee_v1_guide_profile.png)

![Continuous thigh and knee guide rear view](../environment-captures/south_fork_full_reach/m9_continuous_thigh_knee_v1_guide_rear.png)

![Continuous thigh and knee smallest-body profile](../environment-captures/south_fork_full_reach/m9_continuous_thigh_knee_v1_smallest_profile.png)

All five production identities report a continuous thigh/knee silhouette. The smallest
measured thigh radius is 7.479 cm, the smallest half-length is 19.632 cm, and the maximum
solved-knee centreline coverage error is `2.3936797433066204e-8` cm. Guide, broadest, and
smallest-body front/profile/rear captures all preserve a larger thigh with a narrower knee
transition.

The Unreal 5.8 editor target builds; renderer-backed M5 V585 passes 5/5, M4 V586 passes 4/4,
M7 V587 passes 4/4, and M8 V588 passes 4/4. The full V589 matrix passes 1,148 tests with three
expected skips and zero failures in 428.19 seconds. Reconciled M9 V590 and exact confirmation
M9 V591 both pass 6/6.

This closes the disconnected and oversized-knee relationship as a local technical repair
without changing animation, mass, collision, raft, water, rescue, or gameplay forces. Rear
thigh muscle shape, deformation, seams, and wet response remain simplified procedural art.
A named character-art reviewer and qualified guide must approve or replace this anatomy and
its seated biomechanics before photoreal or release-media acceptance. Exact source, roster,
image, and validation hashes are in
`docs/environment-captures/south_fork_full_reach/m9_continuous_thigh_knee_v1_review.json`.

## Cloth and live-wet production PFD V1 — textile response retained, external review open

The torso-wrapped PFD geometry still used a uniformly lit shell that read as molded plastic.
All four shell colors now use Unreal Cloth shading with the existing project-owned ripstop
albedo, normal, and packed AO/roughness maps. Each avatar owns one dynamic shell instance;
native raft surface wetness controls seated dampness, while swimming, re-entry, and falling
immediately impose presentation-only wetness floors.

![Dry cloth PFD close view](../environment-captures/south_fork_full_reach/m9_cloth_wet_pfd_v1_guide_dry.png)

![Wet cloth PFD close view](../environment-captures/south_fork_full_reach/m9_cloth_wet_pfd_v1_guide_wet.png)

The first wet bracket was rejected for a broad lacquer-like highlight. The retained bracket
uses a 0.42 wet specular endpoint, at least 0.40 saturated roughness, and 0.16 retained wet
cloth response. Matched captures hold the same seated pose and camera while changing the
guide shell from 0.0 to 0.84 presentation wetness. The dry frame retains a matte visible
weave; the wet frame darkens and develops narrower water-film highlights without erasing the
fabric response.

The Unreal 5.8 editor target builds. The renderer-backed material audit compiles all four
opaque Nanite Cloth assets with exactly the PfdRipstop texture set. Four focused source and
evidence contracts pass. All five roster identities expose the live material response, and
M5 passes all five production-quality rows with zero failures; one existing motion-vector
configuration warning remains.

This is a cross-river presentation repair only. It does not change collision, crew mass,
raft/water forces, rescue, scoring, progression, or any other gameplay authority. Simplified
PFD hardware and seams, identity-specific fit/deformation, surrounding procedural anatomy,
and named character-art and whitewater-safety approval remain open. Exact hashes and the
fail-closed verdict are in
`docs/environment-captures/south_fork_full_reach/m9_cloth_wet_pfd_v1_review.json`.

## Integrated soft-carrier production PFD V3 — fitted geometry retained, external review open

The torso-wrapped V2 still read as separate flotation blocks with rigid yellow side wings,
projected tubular fit straps, and a round rescue belt. V3 adds a fitted fabric carrier beneath
thinner chest and rear cells, removes all side foam and duplicate tubular adjustment runs, and
uses three flat fit bands per side plus a flat torso-following rescue belt. The vest remains
sleeveless with zero flotation shoulder pads.

![Integrated soft-carrier guide front](../environment-captures/south_fork_full_reach/m9_integrated_soft_carrier_pfd_v3_guide_full.png)

![Integrated soft-carrier guide profile](../environment-captures/south_fork_full_reach/m9_integrated_soft_carrier_pfd_v3_guide_profile.png)

![Integrated soft-carrier guide rear](../environment-captures/south_fork_full_reach/m9_integrated_soft_carrier_pfd_v3_guide_rear.png)

The deterministic generator-v10 source imports at 39.025 x 34.52 x 42.8 cm with 39,448
authored triangles, a 2,667-triangle Nanite fallback, and five material slots. All five
production identities use the new asset with 0.0 cm maximum torso-origin error. The editor
build, six focused Python contracts, renderer turntable, dry/wet close captures, and the
renderer-enabled M5 crew-presentation test pass.

This is a technical presentation improvement, not photoreal or safety acceptance. Remaining
foam faceting, simplified fabric and hardware, pocket/webbing intersections, identity-specific
deformation, seated review lighting, named character-art approval, and qualified whitewater-
safety approval remain open. No collision, crew mass, animation, raft/water physics, D3/D4,
rescue, scoring, or progression authority changed. Exact hashes and the fail-closed verdict are
in `docs/environment-captures/south_fork_full_reach/m9_integrated_soft_carrier_pfd_v3_review.json`.

## Tapered soft-cell production PFD V5 — slab profile reduced, external review open

The later V4 side-webbing pass removed the third adjustment run on each flank and curved the
remaining four runs around the torso, but the chest and back cells still projected as thick
vertical slabs. V5 reduces front foam from 4.2 to 3.0 cm, rear foam from 3.2 to 2.4 cm, and
front/rear crown depth from 1.25/1.60 to 0.65/0.75 cm. Stronger lateral wrap, an eleven-ring
soft crown, thinner carriers, and curved front backup webbing keep the hardware on the vest
surface instead of a flat plane. The source front-to-back bound falls 14.55%, from 39.025 to
33.345 cm, without adding side wings or shoulder flotation.

![Tapered soft-cell guide front](../environment-captures/south_fork_full_reach/m9_tapered_soft_cell_pfd_v5_guide_full.png)

![Tapered soft-cell guide profile](../environment-captures/south_fork_full_reach/m9_tapered_soft_cell_pfd_v5_guide_profile.png)

![Tapered soft-cell guide rear](../environment-captures/south_fork_full_reach/m9_tapered_soft_cell_pfd_v5_guide_rear.png)

The deterministic generator-v12 source imports at 33.345 x 34.22 x 42.8 cm with 40,232
authored triangles, a 2,616-triangle Nanite fallback, and five material slots. Fixed views for
the guide and broadest roster identity show the reduced profile and no clipping. All five
identities retain the production PFD, live wet-material response, and 0.0 cm maximum
torso-origin error. The editor target builds and the renderer-enabled M5 crew-presentation
test passes 1/1 with zero warnings and zero errors.

This is a retained technical improvement, not photoreal or safety acceptance. The wider
first-party character anatomy, fabric/hardware surfacing, pocket/webbing intersections,
identity-specific deformation, seated review lighting, named character-art approval, and
qualified whitewater-safety approval remain open. No collision, crew mass, animation,
raft/water physics, D3/D4, rescue, scoring, or progression authority changed. Exact hashes and
the fail-closed verdict are in
`docs/environment-captures/south_fork_full_reach/m9_tapered_soft_cell_pfd_v5_review.json`.

## CC0 rendered-face-fitted helmet V1 — fallback fit retained, external review open

The packaged CC0 fallback previously positioned the production helmet from a bone-space
estimate. Identity-dependent face/neck deformation left the guide and Crew 01 shells hovering
above their visible faces, while legacy hair cards protruded around the shell.

V1 caches 64 skin vertices nearest each source eye line and averages their live post-skinning
positions, then gives that rendered facial anchor and the head's authored forward/up frame to
the shared production fitter. Bounded guide and Crew 01 offsets seat the shell at the brow. The
continuous shell uses a dedicated zero-opacity material for helmet-contained hair; the original
CC0/CC-BY source files, materials, hashes, and attribution remain packaged.

![CC0 guide fitted helmet front](../environment-captures/south_fork_full_reach/m9_cc0_face_fitted_helmet_v1_guide_full.png)

![CC0 guide fitted helmet profile](../environment-captures/south_fork_full_reach/m9_cc0_face_fitted_helmet_v1_guide_profile.png)

![CC0 Crew 01 fitted helmet profile](../environment-captures/south_fork_full_reach/m9_cc0_face_fitted_helmet_v1_crew01_profile.png)

All five identities pass front/profile/rear capture with exclusive CC0 body ownership, production
PFD/helmet/boots, exactly 1.0 forward alignment, 0.96 fit scale, and maximum solved-anchor error
of `7.312e-10` cm. The editor target builds and the forced-CC0 renderer-backed M5 report contains
five successful result entries with zero failures. Collision, crew mass, water, raft forces,
rescue, scoring, and progression are unchanged.

This closes the reported backward/hovering fallback-helmet transform defect as a technical repair.
It does not make the fallback anatomy, skin/eye shading, clothing deformation, hands, shell and
retention materials, or lighting photoreal. Named character-art approval and qualified
whitewater-safety review remain open. Exact source, import, renderer, metric, and automation
hashes are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_face_fitted_helmet_v1_review.json`.

## CC0 skin reflectance calibration V1 — technical response improved, photoreal review rejected

The five packaged CC0 fallback identities previously shared one broad subsurface response even
though their source atlases were photographed in materially different exposure brackets. Under
the fixed roster rig, the guide and Crew 02/03 faces clipped toward white while Crew 01/04 read
hotter and more orange than their unchanged source atlases.

V1 uses Unreal preintegrated skin shading and one identity-neutral linear scalar for each
existing, rights-tracked atlas: guide 0.36, Crew 01 0.72, Crew 02 0.48, Crew 03 0.42, and Crew 04
0.72. These are reflectance gains, not replacement textures or per-channel identity remaps; the
source pixels, atlas hue, geometry, rigs, animation, and gameplay remain unchanged. In matched
1536×1024 profile captures, candidate p95 luminance is lower for all five identities.

![Calibrated guide profile](../environment-captures/south_fork_full_reach/m9_cc0_skin_reflectance_v1/raftsim_cc0_guide_profile.png)

![Calibrated Crew 01 profile](../environment-captures/south_fork_full_reach/m9_cc0_skin_reflectance_v1/raftsim_cc0_crew01_profile.png)

![Calibrated Crew 03 profile](../environment-captures/south_fork_full_reach/m9_cc0_skin_reflectance_v1/raftsim_cc0_crew03_profile.png)

All five front/profile/rear captures retain exclusive CC0 ownership and the previously verified
helmet/PFD/boot selections. The editor target builds, the focused Python contracts pass, and the
forced-CC0 renderer-backed M5 report contains five successful test entries with zero failures.

This milestone is deliberately fail-closed. The images still show simplified head/body anatomy,
closed-looking or absent eye presentation, weak shoulders/hips/knees, disconnected-looking hands
and boots, clothing/PPE intersections, and synthetic materials. Named character-art approval and
qualified whitewater-safety approval remain open, so M9 and photoreal promotion remain blocked.
Exact captures, measurements, asset/source hashes, and validation are recorded in
`docs/environment-captures/south_fork_full_reach/m9_cc0_skin_reflectance_v1_review.json`.

## CC0 eye reference pose and rendered helmet anchor V1 — attachment fixed, photoreal review rejected

The previous fallback render exposed a source/export mismatch: Blender displayed eyes and
brows after a non-identity Armature deformation, while Unreal populated its reference vertex
buffers from the unbaked raw mesh. The apparent Blender attachment therefore hid detached
raw facial sections and produced closed-looking or missing eyes after import.

V1 bakes the evaluated shape and one Armature deformation into each joined body, promotes
the displayed armature pose to rest, and restores exactly one clean modifier before export.
The validator now checks raw and evaluated reference geometry, stable Skin pairing, and a
58° synthetic head rotation. All five checked-in FBXs pass. The Unreal quality gate measures
maximum p95 separation of 0.368 cm for eyes and 1.120 cm for brows against a 1.25 cm limit.

![Guide repaired eye and helmet close-up](../environment-captures/south_fork_full_reach/m9_cc0_eye_reference_pose_v1/captures/raftsim_cc0_guide_face.png)

![Crew 02 repaired eye and helmet close-up](../environment-captures/south_fork_full_reach/m9_cc0_eye_reference_pose_v1/captures/raftsim_cc0_crew02_face.png)

![Crew 04 repaired eye and helmet full-body view](../environment-captures/south_fork_full_reach/m9_cc0_eye_reference_pose_v1/captures/raftsim_cc0_crew04_full.png)

Runtime helmet fitting now averages the actually rendered Eye-section vertices after live
skinning. Bounded identity offsets seat all five shells on the head; the fixed harness rejects
any solved anchor below the upper body. Twenty fixed views complete with exclusive CC0 body
ownership, production PFD/helmet/boots, 1.0 helmet forward alignment, and 0.96 fit scale. The
Unreal editor target builds, 12 focused Python contracts pass, and renderer-backed M5 reports
five completed tests with zero failures and the existing motion-vector warning.

This closes eye/brow detachment and the resulting off-head helmet regression as technical
defects. It does not accept the fallback as photoreal: anatomy and expression remain
simplified; garment, arm, hand, paddle, and PPE intersections remain visible; and material
response is still synthetic. Named character-art review, qualified whitewater-safety review,
and product-owner release-media approval remain required. Exact hashes and the fail-closed
verdict are in
`docs/environment-captures/south_fork_full_reach/m9_cc0_eye_reference_pose_v1_review.json`.

## Required named decisions

- [ ] Product owner: campaign, scope, disclosures, and every deferred/blocking item.
- [ ] Qualified South Fork guide: three-flow hydraulics, lines, hazards, raft outcomes,
  swimming, rescue, and guide-seat readability.
- [ ] Art director/lead artist: environment, character, raft, water, lighting, VFX, and
  replacement-or-acceptance decision for every visual blocker.
- [ ] Geospatial reviewer: NHD/3DEP/NAIP alignment, stationing, source/inferred boundaries,
  and not-for-navigation disclosure.
- [ ] Rights/legal reviewer: item-level provenance, attribution, redistribution, releases,
  notices, disclosure language, and every press-kit candidate.

## External release matrix

- [ ] Fresh macOS machine — keyboard/mouse.
- [ ] Fresh macOS machine — physical gamepad.
- [ ] Windows x64 Shipping — RTX 3060 target.
- [ ] Windows x64 Shipping — RTX 4070 target.
- [ ] Windows Authenticode signature verification.
- [ ] Linux Steam/Proton run of the immutable Windows artifact.
- [ ] macOS Developer ID signing, notarization, stapling, and Gatekeeper assessment.

## Promotion rule

M9 may pass only after all named reviews include evidence, captures are approved or
replaced, the external platform matrix passes, rights-cleared release media exists, and
the candidate is rebuilt and hashed from one clean milestone commit. Until then the M9
manifest and press-kit media manifest remain `passed: false`.
