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

The first generated preview maps are now available under `/Game/RaftSim/Maps/EnvironmentPreviews/`, and rendered guide-seat captures are written to `docs/environment-captures/photoreal_river_previews/` by the `RaftSim.CreatePhotorealEnvironmentPreviewMaps` and `RaftSim.CapturePhotorealEnvironmentPreviews` editor automation. South Fork, Colorado, and Pacuare now have source-draped preview overlays, source-drape terrain vertex-color blending, generated valley terrain, curved river ribbons, foam/hydraulic cue strips, first-party translucent water glints/foam flecks/haze/spray-mist layers, boulder bars, clustered foliage proxies, and per-river light/fog variants; the automation also scopes UE 5.8 startup-world GC leak checks to nonfatal during generated-map/capture batches so evidence capture can complete while diagnostics remain logged. The latest July 8 pass disables the former visible tapered water-chroma overlay and separate water fleck cards, moving bounded chroma/noise/relief and fleck cues into integrated water meshes. The stricter current review still blocks all six guide-seat/river-eye captures on `low_color_texture_entropy`, with South Fork river-eye also blocked on `low_edge_density`, so the screenshots remain preview-only and not lifelike. Final approval still requires replacing smooth procedural terrain, placeholder rocks/foliage, review-only material instances, and missing production foam/mist/lighting with full reviewed DEM/aerial imports plus rights-cleared or first-party production terrain, water, rock, foliage, foam/mist, lighting, and performance evidence.

The recipe requires guide-seat review captures, desktop/VR/debug quality budgets, source and rights manifests, and replay alignment between rendered water features and solver/runtime telemetry before the environment can count as milestone-complete.
