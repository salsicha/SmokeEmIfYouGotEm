# Unreal Photoreal Open-World Stack

The first Unreal slice targets UE 5.8 and enables the modern photoreal river-corridor stack in source-controlled project configuration.
Landscape, rocks, banks, and foliage are treated as first-class immersion targets, with each river corridor pushed as close to photorealistic reference quality as target hardware, VR comfort, and gameplay readability allow.

## Production Baseline

- Nanite for rocks, canyon walls, terrain detail meshes, raft parts, scanned props, and debris.
- Lumen/Lumen Lite evaluation for canyon bounce lighting, wet-rock reflections, forest shade, weather, and portable performance modes.
- Virtual Shadow Maps for dense foliage and dynamic raft/crew shadows.
- World Partition for real-world river corridors.
- PCG for foliage, rocks, gravel bars, driftwood, debris, foam-line accents, and hazards.
- Niagara for white water spray, mist, splash, foam, rain, paddle effects, and rescue cues.
- Substrate/material-layering workflows for wet rock, rubber, mud, foam, helmets, PFDs, and aerated water.
- OpenXR for VR.

## Evaluation Only

- Procedural Vegetation Editor and Nanite foliage are enabled for isolated source-Landscape evaluation; PVE-exported river-specific species and measured desktop/VR performance are still required before production use. Mesh Terrain and Fast Geometry Streaming remain feature-evaluation items.
- Unreal Water System is enabled for visual water and authoring, but the custom shallow-water solver remains authoritative physics.

The canonical feature manifest is `unreal/Content/RaftSim/Rendering/photoreal_stack.manifest.json`.

The first vertical-slice environment recipe is `unreal/Content/RaftSim/Rendering/vertical_slice_environment_corridor.json`. It binds the South Fork corridor package, photoreal stack, and telemetry presentation cues into map-authoring layers for landscape/bed, banks, rocks, foliage, debris/access context, lighting/weather, audio occlusion/reverb geometry, and water-readability support.

The three-river environment source and capture plan is `unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json`. It records the source stack for South Fork American, Colorado River, and Pacuare: maps, terrain, hydrography, flow evidence, aerial/satellite imagery, link-only social/reference media policy, procedural generation layers, target Unreal map packages, and required guide-seat downstream captures.

The concrete source attachment checklist for tools is `physics/data/real_world/production_geospatial_attachment_ledger.json`. It records existence-checked terrain, hydrography, aerial imagery, mask, flow, access/protected-area, and guide/media annotation artifacts for all three runnable rivers, while keeping every class preview-only until CRS, terms, guide review, rights, and lifelike capture gates pass.

The approved first-party procedural-equivalent environment asset plan is `unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json`. It covers canyon walls, riverbeds, wet boulders, shore vegetation, tropical canopy, water depth/current cues, foam/spray/mist, raft foreground, and river-specific lighting as the traceable replacement path when licensed/photogrammetry assets are not yet cleared. The editor preview and capture commands now require and record this plan, but the current renders remain preview-only until these recipes are implemented as production-quality Unreal assets/materials and verified by capture/performance evidence.

The generated preview maps live under `/Game/RaftSim/Maps/EnvironmentPreviews/`, and `RaftSim.CreatePhotorealEnvironmentPreviewMaps` plus `RaftSim.CapturePhotorealEnvironmentPreviews` rebuild the three base maps, ten flow-variant maps, and 26 guide-seat/river-eye screenshots. The July 9 renderer imports the first-party `ProductionDetailTextures` albedo, tangent normal, and packed AO/roughness/height sets for South Fork, Grand Canyon, and Pacuare. `M_RaftSim_AtlasSampleReview` now uses separate RG `AtlasTileOrigin`/`AtlasTileScale` and `TerrainDetailUvScale`/`TerrainDetailUvOffset` parameters, fixing the UE 5.8 Metal component-mask compile failure that had silently fallen back to Unreal's default material.

