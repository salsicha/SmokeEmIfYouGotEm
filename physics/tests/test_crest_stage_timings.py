import pytest
from audit_crest_stage_timings import summarize


def capture():
    lines = []
    for frame in range(60, 63):
        lines.append(f'WaterCrestVertices frame={frame} copy_ms=0.4 midpoints_ms=0.3 history_ms=0.2 dense={frame%2} source_vertices=100 fine_vertices=20')
        lines.append(f'WaterCrestPerf frame={frame} rebuild={frame%2} total_ms=2 selection_ms=0.5 targets_ms=0.1 vertices_ms=0.9 topology_ms=0.2 normals_ms=0.3 fine_vertices=20 xy_changed={frame%2} indices_changed=0 profile_changed={frame%2} coarse_changed=0 shore_changed=0 detail_changed=0 sample_ms=0.2 assembly_ms=0.1 refine_input_ms=0.1')
    return '\n'.join(lines)


def test_complete_subdivision_and_no_acceptance():
    report = summarize(capture(), 60, 62, True)
    assert report['calls'] == 3 and report['rebuilt']['calls'] == 1
    assert report['changed_xy_without_profile'] == 0
    assert report['vertex_subdivision']['mapped']['calls'] == 2
    assert report['vertex_subdivision']['dense']['mean_ms']['history_ms'] == .2
    assert not report['release_accepted'] and not report['visual_accepted']


def test_multiple_calls_preserved_in_order():
    lines = capture().splitlines()
    lines[2:2] = lines[:2]
    report = summarize('\n'.join(lines), 60, 62, True)
    assert report['calls'] == 4 and report['calls_per_frame'][60] == 2


def test_old_logs_report_missing_subdivision_not_zero_cost():
    old = '\n'.join(line for line in capture().splitlines() if 'Vertices' not in line)
    assert summarize(old, 60, 62)['vertex_subdivision'] is None
    with pytest.raises(ValueError):
        summarize(old, 60, 62, True)


@pytest.mark.parametrize('change', [
    lambda s: '\n'.join(s.splitlines()[2:]),
    lambda s: '\n'.join(s.splitlines()[1:]),
    lambda s: s.replace('copy_ms=0.4', 'copy_ms=nan', 1),
    lambda s: s.replace('copy_ms=0.4', 'copy_ms=inf', 1),
    lambda s: s.replace('copy_ms=0.4', 'copy_ms=-1', 1),
    lambda s: s.replace('copy_ms=0.4', 'copy_ms=0.4 copy_ms=0.4', 1),
    lambda s: s.replace('dense=0', 'dense=2', 1),
    lambda s: s.replace('fine_vertices=20', 'fine_vertices=21', 1),
    lambda s: s.replace('history_ms=0.2', '', 1),
    lambda s: s.replace('frame=60', 'frame=no', 1),
    lambda s: '\n'.join(reversed(s.splitlines())),
])
def test_incomplete_or_invalid_evidence_rejects(change):
    with pytest.raises(ValueError):
        summarize(change(capture()), 60, 62, True)


@pytest.mark.parametrize('first,last', [(-1, 62), (62, 60)])
def test_invalid_interval(first, last):
    with pytest.raises(ValueError):
        summarize(capture(), first, last)
