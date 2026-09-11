"""Register the liquid test footprint to source imagery, without moving terrain."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
import numpy as np

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
WORK = ROOT / 'tmp/south-fork-liquid-control-centered-20260909'


def metric_points(local, origin, downstream, left):
    rotation = np.column_stack([downstream, left])
    if rotation.shape != (2, 2) or not np.isfinite(rotation).all() or not np.allclose(rotation.T @ rotation, np.eye(2), atol=1e-8) or np.linalg.det(rotation) < 0:
        raise ValueError('Expected a rigid right-handed registration')
    if np.asarray(origin).shape != (2,) or not np.isfinite(origin).all() or not np.isfinite(local).all():
        raise ValueError('Expected finite metric coordinates')
    return np.asarray(local) @ rotation.T + np.asarray(origin)


def run(output, window=None):
    sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
    from PIL import Image
    from shapely.geometry import Polygon
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a new output directory inside the workspace')
    if window is None:
        reg = json.loads((WORK / 'registration.json').read_text())
        mesh_meta = json.loads((WORK / 'geometry/manifest.json').read_text())
    else:
        window=Path(window).resolve()
        domain=json.loads((window/'manifest.json').read_text())
        mesh_meta=json.loads((ROOT/domain['source_geometry_manifest']).read_text())
        reg=json.loads((ROOT/domain['source_hydraulic_directory']).parent.joinpath('registration.json').read_text())
    source_meta = json.loads((BASE / 'sources/troublemaker_naip_export.json').read_text())
    regions = json.loads((BASE / 'troublemaker/rock_review_regions.json').read_text())
    controls = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())
    control = next(f for f in controls['features'] if f.get('id') == 'troublemaker_crux_search')
    origin = np.asarray(control['properties']['metric_xy'])
    bounds = source_meta['extent']
    image_center = np.array([(bounds['xmin'] + bounds['xmax']) / 2,
                             (bounds['ymin'] + bounds['ymax']) / 2])
    boundary_path = (ROOT / 'unreal/SourceArt/RaftSim/SouthForkLiquidControlCentered20260909/grid_boundary_profile.json') if window is None else window/'manifest.json'
    boundary = json.loads(boundary_path.read_text())
    if boundary['source_geometry_sha256'] != mesh_meta['mesh_sha256']:
        raise ValueError('Boundary and terrain refer to different geometry')
    if window is None:
        hi = np.asarray(boundary['physical_extents_cm'][:2]) / 200
        lo = -hi
        centre=np.zeros(2)
    else:
        centre=np.asarray(boundary['centre_station_lateral_m'])
        lo,hi=np.asarray(boundary['fluid_domain_local_bounds_m'])[:,:2]+centre
    corners = metric_points([[lo[0],lo[1]], [hi[0],lo[1]], [hi[0],hi[1]], [lo[0],hi[1]]],
                            reg['origin_utm_m'], reg['downstream_unit'], reg['left_unit'])
    footprint = Polygon(corners)
    mesh_path = ROOT / mesh_meta['mesh_path']
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest() != mesh_meta['mesh_sha256']:
        raise ValueError('Registered mesh changed')
    with np.load(mesh_path) as mesh:
        xy = np.column_stack([mesh['east_m'].ravel(), mesh['north_m'].ravel()]) + mesh_meta['origin_utm_m']
        rotation = np.column_stack([reg['downstream_unit'], reg['left_unit']])
        local = (xy - reg['origin_utm_m']) @ rotation
        inside = ((local >= lo) & (local <= hi)).all(axis=1)
        authority = mesh['authority'].ravel()
        counts = {str(int(k)): int(np.sum(inside & (authority == k))) for k in np.unique(authority)}
    report = dict(schema='raftsim.troublemaker_reference_coverage.v1',
        measured_bathymetry=False, production_promoted=False,
        image_center_utm_m=image_center.tolist(), crux_control_utm_m=origin.tolist(),
        crux_control_relative_to_old_plot_origin_m=(origin-image_center).tolist(),
        liquid_origin_utm_m=metric_points([centre],reg['origin_utm_m'],reg['downstream_unit'],reg['left_unit'])[0].tolist(), liquid_footprint_utm_m=corners.tolist(),
        footprint_area_m2=footprint.area, mesh_sha256=mesh_meta['mesh_sha256'],
        boundary_profile_sha256=hashlib.sha256(boundary_path.read_bytes()).hexdigest(),
        vertex_authority_counts_inside_footprint=counts,
        caveat='Region intersection is search coverage, not a verified named-rock or rapid identity.',
        regions=[])
    report['domain_source_path']=str(boundary_path.relative_to(ROOT))
    report['domain_source_kind']='active 21m test boundary' if window is None else 'prepared whole-rapid geometry, not yet active GPU domain'
    fig, ax = plt.subplots(figsize=(11, 8), layout='constrained')
    ax.imshow(Image.open(BASE / 'sources/troublemaker_naip.png'),
              extent=np.array([bounds['xmin'],bounds['xmax'],bounds['ymin'],bounds['ymax']])-origin[[0,0,1,1]])
    for region in regions['regions']:
        polygon = Polygon(np.asarray(region['polygon']) + origin)
        area = polygon.intersection(footprint).area
        report['regions'].append(dict(id=region['id'], search_area_m2=polygon.area,
            area_inside_liquid_window_m2=area, fraction_inside=area/polygon.area))
        outline = np.asarray(polygon.exterior.coords) - origin
        ax.plot(*outline.T, color='#ffd34e', linewidth=1)
        point = np.asarray(polygon.centroid.coords)[0] - origin
        ax.annotate(region['id'].replace('_','\n'), point, fontsize=7, color='white',
                    bbox=dict(facecolor='black',alpha=.55,pad=2))
    closed = np.vstack([corners, corners[0]]) - origin
    label='Actual 21 m liquid test footprint' if window is None else f'Prepared {hi[0]-lo[0]:g} x {hi[1]-lo[1]:g} m domain (not active GPU)'
    ax.plot(*closed.T, color='#ff6085', linewidth=2, label=label)
    ax.scatter([0],[0],marker='+',s=100,color='cyan',label='Interpreted crux search control')
    ax.scatter([-9],[1],marker='x',s=80,color='white',label='Inferred bed-control centre (not surveyed)')
    ax.set(xlim=(-120,100),ylim=(-100,90),xlabel='East of crux search control (m)',
           ylabel='North of crux search control (m)',
           title='Troublemaker: test coverage on 21 July 2022 NAIP\nGeographic evidence review — not a game capture')
    ax.set_aspect('equal'); ax.legend(loc='lower left',fontsize=8)
    if window is not None:
        ax.set_xlim(min(-120,closed[:,0].min()-10),max(100,closed[:,0].max()+10))
        ax.set_ylim(min(-100,closed[:,1].min()-10),max(90,closed[:,1].max()+10))
    output.mkdir(parents=True)
    fig.savefig(output/'coverage.png',dpi=160); plt.close(fig)
    (output/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--window',type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.output,args.window),indent=2))
