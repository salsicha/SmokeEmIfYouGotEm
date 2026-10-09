"""Source-linked construction requirements, NOT invented playable coordinates.

Short factual indexing only: no copied guide images, maps or route prose.
Real measurements, alternative lines and unresolved identities remain explicit.
"""
GC='https://gorafting.com/united-states/arizona/grand-canyon/'
PAC='https://gorafting.com/costa-rica/pacuare-river/'
LODGE='https://rioslodge.com/wp-content/uploads/Pacuare-River-Map.pdf'
CHILKO='https://www.mensjournal.com/travel/chilko-river-north-america-longest-stretch-whitewater/'

# name | family | guide decision | comparison-specific failure/recovery | URL suffix
COLORADO='''Badger Creek|hole|Enter beside upper-right hydraulic, then square the train|Entry avoidance rather than mandatory alternating turns|badger-creek-rapid/
Soap Creek|hole|Use post-2015 right-centre entrance, picking wave and hole gaps|Do not recreate the obsolete pre-flood centre channel|soap-creek-rapid/
House Rock|wall|Build rightward momentum against the leftward current before bottom holes|Late ferry must carry toward the left hydraulics; evaluate downstream recovery|house-rock-rapid/
Georgie|continuous|Square the lateral/wave, then clear the lower-right pin rock|Preserve the low-water seam alternative; test actual contact and high-side|georgie-rapid-grand-canyon/
Sockdolager|train|Maintain a square centre-wave approach between flanking holes|A broad direct line is legitimate; test loss of angle, not forced slalom|https://gorafting.com/?p=17458
Grapevine|continuous|Pass entrance rocks, move inward, then left of the lower centre-right hole|Separate early rock clearance from exit-hole avoidance|grapevine-rapid/
Horn Creek|slalom|Choose a horn entrance and move left behind the right horn|Low-water right/centre hazards and left-wall clearance both constrain the move|horn-creek-rapid/
Granite|wall|Control angle through opposing laterals while resisting the right-wall push|Avoid bottom hydraulic on its right; verify this does not drive into cliff collision|granite-rapid/
Hermit|train|Keep square through the large wave train|Retain legitimate edge bypasses; larger cited waves above 10000 cfs are not an 8000-cfs target|hermit-rapid/
Crystal|continuous|Avoid entry hydraulics and continue positioning around the downstream rocks|Right and left alternatives exist; clearing the first hole must not end the test|crystal-rapid/
Bedrock|slalom|Time the move right of the island without bouncing off the right bank|A missed move enters the left eddy; assess exit and island pin/high-side response|bedrock-rapid/
Upset|hole|Choose a side of the bottom hole and manage the preceding lateral|Preserve both side routes; evaluate retention and the downstream runout|upset-rapid/
Lava Falls|continuous|At lower releases, link ledge-hole avoidance, V-wave angle and the lower waves|Different high-flow line; a single centreline exit cannot validate the sequence|lava-falls-rapid/'''


