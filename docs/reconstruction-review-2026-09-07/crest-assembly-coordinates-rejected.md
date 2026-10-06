# Batched crest assembly coordinates rejected

September28 UTC. Supporting runtime experiment; no playable improvement or
river acceptance. South Fork remains the first unfinished reconstruction.

The v14 rapid11520 stage capture measured5.6685ms of assembly on rebuilt crest
updates, similar to5.7884ms of adaptive sample/selection work. This trial did
not repeat rejected edge storage, root incidence, direct triangle emission or
attribute-midpoint scheduling. It retained original serial edge discovery,
midpoint numbering, parent orientation and triangle emission, but deferred
current-level coordinate evaluation until all new parents were registered.
One array growth then preceded parallel evaluation of the original expression,
with a serial fallback below2,048 new vertices. Coordinates were never reused
across profiles. Selection, accuracy, levels, fields and physics were unchanged.

The candidate was default-off. Editor Development build passed in320.74s.
Three native tests passed, zero failed/warning/not-run tests in0.8094s:
AssemblyCoordinates, ConformingSurfaceRefinement and RefinementTopologyCache.
The new fixture compared183,112 expanded coordinates across changing profiles,
moving/cropped roots, winding changes, repeated builds, invalidation,0..3 levels,
parallel/serial selection, degenerate edges and invalid roots.

One bounded500-frame actual FullReach run at station11520,1280x720 D3D12,
compared64 alternating-order pairs after two warm builds. All ordered parents,
triangles, owners, expanded coordinates and cache decisions were exact and
matched production topology. Frames122..185 compared1,920,941 expanded vertices.
Native and game processes exited0 with no logged runtime Error/Fatal records.
The launch guard found no other engine/build/cook before either process.

| Candidate first | Pairs | Reference build ms | Candidate build ms | Reference assembly ms | Candidate assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| No |32|10.121794|10.472494|4.270610|4.417591|
| Yes |32|10.714878|10.471147|4.547944|4.589966|

Assembly is slower in both orders; whole-build improvement is inconsistent.
The candidate is rejected without an audit-free FPS or package promotion trial.
Its switch, implementation, audit and candidate-only native fixture were removed
with scoped patches. Both pre-existing runtime files have empty content diffs;
the unrelated pre-existing WaterSurfaceTest line-ending change is preserved.
Original evidence remains in ignored tmp; do not rerun this unchanged candidate.

Evidence SHA256:

- `tmp/assembly-coordinates-pairs-v1.json`:
  `0adfe012abe72bab997a95844631710f2f3e944b31ff761892487cebeaab4516`.
- `tmp/assembly-coordinates-pairs-v1.log`:
  `be3366ec88566e939d7219e462d86df21609cf6673c55074dc323973c15555ba`.
- `tmp/assembly-coordinates-native-v1/index.json`:
  `d669e83ef4bcc1f7207c75907159ada845bbe97c9708394a6f08bd252808d225`.

Build log: `tmp/assembly-coordinates-build-v1.log`; bounded recipe:
`tmp/run-assembly-coordinates-v1.ps1` (requires the now-removed experiment).
Restored-source build session23097 completed exit0 in268.45s; log
`tmp/assembly-coordinates-restored-build-v1.log`. The restored native run also
completed exit0: ConformingSurfaceRefinement and RefinementTopologyCache both
pass, zero failures/warnings/not-run tests,0.2071s. Receipt:
`tmp/assembly-coordinates-restored-native-v1/index.json`. All experiment and
restoration processes are terminal; no engine/build/cook is left running.

The v14 packaged game and its failed rapid gates remain unchanged. No new
normal-menu, rendered-motion, collision, shoreline, settled-field or realism
pass is claimed. Do not convert exact diagnostic topology into visual acceptance.
