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
        ('Bienvenidos','unresolved','Resolve which named access-point rapid the catalog means','II+',
         'Guide has two Bienvenidos; lodge map calls its entry III. Do not silently choose the first name match.'),
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
    add('futaleufu','Asleep at the Wheel','hole','Avoid the centre-bottom hydraulic using the right passage',
        'https://www.whitewaterguidebook.com/chile/futaleufu-river-inferno/',
        'Upstream of Terminator and outside the current crop; do not alias an existing Terminator feature',
        source_grade='III',source_flow_scope='Guide class differs from III-IV catalog; flow and raft context must be compared')
    for name in ('Lava Canyon','Green Mile','Miracle Canyon'):
        add('chilko',name,'continuous','Maintain control through linked waves and turns without a reset',CHILKO,
            'Named reach scope and exact boundaries unresolved; the travel account is not a feature-by-feature survey',
            location_evidence='Published reach names only',
            source_flow_scope='Do not infer a numeric grade for entries whose catalog says guide review required',
            aggregate_reach=(name=='Lava Canyon'))
    return entries
