# Eldorado ignored-ground filtering correction

September 26, 2026. Supporting reconstruction repair, not a new playable asset.

The [NOAA survey metadata](https://www.fisheries.noaa.gov/inport/item/66639)
identifies class 2 as bare earth and class **20** as ignored ground. The
reconstruction scripts incorrectly used class 10. Source filtering, supporting
neighbor searches and source-exact cap validation now consistently use 20;
class 1 remains an explicitly uncertain, unclassified candidate where already
allowed. Classified-ground-only searches still exclude class 1. No source
classification or XYZ is rewritten, and clearance, region, pulse, support,
provenance and immutable-geometry checks remain in force.

## Measured impact on retained inputs

The [read-only impact receipt](south-fork-ignored-ground-impact.json) verifies
the retained Troublemaker classified archive hash before and after inspection.
It contains 76 class-20 returns and no class-10 returns; 35 class-20 returns
are within the survey water polygon. With the original exposure screen
(`0.3 < height above flattened surface < 12 m`), correcting the ground classes
increases provisional candidates from 23 to 40: **17 additions, no removals**.
Their exact retained indices, coordinates and residuals are in the receipt.

This is not evidence of 17 individual boulders. Ignored ground is a survey
classification, not semantic rock identification; isolated returns still need
corroboration. The archived `exposed_ground_candidate` mask remains untouched
as historical output. Future candidates must recompute from retained original
classifications into fresh versioned outputs, not overwrite that archive.
Existing asset/cook hashes and historical receipts remain the evidence for
the previously selected geometry, not evidence for newly included points.

## Validation and next action

161 focused tests pass (122 geometry/source tests plus39 adjacent source/staging
regressions). They exercise class20 eligibility, class10/noise/water/bridge
exclusion, unchanged minimum support and clearance, lower-neighbor selection,
and exact mixed-source identity. The previous clearance fixture itself used
the wrong class10; it now uses20 with the same expected support and geometry.

Review these source positions against retained dated imagery and existing
registered geometry before selecting any geometry change. Any accepted change
must update render/collision/bed and recook consistently, then be checked in
normal play at the current 20 FPS / p95 50 ms target. No new source download,
captured-data deletion, solver enablement, asset import or cook occurred here.
South Fork remains first in the queue; Colorado has not been started.

## Follow-through: registered-base and peer screen

The [registered-base screen](south-fork-ignored-ground-registered-screen.json)
now samples all17 observations on exact retained base triangles and records
nearby original ground-return indices/heights. Source and base hashes are
checked before and after. Observations stand0.0406–1.2896m above this base.
This is **not** the final playable cap/terrain union and is not a defect claim.

Within a0.5m horizontal diagnostic radius,14 observations have at least one
other class2/20 return; three (697210,889812,1867764) have none. The query itself
is excluded from every peer count. Nearby ground does not establish a shared
rock surface; the receipt preserves signed height differences for review.
The largest base residual,1.2896m at697210, has no classified-ground peer in
that radius and must not be promoted merely because it is the largest gap.
Five new peer-screen regressions plus ten class-filter tests pass.

The September26 13:54UTC follow-up found another session rebuilding the editor,
then running South Fork captures and normal-menu timing. No competing cook or
game process was launched. Its water-surface source edits were left intact.
The next isolated delivery run must rebuild the standalone executable after
those shared changes settle, refresh cooked content, and verify normal Boot/
menu travel, motion and cost; the older staged-data comparison is already done.
