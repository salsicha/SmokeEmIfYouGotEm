# SmokeEmIfYouGotEm Unreal Project

This directory contains the UE 5.8 source-controlled project shell for the full rafting simulator.

The project remains source-first: `.uproject`, C++ targets, module build rules, config, manifests, and source skeletons stay in git while editor-created binary assets are generated intentionally from reviewed workflows.

Milestone 20 production foundation state is recorded in `Content/RaftSim/Production/production_foundation.json`. That manifest binds the UE 5.8 project lock, enabled project plugins, `RaftSim` module boundaries, and accepted Milestone 20 water report-set lock before live-water integration code is treated as production work.

## Open In Unreal

1. Install Unreal Engine 5.8.
2. Open `SmokeEmIfYouGotEm.uproject`.
3. Let Unreal generate IDE project files.
4. Build the editor target.
5. Open the `RaftSim Tools` menu to inspect replay/debug, rapid/river, feature tuning, geospatial validation, and vertical-slice launcher surfaces as they come online.
6. Create binary map, Blueprint, material, MetaSound, and DataAsset content from the source manifests in this repo.

## Source Policy

- Keep generated build products out of git.
- Keep editor-created binary assets intentional and reviewed.
- Prefer JSON manifests and C++ declarations for early pipeline work until workflows are proven.
- Store large binary assets through Git LFS when they become necessary.
