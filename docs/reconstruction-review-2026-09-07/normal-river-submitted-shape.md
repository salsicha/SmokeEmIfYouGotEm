# Submitted water shape and shoreline fan — September 14

Shoreline fan correction integrated into ordinary South Fork; full water visual
and performance acceptance remain OPEN. The preceding irregular-optics turn was progress: actual visual
evidence rejected that candidate and the saved parent was restored. This turn
traces physical shape rather than making another occupancy-only adjustment.
The earlier native-stage fix already removed optical smoothing from base
geometry; it is retained, not repeated or credited again.

## New observation, not a geometry change

`-RaftSimCarrierShapeAudit=PATH` exports the actual active CPU vertices and
submitted triangles after temporal updates, clipping and fine-crest correction.
It also samples the ALREADY presented fine-detail payload at those vertices.
It does not advance the solver, force a commit, wait for the GPU or edit state.
The metadata is written last as a completion marker. Existing/partial outputs
are never overwritten. Reserve vertices are explicitly excluded.

Source comparison is separately recorded: the double sum of cached source bed
and depth used by clipping, and its connected/available wet mask. It is not a
new native sample and need not have the displayed surface's temporal age.
The reconstructed base residual contains temporal/clipped source and other
relief; it is NOT equated with raw mean stage. Optical normals, GPU exposure
timing, occlusion and photographic acceptance are not measured.

First build12772 failed because the local refresh sample array was unavailable
at submission. Corrected to the persisted bed/depth inputs; build74869 PASS
52.48s. Analyzer8 tests PASS0.223s: plane gradients, winding, negative signed
contributions, coordinate reflection, dry/outside rejection, reserve indices,
source lattice identity, malformed CSV/BOM, nonfinite data and degenerate area.
Native19701 passes6 tests in approximately1.76s: shoreline,
fine crest, support, completed detail contact, catalog and save migration.

## Actual baseline

Game77087 TERMINAL exit0, ordinary South Fork with only the read-only audit and
camera/recording flags. Capture `tmp/south-fork-submitted-shape-v1-20260914.json`
plus `.vertices.csv`, `.triangles.csv`, `.source.csv`; independent analysis in
`tmp/south-fork-submitted-shape-analysis-v1-20260914.json` retains SHA256s.
World13.110338888s, presented-detail sequence103,68,112 active vertices,
77,824 buffer vertices,50,496 triangles and225x225 source lattice.

Within30m of the actual raft:20,990 triangles over2307.473053m2 projected area,
no zero-area triangle. Sum of independently calculated base/crest/detail slope
components matches total slope to1.03444e-11. In the30–60degree group (864
triangles,70.368404m2), the area-weighted signed along-slope contributions are
base0.828449872, crest-0.006592479, detail-0.000626824. Thus added crests are
not the dominant cause of these steep faces. This is a local geometric finding,
not an assertion that all base slopes are incorrect or visible from the camera.
Maximum local crest contribution is0.510301m and fine detail0.149184m; neither
is disabled. Source comparison is available on18,010 fully wet triangles only.

Twelve clipped triangles exceed60degrees over just0.150814m2. The steepest are
about73degrees near field[-5411,3599–3600]m. Their crest contribution is zero.
Actual source/shore vertices reveal a triangulation artifact: the source heights
8.111732576,8.218760295,8.940551758m are connected via a pentagon whose two shore
vertices inherit their wet endpoints. The arbitrary fan anchor creates a narrow
triangle with0.828819182m height difference over0.249545262m in X: slope3.321318.
This finding does NOT explain every broad smooth face or all froth problems.

The actual recording `unreal/Saved/VideoCaptures/RaftSim_20260914-070452.mp4`
fully decodes203 encoded frames from44 source frames over6.772s. Extracted
`detail-motion/south-fork-submitted-shape-v1-20260914_01s.png` inspected: the
restored material still has broad blurred foam and sheetlike green faces.
Visual FAIL; encoding30FPS is not game30FPS. No fresh FPS claim.

## Candidate under qualification

`-RaftSimOppositeDryBankFan` changes only the fan anchor for the three-wet-corner
pentagon: use the wet corner opposite the sole dry corner. Vertex values, wet
polygon and its boundary segments stay unchanged; interior interpolation and
therefore surface normals/contact CAN change. This is not a proof of conserved
presentation volume, a new hydraulic source or a measured bathymetry change.
The support path uses the same submitted triangles. Other wet masks, including
disconnected diagonal channels and fully wet cells, retain original topology.
The mode is part of topology-cache identity. It was opt-in during qualification.
Native controls include the captured cell, every wet mask,
rotations/reflections, storage modes, boundary/vertex identity, sample contact
and cache-mode transitions.

