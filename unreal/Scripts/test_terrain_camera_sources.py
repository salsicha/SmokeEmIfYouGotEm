import numpy as np
import pytest

from audit_terrain_camera_sources import resolve_ray
import audit_terrain_camera_sources as audit


def test_reflected_ray_chooses_nearest_solid_not_native_index():
    triangle = np.array([[0., 0., 2.], [1., 0., 2.], [0., 1., 2.]])
    sources = {'ground': (triangle, np.array([[0, 1, 2]])),
               'cap': (triangle+[0, 0, 1], np.array([[0, 2, 1]]))}
    ray = dict(ray_origin_cm=[525., -725., 1000.], ray_direction=[0., 0., -1.], face_index=7654)
    result = resolve_ray(ray, sources, [500., -700., 0.], [1., -1., 1.])
    assert result['source'] == 'cap' and result['source_triangle'] == 0
    np.testing.assert_allclose(result['local_hit_m'], [.25, .25, 3.], rtol=0, atol=1e-14)
    assert result['distance_m'] == 7 and result['slope_degrees'] == 0


@pytest.mark.parametrize('direction', [[0., 0., 1.], [1., 0., 0.]])
def test_backward_and_parallel_rays_do_not_hit(direction):
    source = {'ground': (np.array([[0., 0., 2.], [1., 0., 2.], [0., 1., 2.]]), np.array([[0, 1, 2]]))}
    assert resolve_ray(dict(ray_origin_cm=[25., 25., 1000.], ray_direction=direction), source, [0., 0., 0.], [1., 1., 1.]) is None


def test_rejects_nonunit_ray():
    with pytest.raises(ValueError, match='Unit ray'):
        resolve_ray(dict(ray_origin_cm=[0., 0., 0.], ray_direction=[0., 0., -2.]), {}, [0., 0., 0.], [1., 1., 1.])


def test_candidate_identity_is_explicit_and_default_remains_strict(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    local = tmp_path/'tmp'
    local.mkdir()
    ground = local/'candidate.npz'
    ground.write_bytes(b'candidate')
    baseline = tmp_path/'baseline.npz'
    baseline.write_bytes(b'baseline')
    cap = tmp_path/'cap.npz'
    cap.write_bytes(b'cap')
    originals = {'ground': (baseline, audit.sha(baseline)), 'cap': (cap, audit.sha(cap))}
    monkeypatch.setattr(audit, 'IDENTITIES', originals)
    assert audit.source_identities() == originals
    selected = audit.source_identities(ground, audit.sha(ground))
    assert selected['ground'][0] == ground and selected['cap'] == originals['cap']
    assert audit.IDENTITIES == originals
    for path, digest in [(ground, None), (None, audit.sha(ground)),
                         (baseline, audit.sha(baseline)), (ground, '0'*64),
                         (ground, 'F'*64), (ground, '')]:
        with pytest.raises(ValueError):
            audit.source_identities(path, digest)
    cap.write_bytes(b'changed')
    with pytest.raises(ValueError, match='identity changed'):
        audit.source_identities(ground, audit.sha(ground))
