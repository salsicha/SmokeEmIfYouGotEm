"""Check logged spray source-centre clearance, not particle motion or visual quality."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re


MARKER = 'LogTemp: Display: SprayEmitterAnchorAudit '
EMITTERS = {'aerosol': 6.0, 'roller': 3.0, 'crest': 3.0}
FIELDS = {'slot', 'emitter', 'enabled', 'sampled', 'x_cm', 'y_cm',
          'z_cm', 'carrier_z_cm', 'clearance_cm'}
# Three independently rounded six-decimal log values enter z - carrier - gap.
LOG_ROUNDING_CM = 0.000002


def audit(text):
    records = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if MARKER not in line:
            continue
        tokens = line.split(MARKER, 1)[1].split()
        pairs = [token.split('=', 1) for token in tokens]
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError(f'Malformed anchor record at line {line_number}')
        row = dict(pairs)
        if len(pairs) != len(row) or set(row) != FIELDS:
            raise ValueError(f'Missing, extra or duplicate fields at line {line_number}')
        if not re.fullmatch(r'[0-5]', row['slot']):
            raise ValueError('Slot outside the six-source pool')
        if row['emitter'] not in EMITTERS:
            raise ValueError('Unknown emitter')
        if any(row[key] not in ('0', '1') for key in ('enabled', 'sampled')):
            raise ValueError('Invalid boolean flag')
        row['slot'] = int(row['slot'])
        row['enabled'] = row['enabled'] == '1'
        row['sampled'] = row['sampled'] == '1'
        for key in FIELDS - {'slot', 'emitter', 'enabled', 'sampled'}:
            row[key] = float(row[key])
            if not math.isfinite(row[key]):
                raise ValueError('Nonfinite anchor record')
        if row['enabled'] and not row['sampled']:
            raise ValueError('Enabled emitter has no visible-carrier sample')
        if row['sampled'] and abs(row['z_cm'] - row['carrier_z_cm'] -
                                  row['clearance_cm']) > LOG_ROUNDING_CM:
            raise ValueError('Logged clearance disagrees with world Z minus carrier Z')
        row['line'] = line_number
        records.append(row)
    if not records or len(records) % 3:
        raise ValueError('Missing or truncated emitter triplets')
    # These three records are emitted consecutively by the same source-site
    # update. This is not a timestamp, continuous-motion, or duration check.
    for start in range(0, len(records), 3):
        group = records[start:start + 3]
        if ([row['emitter'] for row in group] != list(EMITTERS) or
                len({row['slot'] for row in group}) != 1 or
                len({row['enabled'] for row in group}) != 1):
            raise ValueError('Incomplete, reordered or inconsistent source-site triplet')
    result = {}
    for name, expected in EMITTERS.items():
        rows = [row for row in records if row['emitter'] == name]
        active = [row for row in rows if row['enabled'] and row['sampled']]
        if not active:
            raise ValueError('No sampled, enabled clearance evidence for ' + name)
        error = max(abs(row['clearance_cm'] - expected) for row in active)
        if error > LOG_ROUNDING_CM:
            raise ValueError('Source-centre clearance mismatch for ' + name)
        result[name] = dict(expected_clearance_cm=expected, records=len(rows),
                            sampled_enabled_records=len(active),
                            disabled_records=sum(not row['enabled'] for row in rows),
                            unavailable_records=sum(not row['sampled'] for row in rows),
                            max_clearance_error_cm=error,
                            enabled_slots=sorted({row['slot'] for row in active}))
    return dict(schema='raftsim.spray_emitter_anchor.v1',
                source_centre_clearance_passed=True, emitters=result,
                site_triplets=len(records) // 3,
                log_rounding_tolerance_cm=LOG_ROUNDING_CM,
                visual_accepted=False, performance_accepted=False,
                scope='Logged sampled/enabled source centres only. Does not prove capture '
                      'duration, ordinary launch configuration, particle landing, entire '
                      'spawn-plane clearance, water continuity or realistic breaking.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    provenance = dict(source=str(args.log.resolve()), source_sha256=hashlib.sha256(raw).hexdigest())
    try:
        report = audit(raw.decode('utf-8-sig', errors='strict'))
    except ValueError as error:
        report = dict(source_centre_clearance_passed=False, error=str(error),
                      visual_accepted=False, performance_accepted=False)
    report.update(provenance)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['source_centre_clearance_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
