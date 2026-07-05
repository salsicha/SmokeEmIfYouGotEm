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