The first native source-terrain candidates now live under `/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/`. `RaftSim.CreateLandscapeImportCandidateMaps` imports the three review-gated 1009x1009 16-bit PNG heightfields through Unreal's `LandscapeEditor` format API as 16x16-component `ALandscape` maps, builds four Nanite representations per river, audits all 256 source component and Nanite material bindings, and captures guide-seat plus river-eye evidence under `docs/environment-captures/photoreal_river_previews/landscape_candidates/`. Each candidate material combines four source-conditioned Texture2D assets with three independent first-party close-range terrain Texture2D assets. Macro albedo, normals, ambient occlusion, and roughness retain source/detail variation; the material-zone blue channel darkens submerged riverbed color/roughness and its feathered edge conditions the wet bank without altering geometry. River-specific Landscape mapping and all bounded zone settings are recorded in the generated manifest. PVE/Nanite-foliage evaluation is active in these maps: source masks and imported Landscape heights drive complete HISM tree, conifer, shrub, and understory meshes while first-party dense irregular rock meshes add bounded river-specific dressing. The maps bind opaque Default Lit water parents and per-river instances to the solver-owned procedural ribbon, including Zambezi's separately tuned capture-safe parent. These expose surface/vertex tint balance, seam-continuous normal-atlas detail, bounded render overlap/smoothing, reflection support, and a small Fresnel capture fallback without requiring WaterBody/WaterZone or changing physics/forcing authority; inactive Single Layer volume parameters remain manifest-recorded for evaluation. Direct isolation found that the remaining continuous white bank rails were uncovered render gaps rather than the Landscape wet-bank feather: stronger feather-tail shading did not move them, while noncolliding render overlap did. The manifest now records 1.35x South Fork, 1.17x Colorado, and 1.35x Pacuare render widths; recapture removes the South Fork rail and leaves only one tiny distant Pacuare bank point for production microgeometry, without widening collision or changing solver geometry. South Fork additionally binds two clamped Texture2D derivatives from the accepted whole-window median finite-volume C++ frame: tangent macro normals and packed RGBA depth/speed/Froude/detrended-`eta`. `cpp_solver_visualization_field_manifest.json` records source hashes, corrected boundary and HLL semantics, `feature_strength_scale=0`, passing GeoClaw comparison, passing full C++ gate, the accepted report-set lock, visual decode gains, and a lossless ±4 m relief encoding under a 36 cm render ceiling. The noncolliding candidate ribbon uses that relief with only 42% residual analytic displacement and adds a separate noncolliding DefaultLit foam surface whose deterministic breakup is confined to the decoded speed/Froude aeration mask. A dedicated South Fork rapid camera frames the strongest accepted mean-Froude approach, while the standard upstream capture remains calm. None of these render derivatives changes solver state, collision, raft force, conservation evidence, or feature forcing, and none is reused for Colorado or Pacuare. The offscreen renderer uses persistent view state plus a first render to request shader permutations, waits for compilation, recreates Landscape component state, and then records the evidence frame; this prevents UE 5.8's fallback grid or missing reflection history from masquerading as final shading. The candidates remain isolated and review-gated because their analytic preview channel burn is not solver or accepted geospatial geometry, the generic PVE sample species and procedural rocks are evaluation content rather than final biome assets, and visual inspection still shows coarse banks, repeated silhouettes, provisional surface shading, low-resolution whitewater, and missing crest-scale spray, atmosphere, and production VFX.

