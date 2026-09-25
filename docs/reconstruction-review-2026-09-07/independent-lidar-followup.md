# Independent Troublemaker LiDAR candidate — September 25

Supporting source work, not a playable change or river acceptance.

A fresh USGS TNM LPC query for bbox `-120.885,38.798,-120.881,38.802`
returned six tiles: four from the already used Eldorado 2019 survey and two
from `CA_SierraNevada_2_2022`. The latter point cloud has not yet been used
in the disputed cap comparison. Existing project references to SierraNevada
are DEM metadata, not an independent comparison of these rock anchors.

The candidate is `USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz`, catalog
ID `655e8b42d34e3aa43a4394b7`, advertised size 105,423,716 bytes. Its catalog
envelope includes the interpreted crux (-120.88339721792708,38.79966504465925).
An envelope is not proof of actual returns at the rock.

- [USGS catalog](https://www.sciencebase.gov/catalog/item/655e8b42d34e3aa43a4394b7)
- [Original LAZ](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/CA_SierraNevada_B22/CA_SierraNevada_2_2022/LAZ/USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz)
- [NOAA source metadata](https://www.fisheries.noaa.gov/inport/item/79931)
- [USGS work-unit dates](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/CA_SierraNevada_B22/USGS_CA_SierraNevada_B22_Project_Report.pdf)

Despite the project name, work unit 300058 lists acquisition November 16 to
December 1, **2021**. This is not an exact acquisition timestamp for every point.
NOAA lists no access restriction and a temporal-change/fitness warning under
use constraints. No third-party photograph license is inferred from that.

The single-tile download is in progress in
`tmp/troublemaker-independent-lidar-20260925/`; do not start another transfer
or consume the partial file as a complete cloud. Header-only inspection reports
21,084,597 points, horizontal EPSG:6339 and vertical EPSG:5703, explicitly
GEOID18. The older survey used GEOID12B. No numerical datum correction, exact
co-registration, rock classification or underwater geometry is established.

`physics/scripts/audit_troublemaker_independent_lidar.py` is the bounded next
check after the transfer completes and size/hash are verified. It checks the
retained 2019 source hash and original witness indices, requires the declared
horizontal/vertical CRS, streams the new survey and records 0.3/0.5/1/3 metre
neighbourhood counts, classes and height differences at the 18 cap anchors.
These are coordinate neighbourhoods, not identified point correspondences.
The CLI help and four numerical-control tests pass (missing coverage, inclusive
radius boundary, signed height differences, unfiltered classes, invalid inputs).
The actual comparison is still pending. The selected EPSG:6339 to EPSG:32610
operation reports **2 m accuracy**; a 0.3 m coordinate neighbourhood must not
be called sub-metre point registration. Stable-ground agreement is still required.
Raw sources and installed assets
remain unchanged; no cook or engine launch was started.

This changes the next action from speculative photo fitting to an independent
survey comparison. If returns exist, first establish stable-ground horizontal
and vertical agreement and inspect coherent rock/vegetation structure before
proposing any shared render/collision/bed revision. Do not select whichever
epoch happens to make smoother rocks. South Fork remains first unfinished.

## Completed transfer and first actual comparison

The original transfer exited0, with exactly105,423,716 bytes. SHA256:
`2261adeac1a3ea49cdeaaa038cbb8bba40b2c1ada7f15b0e42e98192957fd96e`.
The audit then decoded all21,084,597 declared points and exited0. All18 queried
2019 anchors have2021 returns within0.3m in the nominal transformed frame.
This verifies actual point coverage, not just catalog bounds.

Durable report: [anchor comparison](independent-lidar-followup/anchor-comparison.json).
All queries retain the2m operation-accuracy caveat, the original source/witness
hashes, and the separate geoid realizations. No same-point identity is inferred.

Examples of new-minus-old height ranges within the0.3m query:

| Original point | Returns | Classes | Height range m |
| --- | ---: | --- | --- |
|685449|5|1 only|−0.095827 to−0.035827|
|685469|6|five1, one2|−1.937892 to+0.202108|
|686411|3|1 only|−1.779830 to−1.739830|
|686536|13|1 only|−0.367940 to+1.892060|
|689127|6|1 only|−0.089721 to−0.009721|

Class1 remains unclassified; class2 is source-classified ground, not certified
rock. Several neighbourhoods retain multiple vertical layers. This is useful
independent evidence, but neither a uniform vertical offset nor a permission
to replace every high return by a lower one. The next concrete check is
stable-ground cross-survey registration away from water/vegetation, followed
by coherent local cross-sections at the divergent anchors (especially686411).
No terrain/collision/bed edits, cook, rebuilt game or new scene acceptance.

## Independent ground-consistency screen

`audit_troublemaker_survey_alignment.py` hash-checks both sources, excludes
withheld2021 returns, and selects class2 points outside the2019 water mask,
more than5m from its water returns. One2019 sample per4m spatial bin supplies
a1.5m local plane with at least12points, RMS<=.08m and slope<=1. The nearest
2021 ground point must be within.3m and outside the same water buffer. No
cross-epoch residual trimming is performed. These are candidate stable-ground
controls, not independently surveyed monuments or proven unchanged terrain.

The completed screen retains3,631controls from578,641old and455,114new ground
points. Linear apparent-offset fit (east,north,vertical) is
(-.006375,+.025416,-.079357)m; design condition5.83218. Before correction,
residual5th/median/95th percentiles are(-.167785,-.078843,+.010063)m.
After the diagnostic fit they are(-.089944,-.000726,+.087352)m; extremes still
reach−.976275 and+1.003940m. No fitted transformation is applied to sources.

Four spatial holdouts split controls at the median east/north coordinates;
each fit excludes the entire held-out quadrant. Held-out median residuals are
(.018873,−.009022,.002197,−.014888)m; fifth-to-95th intervals are respectively
[-.055503,.128664],[-.107106,.076684],[-.082970,.085430],[-.099745,.068343]m.
The four fitted vertical offsets range−.090617 to−.074392m. Outliers remain
as large as−.990000 and+1.022918m and are not discarded as invalid source data.
Six numerical tests pass, including exact synthetic offset recovery and
rejection of flat ground that cannot constrain horizontal offsets.

This makes a uniform metre-scale datum/translation explanation for anchor
686411's1.74–1.78m local discrepancy implausible within this screened area.
It does not establish exact rock correspondence or reduce the declared absolute
datum accuracy. Next inspect both local point structures and vertical layers
at686411, retaining lower and upper observations instead of fitting all anchors
to this ground offset. No rock removal/smoothing is yet justified.

[Complete ground controls and residuals](independent-lidar-followup/ground-consistency.json)
retain every selected control for independent spatial holdout reproduction.
All analysis processes are terminal; no gameplay or cooked fields changed.

## Local layers and exact pulse companions at686411

New source-hash-checked8m-square sections retain1,293original2019 points and
1,199independent2021 points. Actual plotted east/height and north/height views
were inspected: both epochs contain upper and lower layers. The2021 upper
layer is not uniformly absent: zero returns lie within.3m of the anchor height
inside.5m horizontal radius, but two appear within1m and18within2m. Therefore
the nearest-return height discrepancy alone is not a vertex-removal rule.

Across the full square,35independent returns are within.3m of the old anchor's
height, all class1. Of these,27are first returns of multi-return pulses. The
lower layer (more than1.5m below the anchor) has667returns, including133class2
and534class1. No withheld points occur in either reported subset.

Matching exact GPS timestamp, point-source ID and scanner channel,24of those
27upper pulses recover every declared numbered return inside the local crop.
Their vertical separations range.89–2.33m; maximum companion horizontal
separation is.990404m. Four complete groups contain a class2 companion. Three
incomplete groups remain explicitly incomplete; no nearby point is substituted.
These matching fields and raw LAZ indices are retained with every point.

Example:2021LAZ indices1404890/1404891 are first/second returns of one pulse,
both class1, separated2.21m vertically and.839524m horizontally. Another pair,
3543145/3543146, spans2.14m vertically and.759276m horizontally. This is direct
layer evidence, not a declaration that every first return is vegetation:
oblique beams can also encounter rock edges. Combined with independent image
vegetation evidence, it strengthens but does not certify that interpretation.

![Independent local sections](independent-lidar-followup/anchor-686411-sections.png)

[Local coordinates, classifications and exact pulse groups](independent-lidar-followup/anchor-686411-sections.json)
were generated by `inspect_troublemaker_anchor_layers.py`. Original heights
are retained; the ground-fit offset is NOT applied. The earlier no-pulse output
is also preserved in ignored tmp. Both analysis runs exited0; no new cook,
geometry, collision, water field or playable acceptance.

### Fixed-camera mixed-cap retrace — September 25

The retained eight diagnosed cap rays have now been traced against both caps,
holding the original ray audit's candidate ground constant. All eight baseline
source hits reproduce (source face and world position), and source/view hashes
match before and after the comparison. Five existing nearest-solid/reflection/
identity tests pass. Report:
[mixed-cap-retrace.json](independent-lidar-followup/mixed-cap-retrace.json).

Seven rays have exactly zero hit displacement, including all four diagnosed
90-degree inferred side walls. Pixel (475,330), originally cap face1137 at
9.260605m along the ray, now first intersects cap face1146 at17.072017m:
7.811412m farther away. Its hit slope changes65.249707 to32.461068 degrees,
but this is a DIFFERENT surface behind the removed foreground triangle, not
proof that the foreground rock has been correctly reconstructed. The candidate
does not repair the other seven diagnosed targets.

This is a source-space occlusion result, not GPU visibility, fresh native
collision or normal-play acceptance. No source data, terrain or water changed.
Next inspect a fresh engine capture at the exact retained camera with candidate
and parent under identical settings; evaluate the revealed surface and remaining
inferred walls against evidence. Do not treat the lower replacement slope as a
repair gate or repeat another unchanged long cook to resolve this visual issue.

### Native retained-camera comparison — September 25

Actual unsaved FullReach PIE pair completed: candidate-v5 in52.82s and parent-v1
in82.41s, both engine exit0 and all protected files unchanged. Native camera
matrices are exactly equal between the pair; projecting the original diagnosed
hit points differs from the retained September18 view by at most0.040328pixels
(fixed-camera float position precision). Both captures are1280x720. This uses
the installed normal ground, not the earlier source-ray audit's candidate ground.

Actual complex-collision rays show seven exactly unchanged world hits and a
781.142120cm displacement at pixel475,330. This independently confirms the
source-space occlusion result. Inspected first-frame images show a reduced local
foreground peak but retain conspicuous triangular spikes and vertical/block-like
walls. No boulder reconstruction or photographic acceptance is claimed.

Both runs use the same candidate50s water configuration to isolate geometry;
the parent cap plus these fields is a diagnostic mismatch, NEVER a promoted
playable bundle. The first frames occur at world12.854427s and43.141078s because
the parent control unnecessarily waited for the intentionally absent candidate
actor. Therefore water, vegetation motion and foam image differences are NOT
a controlled temporal comparison. The harness wait now checks the selected cap;
this final wait/log-volume correction has not yet been rerun. No water/performance
improvement is claimed. Candidate flow remains unsettled and uninstalled.

Earlier attempts are retained in tmp: v1 omitted the explicit scenario and failed
the geometry-presence gate; v2/v3 hit unavailable Python runtime spawn APIs;
v4 captured90-degree FOV, not the retained91.185065degree view. v5 instead uses
the existing native capture camera and player-controller FOV override; captured
FOV is91.185068degrees. Failed attempts are not accepted captures.

Durable runtime receipts and view metadata are in `independent-lidar-followup/`
with `retained-camera-` prefixes. Full images/video remain in Unreal Saved;
candidate `mixed-retained-camera-candidate-v5-20260925_000.png` and parent
`mixed-retained-camera-parent-v1-20260925_000.png` were inspected. Next work must
address the remaining source classification/connectivity and inferred side-wall
geometry, rather than treating this small patch or crease shading as completion.

### Independent lower support at the four diagnosed walls — September 25

The wall closure is an inferred vertical extrusion, not a measured rock face.
A complete hash-checked scan of21,084,597independent LAZ points finds ground-
classified observations within1.5m horizontal radius of every diagnosed wall
hit, where the retained2019archive has no class2points at that radius.
Counts for faces6225/6217/6222/6315 are8/8/12/2 (neighborhoods overlap; these
are not unique totals). Their heights relative to220mNAVD88 span respectively
7.24–7.96,7.09–7.39,6.78–7.23,7.02–7.06m. All source points and flags are retained
in [the support record](independent-lidar-followup/diagnosed-wall-support.json).

The additional [connectivity record](independent-lidar-followup/diagnosed-wall-support-connectivity.json)
checks each non-withheld class2point against the exact mixed-cap roof. Two
observations for face6225 (LAZ1398163,6055843) and five for6222 (1402214,6053500,
11271228,15885478,18546316) have both new edges<=1m, positive triangle area and
zero roof overlap within1e-9m2. Faces6217 and6315 have no passing direct extension.
These checks establish possible local connections, NOT the correct outline,
measured flank, manifold combined patch, classification certainty or acceptance.

Next construct and review a bounded source-exact extension for6225/6222 using
explicit2021dataset/index ownership, with no moved original roof points and no
relaxed edge limit. Verify combined topology/overlap and the remaining outer
closure before export. Do not choose an observation merely because it makes
the lowest/smoothest shape. Survey epoch, GEOID12B/GEOID18 and the declared2m
horizontal transform accuracy remain uncertainty; no fitted offset was applied.
The first scanner attempt failed on LAS bit-field scalar conversion before
writing output; NumPy conversion corrected it. Both completed scans exited0;
no geometry, fields, engine scene or playable executable changed in this pass.

### Two-triangle extension constructed, not promoted — September 25

`build_diagnosed_wall_extension.py` constructs a bounded candidate in
`tmp/troublemaker-wall-extension-v1-20260925/`. It selects the eligible class2
point minimizing maximum new XY edge (index tie-break), explicitly not the
lowest height. Selected LAZ indices6055843 and6053500 preserve raw transformed
coordinates and retain dataset1 ownership. They extend faces6225/6222 respectively.
No old roof coordinates or triangles move; added area is0.1371635404m2.
All edges stay<=1m, old-roof and patch-patch overlap are rejected, and closed
topology has9,654two-face edges with9.09e-13m3volume identity error. Five tests
pass, including overlap, oversized edge and degenerate extension rejection.
Candidate SHA256:949b577303ef8b8ef2f9c25a74e3e89c0143a3e625ca519174391964c9916086.
[Construction receipt](independent-lidar-followup/wall-extension-construction.json).

The diagnosed source rays reject treating this as the wall repair: pixel650,345
now hits the new roof triangle2966, but its slope is still83.809682degrees.
Pixel390,490 hits a NEW inferred vertical wall6282 at90degrees. The short
extension largely relocates the closure instead of resolving its shape. These
are source-space ray checks, not fresh native captures or visual acceptance.
No export, cook, engine install or playable promotion was performed for this
candidate. Its separate manifest schema intentionally cannot masquerade as an
accepted runtime union. Do not spend a long cook on this unchanged patch.

Next evaluate a broader source-supported boundary connection using the retained
exterior observations and intermediate points, rather than optimizing connector
length alone. Preserve the same1m edge bound and original roof; reject candidates
whose diagnosed silhouette still terminates on an exposed artificial wall. The
other two walls and the roof's semantic classification remain unresolved.

### Broader captured exterior connectivity — September 25

`build_broad_wall_extension.py` uses all16unique non-withheld exterior class2
observations in the diagnosed neighborhoods, re-reading their exact LAZ records
and CRS before construction. Of21non-overlapping exterior Delaunay triangles
within the unchanged1mXY edge bound,19connect to the original roof by shared
edges; point-only/disconnected components are rejected. Thirteen added source
observations remain used. Added area1.192842612m2; all original roof triangle
coordinates remain exact. One disconnected vertex fan is split into duplicated
indices with identical XYZ/source ownership, using the existing checked splitter.
The initial unsplit closure failed, not waived. Final closure has9,726two-face
edges and1.36e-12m3volume identity error. Eight focused tests pass.

Candidate is `tmp/troublemaker-broad-wall-extension-v1-20260925/`, cap SHA256
03288230c9e86c54554123d5636c01a8888fb0564412cb2bd934aa67d7b6efa3.
[Full construction and diagnosed-ray receipt](independent-lidar-followup/broad-wall-extension-construction.json).
At pixel390,490 the source ray now hits a57.658288degree roof face between
captured points instead of the vertical closing wall. The other three diagnosed
wall rays still hit90degree closures. This is partial source-space improvement,
not a full wall repair, a measured outline, native collision or visual acceptance.
No runtime manifest, cook, export or playable scene changed. Source epoch/geoid
and2mdeclared transform uncertainty remain; no fitted offset is applied.

Next examine constrained boundary connectivity where the filtered triangulation
still leaves exposed closures (especially6225, which had direct support), while
retaining original roof geometry. A lower slope at one ray alone is not enough
to justify normal-play promotion; shared geometry and engine views remain gates.

### Preserved-boundary variant and shared-loader validation — September 25

The `--constrained-boundary` variant uses the existing source-only cavity recovery
to preserve every original perimeter segment before filtering exterior faces.
It produces28edge-connected additions totaling1.665134584m2, rather than19faces.
All original roof triangles remain coordinate-exact; one point-contact fan is
split without moving coordinates. Closed solid:9,738two-face edges,504inferred
wall triangles,4.55e-13m3volume identity error. This recovers usable connectivity
lost by the unconstrained triangulation, not a new source observation.

Source rays now hit roof at650,345 (83.809682degrees) and390,490 (57.658288degrees).
The other two diagnosed walls remain90degrees. The first face is still very
steep; these results are not photographic repair acceptance or native visibility.
Candidate: `tmp/troublemaker-constrained-wall-extension-v1-20260925/`, cap SHA256
7d1031602413e0dae311574f6b6d03e1542917bf2b9893a5c911875f84404d62.
[Construction receipt](independent-lidar-followup/constrained-wall-construction.json).

`validate_constrained_wall_union.py` creates an explicitly unpromoted manifest
for the existing mixed-source schema and runs the UNMODIFIED `SourceRockUnion`
loader. Every per-vertex source coordinate/classification, underlying source
hash, coordinate frame and reconstructed solid is verified;17independent-source
vertex records include duplicate fan ownership. The manifest replaces stale
single-point metadata with explicit LAZ indices; no source classes are relabelled.
Manifest SHA2565cbe5c2f1ea240c6596fa9f873ea72c201c74004d607df07a7f69107e0688c9c.
[Shared-loader receipt](independent-lidar-followup/constrained-wall-shared-union.json).
Twenty-nine source-connectivity and wall-extension regressions pass.

Next native geometry export/collision/view check should use this bound manifest,
not the earlier short-connector or unconstrained candidate. No hydraulic cook,
normal-play installation or engine acceptance occurred here. Two remaining
walls and the steep face still need evidence-based work; do not mix this mesh
with old flow fields in normal play or mark the river complete.

### Shared geometry and actual native-face collision — September 25

Prepared `tmp/troublemaker-constrained-wall-union-20260925/` from the normal
4900to5400input with `--replace-union`, preserving its explicit bed revision.
The audit checks841cores/5,382,400cells, changes871cells across four cores, and
passes source-field, captured-mask/stage and exact roof-sampling checks. These
are geometry cells, not a new flow solve or settled-water result. The exporter
required this matching shared-union audit; no authorization gate was bypassed.
[Geometry audit](independent-lidar-followup/constrained-wall-geometry-audit.json).

Blender exported3,246vertices/6,492faces without decimation, with the existing
45degree authored crease shading. FBX SHA256
89dca1378bb978bcec60e89c1705ec9e4b0f6073a1b4f965a0688c3dbfc2e433.
Transient Unreal import and every-face outward traces pass:2,994roof,
2,994internal bottom and504inferred wall faces. Maximum error0.000282954cm,
minimum normal dot0.9999999993. Native directed-source SHA256
485dbd25980740b050f45fe11da3d7338e24aadcfda47c0148f03ab05e890b67.
Engine exit0; no saved assets or levels. Full-map union collision is NOT verified.
[Native report](independent-lidar-followup/constrained-wall-native-collision.json).

The face-count check now uses the exact export count instead of the old6428
constant and additionally requires every face index exactly once. Two fingerprint
regressions verify cyclic/face-order invariance and sensitivity to winding/XYZ;
the earlier native baseline hash also reproduces before generating these probes.
Import tangent-basis warnings remain, as in the earlier export; not a clean
release-log claim. This scoped collision pass does not establish rendered shape,
shoreline, motion, flow consistency or performance. No playable content changed.
Next normal-map union and matched-camera review can use the new export plus
its matching geometry, while the two walls/steep face remain unresolved. No
unchanged long cook or old-field production promotion is justified by this pass.

### Full-map union collision follow-through — September 25

The constrained export now passes the unchanged full-map native union gate:
34,935 surface-position and owner checks, maximum error 0.031769855cm against
the existing 0.1cm tolerance. Coverage includes 25,600 hydraulic-grid samples,
4,466 revised-ground centroids, all 1,623 roof vertex records, all 2,994 roof
centroids and 252 boundary samples. Parent-covered targets retain their source
metadata and test the actual upper surface; they are not forced to hit the cap.
[Native receipt](independent-lidar-followup/constrained-wall-full-map-collision.json).

`prepare_constrained_wall_map_check.py` binds the candidate source manifest,
matching audited geometry/export and native collision fingerprint. It retains
6,744 legacy probes separately before adding source-visible vertex rays; it
does not waive legacy failures. The combined probe SHA256 is
75eea9245991e9c5869ecb48994d7607c31bc76bf33e2e4b8969e31905aad264.
The three source-visible probe regressions pass.

The actual FullReach map was loaded in Unreal with null RHI and the candidate
cap swapped transiently. Engine exit0, no failures, original cap restored,
472 protected files checked unchanged, no assets or levels saved. No other
engine/cook process remains live. Import tangent/near-zero binormal warnings
and the retained ground's high-triangle navigation warning remain recorded;
this is not clean-log or rendering acceptance.

This closes the earlier missing full-map collision check only. The two exposed
vertical walls and steep face remain unresolved. No rendered capture, matching
flow solve, shoreline/motion/performance acceptance or normal-play geometry
delivery occurred. Next review the new candidate in the retained engine view,
explicitly separating geometry-only diagnostics from water acceptance; do not
pair this new mesh with the older candidate's flow in normal play.

### Constrained candidate rendered review — September 25

Actual FullReach PIE confirms one candidate cap, one retained ground and no old
cap at the review station. Three 1280x720 captures complete; engine exit0,
47.85s harness duration, protected files unchanged. The retained camera uses
the recorded pose and 91.185degree FOV. First captured frame was visually
inspected: tall flat-sided blocks and sharp triangular faces remain prominent.
This candidate is not accepted or installed despite passing native collision.
[Capture receipt](independent-lidar-followup/constrained-wall-retained-view.json).

The harness now supports an explicitly geometry-only config, restricted to the
retained candidate view. It uses the new bound geometry/collision config but
does not modify installed water settings or invoke the old candidate's runtime
expectations. Existing fields appear only as background; they do not match this
mesh. No water, motion, shoreline or performance conclusion is drawn. No saved
assets/levels or normal launch changes. The harness syntax and diff checks pass.

Next work must address the remaining source selection and inferred closures,
not repeat this unchanged export/capture or launch another long cook. The visual
failure is broader than the small exterior-connectivity additions repaired here.

### Boundary lower-return selection audit — September 25

The constructor selects its lowest return AFTER excluding observations within
0.3m of the flattened DEM, then closes the selected perimeter vertically. A
bounded audit now tests this potential selection bias at all252current boundary
vertices using the original2019archive and unchanged0.5m bins. Fourteen vertices
have an eligible class1/2/10 source observation more than0.5m lower in the same
bin. Eight witnesses would fail the original clearance prerequisite, including
five ground-classified points:658439,658438,685144,688855,689621. Their vertical
separations are approximately1.31,1.48,1.84,1.25,0.71m, respectively.
[Exact indices and coordinates](independent-lidar-followup/boundary-lower-bin-witnesses.json).

This tests a concrete selection mechanism beyond exterior extension. It does
not establish that upper points are vegetation: oblique rock edges can produce
multiple layers, and same-bin proximity is not point correspondence. Most
boundary vertices have no qualifying witness under this test; this cannot solve
the entire shape problem. Original source/mesh hashes are verified, no returns
are discarded and no geometry is changed. Three tests cover stable source ties,
negative-coordinate bins, vegetation/missing-residual exclusion and invalid
bin size. Audit exits0. Next inspect these five ground-supported neighborhoods
against local connectivity and imagery before any source selection replacement.

### Five ground-witness image and topology review — September 25

All five lower class2witnesses lie INSIDE the existing roof footprint. They are
not candidates for another exterior extension. Hypothetical exact-XYZ vertex
substitutions invert2,2,2,2,3incident faces respectively; witnesses685144 and
688855 also create maximum XYedges1.136659m and1.360490m, exceeding the existing
1m limit. The original roof has zero non-upward faces. Direct substitution is
therefore rejected independently of whether its appearance would improve.
[Coordinates and topology receipt](independent-lidar-followup/boundary-ground-context.json).

`inspect_boundary_ground_witnesses.py` verifies retained NAIP image/registration
hashes and produces five nearest-pixel4m contextual views in
`tmp/boundary-ground-witness-review-20260925/context.png`. Visually inspected:
green/dark regions surround the first three targets; the last two have mixed
gray/green context. This does not label individual returns: the registered image
uncertainty is3m, much larger than the0.19–0.43m upper/lower separations. No
imagery resampling is presented as new detail. The upper points are class1,
not certified rock or vegetation. No source coordinates/classes were changed.

The next geometric hypothesis must remove/retriangulate a reviewed local cavity
while preserving unrelated source faces and full source history. It cannot keep
old connectivity and merely lower these vertices, nor claim that these five
observations resolve the whole visible wall problem. Geometry, flow and normal
play remain unchanged; this is source/topology evidence only.

### Exact-source local cavity hypotheses — September 25

Construction established that all five ground witnesses already occur in the
current extended cap:658439/658438/685144/688855/689621 map to roof vertices
62/61/192/665/803. The prior clearance audit describes original selector bias,
NOT missing points in the present roof. An initial duplicate-XY rejection caught
this; the builder now explicitly reuses existing lower vertices. Upper raw
observations remain preserved, and their exclusion from faces is an interpretation.

Three independently constructed hypotheses pass unchanged shared-seam,1m XYedge
and closed-solid gates:658439,658438,689621. They replace7/7/10local triangles
with5/5/8triangles and preserve every unaffected source face exactly. Inferred
footprint losses are0.078956/0.088442/0.105579m2. Maximum new XYedges are
0.734715/0.806622/0.737419m. The other two hypotheses fail retained-seam coverage
and are rejected, not patched by increasing support limits or dropping the gate.
[Full construction receipt](independent-lidar-followup/boundary-ground-cavities.json).

Candidate NPZs are isolated under `tmp/boundary-ground-cavities-v2-20260925/`,
each bound to the original source and constrained-parent hashes. They are not
combined or assigned a production manifest. No source XYZ or classifications
move; unchanged unused vertex records remain for provenance. Three regressions
cover exact local geometry/shared seams, unchanged edge rejection and reuse of
an already present lower point. Tests and actual construction exit0.

This establishes feasible local connectivity at three locations, not that the
excluded class1points were non-rock, nor full source/visual acceptance. Next
compare each hypothesis's shape and source evidence, keeping the two failed
locations explicit. No export, cook, native validation or playable change yet.

### Local cavity relevance to the diagnosed view — September 25

All three passing cavity hypotheses were retraced against the eight retained
diagnosed camera rays, holding the earlier source-audit ground fixed and using
the constrained cap as baseline. All24hit comparisons are unchanged. Source,
candidate, view and construction hashes are checked before comparison.
[Ray comparison receipt](independent-lidar-followup/boundary-cavity-view.json).

These local candidates do not repair any sampled defect in this view. Set them
aside rather than export or cook them on the strength of topology alone. Eight
rays cannot establish whole-image equality, native visibility or that the local
interpretation has no value elsewhere. No new native/cooked/playable state is
claimed. Return to the actual remaining diagnosed faces and their dated-image,
classified-return and inferred-closure evidence. Do not repeat the unchanged
boundary-hypothesis construction as progress toward this view's acceptance.

Earlier next step: compare the coherent lower support layer against the cap's selected roof
connectivity over this footprint. Any candidate must identify excluded upper
observations as interpreted non-ground, retain them as raw source, and avoid
turning absent lower returns into measured rock. A global first-return filter
or indiscriminate smoothing remains unsupported.
