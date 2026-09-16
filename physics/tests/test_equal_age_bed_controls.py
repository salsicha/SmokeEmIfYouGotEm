import copy
import pytest
from compare_south_fork_bed_cooks import same_physical_settings


def fixture():
    return dict(metadata={'provenance':'old'},grid={'nx':80,'dx':1.,'origin_x':10.},
                fixed_dt=.05,roughness=.035,boundaries=[{'edge':'west','kind':'bank'}],
                raft={'mass_kg':420.})


def test_only_provenance_metadata_may_differ():
    old=fixture();new=copy.deepcopy(old);new['metadata']={'provenance':'declared bed revision'}
    same_physical_settings(old,new)


@pytest.mark.parametrize('field,value',[('fixed_dt',.1),('roughness',.03),
    ('grid',{'nx':80,'dx':2.,'origin_x':10.}),('boundaries',[{'edge':'west','kind':'outflow'}]),
    ('raft',{'mass_kg':400.})])
def test_numerics_boundaries_geometry_and_raft_are_not_ignored(field,value):
    old=fixture();new=copy.deepcopy(old);new[field]=value
    with pytest.raises(ValueError,match='physical scenario'):same_physical_settings(old,new)