Zambezi now follows the Default Lit capture contract through its isolated `M_RaftSim_Zambezi_DefaultLitWater` parent. It preserves the former experiment's opposed panned normal layers, secondary-axis swap, short cross-current wavelengths, and restrained world-space variation, but has no Single Layer Water volume output. A bounded first-party emissive fill makes the same surface readable in canonical SceneCapture2D evidence: lower-half mean luminance rises from 0.060286 to 0.247354 in the guide-seat frame and from 0.061027 to 0.223423 at river eye, with no retained lower-half pixels below 0.02. The rejected `M_RaftSim_Zambezi_SingleLayerWater` asset and its volume coefficients remain inactive audit evidence. This changes only the non-colliding presentation ribbon; the broad live solver carrier remains at zero optical coverage, the focused solver-foam sheet and raft/crew exclusion remain active, and no terrain, collision, solver, hydraulics, bathymetry, or raft-force authority changes. The 5 m reference flow field preserves its full-corridor station axis and produces live breaking sites in the launch-window PIE gate, with production Niagara roller and aerosol activity required by the test. Those 25 feature-tagged transitions are explicitly procedural reference infill, not measured hydraulics. The result remains review-gated rather than photoreal because the water still has broad smooth highlight bands and terrain silhouette, local bathymetry, credible crest/foam/spray geometry, vegetation, atmosphere, seasonal calibration, and named guide/art approval remain open.

Pacuare's later isolated Single Layer V1 is now explicitly rejected and inactive. Both direct material isolation and a 31,409-vertex procedural reference-infill bathymetry bracket left the same hard horizontal foreground depth-composition band; a separate terrain-colored shoreline-infill attempt covered bright gaps but introduced broad tessellated bank facets and was also discarded. The retained `M_RaftSim_Pacuare_RainforestDefaultLitWater` preserves Pacuare's two moving normal layers and two world-variation scales without a volume output. A 1.35x non-colliding render overlap removes the continuous shoreline gaps while leaving one tiny distant river-right point for source-aligned production bank microgeometry. No rejected infill changes the saved map, Landscape collision, heightfield, solver geometry, hydraulics, or raft forces.

The August 1 Pacuare field binding supersedes the earlier statement above that
only South Fork had a river-specific solver visualization. Upper Huacas now
has its own deterministic packed derivative from the committed
`rainfed_runnable_planning` arrays: depth, speed, Froude, and detrended
`bed+h` relief. The source contains 5,393 wet cells, 52 supercritical cells, a
4.275 m/s speed maximum, and a 2.525 Froude maximum; the strongest column-mean
Froude occurs at station 286 m. The non-colliding capture ribbon uses at most
18 cm of added field relief, 22% residual analytic ripple, and a separate
masked foam sheet with eight metres of bounded downstream persistence from
adjacent cooked samples. Guide, river-eye, and dedicated solver-crux cameras
frame that hydraulic control. Both authored actors remain hidden in play while
the live cooked-field surface owns runtime rendering and forces; capture
automation temporarily reveals only actors tagged
`RaftSimCaptureOnlyStaticWater` and restores their saved state afterward. This
closes the flat/dark-water evidence bug, not the production-fidelity gate: the
source run is unconverged, and the opaque water, coarse foam bands, generic
foliage, interpreted geography, missing spray/mist, guide validation, and
full-run runtime evidence remain rejected in the V2 review.

The August 3 Pacuare live-water pass supersedes the opaque gameplay-water
limitation above. `L_UpperHuacas` now renders gameplay water through the live
`ARaftSimWaterSurfaceActor`: an all-wet-cell-clipped transmitting volume core
under a 3.5%-14% solver detail skin. A Pacuare-local instance of the shared
raft-transmitting parent binds first-party flow-normal and foam-lace textures;
the lace is masked by solver foam and speed and cannot create whitewater in
calm or dry cells. The prior packed-field ribbon and foam sheet remain
capture-only and hidden in play. Matched over-raft evidence replaces the
uniform pale sheet with visible live relief and shallow riverbed variation,
and the focused native and PIE gates pass. This changes no cooked field,
wet/dry state, bathymetry, coordinate mapping, collision, buoyancy, or raft
force. Rounded procedural banks, generic repeated vegetation, thin water
optics, sparse foam, missing spray/mist, unconverged hydraulics, and six
external gates keep photoreal and production promotion closed; the exact
contract is hash-locked in
`pacuare_live_transmitting_water_v1_review.json`.

