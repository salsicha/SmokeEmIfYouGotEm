# Batoka Gorge High-Resolution Terrain Acquisition Request

## Purpose

Request access to existing high-resolution terrain and imagery for an open-source, physically based whitewater rafting game. The immediate use is a photoreal visual environment for the Zambezi River from Boiling Pot to Mukuni Beach. Survey terrain will remain separate from custom C++ water, GeoClaw comparison, collision, raft contact, hazards, and gameplay authority until independently reviewed.

The July 15, 2026 coverage audit separates four products that earlier notes risked conflating. The 0.3 m LiDAR terrain database in the Dam Safety Plan belongs to an approximately 120 km dam-break model from the proposed Batoka dam downstream to Lake Kariba. The approximately 5 cm eBee DSM is a separate, roughly 13 square kilometre dam-site survey. World Bank completion reporting attributes another LiDAR activity to the Kariba Dam Rehabilitation Project. None is evidence of coverage for the upstream playable reach. The only remaining engineering-survey lead with unknown and potentially relevant coverage is feasibility Vol.3, `230 GEN R SP 001`; request its report and coverage index before requesting a payload.

## Public Contact Routes

- Zambezi River Authority: `info@zambezira.org`
  - Official contact page: https://www.zambezira.org/contact-us
  - Batoka HES document index: https://zambezira.org/hydro-electric-schemes/batoka-hes-project
- Studio Ing. G. Pietrangeli: `info@pietrangeli.it`
  - Official contact page: https://www.pietrangeli.com/contact-us/
- Zambezi Watercourse Commission / ZAMWIS: `zamcom@zambezicommission.org`
  - Official programme page: https://zambezicommission.org/zamwis
  - The public ZAMWIS catalog exposes generalized basin layers and a 1 km elevation product, but no Batoka LiDAR or high-resolution terrain payload.
- World Bank project `P133380` records:
  - Project page: https://projects.worldbank.org/en/projects-operations/project-detail/P133380
  - Access to Information route: https://www.worldbank.org/ext/en/access-to-information
  - The completion report assigns the additional LiDAR to the separate Kariba Dam Rehabilitation Project; use this route to request Vol.3's record disposition and upstream coverage, not the Kariba payload.

The request has not been sent. A project owner should confirm the sender identity, organization, reply address, and willingness to accept any quoted license or data cost before outreach.

Send the technical request first to ZRA and Studio Pietrangeli. Ask ZAMCOM to check unlisted ZAMWIS holdings or identify the current survey custodian. Submit a separate World Bank Access to Information request for project `P133380` records if the direct custodians cannot provide Vol.3, its coverage index, or the underlying survey disposition. Do not request the known downstream dam-break, dam-site drone, or Kariba Rehabilitation products as substitutes for upstream game-reach terrain. Do not upload private project material or accept license terms through any portal without project-owner review.

## Email Draft

**Subject:** Request for BGHES Vol.3 LiDAR coverage index and upstream game-reach licensing

Hello,

We are developing an open-source, physically based whitewater rafting simulator and are building a photoreal visual environment for the Zambezi River through Batoka Gorge. We are seeking terrain and imagery covering the Boiling Pot put-in to Mukuni Beach take-out.

Our current public terrain is Copernicus DEM GLO-30. It is adequate for regional alignment but cannot resolve the gorge walls, ledges, gullies, talus, banks, or named-rapid surroundings needed for a lifelike result. Published feasibility documents name Vol.3, `230 GEN R SP 001 - LiDAR Topographic Survey Report`, but do not publish its footprint. Could you first provide the report and its coverage polygon or sheet index, and advise whether any associated survey covers all or part of our requested reach?

We are not asking you to treat the 0.3 m terrain used for the downstream Batoka dam-to-Lake Kariba dam-break model, the approximately 13 square kilometre 2014 eBee dam-site DSM, or Kariba Dam Rehabilitation LiDAR as upstream coverage. We are specifically trying to establish whether Vol.3 or another distinct survey includes Boiling Pot to Mukuni Beach.

Requested WGS 84 review bounds:

- West: `25.826935535974975`
- South: `-18.02077352349982`
- East: `26.01842667723117`
- North: `-17.90811477650018`
- Route: Boiling Pot to Mukuni Beach, approximately 30 km station length

Preferred products, where available:

1. Vol.3 report, appendices, coverage polygon, or sheet index.
2. Classified ground point cloud or bare-earth DTM within the requested bounds.
3. DSM, orthophoto, or source-image mosaic with acquisition metadata within the requested bounds.
4. Breaklines, channel centerline, cross sections, and survey control within the requested bounds.
5. Horizontal CRS, coordinate epoch, vertical datum, geoid model, point density or raster cell size, void policy, acquisition date, sensor, and accuracy statement.

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

## World Bank Records Request Addendum

For project `P133380`, request records sufficient to identify and lawfully acquire the survey rather than assuming that public financing makes the data redistributable:

- final or draft `230 GEN R SP 001` LiDAR Topographic Survey Report and appendices;
- survey deliverable register, coverage polygon or sheet index, acceptance record, and current custodian;
- contract clauses or data-management records governing ownership, disclosure, reuse, and redistribution;
- confirmation whether Vol.3 includes any terrain upstream of the proposed dam and, specifically, the requested Boiling Pot-to-Mukuni bounds;
- confirmation that the downstream dam-break terrain and Kariba Dam Rehabilitation LiDAR are separate from Vol.3 unless records prove otherwise;
- referral to ZRA, ZAMCOM, Studio Pietrangeli, or another custodian if the World Bank does not hold the payload.

An information disclosure is not a game-use license. Any released report, index, or data must still pass the technical and rights checklist below.

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