def definitions(axes):
    entries={}
    def add(river,name,family,decision,source,review,**extra):
        entries[river,name]=dict(family=family,decision=decision,source=source,
            successful_route_width=axes[family][0],steering_timing=axes[family][1],
            mistake_consequences=axes[family][2],recoverability=axes[family][3],
            construction_review=review,route_coordinates=None,
            source_check='Qualitative source identified; playable geometry and flow-matched outcomes still required',**extra)
    for line in COLORADO.splitlines():
        name,family,decision,review,suffix=line.split('|')
        add('colorado',name,family,decision,suffix if suffix.startswith('https:') else GC+suffix,review,
            location_evidence='USGS georeferenced 2021 construction profile; not exact rapid boundaries',
            source_flow_scope='Flow-dependent guide description; no assumed equivalence of 1-10 and I-VI scales')
    add('colorado','Unkar','wall','Resist the current carrying toward the cliff',
        'https://www.kaibab.org/kaibab.org/show_day.php?day=6&trip=1997A',
        'Primary trip observation is from 1997 with uncertain flow; confirm modern feature geometry before fixing a precise line',
        location_evidence='USGS georeferenced construction profile',source_flow_scope='Trip flow not established')
    pacuare=[
        ('Bienvenidos','train','Read the entry wave train below Tres Equis','II+',
         'Resolved using the lodge PDF: after Tres Equis and before Linda Vista, matching guide km 3.33, '
         'not the separate km 0.26 rapid above Tres Equis. Lodge/catalog III versus guide II+ remains a discrepancy.'),
        ('Pyramid Rock','slalom','Choose the shallow left channel','II',
         'Guide describes a rock changed in 2006; lodge map/catalog say III. Preserve the class discrepancy.'),
        ('Pele El Ojo','slalom','Centre approach, then move right of left boulders','III','Requires a timed move away from the boulder field.'),
        ('Bobo Falls','unresolved','Resolve the lower-run Bobo identity before assigning hazards','uncertain',
         'Lodge PDF visually checked: Bobo III lies below the lodge/gorge entrance and above Rodeo. '
         'AVCostaRica independently lists lower-run Bobo III. Modern guide Bobito II is a candidate alias, '
         'not proven; its Bobito Falls tributary is not a mainstem rapid. Never transplant Upper Pacuare Class V.'),
        ('Rodeo','slalom','Left-centre approach, then ferry behind the central rock','III','Verify the second move and downstream recovery.'),
        ('Cimarrones','wall','Move from left toward right','II','Catalog III-IV conflicts with the current guide and lodge III.'),
        ('Wall of Sorrow','unresolved','Reconstruct the post-2021 feature before assigning a mandatory line','III',
         'Lodge/catalog IV conflicts with current guide III; scout description alone does not define obstacle geometry.'),
        ('Dos Montanas','continuous','Link left drop, right-of-rocks passage, then left exit','IV','Use whole two-part bounds and verify the linked moves.'),
        ('Las Ranitas','hole','Move right from left-centre to avoid the left hydraulic','II','Lodge/catalog III conflicts with guide II.'),
    ]
    for name,family,decision,grade,review in pacuare:
        add('pacuare',name,family,decision,LODGE if name=='Bobo Falls' else PAC,review,
            alternative_source=LODGE,source_grade=grade,
            location_evidence='Published guide order/kilometres; exact current-map registration not yet established',
            source_flow_scope='Qualitative water levels, not a verified match to the game 45 m3/s')
    entries['pacuare','Bienvenidos'].update(guide_km=3.33,
        location_identity='Lower-run rapid between Tres Equis and Linda Vista; not San Martin Bienvenidos',
        identity_sources=[PAC,LODGE])
    entries['pacuare','Las Ranitas'].update(guide_km=24.5,
        location_evidence_file='physics/data/real_world/pacuare_river_costa_rica/review/highway_bridge_registration_2026_10_08.json',
        location_status='bridge_bracketed_search_alternatives_not_verified_rapid_boundaries',
        location_evidence='Dos Montanas and the two captured Highway 32 bridge crossings bracket the guide point. '
                          'Retain both span interpretations, not an averaged point or current-map station.',
        geographic_acceptance='unresolved', boundary_lon_lat=None,
        runtime_placement_authorized=False)
    add('futaleufu','Asleep at the Wheel','hole','Avoid the centre-bottom hydraulic using the right passage',
        'https://www.whitewaterguidebook.com/chile/futaleufu-river-inferno/',
        'Upstream of Terminator and outside the old crop, but downstream of the Rio Azul confluence '
        'inside the full route. Reject the historical catalog-order slot on the Azul tributary; '
        'do not alias an existing Terminator feature or turn a source-distance span into rapid bounds.',
        source_grade='III in Whitewater Guidebook; IV in GoRafting',
        source_flow_scope='Guides differ; neither establishes a numeric flow matching the game',
        location_evidence_file='physics/data/real_world/futaleufu_river_chile/review/guide_distance_locations_2026_10_08.json',
        location_status='mainstem_source_distance_estimates_not_verified_rapid_boundaries',
        alternative_source='https://gorafting.com/chile/futaleufu-river/')
    for name in ('Lava Canyon','Green Mile','Miracle Canyon'):
        add('chilko',name,'continuous','Maintain control through linked waves and turns without a reset',CHILKO,
            'Named reach scope and exact boundaries unresolved; the travel account is not a feature-by-feature survey',
            location_evidence='See source-indexed Chilko location ledger; no accepted rapid endpoints',
            source_flow_scope='Do not infer a numeric grade for entries whose catalog says guide review required',
            aggregate_reach=(name=='Lava Canyon'))
    chilko_evidence='physics/data/real_world/chilko_river_bc/observed_rapids/catalog_location_evidence_2026_10_06.json'
    for name in ('Lava Canyon','Green Mile','Miracle Canyon'):
        entries['chilko',name].update(location_evidence_file=chilko_evidence,
            geographic_acceptance='unresolved', boundary_lon_lat=None,
            source_check='Names attested; actual runtime coordinates expose existing geographic label conflicts. '
                         'Do not use existing gameplay labels as geographic anchors.')
    entries['chilko','Green Mile'].update(
        location_status='sequence_bracket_only',
        location_evidence='2006 trip sequence places Green Mile after Bidwell and before White Mile; '
                          'BC Whitewater map points bound the search interval, not the rapid itself',
        source_marker_bracket_lon_lat=[[-123.821211713868,51.91166777179728],
                                      [-123.80243226946493,51.93985537976434]])
    entries['chilko','Miracle Canyon'].update(location_status='name_attested_location_unresolved',
        location_evidence='2025 eyewitness account names Miracle Canyon but supplies no coordinates. '
                          'No evidence establishes equivalence to the downstream basalt box canyon.')
    entries['chilko','Lava Canyon'].update(
        location_status='aggregate_rafting_reach_distinct_from_geographic_point',
        location_evidence='Official BC geographic Lava Canyon lies upstream of the Bidwell marker; '
                          'do not interchange it with the commercial run name or downstream basalt slot.')
    researched(entries, add)
    return entries