The August 2 Colorado Hance water pass narrows the cooked-field capture relief
ceiling from 45 cm to 9 cm and applies a plane-preserving cardinal five-tap
filter only to all-wet presentation vertices. The live carrier uses the same
river-local concept with 0.72 smoothing strength, 0.55 standing-wave and relief
scales, and a narrower rapid-foam focus; it builds a temporary presentation
height array and leaves authoritative `WaterSamples`, collision, bathymetry,
buoyancy, and raft forces unchanged. The capture foam bracket reduces bright
neutral water-band coverage from 3.68% to 0.37% in the guide/solver view, so the
previous broad white sheets are no longer dominant. This is a retained
technical improvement, not a photoreal pass: horizontal bands remain visible,
foam lacks credible rapid structure and spray, the water remains opaque, the
canyon is terraced, and the hydraulic field and external review gates remain
open. The hash-locked review is
`colorado_hance_subcell_smoothed_water_lace_foam_v1_review.json`.

The August 3 Hance V3 terrain/ecology pass keeps the complete plus-or-minus
39 m C3 solver strip and runtime coordinate map unchanged while replacing the
remaining sine-like outer-bank relief with deterministic seeded massing,
incised drainage, irregular buttresses, talus, and a bounded debris-fan
landform analog. An explicit 1.18 rise/run limiter constrains generated outer
grades; the protected join remains below 8 mm and the dominant cross-bank band
energy falls from 0.432 to 0.345. Four project-owned opaque dryland meshes now
place 3,000 ground-cover and 480 shrub instances in two morphologies each,
outside the solver strip and with no collision or ecology/geography/hydraulic
authority. The fixed-camera result is retained because terrain massing and
bank breakup improve, but it still fails photoreal review: vegetation is
stylized, terrain is not a Hance survey, water/rocks/VFX remain synthetic, and
all six external gates remain open. The hash-locked record is
`colorado_hance_nonperiodic_canyon_dryland_ecology_v3_review.json`.

The August 1 Upper Huacas integration supersedes Pacuare's broad,
scale-mismatched DEM candidate as the active runnable map. `L_UpperHuacas` now
owns a physical 600×78 m, 1009×1009 Landscape derived from the committed C3
window rather than squeezing a roughly 37×44 km GLO-30 review mosaic into a
323×55 m shell. A bounded ±0.38 m procedural relief field affects only
unmeasured outer banks; the protected channel and map perimeter remain
unchanged. A 301-point identity station/lateral coordinate map applies a
454.283 m vertical datum, making the live cooked field and static Landscape
agree exactly along the centerline. The saved map supplies the player
raft/start and game mode, hides its deterministic capture ribbon during play,
and passes its focused runtime load test. This is a reference-runnable
geography correction, not photoreal promotion: water optics, visible rapid
foam/spray, biome-specific foliage, wet-bank/riverbed detail, higher-resolution
terrain, guide/geospatial/hydraulic/ecology/art review, and desktop/VR
performance evidence remain open.

The Zambezi render terrain now uses a V15 organic treatment on four collision-free 12.5 m visual tiles while the source Copernicus Landscape remains the sole terrain/physics authority. Central-difference grid normals, slower relief, variable strata/erosion/talus, and a 3.2 m-capped six-pass reconstruction reduce triangle and regular-terrace artifacts; the first 100 m stays horizontally protected except for upper rock at least 6 m above local water, and morphology remains capped at 2.8 m outside that radius. Since the 30 m DEM still generates a false comb under self-shadow, only those non-colliding visual tiles have shadow casting disabled; an audited movable -48/-90 degree review sun keeps the result deterministic while raft, rock, downstream woody vegetation, and gameplay geometry retain shadows. Two additional source-conditioned 5 m adaptive banks cover the first kilometre, preserve a 3 m dry buffer outside the 72 m active-water half-width, and use at most 1.8 m of dry-shoreline correction plus 0.96 m of bounded erosion/fracture/talus infill. They contribute 42,612 vertices and 61,748 triangles but remain non-colliding and presentation-only. Their shadow-casting V1 was rejected for enormous black wedges; the retained actors suppress self-shadow. Schema v15 rejects any restored high-density bank ribbon and requires all six terrain actors, the four-actor Zambezi atmosphere contract, and their authority tags and properties. The accepted default capture passes dry-clearance and artifact reduction, not photoreal promotion: the canyon remains rounded and bright and is dependent on acquisition of higher-resolution full-reach terrain and reviewed southern African ecology.

