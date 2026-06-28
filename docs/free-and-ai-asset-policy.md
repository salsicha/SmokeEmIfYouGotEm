# Free And AI Asset Policy

## Decision

For the current development phase, SmokeEmIfYouGotEm should use only free/open, first-party generated, procedural, and AI-generated assets for art and sound.

Do not buy paid art packs, paid sound libraries, marketplace packs, subscription libraries, or trial-to-buy asset services yet. Save that decision for the release-readiness gate, after the team has tested whether free/open and AI-generated assets are good enough for the target visual and audio quality.

## Applies To

- Concept art, reference boards, placeholder textures, decals, UI art, icons, foliage/rock/terrain studies, material studies, splash/foam/mist prototypes, and other visual content.
- Water beds, rapids, raft/rock/paddle contact, weather, ambience, UI cues, temporary crew dialogue, guide-command feedback, debug sounds, and spatial audio prototypes.
- Generated or procedural assets produced in-house with tools whose license terms allow the intended development use.
- Free/open assets with clear license terms, including CC0, public-domain, permissive open-source, and CC-BY assets where attribution can be tracked.

## Active Development Source Order

1. First-party procedural/generated assets created inside the project.
2. AI-generated assets with prompt/model/tool metadata and clear development-use terms.
3. Free/open assets with clear license snapshots and attribution tracking.
4. First-party field recordings or photos only when they do not require buying third-party asset licenses.
5. Paid/professional libraries only after the release-readiness asset gate says free/open and AI-generated assets are not good enough.

## Release-Readiness Gate

Before buying any art or sound asset library, run a release-readiness review:

- Quality: do free/open and AI-generated assets meet the photorealistic river, raft, crew, UI, and 3D audio targets?
- Consistency: can the assets form a coherent style and sound without looking or sounding stitched together?
- Rights: are commercial use, platform rights, attribution, derivative rights, and redistribution terms clear?
- Reproducibility: can AI assets be regenerated or traced through prompts, seeds, model versions, dates, and account terms?
- Performance: do generated assets import and run inside Unreal budgets for desktop and VR?
- Risk: would paid libraries meaningfully reduce release risk, production time, quality gaps, or legal uncertainty?

Only buy assets after that review, and only for gaps where free/open and AI-generated assets are not good enough.

## Research Retention

Keep all existing research notes about high-quality asset sources. The vendor comparisons, license URLs, and purchase notes are now reference material for the release gate, not active buying instructions.

Canonical Unreal-facing policy: `unreal/Content/RaftSim/development_asset_source_policy.json`.
