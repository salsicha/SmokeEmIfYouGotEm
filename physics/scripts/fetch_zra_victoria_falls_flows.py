"""Rebuild daily Zambezi flows at Victoria Falls from the ZRA weekly pages (stdlib only).

The Zambezi River Authority publishes a page per review period
(https://www.zambezira.org/hydrology/river-flows/<slug>-<n>) with a 14-day
table of daily flows at Victoria Falls (Big Tree, merged with Nana's Farm) for
the current season and the same dates of the previous season. No bulk file is
offered. This crawler walks the numbered pages of each slug family, parses
the Victoria Falls table and merges the rows into one dated series. Current-
season values take precedence; previous-season columns fill gaps and are
kept apart as a cross-check. Every value keeps the page it came from.

Output: a JSON record (pages, per-row provenance, merged series).
"""
import argparse
import datetime as dt
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'https://www.zambezira.org/hydrology/river-flows/'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
SLUGS = ['victoria-falls-big-tree', 'victoria-fallsbig-tree', 'victoria-falls', 'victoria-falls-nanas-farm-station']
MONTHS = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return None


def text_lines(s):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    t = re.sub(r'<(td|th)[^>]*>', ' | ', t)
    t = re.sub(r'</tr>|<br\s*/?>|</p>|</h\d>', '\n', t)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t)).replace('\xa0', ' ')
    return [re.sub(r'[ \t]+', ' ', l).strip() for l in t.splitlines() if l.strip()]


def parse_page(s):
    """The Victoria Falls block: season labels, period dates and (date, current, previous) rows."""
    lines = text_lines(s)
    start = next((i for i, l in enumerate(lines) if re.fullmatch(r'Victoria Falls( / Big Tree| \(Nana.s Farm Station\))?', l)), None)
    if start is None:
        return None
    block = []
    for l in lines[start + 1:]:
        if re.fullmatch(r'(Chavuma|Ngonye|Lukulu|Senanga|Kafue|Luangwa|Kariba.*)', l):
            break
        block.append(l)
    head = next((l for l in block if re.search(r'Flow \(m3/s\)', l)), None)
    seasons = re.findall(r'(\d{4})/(\d{2,4})', head or '')
    period = next((l for l in block if 'From:' in l and 'To:' in l), None)
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', period or '')]
    rows = []
    for l in block:
        m = re.fullmatch(r'\|\s*\|?\s*([0-9]{1,2}[-/ ][A-Za-z0-9]{1,5}(?:[-/ ][0-9]{2,4})?)\s*\|\s*([0-9,\.]+)\s*\|\s*([0-9,\.]+)?', l)
        if m:
            rows.append((m.group(1), float(m.group(2).replace(',', '')), float(m.group(3).replace(',', '')) if m.group(3) else None))
    summary = next((l for l in block if 'closing the period under review' in l), '')
    return dict(seasons=seasons, period=period, period_years=years, rows=rows, summary=summary)


def resolve_dates(page):
    """Date of each row: explicit d/m/Y, or d-Mon placed in the period's year range."""
    out = []
    years = page['period_years']
    end_match = re.search(r'To:\s*[A-Za-z]*,?\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})', page['period'] or '')
    end_date = None
    if end_match:
        end_date = dt.date(int(end_match.group(3)), MONTHS[end_match.group(1)[:3].lower()], int(end_match.group(2)))
    elif years:
        end_date = dt.date(max(years), 12, 31)
    for label, cur, prev in page['rows']:
        parts = re.split(r'[-/ ]', label)
        date = None
        try:
            if len(parts) == 3 and parts[2].isdigit():
                d, m, y = int(parts[0]), parts[1], int(parts[2])
                y = y + 2000 if y < 100 else y
                m = int(m) if m.isdigit() else MONTHS[m[:3].lower()]
                date = dt.date(y, m, d)
            elif end_date is not None:
                d, m = int(parts[0]), MONTHS[parts[1][:3].lower()]
                date = dt.date(end_date.year, m, d)
                if date > end_date + dt.timedelta(days=1):
                    date = dt.date(end_date.year - 1, m, d)
        except (ValueError, KeyError):
            date = None
        out.append((date, cur, prev))
    return out


