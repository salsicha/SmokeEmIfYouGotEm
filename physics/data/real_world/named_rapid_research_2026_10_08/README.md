# Named-rapid research, 2026-10-08

One file per run, compiled from online sources on 2026-10-08. Each rapid lists:
- name and aliases;
- published chainage from every source (river miles or km), with the
  recommended value;
- class as reported by each source;
- a one-line description of its features, in our own words;
- a position (sourced point or `derived`, with the method and uncertainty);
- sources with their rights;
- confidence and conflicts.

These are review evidence, not surveyed geometry or guide-approved lines.

| File | Run | Rapids | Main position sources |
| --- | --- | --- | --- |
| `south_fork.json` | Chili Bar to Salmon Falls | 46 (22 new) | American Whitewater feature points, River Brain |
| `colorado_rm000_088.json` | Lees Ferry to Phantom Ranch | 50 | USGS GCMRC River Rapids layer (public domain), GNIS |
| `colorado_rm088_280.json` | Phantom Ranch to Pearce Ferry | 93 | USGS GCMRC River Rapids layer, OSM/GNIS |
| `futaleufu.json` | El Limite to El Macal (game run: Rio Azul bridge to the Pasarela) | 61 | OSM nodes upstream; GoRafting km mapped onto OSM relation 9751030 |
| `chilko.json` | Chilko River Lodge to the Taseko junction | 13 | BC Whitewater map points, OSM/CanVec, BC Geographical Names |
| `pacuare.json` | Tres Equis to Siquirres | 32 (17 new) | GoRafting km mapped onto OSM relation 12000489 |
| `zambezi.json` | Boiling Pot to Mukuni Beach | 44 | Derived from satellite whitewater and landmarks (no published rapid coordinates exist) |

Merged so far by `physics/scripts/merge_named_rapid_research.py`: the 20
placeable new South Fork rapids. `add_researched_rapid_titles.py` gave them
on-screen titles and assessment trials on the FullReach map. Second Helping and
Cornholio have no published chainage and are not placed.
