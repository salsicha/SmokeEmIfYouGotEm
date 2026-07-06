# Release Readiness Plan

Milestone 25 turns the alpha production plan into a release-candidate gate. The canonical data contract is `unreal/Content/RaftSim/Production/release_readiness_plan.json`; the Unreal automation gate is `unreal/Content/RaftSim/Automation/release_readiness_gate.json`.

## Platform Targets

- `desktop_high`: primary flat-screen development and beta tier.
- `vr_comfort`: OpenXR tier with stricter frame pacing, comfort, haptics, and spatial-audio review.
- `handheld_or_low_power_review`: future low-power scaling tier that stays review-only until performance captures pass.

## Required Lanes

- Profile custom water, raft/contact authority, game thread, render thread, GPU water/VFX, World Partition streaming, audio, local AI voice, memory, save/replay, and photoreal environment/foliage systems.
- Keep scalability modes explicit for desktop, VR, low-power review, and replay/debug so water authority, visual physics, VFX, lighting, foliage, audio, voice, crew conversation, and manual fallbacks can be tuned without changing scoring-critical behavior.
- Lock release workflows for assets, audio, AI generation, source manifests, attribution, licenses, credits, platform rights, localization, store compliance, release branch, and patch operations.
- Harden QA automation around physics regressions, river import/export, feature-forcing manifests, raft/contact fixtures, rescue outcomes, replay determinism, VR comfort, input devices, accessibility, crash capture, and performance capture.
- Finish player-facing polish for onboarding, training, scoring, after-action feedback, menus, settings, save data, accessibility, subtitles, microphone/privacy controls, haptics, and final audio mix.

## Release Decisions

- Wwise/FMOD are deferred unless measured native audio, MetaSounds, localization, memory, voice-budget, or authoring gates fail.
- Paid asset libraries are deferred until a proven quality gap cannot be closed by first-party, free/open, procedural, or approved generated assets.
- Professional field recordings are a shipping candidate only after source rights and final mix review.
- Generated river shipping features are deferred to internal tools until they pass the same validation and guide-review standards as real-world rivers.
- Multiplayer is deferred until the single-player release candidate is stable.
- Extra local AI features are deferred beyond deterministic voice commands and approved bark layers until latency, privacy, accuracy, memory, safety, and replay gates pass.

## Shipping Blockers

Release remains blocked until the gate has evidence for beta playtests, guide feedback, target-platform performance captures, legal/provenance review, content validation, photoreal environment/foliage quality review, release branch lock, and patch workflow.
