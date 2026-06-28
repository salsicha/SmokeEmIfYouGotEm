# Spatial Audio Preset Plan

RaftSim needs reusable 3D audio presets that make water scale, voice intelligibility, and VR localization consistent across rivers. The source contract is `URaftSimSpatialAudioPresetSet`, and the canonical preset manifest is `unreal/Content/RaftSim/Audio/spatial_audio_presets.json`.

## Preset Families

- Point sources: small rock hits, buckle clicks, rescue gear, and UI-world sounds.
- Line and area water sources: river edge flow, eddy lines, long pour-overs, and shoreline reflections.
- Large rapids: broad standing waves, holes, and multi-emitter features with large source spread.
- Ambisonic ambience: canyon beds, forest/shore ambience, and weather fields.
- Occluded bank/rock sounds: sources that filter through boulders, banks, and canyon bends.
- Raft contact: scrape, flex, slosh, and hull thump near the guide seat.
- Underwater/near-water perspective: low-passed hydrophone-like layers during splash, swim, or camera dip states.
- Crew voice and guide commands: seat-localized dialogue with priority ducking for commands and safety cues.
- Multiplayer voice chat: player-positioned voice with privacy, mute, and intelligibility controls.

## Authoring Rules

- Presets are named by source behavior, not by one asset filename.
- VR and headphones default to binaural unless platform profiling says otherwise.
- Ambisonic beds must support head-tracked rotation in VR.
- Guide commands can become head-locked only for accessibility or safety-critical feedback.
- Voice presets must preserve intelligibility over river roar by routing to voice-priority buses.
