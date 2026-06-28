# AI Audio Prototype Policy

## Decision

AI-generated audio is allowed for prototypes, ideation, non-critical variations, abstract UI/debug sounds, and temp dialogue only.

AI-generated audio is not a shipping backbone for:

- White water realism.
- Raft, paddle, rock, rescue, or safety-critical cues.
- Crew voice performance without explicit performer consent and rights review.
- Music, melodies, celebrity/style imitation, or recognizable voice/style cloning.
- Any gameplay cue that must be reviewed, reproduced, licensed, and trusted under platform review.

## Allowed Prototype Uses

- UI sketches and abstract training/debug tones.
- Mood exploration.
- Scratch crew dialogue before final casting or recorded barks.
- Non-critical variations that are reviewed against recorded material.
- Internal tests of local generation latency, memory, and workflow.

## Shipping Gate

An AI-generated asset can move beyond prototype only if legal and audio review explicitly approve it and its manifest records the tool, model, version, prompt, seed, date, account/license tier, output terms, similarity review, and shipping/prototype flag.

The canonical Unreal-facing policy is `unreal/Content/RaftSim/Audio/ai_audio_prototype_policy.json`.
