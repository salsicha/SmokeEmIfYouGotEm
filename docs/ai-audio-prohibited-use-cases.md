# AI Audio Prohibited Use Cases

AI-generated audio is allowed only inside the prototype policy unless legal and audio review explicitly approve otherwise. Some uses are prohibited by default and should not enter shipping review.

## Prohibited By Default

- Unclear commercial rights: any generation where the provider terms, account tier, output ownership, or platform rights are missing or ambiguous.
- Unlicensed voice cloning: any generated voice based on a real person without written consent, performer rights, and review approval.
- Recognizably similar music: melodies, hooks, stems, lyrics, or music beds that resemble protected works or whose training/output rights are unclear.
- Celebrity or style imitation: prompts or outputs that imitate named performers, celebrities, composers, voice actors, sound designers, brands, or protected signature styles.
- Core gameplay cues that cannot be reviewed or reproduced: any hazard, rescue, guide-command, collision, or safety-relevant sound where the manifest cannot reproduce the output and reviewers cannot audit it.
- Training-data uncertainty for production realism: any whitewater, raft, paddle, rock, or rescue sound intended to carry photorealistic simulation fidelity without a recorded/downloaded source backbone.
- Multiplayer identity confusion: synthetic voices that could be mistaken for a human player, guide, streamer, or team member without explicit labeling and permission.

## Rejection Handling

Rejected AI assets remain in quarantine storage or are deleted. They must not be mixed into production assets, used as hidden layers under recorded sounds, or exported into Unreal-ready content.

The canonical Unreal-facing rule set is `unreal/Content/RaftSim/Audio/ai_audio_prohibited_use_cases.json`.
