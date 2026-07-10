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

- Mesh Terrain, Procedural Vegetation Editor, Fast Geometry Streaming, and Nanite foliage remain feature-evaluation items until they pass editor, performance, memory, and VR comfort checks.
- Unreal Water System is enabled for visual water and authoring, but the custom shallow-water solver remains authoritative physics.

The canonical feature manifest is `unreal/Content/RaftSim/Rendering/photoreal_stack.manifest.json`.

The first vertical-slice environment recipe is `unreal/Content/RaftSim/Rendering/vertical_slice_environment_corridor.json`. It binds the South Fork corridor package, photoreal stack, and telemetry presentation cues into map-authoring layers for landscape/bed, banks, rocks, foliage, debris/access context, lighting/weather, audio occlusion/reverb geometry, and water-readability support.

The three-river environment source and capture plan is `unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json`. It records the source stack for South Fork American, Colorado River, and Pacuare: maps, terrain, hydrography, flow evidence, aerial/satellite imagery, link-only social/reference media policy, procedural generation layers, target Unreal map packages, and required guide-seat downstream captures.

The concrete source attachment checklist for tools is `physics/data/real_world/production_geospatial_attachment_ledger.json`. It records existence-checked terrain, hydrography, aerial imagery, mask, flow, access/protected-area, and guide/media annotation artifacts for all three runnable rivers, while keeping every class preview-only until CRS, terms, guide review, rights, and lifelike capture gates pass.

The approved first-party procedural-equivalent environment asset plan is `unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json`. It covers canyon walls, riverbeds, wet boulders, shore vegetation, tropical canopy, water depth/current cues, foam/spray/mist, raft foreground, and river-specific lighting as the traceable replacement path when licensed/photogrammetry assets are not yet cleared. The editor preview and capture commands now require and record this plan, but the current renders remain preview-only until these recipes are implemented as production-quality Unreal assets/materials and verified by capture/performance evidence.

The generated preview maps live under `/Game/RaftSim/Maps/EnvironmentPreviews/`, and `RaftSim.CreatePhotorealEnvironmentPreviewMaps` plus `RaftSim.CapturePhotorealEnvironmentPreviews` rebuild the three base maps, ten flow-variant maps, and 26 guide-seat/river-eye screenshots. The July 9 renderer imports the first-party `ProductionDetailTextures` albedo, tangent normal, and packed AO/roughness/height sets for South Fork, Grand Canyon, and Pacuare. `M_RaftSim_AtlasSampleReview` now uses separate RG `AtlasTileOrigin`/`AtlasTileScale` and `TerrainDetailUvScale`/`TerrainDetailUvOffset` parameters, fixing the UE 5.8 Metal component-mask compile failure that had silently fallen back to Unreal's default material.

The first native source-terrain candidates now live under `/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/`. `RaftSim.CreateLandscapeImportCandidateMaps` imports the three review-gated 1009x1009 16-bit PNG heightfields through Unreal's `LandscapeEditor` format API as 16x16-component `ALandscape` maps, builds four Nanite representations per river, audits all 256 source component and Nanite material bindings, and captures guide-seat plus river-eye evidence under `docs/environment-captures/photoreal_river_previews/landscape_candidates/`. The offscreen renderer uses a first render to request Landscape shader permutations, waits for compilation, recreates Landscape component state, and then records the evidence frame; this prevents UE 5.8's default grid from appearing in headless captures while material shaders are incomplete. The candidates remain isolated and review-gated because their analytic preview channel burn is not solver or accepted geospatial geometry and their constant-color terrain material is only a render/import diagnostic.

The renderer disables legacy terrain and water overlay proxy geometry plus synthetic film-grain dither. The source-terrain pass samples each review-gated 2017px DEM derivative bilinearly, feathers stitched-tile center seams, separates meter-scale macro relief from bounded multi-scale erosion residuals, and uses river-specific normal flattening. Water now uses a dedicated DefaultLit parent with authoritative ribbon-mesh normals, tile-safe first-party normal detail, river-specific light response, and less destructive near-camera flattening. This makes South Fork banks, Grand Canyon walls, the Pacuare gorge, and flow-scaled wave bands more readable while preserving the analytic channel until conditioning and channel burning are approved. The current base review still reports edge and entropy failures on all six captures, broad low-gradient failures on five, and one Colorado luminance failure. All 20 flow captures fail edge density and entropy, 17 fail broad low-gradient coverage, and 3 Colorado flow captures fail luminance.

Final approval still requires source-aligned production Landscape/Nanite geometry, credible bank and riverbed transitions, biome-specific foliage, varied rocks, physically plausible solver-informed water shading, reviewed foam/mist/lighting, guide/art/geospatial/hazard/rights review, and measured desktop/VR evidence. The current screenshots are cleaner diagnostic blockouts, not photoreal environments.

The source-conditioned corridor-scale candidates remain under `unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/`, while `unreal/Content/RaftSim/Rendering/ProductionDetailTextures/` supplies the independent close-range material layer. Editor automation imports all 21 review textures, binds them to the candidate material instances, and records the exact detail inputs in every capture manifest. Human art/guide/geospatial review begins only after production geometry and shading clear the automated blockers; importing and binding review Texture2D assets alone is not material promotion.

`physics/src/raftsim/photoreal_review_rollups.py` synchronizes each recapture's quality summaries, handoff counts, performance-review counts, production-detail provenance, source-terrain checkpoint, and water-light-response checkpoint into the source plan, procedural asset plan, art research, and gap register. The historical July 8 pixel, production-detail material, and source-terrain geometry checkpoints are explicitly superseded by the active water-light-response checkpoint.

The recipe requires guide-seat review captures, desktop/VR/debug quality budgets, source and rights manifests, and replay alignment between rendered water features and solver/runtime telemetry before the environment can count as milestone-complete.
