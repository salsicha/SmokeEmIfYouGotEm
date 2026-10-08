"""One-metre geometry stays explicit, source guarded, and consumer consistent."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest
from shapely.geometry import LineString

from chilko_encoded_capacity import EncodedSections, capacity_grid, validate_capacity_grid
from chilko_triangle_ownership import support_offsets, support_policy, preserve_triangle_support
from continuous_collision_probes import owners
from export_chilko_corridor_terrain import export
from export_colorado_continuous_terrain import LandscapeTriangles, encode_height, sha, HEIGHT_BASE, HEIGHT_RANGE
from export_colorado_catalog_runtime import landscape_sample
from test_chilko_encoded_capacity import model


@pytest.mark.parametrize('spacing', [1., 2.])
def test_all_37_probes_match_positive_native_basis(spacing):
    z=np.zeros((3,3));z[1,1]=1
    offsets=support_offsets(spacing)
    assert offsets.shape==(37,2)
    for r in range(-4,5):
        for c in range(-4,5):
            present=np.any(np.all(offsets==[c*spacing/4,-r*spacing/4],axis=1))
            assert present == (landscape_sample(z,1+r/4,1+c/4)>0)


@pytest.mark.parametrize('spacing', [0., .5, 3., np.nan, np.inf, True])
def test_unsupported_spacing_rejected(spacing):
    with pytest.raises(ValueError): capacity_grid([0.,0.],spacing)
    with pytest.raises(ValueError): support_offsets(spacing)


def test_grid_receipt_prevents_accidental_two_metre_export():
    fine=capacity_grid([0.,0.],1.)
    validate_capacity_grid(fine,[0.,0.],1.)
    assert fine['support_policy']==support_policy(1.)
    with pytest.raises(ValueError): validate_capacity_grid(fine,[0.,0.])
    with pytest.raises(ValueError): validate_capacity_grid(dict(fine,support_policy=support_policy(2.)),[0.,0.],1.)


def test_fine_fit_matches_guarded_quantized_triangles():
    m=model()
    xy=np.stack(np.meshgrid([100.25,102.75],np.arange(-8.,9.)),axis=-1).transpose(1,0,2)
    sections=EncodedSections(m,xy,[0,0],np.full(2,.01),terrain_spacing_m=1.)
    a,_,q=sections.fit(20.)
    assert np.all(q>=20.)
    m.depth[:]=.05
    sections.apply_geographic_envelope(m,m.depth,a)
    guarded=preserve_triangle_support(m,sections.nodes,m.sample(sections.nodes),spacing_m=1.)
    decoded=HEIGHT_BASE+encode_height(guarded['height_m']).astype(float)*HEIGHT_RANGE/65535
    assert np.all(decoded[sections.indices]<=sections.vertex_heights(a)+1e-10)
    # The finer guard still refuses protected ground in its own footprint.
    assert np.all(guarded['height_m'][~guarded['inferred_bed']]==guarded['source_height_m'][~guarded['inferred_bed']])


def test_depth_builder_records_explicit_fine_grid(tmp_path):
    from build_chilko_corridor_depth import build
    m=model();m.surface=np.array([1000.,1000.]);m.terrain=SimpleNamespace(folder=Path('terrain'))
    m.receipt={key:'fixture' for key in ('profile_manifest_sha256','profile_sha256','terrain_manifest_sha256',
        'route_sha256','planform_sha256','ownership_policy')}
    frame=dict(station=np.array([100.,102.]),source_station=np.array([100.,102.]),
        xy=np.array([[100.,0.],[102.,0.]]),normal=np.array([[0.,1.],[0.,1.]]))
    with patch('build_chilko_corridor_depth.CorridorBed',return_value=m), \
            patch('build_chilko_corridor_depth.hydraulic_frame',return_value=(frame,{})), \
            patch('build_chilko_corridor_depth.validate_branch_coverage',return_value={}), \
            patch('build_chilko_corridor_depth.sha',return_value='fixture'):
        receipt=build('terrain','profile',tmp_path/'depth',origin=[0.,0.],terrain_spacing_m=1.)
    assert receipt['capacity_grid']==capacity_grid([0.,0.],1.)
    assert receipt['hydraulic_solution'] is False
    with np.load(tmp_path/'depth/depth.npz') as z:
        assert np.all(z['inferred_capacity_m3s']>=45.)


def test_one_metre_png_export_seams_and_native_chunk_ownership(tmp_path):
    terrain=tmp_path/'source';terrain.mkdir()
    source=terrain/'manifest.json';source.write_text('{}')
    profile=tmp_path/'profile.json';profile.write_text('{}')
    def sample(xy):
        h=1000+.01*xy[...,0]+.02*xy[...,1]
        return dict(height_m=h,source_height_m=h.copy(),source_kind=np.ones(h.shape,np.uint8),
                    inferred_bed=np.zeros(h.shape,bool),mapped_water=np.zeros(h.shape,bool),
                    reference_m=np.full(h.shape,np.nan))
    m=SimpleNamespace(line=LineString([(0,0),(260,0)]),sample=sample,
        terrain=SimpleNamespace(folder=terrain,manifest=dict(source_kind={'1':'fixture'})),
        receipt=dict(terrain_manifest_sha256=sha(source),profile_manifest=str(profile),profile_manifest_sha256=sha(profile)))
    out=tmp_path/'encoded'
    with patch('export_chilko_corridor_terrain.CorridorBed',return_value=m):
        manifest=export(terrain,tmp_path,out,[0,0],900.,buffer_m=100,spacing_m=1.,chunk_window=[-1,-1,2,0])
    assert manifest['geographic_scope']['chunk_window_inclusive']==[-1,-1,2,0]
    assert 'route_interval_m' not in manifest['geographic_scope']
    assert 'Bounded' in manifest['scope']
    assert len(manifest['chunks'])==8
    assert manifest['landscape']['span_m']==126
    assert manifest['landscape']['scale_xyz'][:2]==[100,100]
    assert manifest['inference_support_policy']==support_policy(1.)
    reader=LandscapeTriangles(out)
    xy=np.array([[0.,0.],[126.,0.],[126.25,.75],[252.,0.],[259.75,-.25]])
    np.testing.assert_allclose(reader.sample(xy),sample(xy)['height_m'],atol=HEIGHT_RANGE/65535/2,rtol=0)
    chunks={tuple(c['chunk']):i for i,c in enumerate(manifest['chunks'])}
    points=np.c_[xy[:,0]*100,-xy[:,1]*100,np.zeros(len(xy))]
    ids=owners(points,chunks,span_cm=12600.)
    for p,i in zip(points,ids):
        corner=np.array(manifest['chunks'][i]['world_northwest_xy_cm'])
        assert np.all(p[:2]>=corner) and np.all(p[:2]<=corner+12600.)
    # A metadata-only relabel to the old scale must fail, not rescale geography.
    manifest['landscape']['spacing_m']=2.
    (out/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError): LandscapeTriangles(out)


@pytest.mark.parametrize('window', [[0,0,1], [1,0,0,1], [0,2,1,1], [0.,0,1,1], [True,0,1,1], [100,100,101,101]])
def test_bad_or_nonintersecting_window_fails_before_writing(tmp_path,window):
    m=model();m.receipt={}
    with patch('export_chilko_corridor_terrain.CorridorBed',return_value=m):
        with pytest.raises(ValueError,match='chunk window|Chunk window'):
            export('terrain','profile',tmp_path/'out',[0,0],900.,spacing_m=1.,chunk_window=window)
    assert not (tmp_path/'out').exists()
