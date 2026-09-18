import pytest
from audit_wet_edge_cache import audit


def inputs():
    text = '\n'.join(f'LogTemp: Display: WetEdgeCacheAudit exact frame={frame} phase={phase} '
                     f'hit={int(phase == 2)} cells=713' for frame in range(64) for phase in (1, 2))
    process = dict(game_arguments=['-RaftSimCacheWetEdges', '-RaftSimWetEdgeCacheAudit'],
                   game_exit_code=0, game_timeout=False, suspend_status=0, resume_status=0)
    return text, process


def test_complete_two_phase_arrays():
    text, process = inputs()
    result = audit('command -RaftSimWetEdgeCacheAudit\n'+text, process)
    assert result['exact_distances'] == 128*713
    assert result['phases'][1]['hits'] == 64
    assert not any(result[k] for k in ('performance_accepted', 'visual_accepted', 'release_accepted'))


@pytest.mark.parametrize('change', ('mismatch', 'missing_phase', 'short', 'zero', 'reversed', 'no_hits', 'no_rebuilds'))
def test_invalid_records_rejected(change):
    text, process = inputs()
    if change == 'mismatch': text += '\nWetEdgeCacheAudit mismatch frame=64 phase=2'
    if change == 'missing_phase': text = '\n'.join(l for l in text.splitlines() if 'phase=1' in l)
    if change == 'short': text = '\n'.join(text.splitlines()[:-1])
    if change == 'zero': text = text.replace('cells=713', 'cells=0', 1)
    if change == 'reversed': text = '\n'.join(reversed(text.splitlines()))
    if change == 'no_hits': text = text.replace('hit=1', 'hit=0')
    if change == 'no_rebuilds': text = text.replace('hit=0', 'hit=1')
    with pytest.raises(ValueError): audit(text, process)


@pytest.mark.parametrize('key,value', [('game_exit_code', 1), ('game_timeout', True),
    ('resume_status', 1), ('suspend_status', 1), ('game_arguments', []),
    ('game_arguments', ['-RaftSimCacheWetEdges', '-RaftSimWetEdgeCacheAudit', '-RaftSimCacheWetEdges'])])
def test_process_evidence_required(key, value):
    text, process = inputs()
    process[key] = value
    with pytest.raises(ValueError): audit(text, process)