Build42263 PASS129.46s. Native10139 all9 PASS (approximately1.70s), including
192 wet-mask/rotation/reflection/storage combinations with both implementations.
The exact captured cell reproduces slope3.32131804479 in the original and
1.27887962467 in the candidate; this is the same-input causal comparison.
Default build26756 PASS22.20s; final native80233 all9 PASS (approximately1.66s).
Eight independent analyzer tests pass again0.219s. No gate was relaxed.

## Playable qualification and integration

Opt-in game69060 TERMINAL exit0. Local submitted-shape audit contains21,053
triangles, no triangle above60degrees. Contact:2,020 wet barycentric points,
zero dry/unavailable points, max carrier/support discrepancy4.76532e-5cm.
This run did not request a GPU detail readback; that was added to final-default
verification below. Its193-frame recording fully decodes46 source frames over
6.434s. Inspected image still has broad blurred foam and smooth green faces;
do not credit the local shoreline correction with solving those issues.

The ordinary `L_SouthForkAmerican_FullReach` component now chooses the opposite
dry-corner fan. Other maps remain unchanged unless explicitly opted in.
`-RaftSimOriginalBankFan` retains the original control and overrides opt-in.
No map, material, captured terrain, hydraulic source, foam or physics change.
The correction changes interior interpolation/contact, not boundary placement
or vertex data; no claim of identical presentation volume is made.

No-opt-in default game16545 TERMINAL exit0; actual audit reports20,836 nearby
triangles, none above60degrees, slope decomposition residual1.75590e-12.
Separate native validation ran concurrently; these are NOT timing captures.
Contact still has2,020 wet points/zero dry or unavailable, max4.76801e-5cm.
903 points include presented detail. GPU audit of the SAME sequence72 passes
all4,226 queries with maxRGBA error2.98023224e-8 against unchanged1e-6 gate.
Its reported sample elapsed9.846406s and simulation4.800000s are distinct;
payload agreement is not proof of wall-clock real-time pacing.
Reports: `tmp/south-fork-bank-fan-default-{analysis,contact,detail}-v1-20260914.json`.
The raw shape capture is `tmp/south-fork-bank-fan-default-v1-20260914.json`.

The final default video `unreal/Saved/VideoCaptures/RaftSim_20260914-071859.mp4`
fully decodes196 encoded frames from42 source frames over6.534s. Unmodified
`detail-motion/south-fork-bank-fan-default-v1-20260914_01s.png` inspected; broad
sheetlike faces and blurred froth remain a visual FAIL. Cameras/trajectories and
source times differ between these separate runs: no pixelwise causal comparison,
full rapid/traversal or photographic acceptance follows. The exact-cell native
comparison, not the different live snapshots, proves the local diagonal effect.

## Ordinary 30 FPS check

Separate, uninstrumented game76382 TERMINAL exit0. All300 CSV samples and footer
pass strict validation. Warm rows120–250:8.921945157FPS, frame p95129.5326ms,
GPU mean37.882964885ms and p9539.0996ms. FAIL30FPS/p9533.333ms. Shared long-job
load remains; this is not a new isolated benchmark or a causal speed comparison.
It does not replace the last isolated18.899245FPS/p9570.33ms failure.
Report `tmp/south-fork-bank-fan-default-performance-v1-20260914.json`, CSV SHA256
`57a96aa43f8b3c7fbafcb3bd1c1f6dd57887f5fafdaec140a20cdc71e67964cb`.
Physics remains120Hz. The old froth material remains SHA256
`44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.

NEXT address the broad source-driven faces, physical fine breaking and froth,
and sustained performance; do not mistake this small shoreline repair for all
wave-shape work. Full-history qualification, terrain/crew/later rivers/release
and final commit remain open. All417/422 frozen research guards are unchanged.
Completed8800 cook passes BOTH audits but is unsettled; next complete8900/local18000
requires both. No original long job was restarted or suspended.

Final direct handle checks confirm all five original jobs LIVE: main59896 at
0.824002567s, observer97152 at0.678217024s, scalar candidate41566 at1.557887734s,
separate diagnostic95666 at pressure call724, cook83142 at8828.5s. These are
unfinished histories, not stability passes; the candidate remains research-only.
