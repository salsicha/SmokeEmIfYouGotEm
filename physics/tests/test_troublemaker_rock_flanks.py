"""Guards for explicitly inferred flanks; no measured-point smoothing."""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from reconstruct_troublemaker_rock_flanks import extend_fixed_surface


def fixture():
    x, y = np.meshgrid(np.arange(9.)*.5, np.arange(9.)*.5)
    xyz = np.column_stack((x.ravel(), y.ravel(), np.zeros(81)))
    xyz[40, 2] = 3.
    faces = []
    for row in range(8):
        for col in range(8):
            a = row*9+col
            faces += [[a, a+1, a+9], [a+1, a+10, a+9]]
    distance = np.linalg.norm(xyz[:, :2]-xyz[40, :2], axis=1)
    editable = (distance > 0) & (distance <= 1.5)
    return xyz, np.asarray(faces), editable


def test_fixed_captured_points_and_exterior_are_exact():
    xyz, faces, editable = fixture()
    before = xyz.copy()
    z, stats = extend_fixed_surface(xyz, faces, editable)
    assert np.array_equal(xyz, before)
    assert np.array_equal(z[~editable], xyz[~editable, 2])
    assert z[40] == 3 and np.all(z >= xyz[:, 2]) and z.max() == 3
    assert np.count_nonzero(z > xyz[:, 2]) == editable.sum()
    assert stats['maximum_residual_m'] < 1e-6
    assert max(abs(z[40]-z[39]), abs(z[40]-z[41])) < 3


def test_no_overshoot_or_lowering_on_registered_irregular_coordinates():
    xyz, faces, editable = fixture()
    xyz[:, 0] += .04*np.sin(xyz[:, 1]*3)
    xyz[:, 2] += .1*xyz[:, 0] + .05*xyz[:, 1]
    z, _ = extend_fixed_surface(xyz, faces, editable)
    assert np.array_equal(z[~editable], xyz[~editable, 2])
    assert np.all(z >= xyz[:, 2]) and z.max() <= xyz[:, 2].max()
    assert np.array_equal(z, extend_fixed_surface(xyz, faces, editable)[0])


def test_unchanged_flat_surface_and_empty_mask():
    xyz, faces, editable = fixture()
    xyz[:, 2] = 1.25
    assert np.array_equal(extend_fixed_surface(xyz, faces, editable)[0], xyz[:, 2])
    assert np.array_equal(extend_fixed_surface(xyz, faces, editable & False)[0], xyz[:, 2])


def test_unconverged_solution_is_rejected():
    xyz, faces, editable = fixture()
    try:
        extend_fixed_surface(xyz, faces, editable, max_iterations=1)
    except ValueError as error:
        assert 'did not converge' in str(error)
    else:
        raise AssertionError('Unconverged surface was accepted')


def test_bad_coordinates_and_unconnected_nodes_are_rejected():
    xyz, faces, editable = fixture()
    invalid = xyz.copy(); invalid[0, 0] = np.nan
    for points, triangles in ((invalid, faces), (xyz, np.empty((0, 3), int))):
        try:
            extend_fixed_surface(points, triangles, editable)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid geometry was accepted')


def test_real_candidate_keeps_captures_and_separates_inferred_provenance():
    import json
    from PIL import Image
    from reconstruct_troublemaker_rock_flanks import ROOT, PARENT
    target = ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912'
    manifest = json.loads((target/'manifest.json').read_text())
    with np.load(PARENT/'registered_mesh_source.npz') as old, np.load(target/'registered_mesh_source.npz') as new:
        changed = new['authority'] != old['authority']
        assert changed.sum() == manifest['flank_reconstruction']['changed_vertices'] > 0
        assert np.all(old['authority'][changed] == 2) and np.all(new['authority'][changed] == 5)
        for key in ('east_m','north_m','triangles','rock_source_return_index'):
            assert np.array_equal(old[key],new[key])
        assert np.array_equal(old['z_m'][~changed],new['z_m'][~changed])
        mask = np.asarray(Image.open(ROOT/'unreal/SourceArt/RaftSim/TroublemakerInferredFlankAuthority20260912/T_TroublemakerSurfaceAuthority.png'))
        assert np.array_equal(mask[:,:,1] > 0, np.isin(new['authority'],[3,5]))
        assert np.array_equal(mask[:,:,2] > 0, new['authority'] == 5)
        assert not mask[:,:,0][new['authority'] != 1].any()


def test_current_flow_route_retains_depth_footprint_and_effort_limits():
    import hashlib
    import json
    from reconstruct_troublemaker_rock_flanks import ROOT
    route = json.loads((ROOT/'docs/reconstruction-review-2026-09-07/guided-route-playable.json').read_text())
    folder = ROOT/route['cooked_fields_dir']
    manifest = json.loads((folder/'manifest.json').read_text())
    assert route['source_geometry_sha256'] == manifest['review']['source_geometry_sha256']
    arrays = manifest['bands'][0]['arrays']
    values = {}
    for name in ('h','u','v'):
        path = folder/arrays[name]['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == arrays[name]['sha256']
        values[name] = np.load(path)
    assert route['required_depth_m'] == .55 and route['paddling_speed_limit_mps'] == 2.2
    assert route['planning_footprint_length_m'] == 4.7 and route['planning_footprint_width_m'] == 2.4
    points = np.asarray(route['station_lateral_m'])
    grid = manifest['grid']
    assert grid['dx_m'] == grid['dy_m'] == 1.
    xy = points-np.array([grid['origin_x_m'],grid['origin_y_m']])
    minimum = np.inf
    # Independent bilinear footprint check, not a recorded planner success flag.
    for dx in (-2.35,-2,-1,0,1,2,2.35):
        for dy in (-1.2,-1,0,1,1.2):
            p = xy+[dx,dy]
            lo = np.floor(p).astype(int); t = p-lo
            x,y = lo.T; u,v = t.T; h = values['h']
            assert x.min() >= 0 and y.min() >= 0 and x.max()+1 < h.shape[1] and y.max()+1 < h.shape[0]
            depth = h[y,x]*(1-u)*(1-v)+h[y,x+1]*u*(1-v)+h[y+1,x]*(1-u)*v+h[y+1,x+1]*u*v
            minimum = min(minimum,float(depth.min()))
    assert minimum >= .55
    steps = np.diff(points,axis=0); direction = steps/np.linalg.norm(steps,axis=1)[:,None]
    index = xy[:-1].astype(int); x,y = index.T
    velocity = np.column_stack((values['u'][y,x],values['v'][y,x]))
    along = np.sum(velocity*direction,axis=1)
    cross = velocity[:,1]*direction[:,0]-velocity[:,0]*direction[:,1]
    assert np.all(abs(cross) < 2.2)
    assert np.all(along+np.sqrt(2.2**2-cross**2) > .1)
