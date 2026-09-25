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
