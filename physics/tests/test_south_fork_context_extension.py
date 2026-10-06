import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
EXT = BASE/'source_context_extension'


def test_context_uses_retained_sources_and_keeps_base_authority():
    report = json.loads((EXT/'manifest.json').read_text())
    assert report['completed'] and report['missing_source_vertex_count'] == 0
    assert report['base_geometry_manifest_sha256'] == hashlib.sha256((BASE/'composite_terrain/manifest.json').read_bytes()).hexdigest()
    assert report['original_source_vertices_bit_identical'] and report['original_bed_vertices_bit_identical']
    assert report['original_coarse_triangles_retained'] and report['registered_rapid_and_seam_unchanged']
    assert not report['measured_bathymetry'] and not report['full_reconstruction_accepted']
    for name,digest in report['artifacts'].items():
        assert hashlib.sha256((EXT/name).read_bytes()).hexdigest() == digest


def test_larger_context_batches_keep_every_source_triangle():
    versions = []
    for folder in ['render_tiles','render_tiles_1024m']:
        manifest = json.loads((EXT/folder/'manifest.json').read_text())
        faces = []
        for tile in manifest['tiles']:
            path = ROOT/tile['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == tile['sha256']
            with np.load(path,allow_pickle=False) as packet:
                faces.append(np.sort(packet['source_grid_vertex_index'][packet['triangles']],axis=1))
        array = np.ascontiguousarray(np.vstack(faces),dtype=np.int64)
        ordered = array.view([('a','<i8'),('b','<i8'),('c','<i8')]).reshape(-1)
        versions.append(np.sort(ordered))
    assert len(versions[0]) == 415380 and np.array_equal(versions[0],versions[1])


def test_supplemental_faces_do_not_overlap_base_faces_or_rapid_cut():
    report = json.loads((EXT/'manifest.json').read_text())
    with np.load(EXT/'topology.npz') as data:
        combined, supplement = data['valid_quads'],data['supplemental_quads']
    with np.load(BASE/'composite_terrain/coarse_topology.npz') as data:
        original = data['valid_quads']
    r,c = report['original_grid_offset_row_col']
    embedded = np.zeros(combined.shape,dtype=bool)
    embedded[r:r+original.shape[0],c:c+original.shape[1]] = original
    assert not (supplement & embedded).any()
    assert np.array_equal(combined, supplement | embedded)
    assert supplement.sum()*2 == 415380
