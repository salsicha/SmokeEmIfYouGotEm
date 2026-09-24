# Folsom source coverage at the South Fork outlet

September24,2026. Supporting source audit only: no rendered geometry, collision,
bed, cook, runtime field or normal-launch change. South Fork remains unfinished.

## Question and result

The current coupled-flow preparation sets its downstream boundary to the median
captured water-surface elevation at the two open west edges. That is
131.04142761230469m NAVD88 (220m datum minus88.95857238769531m), not a calibrated
reservoir stage. No outlet adjustment is justified merely to match inlet flow.

Investigated a new primary-source candidate from the
[Reclamation reservoir survey catalog](https://www.usbr.gov/tsc/techreferences/reservoir.html).
Downloaded the listed Folsom2005 GIS archive and inspected its actual layers,
embedded metadata and spatial intersections, rather than inferring coverage
from the title. Result: **no bathymetric sounding covers the existing outlet**.

The archive has5,961,868 BathymetricPoints and10,237 Contours features. Expanded
outlet query in EPSG:32610 is[669699.5,4293219.5,669819.5,4293419.5], covering
both80m outlet tiles with20m context. Converted XY query in EPSG:2226(ftUS) is
[6833478.471642,2044166.385654,6833879.266787,2044826.773948]. The points'
maximum native easting is6831918.3ftUS: a475.541m projected easting gap to the
query, not a nearest-point distance. Actual spatial query returns0points.

47contour features are candidates and all47intersect the projected query box
under an exact geometry intersection check. Clipped geometry Z spans432..498ft
NAVD88, or131.6736..151.7904m. Even the lowest is above the current131.0414m
water boundary. These mixed-source contours cannot establish the submerged
bed beneath that boundary. They remain a possible historical exposed-bank
comparison source, not a replacement for missing bathymetry.

## Date, datum and reuse cautions

The [survey report](https://www.usbr.gov/tsc/techreferences/reservoir/Folsom%20Lake%202005%20Sedimentation%20Survey.pdf)
is dated January2007. It describes September9-22,2005 sounding collection and
October20/31,2005 aerial surveys. Its project-datum elevations differ from
NAVD88-05 by2.34ft. The GIS layer WKT independently declares NAD83 California
zone2 in USsurvey feet horizontally, NAVD88 in international feet vertically.
Embedded contour documentation explicitly confirms NAVD88-05. Thus use0.3048
for declared vertical feet; do NOT add2.34ft again to these GIS contours.

Embedded metadata identifies Reclamation's Technical Service Center and a
combined aerial/underwater source. No item use-constraint entries were found;
that absence is not a verified shipping license for all contractor-derived
content. Keep license_verified=false/reference-only pending explicit reuse
verification. [DOI's copyright notice](https://www.doi.gov/copyright) cautions
that not every hosted item is public domain. No GIS asset is shipped here.

## Retained evidence and reproduction

Source directory:
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/sources/folsom_2005/`.

- `Folsom_Lake_2005.gdb.zip`:379,446,534bytes; SHA256
  `919489fb171d92ba1e1f71a05649a98ad4dfaf7acf362cf5fc07bd01f956a2ca`.
- `download.json`: officialURL, hash and ZIP member inventory; archive retained
  without extraction. Its initial coverage/license flags record download-time
  status, not acceptance.
- `layer-inventory.json`: exact CRS, bounds, feature counts and fields.
- `outlet-coverage.json`: spatial query and complete embedded documentation;
  SHA256`04084cea595df5354dc0d296a776010787b7f2c265ba76129bcc14b34149684a`.
- `outlet-contour-intersections.json`: exact clipped-feature IDs and Z ranges.

Read-only scripts retained under tmp: `inspect-folsom-bathymetry-20260924.py`,
`check-folsom-outlet-coverage-20260924.py`, and
`clip-folsom-outlet-contours-20260924.py`. They use the existing geospatial deps,
OpenFileGDB through /vsizip, XY-only pyproj transformation and Shapely geometry
intersection. The initial contour check rejected a list bbox argument before
reading features; changing it to the required tuple completed exit0.

Decision: do not extrapolate distant soundings into the outlet, alter its stage
from unmatched historical data, extend the hydraulic domain solely to reach
this archive, or launch an unchanged long cook. Actual local bed/stage evidence
remains missing. This source limitation does not block normal playable water,
geometry and performance work elsewhere in the requested South Fork scene.
