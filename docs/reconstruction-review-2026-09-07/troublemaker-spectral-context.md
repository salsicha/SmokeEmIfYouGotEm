# Troublemaker cap: independent infrared context

September24,2026. New source interpretation evidence, not a river delivery.
No captured XYZ, point class, cap topology, collision, hydraulic bed, water field
or normal-play asset changed. South Fork remains first and unfinished.

## Acquisition and limits

The current [USGS NAIP service](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer?f=pjson)
supports four-band imagery and describes downloadable NAIP orthoimagery as
public domain. Exact spatial query returns only the already known
`m_3812009_se_10_060_20220721` raster for this area, acquired2022-07-21,
0.6m, USDA-FSA-APFO, CNIR, NAD83/UTM10N. No closer-to-2019 acquisition was
found in this service; this is not a claim that other archives contain none.

Unlike the previous natural-colour export, this bounded intake acquires all
four bands (red/green/blue/NIR) with `None` rendering rule and nearest-neighbour
resampling, locked to OBJECTID21979.72x48m window,120x80 pixels,0.6m output,
EPSG32610. The returned catalog polygon covers the entire requested rectangle;
TIFF bounds/CRS/count/shape and every band's valid-data mask are checked.
Provider JSON, exact URLs, hashes and original TIFF bytes are preserved.
The image is a resampled digital-number export, not calibrated reflectance.
3m existing registration uncertainty and2019/2022 date difference remain.

Acquisition: `physics/scripts/fetch_troublemaker_spectral_window.py`;
raw receipt: `tmp/troublemaker-spectral-source-20260924/manifest.json`.
Analysis: `physics/scripts/audit_troublemaker_spectral_context.py`;
report/figure: `tmp/troublemaker-spectral-context-20260924/`.
Small raw TIFF, provider responses, manifests, report and inspected figure are
also preserved with hash-verified copies in
[durable evidence](troublemaker-spectral-context/). Raw TIFF SHA256
`ec03a339263036147c7b8f11ea2d47c3f381c74a555b25efb80eea479e5eed61`;
analysis report SHA256
`4f0fe30a30a80f32d328b4219dfa920aee027ffad8f27497d733167c5cc3fc31`.
Four unit tests pass: unsigned arithmetic, invalid denominators/data, zero
radius and inclusion of pixel squares intersecting the uncertainty disk.
Initial plotting failed because sandbox access hid the existing matplotlib
package; the same analysis succeeded with read access to those dependencies.

## Result tied to actual diagnosed faces

The source cap hash and previously verified native/source camera rays are
checked before sampling. All8diagnosed faces are retained. At each hit, report
the nominal digital-number NDVI and every pixel intersecting the full3m disk;
do not pick the nearest favourable pixel or infer surveyed vegetation borders.

| Source triangle | Nominal NDVI | 3m disk min | 3m disk median | 3m disk max |
| --- | ---: | ---: | ---: | ---: |
|2342|0.3854|-0.0464|0.3575|0.4927|
|2432|0.1966|-0.5200|0.0370|0.4927|
|1137|0.1965|-0.0947|0.1214|0.4927|
|2581|0.1266|-0.1597|-0.0151|0.4927|
|6225|-0.0431|-0.5200|-0.0435|0.3846|
|6217|0.1014|-0.5200|0.0653|0.4836|
|6222|0.1966|-0.5200|0.0286|0.4927|
|6315|-0.0681|-0.3766|-0.0681|0.1585|

Inspected original-band plot shows strong NIR response on the western/northern
extension, contrasting with the eastern pale core. This strengthens the
vegetation hypothesis from natural colour, but all8target disks contain mixed
values across zero. It does NOT establish which2019return is vegetation,
bare rock under vegetation, shadow, water, or another surface. No NDVI threshold
was tuned into an automatic selection or permission to delete/flatten faces.
The prior rejected local-outlier fitting remains rejected.

## Other reference access

