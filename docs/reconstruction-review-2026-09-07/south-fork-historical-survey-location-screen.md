# Provisional historical survey locations

September 26, 2026. **Supporting registration work, not playable delivery.**

The [screened source](south-fork-historical-survey-20260926.md) endpoints cannot
be used as scene coordinates directly: the scene declares EPSG:32610, while
the source table says NAD27 UTM. Under a regional zone-10N hypothesis, the
computed shift is about 216.7 m. Original source metadata remains unchanged.

Using the hashed NOAA NADCON5 grid and explicit transformations, projection
onto the preserved 33.334 km route gives these **approximate site windows**:

| Site | Route station, upper to lower (km) | Endpoint distances to route (m) |
| --- | --- | --- |
| CB-G1 | 2.959-3.249 | 34.61 / 6.91 |
| CB-G2 | 6.704-6.881 | 11.82 / 0.53 |
| CB-G3 | 14.855-15.046 | 18.06 / 8.53 |
| CB-G4 | 27.588-27.741 | 18.90 / 2.18 |

These are nearest-segment projections of site endpoints, **not individual
transect coordinates**. Distance from a river centreline is not a registration
error for a bank endpoint. Do not snap survey points to the centreline or
reinterpret them as rapid identities.

## Reproducibility and limits

`physics/scripts/screen_south_fork_historical_survey_locations.py` refuses an
unexpected grid hash, disables network fallback and ballpark transformations,
and records route/source hashes plus both explicit pipelines in the
[receipt](south-fork-historical-survey-location-screen.json).
Four projection tests pass, including interpolation, endpoint clamping,
degenerate segments and invalid input rejection.

The selected operations advertise 0.15 m and 4 m accuracy; these are not source
survey accuracy estimates. The second operation is an explicitly selected
fallback, not the best available operation: the California refinement grid is
absent, and the scene's WGS84 realization/epoch is unspecified. Round-trip
closure is 2.80-3.33 mm, **failing the diagnostic 1 mm check**, retained as false
in every endpoint record. No precision gate was claimed passed.

Zone confirmation, individual monument ties, vertical registration, survey
dates/flows and estimated readings still need resolution. No bathymetry,
render mesh, collision, cooked field or default solver was changed. The other
session's ongoing bed/cook work was preserved; no competing engine run started.

Method background: [NOAA's coordinate transformation service](https://geodesy.noaa.gov/web_services/ncat/index.shtml).
