import pytest
from audit_crest_interval_pair import summarize


def fixture():
    return dict(schema='raftsim.crest_interval_pair.v1',exact=True,pairs=[dict(pair=i,frame=122+i,
        vertices=50625,triangles=120000,exact=True,candidate_first=bool(i%2),reference_ms=3.,candidate_ms=2.) for i in range(64)])


def test_complete_evidence_stays_component_scoped():
    result=summarize(fixture())
    assert result['exact_topology_and_production'] and result['measured_both_orders_faster']
    assert result['groups']['candidate_first']['pairs']==32 and not result['release_accepted']


def test_losing_order_and_equality_failure_are_not_hidden():
    data=fixture();data['pairs'][10]['exact']=False
    assert not summarize(data)['exact_topology_and_production']
    data=fixture();data['exact']=False
    assert not summarize(data)['exact_topology_and_production']
    data=fixture()
    for row in data['pairs'][::2]:row['candidate_ms']=3.1
    assert not summarize(data)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value',[('pair',True),('pair',1),('frame',119),('frame',120.5),
    ('vertices',0),('triangles',True),('exact',1),('candidate_first',True),('reference_ms',0),
    ('candidate_ms',float('nan')),('candidate_ms',float('inf')),('candidate_ms',True)])
def test_malformed_or_unmeasured_rows_reject(key,value):
    data=fixture();data['pairs'][0][key]=value
    with pytest.raises(ValueError):summarize(data)


def test_missing_pairs_wrong_schema_single_frame_and_reverse_time_reject():
    data=fixture();data['pairs'].pop()
    with pytest.raises(ValueError):summarize(data)
    data=fixture();data['schema']='other'
    with pytest.raises(ValueError):summarize(data)
    data=fixture()
    for row in data['pairs']:row['frame']=120
    with pytest.raises(ValueError):summarize(data)
    data=fixture();data['pairs'][4]['frame']=121
    with pytest.raises(ValueError):summarize(data)
