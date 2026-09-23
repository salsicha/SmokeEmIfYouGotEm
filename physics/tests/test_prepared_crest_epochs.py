import pytest
from audit_prepared_crest_epochs import summarize


def lines():
    return ['LogTemp: Prepared physical crest candidate active: audit=1; original arithmetic'] + [
        f'LogTemp: PREPARED_CREST_EPOCH epoch={i} frame={i*2+1} queries=200000 mismatches=0' for i in range(64)]


def test_every_epoch_retained_without_acceptance_claim():
    r = summarize('\n'.join(lines()))
    assert r['queried_epochs'] == 64 and r['queries'] == 12800000 and r['exact']
    assert len(r['rows']) == 64
    assert not r['performance_accepted'] and not r['visual_accepted']


@pytest.mark.parametrize('change', ('activation','short','zero','duplicate','order','mismatch','malformed','negative'))
def test_incomplete_or_inexact_capture_rejected(change):
    rows = lines()
    if change == 'activation': rows.pop(0)
    elif change == 'short': rows.pop()
    elif change == 'zero': rows[-1] = rows[-1].replace('queries=200000', 'queries=0')
    elif change == 'duplicate': rows.append(rows[-1])
    elif change == 'order': rows[1], rows[2] = rows[2], rows[1]
    elif change == 'mismatch': rows[2] = rows[2].replace('mismatches=0','mismatches=1')
    elif change == 'malformed': rows[-1] += ' missing'
    elif change == 'negative': rows[-1] = rows[-1].replace('queries=200000','queries=-1')
    with pytest.raises(ValueError): summarize('\n'.join(rows))


def test_zero_query_epoch_is_retained_but_does_not_satisfy_coverage():
    r = summarize('\n'.join(lines()+['PREPARED_CREST_EPOCH epoch=64 frame=999 queries=0 mismatches=0']))
    assert len(r['rows']) == 65 and r['queried_epochs'] == 64


def test_distinct_startup_profiles_in_same_frame_are_not_duplicates():
    rows = lines()
    rows[2] = rows[2].replace('frame=3','frame=1')
    assert summarize('\n'.join(rows))['queried_epochs'] == 64


def test_missing_middle_epoch_cannot_be_covered_by_more_later_epochs():
    rows = lines()+['PREPARED_CREST_EPOCH epoch=64 frame=999 queries=200000 mismatches=0']
    rows.pop(30)
    with pytest.raises(ValueError): summarize('\n'.join(rows))
