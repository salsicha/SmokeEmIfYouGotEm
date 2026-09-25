# Mixed-cap shared union validation — September 25 UTC

Supporting work only: no playable geometry, collision, cooked flow or staged
executable changed. South Fork remains unfinished; later rivers remain queued.

The shared SourceRockUnion now accepts an explicit mixed-survey schema. It checks
2019 vertices against the retained source array and the 2021 vertex against its
original LAZ point record, source hash, compound CRS and classification. It rejects
withheld points, unknown datasets, invalid indices, moved vertices, relabelling,
legacy index ambiguity and nonzero vertical adjustments. This verifies captured
positions, not rock identity or underwater flanks.

The first candidate manifest accidentally inherited the parent's closure counts
and volume. It is preserved but now rejected. Preparation writes a separate v2
manifest using the candidate construction receipt, and the shared loader checks
those statistics against the reconstructed solid.

- Corrected manifest: `tmp/troublemaker-mixed-support-candidate-20260925/rock_cap_manifest-v2.json`
- Manifest SHA256: `1d37ed2dd4e9b53b55da3a76c8dc81ef9d811d389086b15a808b523492ec7558`
- Cap SHA256: `2ce993c54e489cf42a9773f5b8f34def310586f9b785c03325af0477033ae4b6`
- Volume: 2086.5066174418944 m3; manifold edges: 9642.
- 41 focused provenance, shared-union and metadata tests passed.
- Actual corrected candidate loaded successfully; actual superseded manifest
  failed specifically on stale closure statistics. `git diff --check` passed.

Follow-through: explicit `--replace-union` now reconstructs the previous union
using its own cap and terrain-revision descriptors and checks its exact identity.
Replacement preserves that bed revision and reconstructs the new geometry from
original source fields. Cells outside a smaller replacement revert to source,
not the previous cap. Two additional regressions cover dependency identity and
full preparation with tampered-core rejection before output: 43 tests pass.

Actual preparation completed at
`tmp/troublemaker-mixed-union-geometry-20260925/manifest.json`, SHA256
`6876cc58378b51627f1516153303614c027e38139b935185c2f0f70386960b6a`.
It checks all 841 cores / 5,382,400 cells against source provenance. Compared
with the previous constriction-source union (not merely the original terrain),
exactly one bed cell changes, by -1.1749487100640579 m. The registered terrain
revision identity and captured surfaces/masks remain exact. The generated
manifest predates the subsequent wording-only clarification of its notes.

Next: fresh source-stage flow initialization, matching runtime packets and
collision/render geometry, then engine validation before playable promotion.
No cook was started and no evolved water state was transferred. Normal-launch
motion, appearance and performance acceptance remain open, including the existing
p95 frame-budget failure. The constriction base is a verified prior candidate;
this report does not establish that it is the installed normal-scene bed.
