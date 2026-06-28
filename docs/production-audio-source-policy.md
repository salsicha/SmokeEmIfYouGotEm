# Development Audio Source Policy

## Decision

For the current development phase, use free/open, first-party generated, procedural, and AI-generated audio only.

Do not buy paid sound libraries, marketplace packs, subscription libraries, or trial-to-buy audio services yet. Save that decision for release-readiness, after the team decides whether free/open and AI-generated assets are good enough.

This applies to:

- White water beds, rapids, hydraulics, eddy lines, boils, spray, foam, and underwater/near-water perspectives.
- Raft tube impacts, floor flex, rock scrapes, paddle catches, blade slips, straps, ropes, pumps, helmets, PFDs, wet gear, and footsteps.
- Weather, canyon reflections, forest/canyon ambience, rescue cues, UI, training cues, crew barks, and multiplayer voice support beds.

## Priority Order

1. First-party procedural/generated audio created inside the project.
2. AI-generated audio with complete manifest metadata and review status.
3. Free/open audio with clear license snapshots and attribution tracking.
4. First-party recordings when no third-party asset license purchase is required.
5. Paid/professional libraries only after the release-readiness gate proves they are needed.

## Paid Library Gate

Existing vendor research stays in the repo as release-gate reference material. Buy assets only if free/open and AI-generated assets cannot meet quality, consistency, legal, platform, or production-risk targets.

## Shipping Gate

No audio asset can ship unless it has:

- A manifest record.
- Clear commercial rights.
- Source provenance.
- Platform rights.
- Attribution status.
- Approval status.
- Storage/LFS classification.
- Spatialization and playback intent.

The canonical Unreal-facing policy is `unreal/Content/RaftSim/Audio/production_audio_backbone_policy.json`.
