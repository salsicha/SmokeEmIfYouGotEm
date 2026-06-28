# AI Audio Manifest Schema

AI-generated audio must carry extra provenance before it can enter the asset review queue. The default assumption is prototype-only, even when the generated output sounds useful.

The schema records:

- Tool, model, version, and provider.
- Prompt, negative prompt, seed, generation date, and generation settings.
- Account or license tier, output terms, and source terms URL.
- Intended use, prototype/shipping flag, and allowed use.
- Similarity check, reviewer notes, audio review status, and legal review status.
- Source asset references and whether any prompt used protected voices, music, lyrics, brands, names, or style references.
- Reproduction package path so approved prototypes can be regenerated and audited.

Shipping approval requires legal review, audio director review, similarity review, explicit platform rights, and an `approved_for_shipping` flag. The canonical schema is `unreal/Content/RaftSim/Audio/ai_audio_manifest.schema.json`.
