import copy
import numpy as np
import pytest
from audit_pressure_stencil_source import decode, audit


def source():
    def cell(x, y): return [1.+x/256.+y/512., .1, -.2, 0.]
    def bed(x, y): return x*.25+y*.5
    inside = [(x,y) for y in range(128) for x in range(128)]
    ring = [(x,y) for y in range(-3,131) for x in range(-3,131) if x<0 or y<0 or x>=128 or y>=128]
    old = [(-1,y) for y in range(128)]+[(128,y) for y in range(128)]+[(x,-1) for x in range(128)]+[(x,128) for x in range(128)]
    return dict(nx=128,ny=128,cell_meters=.5,origin_x=-5450.,origin_y=3566.,native_seconds=1.,revision=1,
        pressure_stencil_width=3,state=[v for p in inside for v in cell(*p)],bed=[bed(*p) for p in inside],
        pressure_stencil_state=[v for p in ring for v in cell(*p)],pressure_stencil_bed=[bed(*p) for p in ring],
        exterior_state=[v for p in old for v in cell(*p)],exterior_bed=[bed(*p) for p in old],face_normal_velocity=[.1]*512)


def test_complete_halo_retains_core_and_old_exterior_without_repair():
    record=source(); full, bed, report=decode(record)
    np.testing.assert_array_equal(full[3:131,3:131],np.array(record['state']).reshape(128,128,4))
    assert report['halo_cells']==1572 and report['old_exterior_cells_exact']==512
    assert report['new_samples_beyond_old_exterior']==1060
    b=copy.deepcopy(record);b['native_seconds']=1.125;b['revision']=2
    result=audit(dict(schema='raftsim.live_temporal_boundary_inputs.v1',first=record,second=b))
    assert result['passed'] and not result['pressure_boundary_qualified']


@pytest.mark.parametrize('bad',['missing','partial','negative','exterior'])
def test_missing_or_changed_samples_are_rejected(bad):
    record=source()
    if bad=='missing': del record['pressure_stencil_width']
    if bad=='partial':record['pressure_stencil_bed'].pop()
    if bad=='negative':record['pressure_stencil_state'][0]=-1.
    if bad=='exterior':record['exterior_state'][0]+=.125
    with pytest.raises(ValueError):decode(record)
