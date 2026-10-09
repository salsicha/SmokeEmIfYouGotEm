"""Give researched catalog rapids an on-screen title and an assessment trial.

For one playable map whose run progress is the catalog's published stationing
(e.g. South Fork FullReach: river miles from Chili Bar), every catalog rapid
added by merge_named_rapid_research.py (it carries research_source_ids) gets:
- a trial in unreal/Tests/Data/rapid_assessment_reaches.json at its
  published station, with interpreted +/- bounds (not surveyed endpoints);
- a title in RaftSimRapidTitles.cpp at the same control station, which
  RaftSim.UI.RapidTitlesMatchAssessmentPlans checks.
Existing trials and titles are untouched; text is inserted in station order.
"""
import argparse
import json
import re
from pathlib import Path

from merge_named_rapid_research import ROOT, CATALOG, span, items, block, rapid_slug

PLANS = ROOT / 'unreal/Tests/Data/rapid_assessment_reaches.json'
TITLES = ROOT / 'unreal/Source/SmokeEmIfYouGotEm/RaftSimRapidTitles.cpp'
SCALE = {'river_mile': 1609.344, 'river_km': 1000.0}


def researched(river_id, start_m, finish_m):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    river = next(r for r in catalog['rivers'] if r['river_id'] == river_id)
    for rapid in river['rapids']:
        if not rapid.get('research_source_ids'):
            continue
        key = next(k for k in SCALE if k in rapid)
        station = round(rapid[key] * SCALE[key], 4)
        if start_m <= station <= finish_m:
            yield rapid, station


def add(map_package, river_id, half_m, start_m, finish_m):
    rapids = list(researched(river_id, start_m, finish_m))
    map_name = map_package.rsplit('/', 1)[-1]
    # Assessment trials (text-preserving insertion into this map's plan).
    text = PLANS.read_bytes().decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    plans = json.loads(text)
    plan_index = next(i for i, p in enumerate(plans) if p['map'] == map_package)
    plan_spans = items(text, text.index('['), span(text, text.index('[')))
    a, b = plan_spans[plan_index]
    plan_text = text[a:b]
    trials_at = plan_text.index('"trials": [') + len('"trials": ')
    trial_spans = items(plan_text, trials_at, span(plan_text, trials_at))
    existing = [(json.loads(plan_text[s:e]), plan_text[s:e]) for s, e in trial_spans]
    ids = {t['id'] for t, _ in existing}
    indent = trial_spans[0][0] - plan_text.rfind('\n', 0, trial_spans[0][0]) - 1
    added = []
    for rapid, station in rapids:
        trial_id = rapid_slug(rapid['name'])
        if trial_id in ids:
            continue
        trial = dict(id=trial_id, name=rapid['name'], catalog_class=rapid['class'], control_m=station,
                     start_m=round(station - half_m), finish_m=round(station + half_m),
                     coverage_note='Researched 2026-10-08 at its published station; interpreted test bounds, '
                                   'not surveyed endpoints or a reconstructed rapid.',
                     coverage_source='physics/data/real_world/named_rapid_source_catalog.json')
        existing.append((trial, block(trial, indent, newline)))
        added.append(trial)
    if added:
        existing.sort(key=lambda pair: pair[0]['control_m'])
        joined = (',' + newline + ' ' * indent).join(t for _, t in existing)
        plan_text = plan_text[:trial_spans[0][0]] + joined + plan_text[trial_spans[-1][1]:]
        text = text[:a] + plan_text + text[b:]
        parsed = json.loads(text)
        if len(parsed[plan_index]['trials']) != len(plans[plan_index]['trials']) + len(added):
            raise ValueError('Trial insertion failed')
        PLANS.write_bytes(text.encode('utf-8'))
    # Titles (same ids and control stations).
    source = TITLES.read_bytes().decode('utf-8')
    pattern = re.compile(r'    \{TEXT\("' + re.escape(map_name) + r'"\), TEXT\("([^"]+)"\), TEXT\("(?:[^"\\]|\\.)*"\), '
                         r'TEXT\("[^"]*"\), ([0-9.]+)f, (?:true|false)\},\r?\n')
    rows = [(float(m.group(2)), m.group(0)) for m in pattern.finditer(source)]
    if not rows:
        raise ValueError('No title block for ' + map_name)
    first, last = pattern.search(source), list(pattern.finditer(source))[-1]
    titled = {m.group(1) for m in pattern.finditer(source)}
    line_end = '\r\n' if rows[0][1].endswith('\r\n') else '\n'
    for trial in added:
        if trial['id'] in titled:
            continue
        name = trial['name'].replace('\\', '\\\\').replace('"', '\\"')
        grade = 'surf' if 'surf' in trial['catalog_class'] else trial['catalog_class']
        rows.append((trial['control_m'], f'    {{TEXT("{map_name}"), TEXT("{trial["id"]}"), TEXT("{name}"), '
                                         f'TEXT("{grade}"), {trial["control_m"]:.1f}f, false}},{line_end}'))
    rows.sort(key=lambda row: row[0])
    source = source[:first.start()] + ''.join(r for _, r in rows) + source[last.end():]
    TITLES.write_bytes(source.encode('utf-8'))
    return added


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map', required=True, help='Map package, e.g. /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach')
    parser.add_argument('--river', required=True)
    parser.add_argument('--half-m', type=float, default=150.0)
    parser.add_argument('--start-m', type=float, default=0.0)
    parser.add_argument('--finish-m', type=float, default=1e9)
    args = parser.parse_args()
    for trial in add(args.map, args.river, args.half_m, args.start_m, args.finish_m):
        print(f"{trial['control_m']:9.1f} {trial['id']:35s} {trial['catalog_class']}")
