import json
import numpy as np
import pytest
from audit_detail_wave_regime import read_snapshot


def fixture(tmp_path):
    path = tmp_path/'paired.json'
    metadata = dict(schema='raftsim.detail.snapshot.v2', arrays_complete=True,
        dtype='little-endian float32', shape=[3, 4, 4], elapsed_s=10.,
        mean_sample_elapsed_s=9.9, height_datum='river_vertical_datum',
        mean_geometry_channels=['bed_m', 'sampled_surface_m', 'unmasked_depth_m', 'wet_fraction'])
    path.write_text(json.dumps(metadata))
    for name in ('flow', 'state', 'mean_geometry'):
        np.zeros((3, 4, 4), dtype='<f4').tofile(path.with_suffix(f'.{name}.f32'))
    return path, metadata


def test_paired_geometry_loaded_and_hash_bound(tmp_path):
    path, _ = fixture(tmp_path)
    _, arrays, hashes = read_snapshot(path)
    assert arrays['mean_geometry'].shape == (3, 4, 4)
    assert str(path.with_suffix('.mean_geometry.f32')) in hashes
    before = hashes[str(path.with_suffix('.mean_geometry.f32'))]
    np.ones((3, 4, 4), dtype='<f4').tofile(path.with_suffix('.mean_geometry.f32'))
    assert read_snapshot(path)[2][str(path.with_suffix('.mean_geometry.f32'))] != before


@pytest.mark.parametrize('change', [dict(height_datum='unknown'), dict(mean_sample_elapsed_s=10.1),
    dict(mean_sample_elapsed_s=float('nan')), dict(mean_geometry_channels=['bed', 'surface', 'depth', 'wet'])])
def test_paired_metadata_rejects_ambiguous_or_future_mean(tmp_path, change):
    path, metadata = fixture(tmp_path)
    metadata.update(change); path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError): read_snapshot(path)


def test_geometry_truncation_and_legacy_compatibility(tmp_path):
    path, metadata = fixture(tmp_path)
    path.with_suffix('.mean_geometry.f32').write_bytes(b'bad')
    with pytest.raises(ValueError): read_snapshot(path)
    metadata['schema'] = 'raftsim.detail.snapshot.v1'; path.write_text(json.dumps(metadata))
    assert 'mean_geometry' not in read_snapshot(path)[1]
