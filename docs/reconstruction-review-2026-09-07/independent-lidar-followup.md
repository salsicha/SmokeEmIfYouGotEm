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

Earlier next step: compare the coherent lower support layer against the cap's selected roof
connectivity over this footprint. Any candidate must identify excluded upper
observations as interpreted non-ground, retain them as raw source, and avoid
turning absent lower returns into measured rock. A global first-return filter
or indiscriminate smoothing remains unsupported.
