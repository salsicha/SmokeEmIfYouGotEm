# Selective exact crest normals

Ordinary-start baseline on the previous build failed at p9533.9212ms.
Normals measured0.84ms mean/1.61ms p95 within3.46ms mean/7.42ms p95 crest update.
This change skips face normals with no consumer, not triangles or crest detail.
The topology cache now records touched vertices and every face incident on at
least one touched vertex. Adjacent coarse faces remain included. Each touched
vertex sums its original complete incidence list in its original order, using
current positions; normal/tangent math remains unchanged. Topology/source-count
changes rebuild membership, and Reset clears it. The full-face parallel control
remains callable with Selective=false.

Editor build succeeds in252.53s, retaining two C4305 double-to-float warnings
in unchanged RaftSimD6ChaosMeasuredRunner.cpp. Three native suites pass with
no test warnings/failures: CrestNormals, ReferencedWaterComponent and
ShorelineFineCrest. The normals regression now compares both full-face parallel
and selective outputs against the scalar reference across24 evolving frames,
including sparse fine membership, no/all fine vertices, degeneracies, repeated
indices, winding changes, dry/rewet topology and reset. Report:
`tmp/selective-crest-normals-native-v1-20260924/index.json`.

Candidate Game build succeeds in189.94s. Actual ordinary-start900-frame run
`south-fork-selective-normals-normal-cost-v1-20260924` exits0/no timeout, with
exact cook suspend/resume success. Confirmed nonlegacy timing, offset1, audited
rows60–840: mean25.403429ms, p9534.0391ms **FAIL**, maximum45.9625ms. Normals
mean0.868012ms/p951.8195ms does not improve the prior run. This is not a causal
regression proof, but provides no basis for default promotion. CSV SHA256:
`5c9b2e2a79d18b2891a6853a7bcb471570445486c982bfd82ff046eee7ac1e58`;
audit `tmp/selective-normals-normal-frame-v1-20260924.json`.

The actual-input motion audit records151 exact normal/all-attribute comparisons
against the scalar reference and0 mismatches (engine exit0, no timeout, cook
resumed). Recording `unreal/Saved/VideoCaptures/RaftSim_20260923-213719.mp4`,
SHA256 `c7b479c260bc0462125867226ad07c6d2f41e67639adde7cfa1a8280c19283ed`.
Audit overhead means this recording is not performance evidence.

Selective scheduling is now explicit `-RaftSimSelectiveCrestNormals` only in
source. Default full-face calculation avoids building the selective lists.
Native tests explicitly exercise both paths with separate caches. The v2
Editor/Game rebuilds succeed in256.23s/173.50s. The v2 native report again has
3success/0failure/0warning. Both binaries now match the restored default.

Fresh ordinary-launch900-frame verification
`south-fork-restored-normals-normal-cost-v2-20260924` exits0 without timeout and
resumes the cook. No selective flag or station override. Confirmed nonlegacy
timing, offset1, rows60–840: mean24.804112ms, p9533.7393ms **FAIL**, max42.2633ms.
CSV SHA256 `efe3a2cee055ae83e60954d23b8e49cdd7d8f346d07417701158fd8c9333035d`;
audit `tmp/restored-normals-normal-frame-v2-20260924.json`. This restores the
established path, not performance acceptance or a causal comparison.

The retained candidate recording fully decodes466frames through15.5s with26
adjacent duplicates. Original3s/11s images were inspected: seated crew/water
remain visible and station advances0.12→0.14km. These sparse samples do not
prove flicker-free lighting or accepted realism. Decoder artifacts:
`tmp/selective-normals-motion-decoded-v1-20260924/`.

No visual improvement, frame-time benefit or water-realism acceptance. Captured
geometry, installed4950s fields and nonlinear OFF remain unchanged. Do not
repeat this unchanged selective-normal experiment as the next optimization.
Guide reentry remains distinct from passenger rescue and unqualified in actual
play: UpdateSwimmingAndRescueAim follows the named guide swimmer, detaches the
pawn, then reattaches at the stern when that swimmer leaves the rescue state.