def researched(entries, add):
    """Catalog rapids added from the 2026-10-08 research and not yet built.

    Family follows the researched feature tags. The decision is the researched
    one-line description, which names the feature but does not prescribe a
    verified line.
    """
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    catalog = json.loads((root / 'physics/data/real_world/named_rapid_source_catalog.json').read_text(encoding='utf-8'))
    urls = {s['source_id']: s['url'] for s in catalog['sources']}
    rivers = {'south_fork_american_chili_bar': 'south-fork', 'colorado_river_grand_canyon_rowing': 'colorado',
              'pacuare_river_costa_rica': 'pacuare', 'futaleufu_river_chile': 'futaleufu',
              'chilko_river_lava_canyon': 'chilko', 'zambezi_batoka_gorge': 'zambezi'}
    for river in catalog['rivers']:
        key = rivers[river['river_id']]
        for rapid in river['rapids']:
            if (key, rapid['name']) in entries or not rapid.get('research_source_ids'):
                continue
            tags = set(rapid['feature_tags'])
            family = ('surf' if 'surf_wave' in tags and len(tags) <= 2 else
                      'hole' if tags & {'hole', 'pourover', 'ledge'} else
                      'continuous' if 'continuous_whitewater' in tags else
                      'slalom' if tags & {'boulder', 'boulder_garden', 'island_split', 'pin_hazard'} else
                      'wall' if tags & {'constriction', 'bend', 'lateral'} else 'train')
            add(key, rapid['name'], family, rapid.get('research_summary') or rapid['name'],
                urls[rapid['research_source_ids'][0]],
                'Researched 2026-10-08 at its published station; the line and flow-specific behaviour are not yet reviewed',
                location_evidence='Researched position: ' + ('derived' if (rapid.get('research_position') or {}).get('derived')
                                                              else 'source point' if rapid.get('research_position') else 'chainage only'),
                source_flow_scope='Not matched to the game flow',
                location_evidence_file='physics/data/real_world/named_rapid_research_2026_10_08/README.md',
                geographic_acceptance='unresolved', boundary_lon_lat=None)
