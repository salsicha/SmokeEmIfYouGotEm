# Audio Storage And LFS Policy

Large audio binaries, Unreal audio assets, videos, and packaged exports are tracked through Git LFS when they are allowed in the repository. Manifests, schemas, cue sheets, source comparison notes, and other text metadata stay in normal Git.

## Storage Classes

- `raw_recordings`: field WAV/BWF/FLAC/AMB/Caf captures; store in LFS after ingest selection.
- `purchased_libraries`: vendor source packs; store outside Git by default unless the license explicitly permits team redistribution through the repository.
- `edited_masters`: cleaned loops, one-shots, ambisonic beds, and stem renders; store in LFS.
- `generated_prototypes`: AI or procedural prototypes; store in LFS only when they are needed for reproducible review.
- `unreal_ready_exports`: WAV/OGG/OPUS/WEM/BANK/BNK/UAsset/UMAP runtime assets; store in LFS.
- `delivery_archives`: ZIP/7Z/RAR asset batches; store in LFS only for short-lived handoff or legally approved internal mirrors.

## Repository Rules

- Every audio binary must have a manifest record before it is treated as production content.
- Purchased libraries require a license or purchase record and redistribution approval before source packs are committed.
- Raw field recordings should be archived externally first, then curated takes can be committed through LFS.
- Unreal binary assets are LFS-tracked because diffs are not useful and file sizes can grow quickly.
- Generated prototype audio is never proof of shipping rights by itself; the AI audio manifest and review state decide whether it can advance.

The canonical Unreal-facing policy is `unreal/Content/RaftSim/Audio/audio_storage_lfs_policy.json`.
