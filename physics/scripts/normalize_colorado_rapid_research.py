"""Normalize the Colorado (Lees Ferry-Pearce Ferry) rapid research for the merge.

The two Colorado research files (named_rapid_research_2026_10_08/colorado_*)
give USGS GCMRC river miles, 1-10 Grand Canyon ratings and USGS/GNIS/OSM
positions in their own schema. This writes them in the generic research shape
merge_named_rapid_research.py reads:
- the catalog's existing rapids are matched by name, ignoring a trailing
  "Rapid"/"Riffle" and using aliases, and flagged not new;
- drowned, historical or washed-out entries and plain obstacles are left
  out;
- new names drop a trailing " Rapid", as the catalog does ("Hance").
Ratings stay on the 1-10 scale ("6/10"), as in the catalog, with no claimed
equivalence to international classes.
"""
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'physics/data/real_world/named_rapid_research_2026_10_08'
CATALOG = ROOT / 'physics/data/real_world/named_rapid_source_catalog.json'



def norm(name):
    name = re.sub(r'\b(rapids?|riffle)\b', '', name.lower())
    return re.sub(r'[^a-z0-9.]+', '', name)


def ratings(record):
    values = []
    gc = (record.get('rating') or {}).get('grand_canyon_1_10')
    if isinstance(gc, dict):
        values = [v for v in gc.values() if isinstance(v, (int, float))]
    elif isinstance(gc, list):
        for row in gc:
            try:
                values.append(float(str(row.get('value')).split('-')[0]))
            except (TypeError, ValueError):
                pass
    return values


def main():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    river = next(r for r in catalog['rivers'] if r['river_id'] == 'colorado_river_grand_canyon_rowing')
    existing = {norm(r['name']) for r in river['rapids']}
    for r in river['rapids']:
        existing.update(norm(a) for a in r.get('aliases', []))
    sources, rapids, seen = {}, [], set()
    for part in ('colorado_rm000_088', 'colorado_rm088_280'):
        data = json.loads((RESEARCH / f'{part}.json').read_text(encoding='utf-8'))
        for source in data['sources']:
            sid = source.get('source_id') or source.get('id')
            sources.setdefault(sid, dict(source_id=sid, title=source.get('title', sid), url=source.get('url'),
                                         kind=source.get('kind', 'research_reference'),
                                         rights=source.get('rights') or source.get('rights_note') or source.get('license', '')))
        for record in data['rapids']:
            name = record['name']
            kind = record.get('kind') or 'rapid'
            status = str(record.get('status') or '').strip().lower()
            if kind == 'obstacle' or (status and not status.startswith('active')):
                continue
            key = norm(name)
            if key in seen or not isinstance(record.get('river_mile'), (int, float)):
                continue
            seen.add(key)
            aliases = record.get('aliases') or []
            is_new = key not in existing and not any(norm(a) in existing for a in aliases)
            values = ratings(record)
            low = high = None
            if values:
                low, high = f'{int(min(values))}/10', f'{int(max(values))}/10'
            text = record.get('description') or record.get('features') or ''
            if isinstance(text, list):
                text = '; '.join(map(str, text))
            position = None
            if isinstance(record.get('latitude'), (int, float)):
                position = dict(lat=record['latitude'], lon=record['longitude'], derived=False,
                                source_id=str(record.get('position_source', '')))
            cited = []
            for s in record.get('sources', []):
                sid = s if isinstance(s, str) else (s.get('source_id') or s.get('id'))
                if sid in sources:
                    cited.append(dict(source_id=sid))
            rapids.append(dict(name=re.sub(r'\s+Rapid$', '', name), aliases=aliases, kind=kind, is_new=is_new,
                               chainage=dict(published_median_mi=round(record['river_mile'], 2)),
                               **{'class': dict(low=low, high=high,
                                                range_note='Grand Canyon 1-10 scale as published; flow dependent')},
                               feature=str(text)[:300], position=position, sources=cited,
                               confidence=record.get('confidence')))
    rapids.sort(key=lambda r: r['chainage']['published_median_mi'])
    out = RESEARCH / 'colorado_normalized.json'
    out.write_text(json.dumps(dict(river_id='colorado_river_grand_canyon_rowing', sources=list(sources.values()),
                                   rapids=rapids), indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(len(rapids), 'records;', sum(r['is_new'] for r in rapids), 'new')


if __name__ == '__main__':
    main()
