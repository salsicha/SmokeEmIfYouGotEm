# Dated imagery review of supported class-20 clusters

September 27, 2026. Supporting source interpretation, **not a playable change**.
No engine, build, duplicate cook, scene import or hydraulic change was started.

The previous installed-union check narrowed the remaining question to whether
positive original-return residuals justify additional rock geometry. This run
reviewed the two spatially supported groups against the retained, raster-locked
**July 21, 2022 NAIP** image and original LiDAR classifications. Selection is
explicit: at least three other class-2/20 neighbors within the earlier 0.5 m
screen, at least two observations connected within 4 m. This is a diagnostic
search rule, not a rock outline.

## Evidence and interpretation

Both 20 m review windows lie entirely inside the actual returned EPSG:32610
image extent. The source is `m_3812009_se_10_060_20220721`, locked raster 21979,
0.6 m native resolution; the exported grid spacing is 0.5078125 m and does not
add spatial information. Original image/archive/base hashes were checked before
and after. No colors, source XYZ, classifications or geometry were modified.

I inspected both registered three-panel figures (imagery, original classes,
ground-to-base residuals). The groups lie along apparent exposed-bank/water
transitions, with residuals continuing along narrow shoreline strips. Neither
view establishes a separate closed boulder outline. This is visual inference:
the 3 m circles show registration sensitivity, not measured error bounds, and
the imagery is not contemporaneous with the older LiDAR acquisition.

| Original observation group | Ground returns compared in window | Above base by >0.3 m | Ground returns outside registered mesh |
| --- | ---: | ---: | ---: |
| 597440, 597723, 597730 | 690 | 12 | 0 |
| 1174998, 1175001 | 1490 | 30 | 65 |

These context residuals use the registered **base only**, not the final scene
union. The five central observation-to-current-collision residuals were checked
in the previous native run; the additional context points have not been traced
against the playable scene. Class 1 points remain unclassified, class 9 water
is shown as context, and class 7 noise is excluded from geometry comparisons.
No returned class is silently relabeled as rock.

The first analysis attempt stopped rather than extrapolating 65 points beyond
the registered mesh. The final run uses the exact outer registered-grid
perimeter to separate these points; they are marked and listed, never clamped,
filled or assigned fabricated residuals. Three selection regressions pass.

## Decision

**Do not turn these five points into standalone boulders.** Keep both groups
as provisional bank-edge constraints for a coupled terrain/shoreline review.
Nearby ground returns corroborate elevations, but do not establish flank
shape, a surveyed bank breakline, submerged geometry or hydraulic control.
Do not rerun the unchanged 17-point screen, collision snapshot or these crops.

A bank correction would need a bounded support polygon and explicit uncertain
transition into the underwater bed, then shared render/collision/bed sampling,
recooking and normal-play validation. It cannot be delivered as a cosmetic
rock pasted over the existing water. This analysis supplies no reason to enable
an unstable solver or relax the 20 FPS / p95 50 ms requirement. Busy-rapid
performance, inferred flanks, hydraulic balance and visual continuity remain
open; South Fork is still first in the queue.

## Reproduction / provenance

Script: `physics/scripts/review_ignored_ground_clusters.py`; output directory:
`tmp/ignored-ground-cluster-review-v2-20260927`. The report retains all compared
original indices/XYZ, classifications, base heights, uncovered indices, and
input/figure hashes. Partial first-attempt figures are preserved separately;
that failed attempt produced no completed report.

| File | SHA-256 |
| --- | --- |
| report.json | `caf47c9c48880272054c62444740fb990432da519f51f0d9f18822aaf17fb3ba` |
| cluster-597440.png | `9ab94dd34d0d64eb34bb990b82a42bb01d49643d6ead5475187de421e3528249` |
| cluster-1174998.png | `d0506a48a44fb689f86ba5da6606218187c1637ebf1752d5f95910084197893e` |

The original raster-locked download URL, date, image hash and actual export
extent remain in `sources/rapid_atlas/troublemaker/manifest.json` under the
South Fork reconstruction data directory. The [USGS service description](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer?f=pjson),
rechecked September 27, describes NAIP compressed orthoimagery as public domain.
Credit: USDA, USGS, The National Map. No new imagery was downloaded or shipped.
