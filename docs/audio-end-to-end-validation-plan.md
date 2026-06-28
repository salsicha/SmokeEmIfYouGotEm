# Audio End-To-End Validation Plan

The final Milestone 13 audio gate combines spatial playback, voice commands, and multiplayer voice chat. It should be run after the Unreal-native MetaSounds prototype and networked voice slice are playable.

## Validation Conditions

- Stereo speakers: verify mix translation, command feedback, and hazard readability without binaural cues.
- Headphones: verify localization, fatigue, near-field raft detail, and crew position readability.
- VR spatial audio: verify head-tracked HRTF stability, ambisonic rotation, comfort, and front/back discrimination.
- Noisy voice-command conditions: verify guide commands with river roar, wind, rain, paddle impacts, crew chatter, and network voice present.
- Multiplayer voice chat: verify seat-positioned player voice, push-to-talk, mute, ducking, privacy, packet loss behavior, and guide-command priority.

## Required Metrics

- Voice command latency, false accept rate, false reject rate, and confidence by noise profile.
- Crew/player speech intelligibility over rapid classes II through V.
- Hazard localization accuracy and warning lead time.
- Audio render cost, spatialization cost, active voices, and virtualization behavior.
- VR comfort, fatigue, and head-tracked localization stability.
- Multiplayer voice continuity under packet loss, jitter, and seat changes.

The canonical Unreal-facing validation matrix is `unreal/Content/RaftSim/Audio/audio_end_to_end_validation.json`.
