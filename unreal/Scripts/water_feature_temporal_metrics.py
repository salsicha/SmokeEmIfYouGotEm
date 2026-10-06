"""Strict observed frame coverage; integrator duration is not cache time."""
import math


def step_clock(steps, first, last, subdivision, native_units_per_second=2.5):
    if not steps or first > last or subdivision not in (1,2,4):
        raise ValueError('A nonempty bounded native control is required')
    groups = {frame:[] for frame in range(first,last+1)}
    for index,row in enumerate(steps):
        if (row['index'] != index or row['frame'] not in groups or
                not math.isfinite(row['dt_native']) or row['dt_native'] <= 0 or
                not math.isfinite(row['time_total_native']) or
                not math.isfinite(row['time_per_frame_native']) or
                row['primary_before'] <= 0 or row['primary_after'] <= 0):
            raise ValueError('Missing, out-of-range or invalid native observation')
        groups[row['frame']].append(row)
    if [r['frame'] for r in steps] != sorted(r['frame'] for r in steps):
        raise ValueError('Native steps must remain in actual time order')
    rows = []
    for frame,group in groups.items():
        if not 2*subdivision <= len(group) <= 8*subdivision or group[0]['time_per_frame_native'] != 0.:
            raise ValueError('Incomplete frame or wrong declared subdivision')
        if any(b['time_per_frame_native'] <= a['time_per_frame_native']
                for a,b in zip(group,group[1:])):
            raise ValueError('Native substep time did not advance')
        rows.append(dict(frame=frame,substeps=len(group),
            integrated_duration_s=sum(r['dt_native'] for r in group)/native_units_per_second))
    return dict(frames=rows,step_count=len(steps),
        integrated_duration_s=sum(r['integrated_duration_s'] for r in rows),
        scope='Sum of observed native liquid-step dt; distinct from frame/cached clock, not retimed')


def paired_column_differences(left,right):
    if len(left) != len(right):
        raise ValueError('Same fixed column cohort required')
    rows = []
    for a,b in zip(left,right):
        if a['column'] != b['column']:
            raise ValueError('Column order changed')
        usable = a['interface']['status']==b['interface']['status']=='supported'
        rows.append(dict(column=a['column'],supported=usable,
            left_status=a['interface']['status'],right_status=b['interface']['status'],
            vertical_difference_m=(b['interface']['crossings'][0]['relative_height_m']-
                a['interface']['crossings'][0]['relative_height_m']) if usable else None))
    return rows
