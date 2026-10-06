# Field evidence follow-up

The UC Davis researchers' [South Fork field measurements](https://pasternack.ucdavis.edu/falls/aircontent/field.htm)
identify four sampled jumps: Upper Chili Bar, Upper Meatgrinder, Little Maya and
First Threat. Reported mean air fractions are 25.59%, 18.06%, 23.24% and 58.28%,
respectively. These are local probe measurements, not visible foam area, and
must not become shader coverage percentages. The page's final distribution
interpretation appears inconsistent with its summary table; do not calibrate
quantile targets from that paragraph without checking the underlying paper.
Copyright is explicitly reserved. Reference only; no photos imported as assets.

The [UC Water Resources Center report](https://ciwr.ucanr.edu/files/169350.pdf),
printed pages 19–20 (PDF pages 25–26), was visually inspected using the PDF
workflow after web rendering failed. Its pictured feature is **Shady Jump on
the upper South Fork**, not Troublemaker. The study describes highly variable
bed and water topography, but supplies no georeferenced Troublemaker bathymetry
in these pages. It cannot replace the explicitly inferred bed of this candidate.

The [authors' project index](https://pasternack.ucdavis.edu/research/projects/waterfalls)
links further mapping and aeration studies. These are useful leads for the
water's behavior and source-specific calibration, not evidence that all twenty
rapid layouts have been reconstructed. A new search has not yet produced an
importable surveyed Troublemaker riverbed. That is a search result limitation,
not proof that such data does not exist. No external contact was made.

The original USDA orthophoto and USGS captured terrain remain the geometric
sources. The PDF review prevented transferring a different rapid's shape to
Troublemaker; it did not authorize invented measured boulder coordinates.

## Dated discharge context — September 7 continuation

The Troublemaker atlas is explicitly locked to USDA NAIP raster
`m_3812009_se_10_060_20220721`, acquired July 21, 2022. The
[USGS daily-value API](https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?f=json&monitoring_location_id=USGS-11444500&parameter_code=00060&time=2022-07-21T00%3A00%3A00Z%2F2022-07-22T00%3A00%3A00Z&limit=10)
returns an approved daily mean of **584 ft³/s (16.537 m³/s)** for that date at
USGS-11444500, versus the diagnostic cook's chosen 1,600 ft³/s (45.307 m³/s).
The date-matched value is upstream daily context, **not instantaneous flow in
the image**. Exposure time, travel time and contemporaneous rapid stage remain
unknown, so no cook forcing or captured-source authority flag was changed.

The [gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11444500/)
lists daily records but no continuous data in this presentation. Do not infer
that every other archive lacks finer records. Its ground altitude is in NGVD29
and is not a measured rapid water stage. The API query schema identifies 00003
as the mean statistic; raw observation values and stable time-series/date keys
are retained in [the extracted reference record](naip-date-discharge-context.json).

USGS-produced data are public domain under its
[copyright policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits),
with credit requested; third-party images are an exception and were not copied.
This source context improves provenance, not geometric or visual acceptance.

## Viewed video dates

The public player frame review now identifies the user's trip title-card date
as June 24, 2016. Its upstream approved daily mean is 748 ft³/s. The bank-side
reference titled July 15, 2022 has a daily mean of 652 ft³/s. Both records were
retrieved from the same USGS daily series, selecting the exact date rather
than the next-day record also returned by the inclusive interval query.
[Extracted observations and exact API URLs](video-date-discharge-context.json)
retain the identifiers. These means are neither video-time discharge nor
measured Troublemaker stage. The chosen diagnostic 1,600 ft³/s forcing remains
unchanged; do not rerun the flow at a daily average merely to match a title date.
