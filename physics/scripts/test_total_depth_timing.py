import pytest
from audit_total_depth_timing import summarize


def log():
    lines=['four alternating warm-up intervals, then eight paired samples with alternating order',
        'Test Completed. Result={Success} Name={TemporalEvolutionGPU}',
        '**** TEST COMPLETE. EXIT CODE: 0 ****',
        'temporal evolution trials2 accepted2 status1 mode1 bits0/0/0/1']
    for s in range(8):
        for c in range(2):
            for g in range(2):lines.append(f'GPU temporal evolution sample{s} graph{g} slots2 cull{c} {1+s+g+c}.0 ms')
    return '\n'.join(lines)


def test_all_active_and_inactive_samples_retained_separately():
    result=summarize(log())
    assert result['direct']['active_two_steps']['samples']==list(range(1,9))
    assert result['direct']['active_two_steps']['p95_ms_nearest_rank']==8
    assert result['indirect']['inactive_two_slots']['samples']==list(range(3,11))
    assert result['indirect']['active_graph_mean_per_accepted_step_ms']==2.75


@pytest.mark.parametrize('bad',['missing','duplicate','failed','no_warmup','wrong_steps','wrong_slots','zero'])
def test_incomplete_or_unpaired_timing_rejected(bad):
    text=log()
    if bad=='missing':text='\n'.join(text.splitlines()[:-1])
    if bad=='duplicate':text+='\n'+text.splitlines()[-1]
    if bad=='failed':text=text.replace('EXIT CODE: 0','EXIT CODE: 1')
    if bad=='no_warmup':text='\n'.join(text.splitlines()[1:])
    if bad=='wrong_steps':text=text.replace('trials2 accepted2','trials3 accepted3')
    if bad=='wrong_slots':text=text.replace('slots2','slots4')
    if bad=='zero':text=text.replace(' 1.0 ms',' 0.0 ms')
    with pytest.raises(ValueError):summarize(text)
