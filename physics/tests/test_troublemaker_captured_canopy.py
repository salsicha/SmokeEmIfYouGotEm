"""Registration, deterministic selection, provenance and normal-delivery guards."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from build_troublemaker_captured_canopy import image_pixels, separated_peaks
from audit_captured_rock_selection_edges import connected_to_seed, polygon_distance


def test_canopy_north_up_image_registration():
    bounds = {'xmin': 10, 'xmax': 20, 'ymin': 30, 'ymax': 40}
    row,col = image_pixels(np.array([10.5,19.5]), np.array([39.5,30.5]), bounds, (10,10,3))
    assert row.tolist() == [0,9] and col.tolist() == [0,9]


def test_canopy_outside_image_is_not_clamped():
    try:
        image_pixels(np.array([21]),np.array([35]),{'xmin':10,'xmax':20,'ymin':30,'ymax':40},(10,10,3))
    except ValueError:
        return
    raise AssertionError('Outside image was silently accepted')


def test_canopy_peaks_are_deterministic_and_not_random_scatter():
    xy = np.array([[0.,0.],[1,0],[10,0],[10.1,0]])
    h = np.array([4.,10.,8.,6.])
    assert separated_peaks(xy,h).tolist() == [1,2]
    assert separated_peaks(xy,h).tolist() == separated_peaks(xy,h).tolist()


def test_rock_support_does_not_bridge_diagonal_gap():
    available = np.eye(3,dtype=bool)
    seed = np.zeros((3,3),dtype=bool); seed[0,0] = True
    assert connected_to_seed(available,seed).sum() == 1


def test_search_region_distance_does_not_mean_rock_outline():
    assert np.allclose(polygon_distance(np.array([0.,.5,2]),np.array([.5,.5,.5]),[[0,0],[1,0],[1,1],[0,1]]),[0,.5,1])


def test_playable_canopy_provenance_and_uncertainty():
    path = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_canopy.json'
    data = json.loads(path.read_text())
    for source,digest in data['sources'].items():
        assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest() == digest
    assert data['normal_playable_level'] == '/Game/RaftSim/Maps/L_SouthFork_Troublemaker'
    assert data['world_y_sign'] == -1
    assert not data['tree_inventory_surveyed'] and not data['terrain_or_hydraulic_geometry_modified']
    assert data['instance_count'] == len(data['instances']) > 0
    assert all(i['ground_authority']==1 and i['support_return_count']>=12 and 3.5<=i['height_m']<=30 for i in data['instances'])


def test_canopy_has_no_runtime_scatter_tick_or_collision():
    source = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCapturedCanopyActor.cpp').read_text()
    assert 'PrimaryActorTick.bCanEverTick = false' in source
    assert 'ECollisionEnabled::NoCollision' in source
    assert 'SetGenerateOverlapEvents(false)' in source
    assert 'Rand' not in source


def test_canopy_waits_for_collision_before_root_validation():
    source = (ROOT/'unreal/Scripts/integrate_troublemaker_captured_canopy.py').read_text()
    assert source.index('finish_all_asset_compilation()') < source.index('line_trace_single(')
    assert 'abs(values[5].z-z) >= .1' in source
    assert 'root_failures' in source and 'raise AssertionError' in source
