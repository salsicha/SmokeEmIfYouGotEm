"""Merge researched named rapids into the named-rapid source catalog.

Input is one river's research file (scratch JSON: sources plus rapids, each
with name, published chainage, class range, a one-line feature description,
an optional sourced or derived position, sources and confidence). Only
records flagged new are added; existing catalog rapids and their stations
are never changed. A new rapid keeps the river's stationing convention:
published river miles (--unit mile) or kilometres (--unit km), the
median of the published values, falling back to the projected value.
Rapids with no chainage are reported, not placed. Positions are kept with
their provenance (source point or derived) and are review evidence, not
surveyed geometry. Sources are added link-only (government data as
government_source).
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'physics/data/real_world/named_rapid_source_catalog.json'

TAG_WORDS = [
    (r'pour-?over', 'pourover'), (r'\bholes?\b', 'hole'), (r'\bledges?\b', 'ledge'),
    (r'wave train|wave-train|waves', 'wave_train'), (r'\bsurf', 'surf_wave'), (r'\bwave\b', 'wave'),
    (r'boulder|rock garden|rocky', 'boulder_garden'), (r'\bboofs?\b|\bdrops?\b|\bfalls?\b', 'drop'),
    (r'island|channels?|split', 'island_split'), (r'narrow|constrict|gorge|canyon', 'constriction'),
    (r'\brocks?\b', 'boulder'), (r'eddy|eddies', 'eddy_line'), (r'lateral', 'lateral'), (r'boils?', 'boil'),
    (r'chute', 'chute'),
    (r'\bbend|\bturn', 'bend'), (r'undercut|pin|wrap|sieve', 'pin_hazard'), (r'portage', 'portage'),
    (r'scout', 'scout'), (r'continuous|long', 'continuous_whitewater'),
]
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}


def tags_for(text):
    found = []
    for pattern, tag in TAG_WORDS:
        if re.search(pattern, text or '', re.IGNORECASE) and tag not in found:
            found.append(tag)
    return found or ['rapid']


SUBFEATURE_FOR_TAG = [('pourover', 'pourover'), ('hole', 'hole'), ('ledge', 'ledge'), ('wave_train', 'wave_train'),
                      ('surf_wave', 'wave'), ('wave', 'wave'), ('island_split', 'island'), ('boulder', 'boulder'),
                      ('boulder_garden', 'boulder'), ('eddy_line', 'eddy_line'), ('lateral', 'lateral'), ('boil', 'boil'),
                      ('pin_hazard', 'pin_rock'), ('continuous_whitewater', 'continuous_whitewater')]


def main_subfeature(record, entry, source_ids):
    tags = entry['feature_tags']
    kind = next((sub for tag, sub in SUBFEATURE_FOR_TAG if tag in tags), 'line')
    text = record.get('feature', '')
    across = next((side for side in ('left', 'right') if re.search(r'\b(river[- ])?' + side + r'\b', text, re.I)), 'center')
    high = grade_value(entry['class_reported_range']['high'])
    consequence = 'surf_or_retention' if kind in ('hole', 'pourover') else (
        'swim_risk' if high >= 3 else 'low_nuisance')
    unresearched = 'Not described per flow by the researched sources; review at this band.'
    return {'subfeature_id': re.sub(r'[^a-z0-9]+', '_', record['name'].lower()).strip('_') + '_main',
            'display_name': record['name'] + ' main feature', 'feature_type': kind,
            'relative_position': {'along': 'middle', 'across': across, 'notes': text or record['name']},
            'flow_dependence': {band: unresearched for band in ('low_review', 'reference_review', 'high_review')},
            'consequence_class': consequence, 'source_ids': source_ids, 'guide_review_status': 'required'}


def rapid_slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def grade_value(grade):
    match = re.match(r'(VI|IV|V|I{1,3})', grade or '')
    return ROMAN.get(match.group(1), 0) if match else 0


def class_label(cls):
    low, high = (cls or {}).get('low'), (cls or {}).get('high')
    if not low and not high:
        return None
    if not high or low == high:
        return low or high
    return f'{low}-{high}'


def published_value(chainage, unit):
    key = 'mi' if unit == 'mile' else 'km'
    for name in (f'published_median_{key}', f'recommended_{key}'):
        value = chainage.get(name)
        if isinstance(value, (int, float)):
            return round(float(value), 3)
    return None


def rights_status(text):
    text = (text or '').lower()
    if 'public domain' in text or 'government' in text or 'usgs' in text:
        return 'government_source_public_domain'
    if 'odbl' in text:
        return 'link_only_odbl_attribution'
    return 'link_only_factual_index'


def merge(research_path, river_id, unit, prefix, catalog_path=CATALOG, dry_run=False):
    catalog = json.loads(Path(catalog_path).read_text(encoding='utf-8'))
    research = json.loads(Path(research_path).read_text(encoding='utf-8'))
    river = next(r for r in catalog['rivers'] if r['river_id'] == river_id)
    station_key = 'river_mile' if unit == 'mile' else 'river_km'
    known = {r['name'].casefold() for r in river['rapids']}
    for rapid in river['rapids']:
        known.update(alias.casefold() for alias in rapid.get('aliases', []))
    by_url = {s['url']: s['source_id'] for s in catalog['sources']}
    id_map = {}
    for source in research.get('sources', []):
        url = source.get('url') or ''
        if not url.startswith('https://'):
            continue
        if url in by_url:
            id_map[source['source_id']] = by_url[url]
            continue
        new_id = f"{prefix}_{re.sub(r'[^a-z0-9]+', '_', source['source_id'].lower()).strip('_')}"
        catalog['sources'].append(dict(source_id=new_id, river_id=river_id, title=source.get('title', new_id), url=url,
                                       source_kind=source.get('kind', 'research_reference'),
                                       rights_status=rights_status(source.get('rights'))))
        by_url[url] = new_id
        id_map[source['source_id']] = new_id
    references = [r.get('flow_band_reference') for r in river['rapids']]
    flow_reference = references[0] if references and all(references) else None
    added, unplaced = [], []
    for record in research['rapids']:
        is_new = record.get('is_new', record.get('in_existing_catalog') is False)
        if not is_new or record['name'].casefold() in known:
            continue
        value = published_value(record.get('chainage') or {}, unit)
        if value is None:
            unplaced.append(record['name'])
            continue
        cls = record.get('class') if isinstance(record.get('class'), dict) else {}
        label = class_label(cls) or ('surf feature' if 'surf' in (record.get('kind', '') + record.get('feature', '')).lower() else 'II')
        source_ids = sorted({id_map[s['source_id']] for s in record.get('sources', []) if s.get('source_id') in id_map})
        entry = {'name': record['name'], 'order': 0, station_key: value, 'class': label,
                 'class_reported_range': {'low': cls.get('low') or label, 'high': cls.get('high') or label,
                                          'note': cls.get('range_note') or 'Researched 2026-10-08; see research_source_ids.'},
                 'feature_tags': tags_for(record.get('feature', '')),
                 'review_priority': 'high' if grade_value(cls.get('high')) >= 4 else 'medium',
                 'research_summary': record.get('feature', ''),
                 'research_source_ids': source_ids,
                 'research_confidence': record.get('confidence')}
        if record.get('aliases'):
            entry['aliases'] = record['aliases']
        if flow_reference is not None and source_ids:
            # The river's review contract wants each rapid's flow bands and
            # at least one sub-feature: the researched main feature, with
            # flow dependence stated as unresearched, pending guide review.
            entry['flow_band_reference'] = flow_reference
            entry['feature_inventory'] = [main_subfeature(record, entry, source_ids)]
        position = record.get('position') or record.get('derived_position')
        if isinstance(position, dict) and isinstance(position.get('lat'), (int, float)):
            entry['research_position'] = dict(lat=position['lat'], lon=position['lon'],
                                              derived=bool(position.get('derived', record.get('position') is None)),
                                              basis=position.get('method') or position.get('selection') or position.get('source_id'))
        added.append(entry)
    combined = river['rapids'] + added
    # Downstream order by station; existing rapids keep their stations.
    combined.sort(key=lambda r: (r.get(station_key, float('inf')), r['order'] if r['order'] else 1e9))
    for order, rapid in enumerate(combined, start=1):
        rapid['order'] = order
    river['rapids'] = combined
    river['source_ids'] = sorted(set(river['source_ids']) | {i for r in added for i in r['research_source_ids']})
    if not dry_run:
        text = Path(catalog_path).read_bytes().decode('utf-8')
        updated = rewrite_text(text, catalog, river_id, added, catalog['sources'])
        if json.loads(updated) != catalog:
            raise ValueError('Text-preserving rewrite does not reproduce the merged catalog')
        Path(catalog_path).write_bytes(updated.encode('utf-8'))
    return added, unplaced


def span(text, start):
    """End index (exclusive) of the bracketed value opening at text[start]."""
    depth, i, in_string = 0, start, False
    while i < len(text):
        c = text[i]
        if in_string:
            if c == '\\':
                i += 1
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
        elif c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('Unbalanced JSON text')


def items(text, start, end):
    """Spans of the top-level values inside the array text[start:end] (brackets included)."""
    result, i = [], start + 1
    while True:
        while i < end and text[i] in ' \t\r\n,':
            i += 1
        if i >= end - 1 or text[i] == ']':
            return result
        stop = span(text, i)
        result.append((i, stop))
        i = stop


def block(value, indent, newline):
    lines = json.dumps(value, indent=2, ensure_ascii=False).split('\n')
    return newline.join((' ' * indent if n else '') + line for n, line in enumerate(lines))


def rewrite_text(text, catalog, river_id, added, sources):
    newline = '\r\n' if '\r\n' in text else '\n'
    rivers_at = text.index('"rivers"')
    river_at = text.index(f'"river_id": "{river_id}"', rivers_at)
    river = next(r for r in catalog['rivers'] if r['river_id'] == river_id)
    # Rapids: keep each existing rapid's text, renumbering only its order.
    rapids_at = text.index('"rapids": [', river_at) + len('"rapids": ')
    rapids_end = span(text, rapids_at)
    spans = items(text, rapids_at, rapids_end)
    first = spans[0][0]
    indent = first - text.rfind('\n', 0, first) - 1
    existing = {json.loads(text[a:b])['name']: text[a:b] for a, b in spans}
    pieces = []
    for rapid in river['rapids']:
        if rapid['name'] in existing:
            pieces.append(re.sub(r'"order": \d+', f'"order": {rapid["order"]}', existing[rapid['name']], count=1))
        else:
            pieces.append(block(rapid, indent, newline))
    separator = ',' + newline + ' ' * indent
    text = text[:first] + separator.join(pieces) + text[spans[-1][1]:]
    # River source IDs (a single-line list).
    river_at = text.index(f'"river_id": "{river_id}"', text.index('"rivers"'))
    ids_at = text.index('"source_ids": [', river_at) + len('"source_ids": ')
    text = text[:ids_at] + json.dumps(river['source_ids'], ensure_ascii=False) + text[span(text, ids_at):]
    # Catalog sources: append the new ones.
    sources_at = text.index('"sources": [') + len('"sources": ')
    source_spans = items(text, sources_at, span(text, sources_at))
    present = {json.loads(text[a:b])['source_id'] for a, b in source_spans}
    fresh = [s for s in sources if s['source_id'] not in present]
    if fresh:
        last = source_spans[-1]
        s_indent = last[0] - text.rfind('\n', 0, last[0]) - 1
        insert = ''.join(',' + newline + ' ' * s_indent + block(s, s_indent, newline) for s in fresh)
        text = text[:last[1]] + insert + text[last[1]:]
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', required=True, type=Path)
    parser.add_argument('--river', required=True)
    parser.add_argument('--unit', choices=('mile', 'km'), required=True)
    parser.add_argument('--prefix', required=True, help='Source-ID prefix for new sources')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    added, unplaced = merge(args.research, args.river, args.unit, args.prefix, dry_run=args.dry_run)
    for entry in added:
        print(f"{entry['order']:3d} {entry['name']:40s} {entry.get('river_mile', entry.get('river_km'))} {entry['class']:10s} {entry['feature_tags']}")
    print(f'added {len(added)}; unplaced (no chainage): {unplaced}')
