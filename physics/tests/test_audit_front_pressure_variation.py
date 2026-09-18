from copy import deepcopy
from fractions import Fraction as F

import pytest

from audit_south_fork_front_pressure_variation import check_case
from test_subcell_moving_pressure_metric import geometry, metric
from test_subcell_front_pressure_variation import P, PD


@pytest.fixture
def original():
    g=geometry();m=metric(g);solved=m.evaluate(P,PD)
    prior=dict(active_original_parts=g.active,volumes=g.volumes,volume_rates=g.volume_rates,
               divergence=g.divergence,divergence_rate=g.divergence_rate,kinetic=g.kinetic,
               kinetic_rate=g.kinetic_rate,faces=g.faces,outer_pressure_boundary='reflecting')
    record=dict(common_front_pressure=prior,moving_physical_metric=solved,
        wet_side=dict(momentum=P[0]),dry_side=dict(momentum=P[1]),
        wet_side_rates=dict(momentum_rate=PD[0]),dry_side_rates=dict(momentum_rate=PD[1]))
    record['moving_physical_metric'].update(physical_momentum=P,physical_momentum_rate=PD)
    return g,record


def test_full_original_case_work_in_both_coordinates(original):
    g,record=original;result=check_case(g,record)
    assert result['exact_original_case_pullback']
    assert result['physical_time_work']['energy_direction']==result['canonical_time_work']['energy_direction']
    assert result['physical_time_work']['face_column_work']!=0
    assert not result['native_or_conservative_force_or_wetting_or_gameplay_accepted']


@pytest.mark.parametrize('kind',('boundary','owners','volume','matrix','face_count','face_owners','face_column',
                               'momentum','rate','canonical_rate','energy','work'))
def test_changed_original_evidence_is_not_reinterpreted(original,kind):
    g,record=original;record=deepcopy(record);prior=record['common_front_pressure'];solved=record['moving_physical_metric']
    if kind=='boundary':prior['outer_pressure_boundary']='open'
    elif kind=='owners':prior['active_original_parts']=tuple(reversed(g.active))
    elif kind=='volume':prior['volumes']=(g.volumes[0]+F(1,10**400),g.volumes[1])
    elif kind=='matrix':prior['kinetic'][0][0]+=F(1,10**400)
    elif kind=='face_count':prior['faces'].pop()
    elif kind=='face_owners':prior['faces'][0]['owners']=(-1,)
    elif kind=='face_column':prior['faces'][0]['column_normal']=(F(1,10**400),F(0))
    elif kind=='momentum':record['wet_side']['momentum']=(0,0)
    elif kind=='rate':record['wet_side_rates']['momentum_rate']=(0,0)
    elif kind=='canonical_rate':solved['canonical_momentum_rate']=((0,0),(0,0))
    elif kind=='energy':solved['kinetic_energy_rate']+=F(1,10**400)
    elif kind=='work':solved['geometry_time_work']+=F(1,10**400)
    with pytest.raises(ValueError):check_case(g,record)