Zambezi also has an isolated camera-visible bank-cover component. It adds 1,200
grounded instances of the project-owned opaque savanna mesh across the two
canonical downstream windows, outside the active water corridor and selected
against the lowest available DEM slope. Together with 5,600 full-corridor tree,
scrub, and ground-cover instances, the saved map now audits 6,800 opaque,
non-colliding vegetation instances and zero legacy alpha-card actors. Both
captures visibly contain bank cover, but the procedural clumps, sparse ecology,
coarse DEM silhouette, and synthetic materials still fail photoreal promotion.

The next Zambezi ecology layer adds 232 camera-visible woody instances in three
separate HISM actors: 58 riparian trees, 57 umbrella trees, and 117 thorn-scrub
forms. A deterministic forty-candidate search rejects eight placements above a
hard 24° DEM-slope ceiling; the maximum accepted slope is 15.83°. Muted olive
vertex colours and a stronger low-light material floor reduce the first
bracket's graphic green/black contrast. That milestone audited 7,032
opaque, non-colliding vegetation instances across eight components. The result
is more legible ecology, not production foliage: repeated procedural crowns,
missing wind/seasonal variation, coarse lighting, and absent species/art/guide
approval remain open.

The runnable launch has four additional HISM components rather than depending
on those downstream documentary windows. The expanded deterministic search
places 1,721 solid savanna-cover instances approximately 151-842 m downstream
and 174 woody instances approximately 215-864 m downstream, split 44/43/87
between riparian tree, umbrella tree, and thorn scrub. Every candidate is
checked against all route segments, conditioned-water height, and a hard DEM
slope ceiling; woody plants stay at least 50 m beyond the active half-width.
These launch-only, non-colliding components suppress shadows to avoid the
rejected crown/wall streak under the low review sun; the full-corridor and
camera-mosaic ground-cover layers are also shadowless, while downstream woody
ecology retains shadows. The saved map now audits 8,927 instances across 12
components under schema v15. The retained gameplay frame is stable and contains
no adaptive-bank shadow wedge, but the extra ground cover reads as a thin,
repeated shoreline band and the foreground remains sparse and synthetic. This
is technical coverage and dry-bank conditioning, not photoreal art or ecological
promotion.

The same runnable window now has six separately auditable talus HISM actors
because the legacy 180-rock corridor distribution starts roughly 5 km
downstream. A deterministic 128-candidate search places 360 rights-reviewed CC0
rock analogs approximately 118-993 m downstream, split 60 per mesh. Full-route,
conditioned-water dry-height, and 48-degree hard-slope gates accept all targets;
the maximum accepted slope is 37.817 degrees. The 0.95-5.20 m visual instances
cast shadows but are source-Landscape-grounded, non-colliding, and explicitly
barred from Batoka-lithology, water, solver, and raft-force authority. All six
components now bind `MI_RaftSim_Zambezi_BasaltTalusV1` instead of the source
moss material directly. The project-owned parent preserves bounded scan
microstructure while the instance limits that already desaturated branch to
0.42 and supplies 0.58 neutral mineral response. A -10,000,000 cm waterline
keeps the parent's 70 cm wet band inactive until a validated per-instance local
water elevation exists. Schema v15 and
`RaftSim.M9.FZambeziTalusMaterial` prevent the old material binding from
returning. The standard fixed views retain the bank breakup without route
obstruction but do not resolve the rocks closely enough for visual material
acceptance; generic geometry, hard shadowing, repeated bright vegetation,
rounded coarse terrain, and the missing credible wet-bank transition still
reject photoreal promotion.

