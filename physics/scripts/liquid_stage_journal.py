"""Iterate exact observed stages from legacy records or a bounded lossless journal.

No inferred stages, sampling, averaging or omitted native birth records.
"""


def stage_groups(report):
    if 'stage_journal' not in report:
        yield from report['groups']
        return
    journal = report['stage_journal']
    rows, templates = journal['records'], journal['templates']
    if (report.get('groups') or journal['schema'] != 'raftsim.liquid_stage_journal.v1' or
            journal['failed'] is not False or report.get('records_truncated') is not False or
            len(rows) != journal['record_count'] or not 0 < len(rows) <= 262144 or
            not 0 < len(templates) <= 4096 or not 0 < journal['template_chars'] <= 8*1024*1024 or
            sum(report[k] for k in ('complete_aligned_groups','incomplete_groups','misaligned_groups')) != len(rows)):
        raise ValueError('Incomplete or invalid lossless stage journal')
    for template in templates:
        if (set(template) != {'simulation_generation','complete','aligned','entries'} or
                template['simulation_generation'] != report['simulation_generation'] or
                type(template['complete']) is not bool or type(template['aligned']) is not bool or
                not 1 <= len(template['entries']) <= 12):
            raise ValueError('Invalid or stale stage template')
        for entry in template['entries']:
            if (set(entry) != {'owner','name','stage','iteration','iterations','loop','loops','first','reset','last',
                               'native_rate_spawns','native_event_spawns'} or
                    not isinstance(entry['name'], str) or not entry['name'] or
                    any(type(entry[k]) is not bool for k in ('first','reset','last')) or
                    any(type(entry[k]) is not int or not 0 <= entry[k] <= 2**32-1 for k in
                        ('owner','stage','iteration','iterations','loop','loops','native_rate_spawns','native_event_spawns')) or
                    entry['owner'] >= 12):
                raise ValueError('Invalid native stage entry')
    counts = [0,0,0]
    for row in rows:
        if (not isinstance(row,list) or len(row) != 3 or
                any(type(v) is not int or not 0 <= v <= 2**32-1 for v in row) or row[2] >= len(templates)):
            raise ValueError('Invalid stage journal address')
        t = templates[row[2]]
        if t['aligned'] and not t['complete']:
            raise ValueError('Incomplete group cannot be aligned')
        counts[0 if t['aligned'] else (2 if t['complete'] else 1)] += 1
    if counts != [report[k] for k in ('complete_aligned_groups','incomplete_groups','misaligned_groups')]:
        raise ValueError('Stage journal counters disagree with observed records')
    for frame, group, index in rows:
        yield dict(templates[index], render_frame=frame, graph_group=group)
