# Unreal Engine Version Lock

## Decision

Target Unreal Engine **5.8** for the first SmokeEmIfYouGotEm visualization and VR slice.

This lock is based on the June 2026 UE 5.8 public release. UE 5.8 is the latest major UE5 release available in the current planning pass and is described by Epic as the last planned major UE5 release while UE6 work ramps up.

## Feature Set To Evaluate

Use the stable UE5 production stack first:

- Nanite for high-detail rocks, canyon walls, raft parts, debris, and scanned props.
- Lumen for dynamic global illumination, with Lumen Lite profiled for lower-end desktop and portable targets.
- Virtual Shadow Maps for high-resolution dynamic shadowing.
- World Partition and One File Per Actor for long river corridors.
- PCG for bank vegetation, rock fields, gravel bars, driftwood, foam cues, and hazard dressing.
- Niagara for spray, mist, paddle splash, foam bursts, rain, and rescue effects.
- Substrate/material layering for wet rubber, wet rock, foam, aerated water, helmets, PFDs, and river mud.
- OpenXR for VR runtime support.

Evaluate but do not depend on experimental features for the first vertical slice:

- Mesh Terrain for complex river corridors, overhangs, undercut banks, boulders, and caves.
- Procedural Vegetation Editor for Nanite-ready riverbank vegetation authoring.
- Fast Geometry Streaming for massive non-gameplay scenery.
- Experimental MCP tooling only for editor productivity experiments, not runtime gameplay dependency.

## Project Policy

- Lock the repo scaffolding to UE 5.8 source/config conventions.
- Keep generated/editor binary assets out of source until Unreal Editor creates them intentionally.
- Prefer text config, C++ modules, JSON manifests, and schema files while the editor is unavailable locally.
- Re-run this version review before the first playable build ships, and again before any console/handheld target is committed.

## Sources Checked

- Epic Games, "Unreal Engine 5.8 is now available"
- Epic Developer Community, "Mesh Terrain"
- Epic Developer Community, "Procedural Vegetation Editor (PVE)"
- Epic Developer Community, "Lumen Performance Guide"
