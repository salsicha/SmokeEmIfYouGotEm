# Downstream spikes: retained cap, not the new ground flanks

September 18, 2026. Supporting reconstruction work only. No normal-play terrain,
water, menu, material or physics change; no new visual/performance acceptance.

## New actual engine evidence

A fresh paired FullReach run starts at8300 with the same verified source-ground
candidate and matching50s atlas as the previous review. It rechecks25,600 native
water samples, uses the ordinary unsteered raft/seated camera and saves84 actual
1280x720 player-backbuffer frames.123 recorded raft poses span0.4..43.832s.
The editor exits0, and both exact live cooks are suspended/resumed successfully
through their retained handles. No saved map, asset or profile changes.

At capture080, world42.442681s/game347, twelve new native complex-terrain rays
are independently intersected with the exact candidate ground AND retained cap.
All twelve reproduce actor and hit position within the unchanged0.1cm gate;
maximum error0.000281232cm. Native face indices are not treated as source indices.
Game-thread rays and the last rendered player backbuffer are not GPU-fenced,
nor do these rays include water refraction or crew occlusion.

Four upper/background rays hit DEM-authority ground. The eight rays across the
foreground jagged mass all hit the **retained cap**: four original-return roof
triangles, slopes58.696..76.636degrees, and four vertical inferred closing walls.
This is different from the earlier8330 foreground diagnosis. Changing only the
new registered-ground flanks will not fix this downstream mass. Nor can merely
beveling its closing walls remove steep roof triangles between original points.

![Actual player frame080](downstream-cap-provenance/player-080.png)

The new41.687s movie fully decodes to1251 frames at1280x720, with68 exact adjacent
duplicates and lastPTS41.666667s. The inspected40s frame still shows the spikes
and broad smooth whitewater bands. Encoded30Hz is not game FPS. Original movie
SHA256: `54a82215f718e9f0289ecc433da0d3a9605c62e769fafd9b26ad6f3863b1bc7c`.

## Original point evidence, not automatic rock classification

The new source audit examines18 unique roof anchors used by the eight cap hits.
It identifies nearby lower original returns within an explicit0.3m diagnostic
radius, then reopens and hash-checks all four retained original LAZ tiles.
All26 requested original IDs reproduce XYZ and classification EXACTLY after the
original EPSG6418-to32610 transformation and NAVD88 US-survey-foot conversion.
LAS point indices, flight/source IDs, pulse return counts, timestamps and other
available flags are retained. No nearest-point substitution, source movement,
classification change or new download is involved.

All18 selected anchors are class1 (unclassified). One example, source685469,
is return1/2 at local[-21.551864,19.801981,9.097892]m. Source685288 is1.516078m
lower and0.226595m away horizontally; it is return2/2, but its GPS timestamp is
different. These are NOT the two returns of the same laser pulse. The recorded
same-timestamp/source/scanner-channel neighbourhood search does not find that
first point's second return. Missing siblings are explicitly reported, not
invented or matched by proximity. Other tall anchors are single returns.

Consequently, a blanket first-return filter or flattening captured anchors
would be unjustified. Lower nearby observations can indicate layered surfaces,
occlusion, sharp rock or source uncertainty; they do not certify vegetation or
an alternative rock surface. The source cloud omits no pulse fields permanently:
they are recoverable from the preserved original LAZ even though the convenient
derived NPZ contains only XYZ/classification and terrain-mask fields.

The original aerial was inspected again, but its2022 pixels versus2019 LiDAR,
roughly0.425m image sampling and existing3m registration uncertainty cannot resolve
these sub-metre semantic ambiguities. No new reference-video observation or
licensing claim is made. Captured source data remain immutable.

## Next bounded reconstruction action

Use these exact cap triangles and original IDs to review the cap's interpreted
source selection and connectivity against local imagery/point structure. Treat
any revision as a new interpreted surface, retaining the old cap and all raw
observations. Do not repeat the generic actor-identification capture, assume
every class1 point is rock, or keep modifying the unrelated foreground ground.
A justified revision must update the shared cap/terrain union, collision and
hydraulic bed together, then reach normal playable South Fork incrementally.
Source-exact roof vertices and closed topology alone are not visual acceptance.

## Validation and continuing jobs

130 focused Python tests PASS, including the new exact-source/nearby-return
controls and existing paired-play gates. PowerShell controls pass for exact
dual-cook identity, confined paths, every numbered player capture and new scoped
terrain-pixel arguments. Invalid/missing pixel pairs, coordinates outside the
viewport and capture indices outside the series are rejected before pausing any
process. Ordinary launches get no ray diagnostics. No C++ change or new engine
build is claimed; this run exercises the existing rebuilt game modules.

Baseline9650/9700/9750/9800 and candidate150/200s each pass BOTH full-state and
artificial-bank audits. All86,720 artificial-bank cells remain exactly dry;
neither cook is settled or accepted. Same jobs13584/startUTC12:17:39.4321093Z
and30276/startUTC13:46:11.8084132Z continue, no duplicate cooks or restarts.
Next baseline9850/local17000 and candidate250/local5000 need their completion
markers and BOTH audits. Captures still use the already verified50s candidate,
not newly cooked unaudited fields.

Saved FullReach SHA256 remains
`c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`;
installed4950s flow and the five South Fork launch contracts remain unchanged.
Troublemaker is still not a menu scenario. Latest ordinary24.937420FPS/
p9549.3295ms still FAILS30FPS. Nonlinear runtime remains OFF. South Fork is
unfinished; Colorado, Pacuare and Futaleufu remain queued in that order.

Durable evidence: [source rays](downstream-cap-provenance/source-rays.json),
[original pulse metadata](downstream-cap-provenance/original-pulses.json),
[play report](downstream-cap-provenance/play-report.json),
[process receipt](downstream-cap-provenance/process-report.json), and
[complete decode](downstream-cap-provenance/decode-report.json).