def merge(pages):
    """Every candidate per date (current-season rows, and previous-season columns
    shifted back a year), then an accepted value only where the candidates agree
    within 5 % and the value is within 25 % of its accepted neighbours' median
    (catches dropped digits such as 229 for 2290 and rows placed in the wrong
    season). Rejected and conflicting dates stay listed with their candidates."""
    cand = {}
    for pg in pages:
        for d, cur, prev in pg['rows']:
            if not d:
                continue
            cand.setdefault(d, []).append(dict(flow_m3s=cur, source=pg['url'], column='current'))
            if prev is not None:
                try:
                    dd = dt.date.fromisoformat(d); py = dd.replace(year=dd.year - 1).isoformat()
                except ValueError:
                    continue
                cand.setdefault(py, []).append(dict(flow_m3s=prev, source=pg['url'], column='previous_season'))
    first = {}
    for d, cs in cand.items():
        vals = sorted(c['flow_m3s'] for c in cs)
        med = vals[len(vals) // 2]
        if all(abs(v - med) <= 0.05 * max(med, 1.0) for v in vals):
            first[d] = med
    dates = sorted(first)
    accepted, rejected = {}, []
    for i, d in enumerate(dates):
        nb = [first[dates[j]] for j in range(max(0, i - 3), min(len(dates), i + 4)) if j != i
              and abs((dt.date.fromisoformat(dates[j]) - dt.date.fromisoformat(d)).days) <= 4]
        if nb:
            nb.sort(); m = nb[len(nb) // 2]
            if abs(first[d] - m) > 0.25 * max(m, 1.0):
                rejected.append(dict(date=d, flow_m3s=first[d], neighbour_median_m3s=m, candidates=cand[d])); continue
        accepted[d] = first[d]
    conflicts = [dict(date=d, candidates=cs) for d, cs in sorted(cand.items()) if d not in first]
    series = [dict(date=d, flow_m3s=accepted[d], sources=sorted({c['source'] for c in cand[d]}),
                   columns=sorted({c['column'] for c in cand[d]})) for d in sorted(accepted)]
    years = {}
    for d in accepted:
        years[d[:4]] = years.get(d[:4], 0) + 1
    return dict(schema='raftsim.zambezi.victoria_falls_daily_flows.v2',
                source="Zambezi River Authority weekly river-flow pages (Victoria Falls / Big Tree, merged with Nana's Farm)",
                source_base=BASE, retrieved_on=dt.date.today().isoformat(),
                licence='published on the ZRA website; no licence stated - cite the Zambezi River Authority',
                merge_rule=merge.__doc__.strip(), page_count=len(pages),
                summary=dict(pages=len(pages), candidate_dates=len(cand), accepted_days=len(accepted), conflicting_dates=len(conflicts),
                             rejected_outliers=len(rejected), first=dates[0] if dates else None, last=dates[-1] if dates else None,
                             accepted_days_per_year=dict(sorted(years.items()))),
                series=series, conflicts=conflicts, rejected=rejected, pages=pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--remerge', type=Path, help='rebuild the merged series from the pages of an earlier output (no crawl)')
    ap.add_argument('--max-n', type=int, default=400)
    ap.add_argument('--stop-after-misses', type=int, default=40)
    ap.add_argument('--delay-s', type=float, default=0.4)
    args = ap.parse_args()
    pages = []
    if args.remerge:
        pages = json.loads(args.remerge.read_text())['pages']
    for slug in ([] if args.remerge else SLUGS):
        misses = 0
        for n in range(0, args.max_n + 1):
            url = BASE + (slug if n == 0 else f'{slug}-{n}')
            s = fetch(url)
            time.sleep(args.delay_s)
            parsed = parse_page(s) if s else None
            if not parsed or not parsed['rows']:
                misses += 1
                if misses >= args.stop_after_misses:
                    break
                continue
            misses = 0
            dated = resolve_dates(parsed)
            pages.append(dict(url=url, seasons=parsed['seasons'], period=parsed['period'], summary=parsed['summary'],
                              rows=[[d.isoformat() if d else None, c, p] for d, c, p in dated]))
            print(url, parsed['period'], len(dated), flush=True)
    rec = merge(pages)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rec, indent=0) + '\n')
    print(json.dumps(rec['summary']))


if __name__ == '__main__':
    main()
