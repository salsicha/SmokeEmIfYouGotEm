import copy
import pytest
from audit_pressure_cut_face import columns, summarize


def fixture():
    def probe(opened):
        return dict(edge_open=opened, hydrostatic_face_passes=[dict(
            reconstructed_a=2., reconstructed_b=1., hydrostatic_a=1e-10 if opened else 0.,
            hydrostatic_b=1.)], pressure=dict(cells=[
                dict(yx=[1, 2], h=2., integrated_nonhydrostatic=3. if opened else -1.,
                     bottom_nonhydrostatic=4. if opened else -2.),
                dict(yx=[2, 2], h=1., integrated_nonhydrostatic=.01, bottom_nonhydrostatic=.02)]))
    return dict(schema='raftsim.pressure_wetting_edge_probe.v1', wetting_limit=dict(cases=[
        dict(changed_graph_cells=1, maximum_state_difference=1e-15,
             force_jump_at_owner=[.1, .2], probes=[probe(False), probe(True)])]))


def test_probe_preserves_source_and_distinguishes_fixed_from_changed_pressure():
    source = fixture(); before = copy.deepcopy(source)
    row, = summarize(source)
    assert source == before
    assert row['unchanged_source_force_jump'] == [.1, .2]
    opened = row['actual_open_columns'][0]
    frozen = row['fixed_left_pressure_open_geometry_columns'][0]
    assert opened['transmitted'] > 0 and frozen['transmitted'] > 0
    assert opened['blocked'] == 3 and frozen['blocked'] == -1
    assert row['actual_integral_changes'][0]['blocked'] == 4
    assert row['actual_closed_columns'][0]['transmitted'] == 0
    assert row['actual_open_columns'][1]['blocked'] == 0
    assert 'transmitted_rate' not in opened  # Snapshot rates were not measured.
    opened['height'] = 999
    assert source == before


@pytest.mark.parametrize('bad', ['reconstruction', 'missing_face', 'missing_cell', 'out_of_column'])
def test_unprovided_pressure_reconstruction_or_invalid_cut_is_not_invented(bad):
    source = fixture()['wetting_limit']['cases'][0]['probes'][1]
    if bad == 'reconstruction': source['hydrostatic_face_passes'][0]['reconstructed_a'] = 3
    elif bad == 'missing_face': source['hydrostatic_face_passes'] = []
    elif bad == 'missing_cell': source['pressure']['cells'].pop()
    else: source['hydrostatic_face_passes'][0]['hydrostatic_a'] = 3
    with pytest.raises(ValueError):
        columns(source)


@pytest.mark.parametrize('bad', ['schema', 'empty', 'edge_count', 'order', 'probe_count'])
def test_invalid_limit_probe_is_rejected(bad):
    source = fixture()
    case = source['wetting_limit']['cases'][0]
    if bad == 'schema': source['schema'] = 'unknown'
    elif bad == 'empty': source['wetting_limit']['cases'] = []
    elif bad == 'edge_count': case['changed_graph_cells'] = 2
    elif bad == 'order': case['probes'].reverse()
    else: case['probes'].pop()
    with pytest.raises(ValueError):
        summarize(source)
