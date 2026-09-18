import pytest

from audit_crest_prefetch import audit


def evidence():
    log = '\n'.join(f'LogTemp: Display: CrestPrefetchAudit exact frame={2*i+5} samples=123 batches=3'
                    for i in range(64))
    process = dict(game_arguments=['-RaftSimPrefetchCrestProfile', '-RaftSimCrestPrefetchAudit'],
                   game_exit_code=0, game_timeout=False, suspend_status=0, resume_status=0)
    return log, process


def test_complete_exact_work_retains_all_rows_without_acceptance():
    log, process = evidence()
    log = 'LogInit: Command Line: -RaftSimPrefetchCrestProfile -RaftSimCrestPrefetchAudit\n'+log
    result = audit(log, process)
    assert result['passed'] and result['adopted_profiles'] == 64
    assert result['exact_sample_comparisons'] == 64*123
    assert len(result['rows']) == 64
    assert not any(result[k] for k in ('performance_accepted', 'visual_accepted', 'release_accepted'))


@pytest.mark.parametrize('change', ['short', 'mismatch', 'zero', 'malformed', 'duplicate', 'unordered',
                                  'exit', 'timeout', 'resume', 'suspend', 'missing', 'duplicate-option'])
def test_incomplete_or_failed_work_is_rejected(change):
    log, process = evidence()
    if change == 'short': log = '\n'.join(log.splitlines()[:-1])
    if change == 'mismatch': log += '\nCrestPrefetchAudit mismatch frame=200'
    if change == 'zero': log = log.replace('samples=123', 'samples=0', 1)
    if change == 'malformed': log = log.replace('batches=3', 'batches=3 unknown=1', 1)
    if change == 'duplicate': log += '\n'+log.splitlines()[-1]
    if change == 'unordered': log = '\n'.join(reversed(log.splitlines()))
    if change == 'exit': process['game_exit_code'] = 1
    if change == 'timeout': process['game_timeout'] = True
    if change == 'resume': process['resume_status'] = 1
    if change == 'suspend': process['suspend_status'] = None
    if change == 'missing': process['game_arguments'].pop()
    if change == 'duplicate-option': process['game_arguments'].append(process['game_arguments'][0])
    with pytest.raises(ValueError):
        audit(log, process)
