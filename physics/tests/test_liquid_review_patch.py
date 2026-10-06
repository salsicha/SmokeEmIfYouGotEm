"""Offline liquid diagnostics must preserve bed shape and remain review-only."""
from collections import Counter
from pathlib import Path
import json
import runpy
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def geometry():
    return runpy.run_path(str(ROOT/'unreal/Scripts/liquid_review_geometry.py'))['height_volume_geometry']


def test_liquid_volume_is_closed_outward_and_preserves_interior_bed():
    lower = [[0., .3, .2], [.1, .8, .3], [.2, .4, .2]]
    upper = [[z+1. for z in row] for row in lower]
    vertices, faces = geometry()(upper, lower, .5, .5)
    assert vertices[9+4] == (.5,.5,.8)  # The lower interior point cannot be flattened.
    edges = Counter((a,b) for f in faces for a,b in zip(f, f[1:]+f[:1]))
    assert all(count == 1 and edges[(b,a)] == 1 for (a,b),count in edges.items())
    # Triangulate faces for a signed volume; outward winding must be positive.
    v = np.array(vertices)
    volume = sum(np.dot(v[f[0]], np.cross(v[f[i]],v[f[i+1]]))/6.
                 for f in faces for i in range(1,len(f)-1))
    assert abs(volume-1.) < 1e-10


def test_liquid_volume_rejects_inverted_nonfinite_and_mismatched_grids():
    valid = [[1.,1.],[1.,1.]]
    for lower, dx in [([[0.],[0.]],1.), ([[2.,0.],[0.,0.]],1.),
                      ([[float('nan'),0.],[0.,0.]],1.), ([[0.,0.],[0.,0.]],0.)]:
        try:
            geometry()(valid,lower,dx,1.)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid liquid volume accepted')


def exporter():
    sys.path.insert(0,str(ROOT/'physics/scripts'))
    try:
        return runpy.run_path(str(ROOT/'physics/scripts/export_liquid_review_patch.py'))['export']
    finally:
        sys.path.pop(0)


def test_liquid_patch_export_units_datum_flux_and_no_overwrite():
    export = exporter()
    grid = SimpleNamespace(nx=9,ny=9,dx=.5,dy=.5,origin_x=100.,origin_y=-2.)
    bed = np.full((9,9),10.)
    scenario = SimpleNamespace(grid=grid,bed=bed)
    state = SimpleNamespace(depth=np.full_like(bed,2.), eta=bed+2.,
        u=np.full_like(bed,3.),v=np.zeros_like(bed))
    with TemporaryDirectory(prefix='raftsim-liquid-test-') as temporary:
        parent = Path(temporary)
        frame = parent/'frame.csv'
        frame.write_text('row,col\n0,0\n')
        output = parent/'input.json'
        with patch.dict(export.__globals__, read_scenario2_5d_package=lambda _:scenario,
                        validated_frame_state=lambda *_:state):
            result = export(parent,frame,output,[100.,104.,-2.,2.])
            assert result['source_origin_station_lateral_datum'] == [100.,-2.,10.]
            assert result['inlet_section_flux_m3s'] == 24.
            assert result['bed'][4][4] == 0. and result['eta'][4][4] == 2.
            assert not result['production_promoted'] and not result['photorealism_accepted']
            assert json.loads(output.read_text()) == result
            try:
                export(parent,frame,output,[100.,104.,-2.,2.])
            except ValueError:
                pass
            else:
                raise AssertionError('Existing evidence overwritten')
            for bounds, speed in [([99.,103.,-2.,2.],3.),([100.,104.,-2.,2.],-1.)]:
                state.u[:] = speed
                try:
                    export(parent,frame,parent/'invalid.json',bounds)
                except ValueError:
                    pass
                else:
                    raise AssertionError('Outside or reversed-inlet patch accepted')
            assert not (parent/'invalid.json').exists()
            state.u[:] = 3.
            state.depth[4,4] = .01
            try:
                export(parent,frame,parent/'dry.json',[100.,104.,-2.,2.])
            except ValueError:
                pass
            else:
                raise AssertionError('Dry interior accepted into closed water fill')
            assert not (parent/'dry.json').exists()
    assert np.all(bed == 10.)
