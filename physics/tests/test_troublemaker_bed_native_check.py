import numpy as np
import pytest
from prepare_troublemaker_bed_native_check import delta_probes
from test_south_fork_terrain_revision import meshes


def test_all_changed_faces_and_native_coordinates():
    old, new = meshes()
    result = delta_probes(old, new, [100,200], 20)
    assert result['terrain_vertex_changes_cm'] == [dict(source_vertex_index=5,
        before=[100.,-100.,0.], after=[100.,-100.,-75.])]
    expected = np.flatnonzero(np.any(new['triangles'] == 5, axis=1))
    assert result['changed_triangle_indices'] == expected.tolist()
    assert result['changed_triangle_probe_count'] == len(expected)
    xyz = np.column_stack([new[k].ravel() for k in ('east_m','north_m','z_m')])
    np.testing.assert_array_equal(result['ground_triangle_centroids_cm'],
                                  xyz[new['triangles'][expected]].mean(axis=1)*100)


def test_protected_source_height_is_not_a_permitted_native_delta():
    old, new = meshes()
    new['z_m'][2,2] = -1
    with pytest.raises(ValueError, match='submerged-prior'):
        delta_probes(old, new, [100,200], 20)


def test_no_native_topology_or_source_frame_repair():
    old, new = meshes()
    new['east_m'][1,1] += .05
    with pytest.raises(ValueError, match='protected'):
        delta_probes(old, new, [100,200], 20)
