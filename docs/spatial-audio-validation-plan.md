# Spatial Audio Validation Plan

Spatial audio must be validated as a platform behavior, not just as individual sound assets. Every major preset family should be checked on stereo speakers, headphones, VR binaural/HRTF, and 5.1/7.1 surround where the target platform supports it.

## Playback Targets

- Stereo speakers: verify downmix balance, front-stage readability, voice intelligibility, and river-bed loudness.
- Headphones: verify binaural localization, fatigue, near-field contact sounds, and crew seat positioning.
- VR binaural/HRTF: verify head-tracked stability, front/back discrimination, ambisonic rotation, and comfort during rapid motion.
- 5.1 surround: verify speaker routing, LFE discipline, center-channel voice clarity, and wraparound ambience.
- 7.1 surround: verify side/rear continuity, large rapid spread, and no phantom gaps during raft turns.

## Required Scenario Cases

- Nearby rock hazard.
- Downstream large rapid.
- Hydraulic hole.
- Crew seat positions.
- Guide command priority.
- Multiplayer voice seats.
- Canyon reflection pass.
- Raft scrape/contact.
- Near-water and underwater perspective.

The canonical Unreal-facing validation matrix is `unreal/Content/RaftSim/Audio/spatial_audio_platform_validation.json`.
