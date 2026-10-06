"""Source-identity guards for full-river integration candidates, not acceptance."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
GEOMETRY = BASE/'composite_terrain'
EXPORT = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912/Tiles'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_composite_retains_registered_source_and_explicit_inference():
    manifest = read(GEOMETRY/'manifest.json')
    for name, digest in manifest['artifacts'].items():
        assert sha(GEOMETRY/name) == digest
    assert manifest['registered_rapid_sha256'] == manifest['artifacts']['troublemaker_registered_source.npz']
    assert manifest['source_dry_vertices_bit_identical']
    assert manifest['captured_rapid_arrays_and_topology_byte_identical']
    assert manifest['seam_is_inferred']
    assert not manifest['coarse_bed_prior']['measured']
    assert not manifest['coarse_bed_prior']['calibrated']


def test_all_exported_tiles_share_source_and_full_river_world_frame():
    source = read(GEOMETRY/'render_tiles/manifest.json')
    exported = read(EXPORT/'manifest.json')
    coordinates = read(BASE/'playable_route/coordinate_map.json')
    assert source['source_composite_manifest_sha256'] == sha(GEOMETRY/'manifest.json')
    assert source['source_coordinate_map_sha256'] == sha(BASE/'playable_route/coordinate_map.json')
    assert exported['source_tile_manifest_sha256'] == sha(GEOMETRY/'render_tiles/manifest.json')
    assert len(source['tiles']) == len(exported['tiles']) == 390
    assert sum(t['triangle_count'] for t in source['tiles']) == read(GEOMETRY/'manifest.json')['coarse_triangle_count']
    assert len({t['name'] for t in source['tiles']}) == len(source['tiles'])
    for packet, tile in zip(source['tiles'], exported['tiles']):
        assert all(tile[k] == v for k, v in packet.items())
        assert sha(ROOT/packet['path']) == packet['sha256']
        assert sha(ROOT/tile['fbx']) == tile['fbx_sha256']
        expected = (np.array(packet['origin_utm_m'])-coordinates['origin_utm_m'])*[100, -100]
        assert np.allclose(packet['actor_translation_cm'], [*expected, 0], atol=1e-7, rtol=0)
        assert packet['actor_scale'] == [1, -1, 1]


def test_join_fields_remain_bound_to_geometry_and_global_progress_contract():
    folder = BASE/'rapid_join_flow'
    delivery, manifest = read(folder/'delivery.json'), read(folder/'manifest.json')
    for name, digest in delivery['files'].items():
        assert sha(folder/name) == digest
    assert delivery['source_geometry_sha256'] == sha(GEOMETRY/'manifest.json')
    assert delivery['source_bed_sample_bit_identical']
    assert manifest['review']['source_geometry_sha256'] == delivery['source_geometry_sha256']
    assert manifest['review']['frame_sha256'] == delivery['source_frame_sha256']
    coordinates = read(folder/'coordinate_map.json')
    assert sha(ROOT/coordinates['full_river_progress_coordinate_map']) == coordinates['full_river_progress_coordinate_map_sha256']
    assert coordinates['origin_utm_m'] == read(BASE/'playable_route/coordinate_map.json')['origin_utm_m']
    assert coordinates['world_y_sign'] == -1
    assert manifest['grid']['nx'] == 461 and manifest['grid']['ny'] == 321
    for record in manifest['bands'][0]['arrays'].values():
        values = np.load(folder/record['file'], allow_pickle=False)
        assert list(values.shape) == record['shape']
        assert str(values.dtype) == record['dtype']
        assert np.isfinite(values).all()


def test_candidate_diagnostics_do_not_claim_reconstruction_acceptance():
    manifest = read(BASE/'rapid_join_flow/manifest.json')
    delivery = read(BASE/'rapid_join_flow/delivery.json')
    assert not manifest['all_bands_passed'] and not manifest['production_promoted']
    assert not manifest['bands'][0]['validation']['passed']
    assert not manifest['review']['photorealism_accepted']
    assert not delivery['full_reconstruction_accepted']