Candidate lighting and post-processing now come from one river-specific `FRaftSimPhotographicCaptureSettings` contract rather than scattered desert/rainforest conditionals. Sun, skylight, fog, manual exposure, saturation, contrast, sharpening, vignette, and zero camera-film-grain values are serialized into `landscape_candidate_manifest.json` for every evidence frame. A clean UE 5.8 rebuild and offscreen recapture produced no material or shader errors and all 26 environment tests pass. The controlled sky fill improves diagnostic shadow retention, but visual review still finds near-black repeated foliage, coarse terrain plates, and a flat overlapping foreground water/bank ribbon; these are production material/geometry blockers, not reasons to hide the scene with stronger exposure or post-process noise.

The PVE evaluation path now uses complete exported geometry rather than assembling crowns from twig fragments and cylinder trunks. Editor automation loads the installed deciduous tree, conifer, shrub, and plant Nanite skeletal sources, converts them once into four saved static meshes under `/Game/RaftSim/Environment/BiomeSpecies/`, and places whole meshes with source water/vegetation masks through HISM components. Three complete-species `TwoSidedFoliage` slots receive river-specific texture-preserving material instances and the fourth keeps its native PVE material. The manifest records four source assets, four conversions, three custom bindings, one native fallback, Nanite state, and canopy/understory counts: 160/100 for South Fork, 0/110 for Colorado, and 194/226 for Pacuare. A near-camera ecology rule restricts the immediate evidence corridor to shrubs and understory so full crowns cannot occlude the river-eye frame. The twig-pile construction is gone, but the small generic sample set still has oversized repeated leaf forms and is not a substitute for rights-clear biome-specific species, canopy age/shape diversity, wind, seasonal state, or performance review.

`unreal/Content/RaftSim/Environment/BiomeSpecies/pve_species_conversion_manifest.json` is the shared provenance and promotion record for those four derivatives. It marks them as installed UE 5.8 engine-plugin sample content used only for isolated Unreal evaluation, records that no external asset was downloaded in this pass, and keeps species identity, ecology, rights, wind, and performance approval open.

The renderer disables legacy terrain and water overlay proxy geometry, engine-side synthetic film-grain dither, and camera film grain. The source-terrain pass samples each review-gated 2017px DEM derivative bilinearly, feathers stitched-tile center seams, separates meter-scale macro relief from bounded multi-scale erosion residuals, and uses river-specific normal flattening. Legacy/base water uses a dedicated DefaultLit parent; the Landscape candidate branch now uses the opaque DefaultLit solver-surface parent with river-specific surface, normal, reflection, roughness, displacement, and solver-field controls while preserving the same C++ ribbon authority. The former Single Layer Water assets remain inactive evaluation evidence after direct isolation tied their lower-frame split to depth composition over provisional bathymetry. This makes South Fork banks, Grand Canyon walls, the Pacuare gorge, and flow-scaled wave bands more reviewable while preserving the analytic channel until conditioning and channel burning are approved. Neither branch is production water: the current captures still lack credible production reflection/refraction, live solver-derived displacement, riverbed transitions, crest-scale foam, spray, mist, and seasonal guide approval.

Final approval still requires source-aligned production Landscape/Nanite geometry, credible bank and riverbed transitions, biome-specific foliage, varied rocks, physically plausible solver-informed water shading, reviewed foam/mist/lighting, guide/art/geospatial/hazard/rights review, and measured desktop/VR evidence. The current screenshots are cleaner diagnostic blockouts, not photoreal environments.

The source-conditioned corridor-scale candidates remain under `unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/`, while `unreal/Content/RaftSim/Rendering/ProductionDetailTextures/` supplies the independent close-range material layer. Editor automation imports all 21 review textures, binds them to the candidate material instances, and records the exact detail inputs in every capture manifest. Human art/guide/geospatial review begins only after production geometry and shading clear the automated blockers; importing and binding review Texture2D assets alone is not material promotion.

