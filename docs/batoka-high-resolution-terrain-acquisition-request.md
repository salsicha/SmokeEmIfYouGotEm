# Batoka Gorge High-Resolution Terrain Acquisition Request

## Purpose

Request access to existing high-resolution terrain and imagery for an open-source, physically based whitewater rafting game. The immediate use is a photoreal visual environment for the Zambezi River from Boiling Pot to Mukuni Beach. Survey terrain will remain separate from custom C++ water, GeoClaw comparison, collision, raft contact, hazards, and gameplay authority until independently reviewed.

## Public Contact Routes

- Zambezi River Authority: `info@zambezira.org`
  - Official contact page: https://www.zambezira.org/contact-us
  - Batoka HES document index: https://zambezira.org/hydro-electric-schemes/batoka-hes-project
- Studio Ing. G. Pietrangeli: `info@pietrangeli.it`
  - Official contact page: https://www.pietrangeli.com/contact-us/

The request has not been sent. A project owner should confirm the sender identity, organization, reply address, and willingness to accept any quoted license or data cost before outreach.

## Email Draft

**Subject:** Request for Batoka Gorge LiDAR / photogrammetry coverage and game-derivative licensing

Hello,

We are developing an open-source, physically based whitewater rafting simulator and are building a photoreal visual environment for the Zambezi River through Batoka Gorge. We are seeking terrain and imagery covering the Boiling Pot put-in to Mukuni Beach take-out.

Our current public terrain is Copernicus DEM GLO-30. It is adequate for regional alignment but cannot resolve the gorge walls, ledges, gullies, talus, banks, or named-rapid surroundings needed for a lifelike result. Published project documents indicate that a 0.3 m LiDAR DTM and high-resolution drone photogrammetry were produced for Batoka engineering work. Could you advise whether either survey covers all or part of our requested reach and whether access or a commercial derivative license is available?

Requested WGS 84 review bounds:

- West: `25.826935535974975`
- South: `-18.02077352349982`
- East: `26.01842667723117`
- North: `-17.90811477650018`
- Route: Boiling Pot to Mukuni Beach, approximately 30 km station length

Preferred products, where available:

1. Classified ground point cloud or bare-earth DTM.
2. DSM, orthophoto, or source-image mosaic with acquisition metadata.
3. Breaklines, channel centerline, cross sections, survey control, and coverage polygon.
4. Horizontal CRS, coordinate epoch, vertical datum, geoid model, point density or raster cell size, void policy, acquisition date, sensor, and accuracy statement.

We need explicit terms for:

- commercial desktop, console, handheld, and VR game use;
- creation and distribution of optimized terrain derivatives in packaged games;
- public screenshots, video, trailers, documentation, and guide-review evidence;
- team storage, backups, build systems, and contractor access;
- attribution requirements;
- whether raw survey data may be redistributed, must remain private, or may be represented only by non-reversible derivatives;
- geographic, platform, seat, revenue, and term limits;
- quote, payment, and delivery process.

The open-source repository can keep raw licensed survey data outside version control if redistribution is restricted. We can publish only code, manifests, provenance, and permitted non-reversible game derivatives.

Thank you for any guidance or referral to the appropriate survey custodian.

## Technical Acceptance Checklist

- Coverage polygon intersects the complete requested route and identifies gaps.
- Horizontal CRS and coordinate epoch are explicit and transformable to WGS 84 / UTM zone 35S.
- Vertical datum and geoid model are explicit.
- Bare-earth and surface products are distinguished.
- Resolution, point density, horizontal accuracy, and vertical accuracy are documented.
- Water voids, cliff interpolation, vegetation filtering, and edge artifacts are documented.
- Acquisition date, sensor, control network, and processing lineage are supplied.
- License allows optimized game derivatives and public visual media.
- Raw-data redistribution and source-control restrictions are explicit.
- Attribution text and placement are explicit.
- Cost, delivery size, file format, and support contact are explicit.
- A geospatial reviewer signs off before any Unreal import.

## Commercial Stereo Fallback Specification

If the engineering surveys are unavailable, request quotes for a new or archival stereo-derived product over the same bounds:

- target DTM/DSM posting: `1-2 m` or better;
- orthorectified imagery: `0.5 m` or better;
- full route plus at least `1 km` lateral context on both banks;
- documented cliff/occlusion and water-void treatment;
- ground control and vertical RMSE appropriate for gorge-scale visual reconstruction;
- delivery in GeoTIFF and, if available, LAS/LAZ plus breaklines;
- commercial game-derivative, screenshot, video, storage, and attribution rights;
- raw source may remain private and excluded from the open-source repository.

No product is production-approved until rights, coverage, datum, accuracy, cliff behavior, guide alignment, and Unreal exact-camera review pass.