Browser runtime failed before opening a page with `failed to write kernel
assets ... (os error3)`. No browser input or new video-frame observation.
[Garden Betty's primary trip account](https://gardenbetty.com/troublemaker-on-the-american-river/)
reports end-of-June1600cfs and its2013comment chronology; linked images could
not be fetched. These do not establish exact capture dates or calibration.
[Dreamflows' photo page](https://www.dreamflows.com/American/troublemaker.wavewheel.lg.php)
explicitly identifies Gunsight Rock and credits Chris Shackleton, copyright2006,
all rights reserved. The photo itself also could not be fetched. No image
download, shipping license, visual identification or point registration is
inferred from these text pages.

## Next reconstruction decision

The western extension cannot honestly remain treated as semantically certified
rock merely because its XYZ reproduces unclassified returns. Conversely this
spectral result cannot justify cutting it away. A coherent interpreted envelope
needs fixed-landmark boat/bank-height constraints with registration/occlusion
uncertainty, then the same shape must drive collision, bed and fresh flow before
normal-play integration. No new cook was launched from unchanged ambiguity.
Other water/crew/regression work remains actionable; this is not a global block.

## Browser reference access recovered — September 25

The computer-use skill's browser-first guidance enabled direct visual inspection
of three previously inaccessible references. Text-fetch cache misses persist;
ordinary in-app-browser rendering succeeds. No images were downloaded, edited,
packaged or treated as licensed game assets.

- [Dreamflows photograph and caption](https://www.dreamflows.com/American/troublemaker.wavewheel.lg.php):
  the caption identifies Gunsight Rock in the foreground. The visible exposed
  part has an angular sloping face, with water passing over/around its upper
  edge and aerated water below. The caption retains Chris Shackleton's 2006
  copyright/all-rights-reserved notice; this is not an exact acquisition date
  or discharge observation.
- [Garden Betty bank overview](https://gardenbetty.com/wp-content/uploads/2013/07/2013-07-10-16.jpg):
  several separate exposed bedrock ledges interrupt the rapid. Vegetated bank
  and foreground rock outlines are visible, with a blurred patch near the
  upper-right background. Displayed source is 520 by 390 pixels.
- [Garden Betty drop sequence image](https://gardenbetty.com/wp-content/uploads/2013/07/2013-07-10-21.jpg):
  a localized steep water face lies beside sloping/angular exposed rock at
  image right. Displayed source is 520 by 346 pixels. Its position within the
  [trip account](https://gardenbetty.com/troublemaker-on-the-american-river/)
  supplies context, not a surveyed camera pose or the identity of every rock.

These observations replace the earlier statement that no visual identification
was possible through the available tools. They do NOT register any of the eight
diagnosed cap faces to a photo. Camera intrinsics/pose, exact water level and
2019 correspondence remain unknown. The 3 m registration uncertainty is not
reduced by viewing a picture. The newly visible angular rock surfaces also rule
out treating angular appearance alone as evidence for smoothing/removal.

Next use distinct rock corners and ledge relationships to test candidate camera
registration against the preserved source, retaining occlusion and date/flow
uncertainty. Do not derive metre-scale dimensions from kayak/person pixels or
silently substitute the photo's waterline for submerged geometry. No new cook,
geometry/collision edit, playable improvement or acceptance is claimed here.

## Low-water reference lead screened — September 25 follow-up

The [American Whitewater June 29, 2009 incident record](https://www.americanwhitewater.org/accident/jun-29-2009-american-s-fork-6-chili-bar/)
links Kurt Hoge's low-water photographs through Flickr account
`40311817@N05`. The indexed record explicitly locates that rock at the play wave
**below Troublemaker itself**, not at a confirmed diagnosed cap-face landmark.
The incident date and reported incident flows are not photograph acquisition
metadata. Direct AW access returned HTTP403 and the Flickr page could not be
retrieved in this check; no photograph, exact capture date, camera registration
or reuse license was verified. Do not use this lead to lower or reclassify the
unclassified 2019 cap returns. It remains a downstream reference lead only.

The Garden Betty account and sequence were already visually reviewed above;
rediscovering them is not new coverage. No duplicate source download, geometry
edit, flow cook or playable acceptance resulted from this reference screen.

## Additional high-resolution resort views inspected — September25

The computer-use skill's browser-first fallback exposed three real gallery
links that the text fetcher represented with a transparent placeholder. All
three originals were visually inspected in the in-app browser, not downloaded:

- [Bank-height view1,2000x1333](https://www.americanriverresort.com/wp-content/uploads/2021/01/troublemaker-1-of-3.jpg):
  exposed angular ledges upstream, a building and tall conifer in the background,
  and a sloping partly wetted rock beside the raft's drop. Raft/spray obscure
  the central drop; this is not an unobstructed rock survey.
- [Overhead view2,2000x1125](https://www.americanriverresort.com/wp-content/uploads/2021/01/troublemaker-2-of-3.jpg):
  a central elongated fractured rock, a smaller adjacent rock separated by
  water, broad fractured ledges toward image lower-right, and opposite-bank
  ledges, vegetation and a small gravel/sand opening. Exposed outlines offer
  candidate fixed landmarks; foam edges and the waterline do not.
- [Bank-height view3,1936x1296](https://www.americanriverresort.com/wp-content/uploads/2021/01/troublemaker-3-of-3.jpg):
  an upstream boulder garden and a rounded/sloping partly submerged foreground
  rock, with substantial raft/spray occlusion and a building/conifer backdrop.

The [hosting page](https://www.americanriverresort.com/adventures/whitewater-rafting-on-the-american-river/troublemaker)
identifies Troublemaker and displays a copyright/rights-reserved footer. Its
`2021/01` asset path is NOT verified acquisition metadata. Exact capture dates,
discharges, camera poses/intrinsics and reuse rights remain unverified. No
permission to package these images is inferred. The three photographs must not
be presumed simultaneous or treated as calibrated stereo.

Compared the overhead image visually with the retained registered
`troublemaker-spectral-context/spectral-context.png`. The0.6m NAIP context and
different water/occlusion conditions do not yet establish unique point matches
for the diagnosed cap faces. No homography, metre-scale dimension or reduced
registration error is claimed. Next identify at least four well-distributed
exposed-rock correspondences and independent held-out landmarks; model relief
and camera projection explicitly rather than fit a waterline to the cap.

The [All-Outdoors aerial article](https://www.aorafting.com/blog/aerieal-videos-high-flows-on-the-south-fork/)
labels its Troublemaker flyover26,000CFS on February7. It is a high-flow lead,
not low-water face coverage; the video was not visually inspected this pass.
No new geometry, collision, field cook, game asset or acceptance status changed.
