"""Evidence-linked inventory of ALL indexed rapids, including absent geometry.

Input directories contain native RiverDifficulty trial receipts. The script does
not infer Class VI from failed automation or treat checkpoint resets as recovery.
Legacy variant observations do not establish a game class. Use source-matched
decision, approach, timing and recovery campaigns for that separate assessment.
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDS = {
    'south_fork_american_chili_bar': 'south-fork',
    'colorado_river_grand_canyon_rowing': 'colorado',
    'pacuare_river_costa_rica': 'pacuare',
    'futaleufu_river_chile': 'futaleufu',
    'chilko_river_lava_canyon': 'chilko',
    'zambezi_batoka_gorge': 'zambezi',
}
FLOWS = {'south-fork': '1,600 cfs', 'colorado': '8,000 cfs',
         'pacuare': '1,589 cfs (45 m³/s)', 'futaleufu': '14,126 cfs (400 m³/s)',
         'chilko': '3,284 cfs (93 m³/s)',
         'zambezi': 'Simulated discharge uncalibrated; catalogue range ≈7,063–10,594 cfs (200–300 m³/s), not a verified in-game flow',
         'zambezi-upper': '9,994 cfs (283 m³/s)'}


def norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def inventory():
    catalog = json.loads((ROOT / 'physics/data/real_world/named_rapid_source_catalog.json').read_text())
    plans = json.loads((ROOT / 'unreal/Tests/Data/rapid_assessment_reaches.json').read_text())
    lookup, owners = {}, {}
    for plan in plans:
        key = plan.get('catalog_river',plan['river'])
        if key not in lookup:
            lookup[key] = dict(plan,trials=[])
        for trial in plan['trials']:
            if (key,trial['id']) in owners:
                raise ValueError('Ambiguous catalog trial identity')
            owners[key,trial['id']] = plan['river']
            lookup[key]['trials'].append(trial)
    rows = []
    for river in catalog['rivers']:
        key = IDS[river['river_id']]
        matched = set()
        for rapid in river['rapids']:
            name = norm(rapid['name'])
            candidates = [t for t in lookup[key]['trials'] if norm(t['name']) == name]
            if key == 'colorado' and name == 'hance':
                candidates = [t for t in lookup[key]['trials'] if norm(t['name']) == 'hancemain']
            if key == 'chilko' and name == 'bidwellrapids':
                candidates = [t for t in lookup[key]['trials'] if t['id'] == 'bidwell']
            if key == 'futaleufu' and name == 'terminator':
                candidates = [t for t in lookup[key]['trials'] if t['id'] == 'terminator_core']
            if key == 'zambezi':
                candidates = [t for t in lookup[key]['trials'] if t['id'] == f"rapid_{rapid['order']}"]
            assert len(candidates) <= 1
            trial = candidates[0] if candidates else None
            if trial:
                matched.add(trial['id'])
            rows.append(dict(river=key, name=rapid['name'], catalog_class=rapid['class'],
                             master_catalog=True, trial=trial, flow=FLOWS[key],
                             assessment_river=owners.get((key,trial['id']),key) if trial else key,
                             source='physics/data/real_world/named_rapid_source_catalog.json'))
        for trial in lookup[key]['trials']:
            if trial['id'] not in matched:
                rows.append(dict(river=key, name=trial['name'], catalog_class=trial.get('catalog_class', 'Unspecified'),
                                 master_catalog=False, trial=trial, flow=FLOWS[key],
                                 assessment_river=owners[key,trial['id']],source=lookup[key]['source']))
    for trial in lookup['zambezi-upper']['trials']:
        rows.append(dict(river='zambezi-upper', name=trial['name'].replace('_', ' '),
                         catalog_class=trial['catalog_class'], master_catalog=False, trial=trial,
                         flow=FLOWS['zambezi-upper'], source=lookup['zambezi-upper']['source']))
    assert sum(r['master_catalog'] for r in rows) == sum(len(r['rapids']) for r in catalog['rivers'])
    return rows


def observations(directories):
    found = {}
    for directory in directories:
        for path in sorted(directory.glob('*/*.json')):
            if '--' not in path.stem:
                continue
            value = json.loads(path.read_text(encoding='utf-8-sig'))
            if 'outcome' not in value:
                continue
            key = (path.parent.name, value['rapid_id'], value['variant'])
            # Later command-line directories explicitly supersede earlier trials.
            found[key] = dict(value, evidence=str(path.resolve()))
    return found


def passing_track_spread(trial, lanes):
    """First downstream crossings at interior transects; NOT a safe-width proof."""
    if len(lanes) < 2:
        return None
    spans = []
    for fraction in (.2, .35, .5, .65, .8):
        station = trial['control_m'] + fraction * (trial['finish_m']-trial['control_m'])
        lateral = []
        for lane in lanes:
            samples = lane.get('samples', [])
            for a, b in zip(samples, samples[1:]):
                if a['station_m'] <= station < b['station_m']:
                    t = (station-a['station_m'])/(b['station_m']-a['station_m'])
                    lateral.append(a['lateral_m']+t*(b['lateral_m']-a['lateral_m']))
                    break
        if len(lateral) == len(lanes):
            spans.append(max(lateral)-min(lateral))
    return min(spans) if len(spans) == 5 else None


ROMAN = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI'}
# Outcomes that say something about the test rig, not the rapid.
HARNESS_FAULTS = {'physics_step_refused_not_rapid_outcome', 'start_placement_intersects_ground',
                  'checkpoint_preparation_rejected', 'checkpoint_start_mismatch', 'start_projection_unavailable',
                  'initial_water_unavailable', 'initial_surface_alignment_rejected', 'destination_water_unavailable',
                  'start_coordinate_unavailable', 'offset_start_unavailable'}
# The game resets to the checkpoint when a swimmer passes the 120 s rescue
# window; the test driver never rescues, so that reset means crew lost.
OUTCOME_TEXT = {'checkpoint_reset_not_recovery': 'crew lost (swimmers past the rescue window; the game reset the run)',
                'stalled_driver_not_proof_impassable': 'stuck (no progress for 60 s)',
                'time_limit_partial': 'ran out of time', 'left_mapped_route': 'left the mapped river'}


def evidence_fault(v):
    if v is None:
        return None
    if v['outcome'] in HARNESS_FAULTS:
        return v['outcome']
    if not v.get('finite', False):
        return 'nonfinite or unverified motion'
    if v.get('high_side_responses', 0) and v.get('assessment_protocol_version', 0) < 8:
        return 'superseded high-side input'
    return None


def checkpoint_restored(v):
    return bool(v.get('checkpoint_restores_during_trial', 0) or v.get('checkpoint_restores', 0))


def cleared(v):
    """The boat reached the exit, whatever happened on the way."""
    # Deep burials are real here (the Huacas surges hold the raft 1-4 m under
    # and its own support surface agrees), so depth alone does not void a run.
    return (v is not None and not evidence_fault(v) and not checkpoint_restored(v)
            and v['outcome'] in ('section_cleared', 'exit_with_unrecovered_crew'))


def clean(v):
    """Through the section upright, nobody out of the boat, no lasting pin."""
    return (cleared(v) and v['outcome'] == 'section_cleared' and not v.get('capsized_during_trial') and v.get('max_swimmers', 0) == 0
            and v.get('pin_seconds', 0) <= 3.)


def incident(v):
    parts = []
    if v.get('capsized_during_trial'):
        parts.append('flipped')
    if v.get('max_swimmers', 0):
        parts.append(f"{v['max_swimmers']} swimmer(s)")
    if v.get('pin_seconds', 0) > 3.:
        parts.append(f"pinned {v['pin_seconds']:.0f} s")
    return ', '.join(parts)


def describe(v):
    if v is None:
        return 'not tested'
    if evidence_fault(v):
        return f"test fault ({evidence_fault(v)})"
    if checkpoint_restored(v):
        return 'checkpoint restored; not an uninterrupted passage or recovery'
    what = ('clean' if clean(v) else ('got through, ' + (incident(v) or 'not upright at the exit')) if cleared(v)
            else OUTCOME_TEXT.get(v['outcome'], v['outcome'].replace('_', ' ')))
    if not cleared(v) and incident(v):
        what += ' after ' + incident(v)
    return what


def catalogue_range(text):
    """Parse I-VI labels only; Grand Canyon's numeric scale is not convertible."""
    numbers = [{'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}[x]
               for x in re.findall(r'\b(VI|IV|V|III|II|I)\b', text)]
    if numbers:
        return min(numbers), max(numbers)
    return None


def assess(row, data):
    trial = row['trial']
    blank = dict(criteria={}, game_class=None, hands_off='Not tested')
    if not trial:
        aggregate = row['name'] == 'Lava Canyon'
        return dict(blank, status='Reach-level entry; individual sections below' if aggregate else 'Not modeled in current playable reach',
                    rating='Not rateable', comparison='No in-game comparison', route='No complete testable section',
                    steering='Not measured', consequences='Not measured', recovery='Not measured', evidence=[])
    if trial.get('portage'):
        return dict(blank, status='Intentional mandatory portage', rating='Portage, not a navigation grade',
                    comparison='Catalogue V–VI; not a broken playable rapid', route='No intended boat route',
                    steering='Not driven', consequences='Do not infer from forced passage', recovery='Use authored portage', evidence=[])
    names = ('hands-off', 'center', 'left', 'right', 'missed-turn')
    raw = {name: data.get((row.get('assessment_river',row['river']), trial['id'], name)) for name in names}
    available = [v for v in raw.values() if v]
    faults = [f"{k}: {evidence_fault(v)}" for k, v in raw.items() if evidence_fault(v)]
    # A rig fault is missing evidence, never a verdict on the rapid.
    variants = {k: (None if evidence_fault(v) else v) for k, v in raw.items()}
    hands, center, miss = variants['hands-off'], variants['center'], variants['missed-turn']
    lanes = {k: variants[k] for k in ('center', 'left', 'right')}
    tested_lanes = {k: v for k, v in lanes.items() if v}
    clean_lanes = [v for v in tested_lanes.values() if clean(v)]
    labels = {'center': 'center', 'left': '−4 m', 'right': '+4 m'}

    # 1. How narrow and demanding the successful route is.
    spread = passing_track_spread(trial, clean_lanes)
    def lane(k, v):
        text = f"{labels[k]} {describe(v)}"
        if v and v.get('blocked_start_placements', 0):
            text += f" (its start was on the bank; started at {v.get('start_lateral_m', 0):+.0f} m)"
        return text
    route = '; '.join(lane(k, v) for k, v in lanes.items())
    if spread is not None:
        route += f'; minimum clean-track spread at five sampled transects {spread:.1f} m (not a safe-width envelope)'

    # The hands-off run: what the river does with nobody steering.
    hands_text = describe(hands) if hands else 'Not tested'
    if hands and not cleared(hands):
        furthest = max((x['station_m'] for x in hands.get('samples', [])), default=trial['start_m'])
        hands_text += f"; reached {furthest - trial['start_m']:.0f} of {trial['finish_m'] - trial['start_m']:.0f} m"

    # 2. How much timely steering and maneuvering it takes. The test driver
    # corrects toward its lane all the time; workload is not necessary timing.
    if center and center.get('elapsed_s'):
        workload = center.get('turn_command_seconds', 0)/max(center['elapsed_s'], 1)
        steering = (f"driver turn calls {100*workload:.0f}% of the center run, {center.get('guide_strokes', 0)} guide strokes, "
                    f"{center.get('crew_command_changes', 0)} crew calls, {center.get('backstroke_seconds', 0):.0f} s backpaddling")
        steering += '; observed controller workload, not a steering-timing envelope'
    else:
        steering = 'Not measured'

    # 3. What happens after a missed turn; 4. whether normal controls recover it.
    if miss and miss.get('mistake_start_s', -1) >= 0:
        after = [s for s in miss.get('samples', []) if s['elapsed_s'] >= miss['mistake_start_s']]
        deviation = max((abs(s['lateral_m']-s.get('preferred_lateral_m', 0)) for s in after), default=0)
        consequences = f"6 s with no steering at the entry: {describe(miss)}; drifted up to {deviation:.1f} m off line"
        at = miss.get('recovered_route_at_s', -1)
        resumed = at - miss['mistake_start_s'] - 6 if at >= 0 else None
        tools = []
        if miss.get('backstroke_seconds', 0) >= 1:
            tools.append(f"{miss['backstroke_seconds']:.0f} s backpaddling")
        if miss.get('high_side_responses', 0):
            tools.append(f"{miss['high_side_responses']} high-side")
        if miss.get('reflip_requests', 0):
            tools.append(f"{miss['reflip_requests']} reflip")
        used = (' using ' + ', '.join(tools)) if tools else ''
        if clean(miss):
            # Got through clean, so normal controls evidently suffice; how long
            # the driver took to settle back on its own lane is not difficulty.
            recovery = ((f"Back on line {resumed:.0f} s after steering resumed{used}" if resumed >= 1.
                         else f"Back on line as soon as steering resumed{used}") if resumed is not None
                        else f"Never fully back on line, but the boat still ran the rapid cleanly{used}")
        elif cleared(miss):
            recovery = f"Got through with normal controls, but after {incident(miss)}{used}"
        elif checkpoint_restored(miss) or miss['outcome'] == 'checkpoint_reset_not_recovery':
            recovery = 'Checkpoint reset; not recovery with normal controls'
        elif not incident(miss):
            recovery = f"Ended {OUTCOME_TEXT.get(miss['outcome'], miss['outcome'].replace('_', ' '))}; normal controls did not free it{used}"
        else:
            recovery = f"Not recovered with normal controls{used}"
    else:
        consequences, recovery = 'Missed maneuver not exercised', 'Not established'

    # Approach success counts and controller workload are observations, not
    # ordinal river classes. In particular, surviving one hands-off line does
    # not prove broad easy routes, forgiving timing or recoverable mistakes.
    criteria = {'route': None, 'steering': None, 'miss': None, 'recovery': None}
    status = 'Observation coverage complete' if all(variants.values()) else 'Incomplete evidence'
    if faults:
        status += '; test faults: ' + ', '.join(faults)
    game = None
    rating = 'Not yet established — legacy observations do not grade river class'

    if row['catalog_class'].startswith('surf'):
        comparison = 'Catalogue lists a surf wave, not a passage class'
    elif row['river']=='colorado':
        comparison = 'Not established; Grand Canyon 1–10 ratings are not converted to I–VI'
    else:
        comparison = 'Not established; source-matched decision and recovery evidence required'
    return dict(status=status, rating=rating, game_class=game, criteria=criteria, hands_off=hands_text,
                comparison=comparison, route=route, steering=steering, consequences=consequences,
                recovery=recovery, evidence=[v['evidence'] for v in available])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directories', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = observations(args.directories)
    rows = inventory()
    for row in rows:
        row.update(assess(row, data))
        detail_class = row['trial'].get('catalog_class') if row['trial'] else None
        if row['master_catalog'] and detail_class and detail_class != row['catalog_class']:
            row['catalog_class'] += ' | modeled-section catalogue: '+detail_class
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'report.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
    esc = html.escape
    sections = []
    river_summaries = []
    for river in dict.fromkeys(row['river'] for row in rows):
        body = []
        river_rows = [r for r in rows if r['river'] == river]
        playable = [r for r in river_rows if r['trial'] and not r['trial'].get('portage')]
        observed_rows = [r for r in playable if r['evidence']]
        scope = 'Observation inventory; not a continuous descent or whole-river grade'
        river_summaries.append('<tr>'+''.join('<td>'+esc(str(c))+'</td>' for c in
            (river, FLOWS[river], f'{len(observed_rows)}/{len(playable)}', scope))+'</tr>')
        for row in [r for r in rows if r['river'] == river]:
            evidence = ' '.join(f'<a href="{esc(Path(p).as_uri())}">trial {i+1}</a>' for i, p in enumerate(row['evidence']))
            cells = [row['name'], row['catalog_class'], row['rating'], row['comparison'], row['hands_off'],
                     row['route'], row['steering'], row['consequences'], row['recovery'], row['status']]
            body.append('<tr>'+''.join('<td>'+esc(str(c))+'</td>' for c in cells)+'<td>'+evidence+'</td></tr>')
        sections.append(f'<h2>{esc(river)} — {esc(FLOWS[river])}</h2><div class="table"><table><thead><tr>'+''.join(
            '<th>'+h+'</th>' for h in ('Rapid','Catalog class','In-game class','Comparison','Hands-off run',
                                    '1. Route observations','2. Steering','3. Missed turn',
                                    '4. Recovery','Coverage/status','Evidence'))+
            '</tr></thead><tbody>'+''.join(body)+'</tbody></table></div>')
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>River difficulty assessment</title>
<style>body{font:16px/1.5 system-ui;background:#f6f8fa;color:#172b3a;margin:36px}h1,h2{color:#124d67}p{max-width:1100px}
.table{overflow:auto}table{border-collapse:collapse;background:white;width:100%;font-size:13px}td,th{padding:12px;border:1px solid #cdd9df;vertical-align:top;min-width:100px}th{background:#163f53;color:white}a{color:#086f9c}</style>
<h1>Every catalogued rapid: game difficulty evidence</h1>
<p style="padding:14px;background:#fff1cd;border-left:5px solid #a56d12">ASSESSMENT_PROGRESS</p>
<p>Scope: six rivers, including both selectable Zambezi maps. Every master catalogue entry plus the detailed authored subrapids is included.
Catalogue-only markers are not reconstructed rapids. Missing geometry is explicitly not rated. Flow figures are nominal authored band discharges,
not independent flow-gauge measurements; the procedural full Zambezi has no calibrated discharge.</p>
<p>This legacy inventory preserves four kinds of observations: sampled approach tracks, controller commands, consequences of a six-second
steering omission, and recovery attempts with normal controls. It does not assign river classes. A clean hands-off run demonstrates only that
one tested approach passed without commands; it does not establish Class I, a broad successful-route envelope or forgiving timing.
Three approach lines and controller workload likewise do not establish the documented decisions of a real rapid. A class comparison requires
the separate source-matched decision campaign: genuinely different approaches, measured success and failure boundaries, early/late/absent
steering, documented hazards and completed recovery trials. Failed automation is not Class VI. Grand Canyon's numeric ratings remain on their
own scale, without conversion to I–VI. Clean means through the section upright, nobody out of the boat and no pin over 3 s.
Tests start independently at checkpoints, then use actual game physics and ordinary crew/guide commands. Cold checkpoint activation gets at most three setup attempts before failure.
The legacy test IDs “left/right” mean −4/+4 m in map coordinates, not bank directions; the report uses the signed offsets.
They sample approaches, not the entire navigable width. A six-second steering omission begins 12 m before the rapid control station.
The driver scouts live water depth across a raft-sized footprint to seek a wet opening near its preferred lane. These are scouted-route assessments, not blind human first descents.
It uses a 12 m lookahead, extending it to 40 m after 15 s without new downstream progress, and three-second ordinary backstroke attempts after longer stalls.
Troublemaker additionally has an explicit depth-scouted slalom route and a 24 m initial lookahead; the test starts upstream enough to approach its first rock rather than spawning beside it.
All movement along those waypoints is produced by normal controls, never by assigning boat transforms. Actual passing tracks, not the waypoint spacing, determine the reported spread.
Protocol 8 adds the hands-off run and uses the player's production high-side command; older trials with high-side responses are retained as linked evidence but excluded from usable observations.
Observed command workload is not proof that every command was necessary. A recovered route requires being upright, with no swimmers/pin, within 2 m of target;
that instant alone is not a completed recovery unless the section also clears. No checkpoint reset counts as recovery.</p>
<p>This inventory reports observations, not class ratings, human skill certification or real-river safety advice. Headless trials do not validate rendering;
South Fork must be rendered for its GPU water detail. Fixed-step tests are not FPS benchmarks. No untested rapid is assigned a difficulty by copying the catalogue.</p>
<p>Controller failures and timeouts must be diagnosed before grading. The 
<a href="https://site-media.americanwhitewater.org/Scale-of-River-Difficulty-Safety-Code-2024.pdf">American Whitewater scale</a>
is only a qualitative reference. <a href="https://home.nps.gov/grca/learn/photosmultimedia/b-roll_hd22.htm">Grand Canyon uses a distinct 1–10 convention</a>;
no numeric conversion is used here.</p>
<h2>River-level coverage</h2><p>Receipt coverage includes failed and superseded trials; it does not imply completed validation or a whole-river grade.</p>
<div class="table"><table><thead><tr><th>River / scene</th><th>Nominal flow</th><th>With receipts / modeled</th><th>Scope</th></tr></thead><tbody>'''+''.join(river_summaries)+'</tbody></table></div>'+''.join(sections)+'</html>'
    observed = sum(bool(r['evidence']) for r in rows)
    modeled = sum(bool(r['trial']) and not r['trial'].get('portage', False) for r in rows)
    progress = f"OBSERVATION INVENTORY — {observed}/{modeled} runnable modeled rapid/scene sections have receipts; {len(data)} native trial receipts. These legacy variants do not establish a river class or a catalog match."
    document = document.replace('ASSESSMENT_PROGRESS', progress)
    (args.output/'report.html').write_text(document, encoding='utf-8')
    print(json.dumps({'master_entries': sum(r['master_catalog'] for r in rows), 'total_rows': len(rows),
                      'native_trial_receipts': len(data), 'report': str(args.output/'report.html')}))


if __name__ == '__main__':
    main()
