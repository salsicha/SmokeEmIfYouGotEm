# Milestone 25 Release Readiness Gate

Milestone 25 is closed at the release-readiness contract layer. The canonical gate lives at `unreal/Content/RaftSim/Automation/release_readiness_gate.json`, and the production plan lives at `unreal/Content/RaftSim/Production/release_readiness_plan.json`.

The gate covers seven lanes:

- profiling and optimization across custom water, raft/contact authority, game/render/GPU, streaming, audio, local AI, memory, save/replay, and photoreal foliage systems;
- scalability modes for desktop, VR, handheld or low-power review, and replay/debug;
- release-quality source, audio, AI-generation, attribution, rights, localization, and store-compliance workflows;
- QA automation for physics, river import/export, feature forcing, raft/contact, rescue, replay, VR comfort, input, accessibility, and crash/performance capture;
- player-facing polish for onboarding, training, scoring, after-action feedback, settings, save data, accessibility, subtitles, microphone/privacy, haptics, and final mix;
- release/defer decisions for Wwise/FMOD, paid libraries, professional recordings, generated rivers, multiplayer, and extra local AI;
- final release signoff requirements.

This is not a claim that the game is ready to ship today. Shipping remains blocked until beta playtests, guide feedback, target-platform performance captures, legal/provenance review, content validation, photoreal environment/foliage review, release branch lock, and patch workflow evidence are attached to the gate.
