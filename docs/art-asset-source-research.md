# Art Asset Source Research

## Current Decision

Use free/open, first-party generated, procedural, and AI-generated art assets during development. Do not buy paid art packs, marketplace packs, subscription libraries, or trial-to-buy services yet.

Use this research at the release-readiness gate if free/open and AI-generated art is not good enough.

## Free / Open Sources To Use First

| Source | Best Use | Notes |
| --- | --- | --- |
| Poly Haven | HDRIs, textures, and 3D models | Strong fit for free development look-dev; assets are presented as CC0 on the source license page. |
| Kenney | Simple game-ready 2D/3D assets, UI pieces, icons, prototypes | Good for placeholder UI, simple props, and control/debug art; support page says game assets are CC0. |
| OpenGameArt | Mixed 2D, 3D, textures, music, and sound | Useful for prototypes, but licenses vary per asset; attribution and share-alike requirements must be tracked. |
| Free Fab assets | Unreal-ready packs, meshes, materials, audio, scans | Review each asset's price, license tier, source provenance, and redistribution restrictions before ingest. |
| First-party procedural generation | Rocks, banks, riverbed details, foam masks, splashes, UI/debug art | Preferred when a source can be reproduced from seed/config and kept stylistically consistent. |
| AI-generated art | Concept art, texture studies, decals, UI drafts, foam/spray/mist references | Allowed for development only with prompt/model/tool/date/terms metadata and review status. |

## Paid / Professional Sources To Preserve For Release Gate

- Fab paid marketplace packs: potentially useful for production-ready Unreal materials, scans, rocks, foliage, props, and environment kits if free/AI coverage falls short.
- ArtStation Marketplace and similar stores: useful for concept/reference and environment packs, but only after per-product rights review.
- Specialist photogrammetry/scan libraries: useful if river rocks, canyon walls, bark, ground cover, or wet material realism cannot be met with free/open or generated assets.
- Outsourced custom art/photogrammetry: useful only if release quality needs a controlled, consistent art direction beyond stock/free/generative material.

## Review Rules

- Prefer CC0/public-domain assets where possible.
- Use CC-BY only when attribution can be tracked in manifests and credits.
- Avoid NC, ND, unclear, scraped, fan-art, brand-heavy, celebrity, or style-imitation assets.
- Record source URL, license URL/date, creator, modifications, Unreal import path, and approval status.
- For AI art, record tool, model, version, prompt, negative prompt, seed, date, account/license tier, output terms, and similarity/provenance review.
- Keep paid-source links and notes as research; do not purchase until release-readiness.

## Sources Checked

- Poly Haven License: https://polyhaven.com/license
- Kenney Support / License FAQ: https://kenney.nl/support
- OpenGameArt FAQ: https://opengameart.org/content/faq
- Fab Standard License/EULA: https://www.fab.com/eula
