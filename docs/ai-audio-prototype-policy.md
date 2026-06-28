# AI Audio Development Policy

## Decision

AI-generated audio is allowed for development assets, prototypes, ideation, water/impact studies, non-critical variations, abstract UI/debug sounds, and temp dialogue.

AI-generated audio is not automatically release-ready. It must stay development-only unless the release-readiness gate explicitly clears it for shipping.

AI-generated audio needs extra review before shipping for:

- White water realism.
- Raft, paddle, rock, rescue, or safety-critical cues.
- Crew voice performance without explicit performer consent and rights review.
- Music, melodies, celebrity/style imitation, or recognizable voice/style cloning.
- Any gameplay cue that must be reviewed, reproduced, licensed, and trusted under platform review.

## Allowed Development Uses

- UI sketches and abstract training/debug tones.
- Mood exploration.
- Scratch crew dialogue before final casting or recorded barks.
- Non-critical variations that are reviewed against free/open, first-party, or generated references.
- Temporary water, raft, paddle, rock, weather, and ambience studies while evaluating whether paid assets are needed.
- Internal tests of local generation latency, memory, and workflow.

## Shipping Gate

An AI-generated asset can move beyond development-only status only if legal and audio review explicitly approve it and its manifest records the tool, model, version, prompt, seed, date, account/license tier, output terms, similarity review, and shipping/development flag.

The canonical Unreal-facing policy is `unreal/Content/RaftSim/Audio/ai_audio_prototype_policy.json`.