`physics/src/raftsim/photoreal_review_rollups.py` synchronizes each recapture's quality summaries, handoff counts, performance-review counts, production-detail provenance, source-terrain checkpoint, and water-light-response checkpoint into the source plan, procedural asset plan, art research, and gap register. The historical July 8 pixel, production-detail material, and source-terrain geometry checkpoints are explicitly superseded by the active water-light-response checkpoint.

The recipe requires guide-seat review captures, desktop/VR/debug quality budgets, source and rights manifests, and replay alignment between rendered water features and solver/runtime telemetry before the environment can count as milestone-complete.

Futaleufú Terminator now has a river-local transmitting-water V3 path without changing the committed runnable map. The live solver-conforming Single Layer Water core resolves a Futaleufú material instance, first-party flow normal, and solver-masked foam-lace texture from the existing cooked-field identity when an older map lacks serialized V3 references; future filtered regeneration stores those references explicitly. The capture-water generator also authors a translucent Default Lit ribbon with IOR 1.333 and CPU depth/bank/aeration opacity for future evidence. The current `L_Terminator` package stays byte-identical, and no solver, topology, collision, bathymetry, wet-mask, or raft-force authority moves. The retained identical-camera live frame has lower mean/highlight response and stronger cold-water color separation than V2, but still fails photoreal review because highlights, standing-wave shape, foam depth, spray/mist, shoreline material, terrain, and ecology remain synthetic or incomplete.

Colorado Hance now uses the same split optical architecture without changing
the runnable `L_Hance` package: a solver-clipped wet-cell volume core supplies
the river body, while the existing plane-preserving live mesh is a low-coverage
detail skin. The fixed capture ribbon is translucent Default Lit water with IOR
1.333 and vertex opacity derived only from already sampled depth, wet-bank edge,
and aeration. Project-owned Hance flow-normal and foam-lace textures are visual
inputs only; solver state, wet/dry ownership, bathymetry, collision, buoyancy,
and raft forces remain authoritative and unchanged. Fixed views retain the V2
candidate because riverbed and bank readability improve over the opaque
baseline, but coarse cross-river bands, weak hydraulic volume/VFX, duplicate
camera evidence, and blockout canyon/ecology keep photoreal promotion closed.

Chilko Lava Canyon now completes the river-local split-optics rollout for the
five original playable rivers. Its regenerated `L_LavaCanyon` map persists a
Chilko-only instance on the all-wet-cell transmitting core plus a restrained
Default Lit hydraulic-detail skin. Project-owned flow-normal and foam-lace
textures replace inherited optical inputs; the foam mask is multiplied by live
solver foam and speed and cannot create wet cells or hydraulic features. A
matching translucent capture parent uses physical IOR 1.333 and vertex alpha
derived only from already-sampled depth, wet-bank coverage, and aeration. The
identical side-on runtime comparison materially reduces broad and extreme
highlights and increases blue/cyan separation, but smooth wave faces,
procedural shore geometry, repeated ecology, missing spray/mist and entrained
air, and uncalibrated hydraulics keep the result technical rather than
photoreal. Solver arrays, wet/dry ownership, bathymetry, collision, buoyancy,
and raft forces remain unchanged.

Zambezi V2 now closes the corresponding live-core opacity mismatch. The shared
raft-transmitting parent preserves its depth-, foam-, and raft-interior-aware
optical graph, then multiplies opacity by the station/lateral wet-cell coverage
already carried in live-core vertex alpha. The Zambezi map binds a new river-
local instance, widens the presentation-only bank blend to 7.5 m, raises
smoothing to 0.62, reduces the detail skin to 0.025/0.13 calm/active coverage,
and restrains specular, reflection, and fallback-sky response. Exact-transform
gameplay evidence reduces high launch-water luminance and the sampled right-
bank edge while preserving solver counts and 4,224 optical-core triangles.
This does not supersede terrain, shoreline, bathymetry, hydraulics, collision,
buoyancy, or raft-force authority; coarse DEM and wet-cell geometry plus open
art, guide, geospatial, rights, seasonal-flow, VFX, character, and performance
review keep the runnable map below photoreal promotion.
