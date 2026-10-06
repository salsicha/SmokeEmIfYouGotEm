"""Local planar-ground consistency screen, not surveyed registration controls."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
import laspy
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree


def fit_offset(gradients, residuals):
    # residual = old gradient dot apparent XY shift + apparent Z offset.
    # A consistency model only: vegetation/terrain change can also cause it.
    design = np.column_stack([gradients, np.ones(len(gradients))])
    if len(design) < 12 or not np.isfinite(design).all() or not np.isfinite(residuals).all():
        raise ValueError('Insufficient or invalid controls')
    if np.linalg.matrix_rank(design) != 3:
        raise ValueError('Ground slopes do not constrain all three offsets')
    return np.linalg.lstsq(design, residuals, rcond=None)[0], float(np.linalg.cond(design))


def main():
    work = ROOT/'tmp/troublemaker-independent-lidar-20260925'
    output = work/'ground-consistency.json'
    if output.exists():
        raise ValueError('Refusing to overwrite prior evidence')
    laz = work/'USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz'
    expected = '2261adeac1a3ea49cdeaaa038cbb8bba40b2c1ada7f15b0e42e98192957fd96e'
    if hashlib.sha256(laz.read_bytes()).hexdigest() != expected:
        raise ValueError('Independent source changed')
    source = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/classified_lidar_returns.npz'
    old_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if old_hash != '7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe':
        raise ValueError('Original source changed')
    with np.load(source) as data:
        xyz = np.column_stack([data['utm_easting_m'], data['utm_northing_m'], data['navd88_m']])
        water = xyz[data['within_survey_water'], :2]
        selected = (data['classification']==2) & ~data['within_survey_water']
        old = xyz[selected]
    water_tree = cKDTree(water)
    old = old[water_tree.query(old[:,:2])[0] > 5]
    lo, hi = old[:,:2].min(axis=0), old[:,:2].max(axis=0)
    transform = Transformer.from_crs(6339,32610,always_xy=True)
    new_chunks = []
    with laspy.open(laz) as reader:
        crs = reader.header.parse_crs()
        if not crs.is_compound or [c.to_epsg() for c in crs.sub_crs_list] != [6339,5703]:
            raise ValueError('Unexpected independent CRS')
        for points in reader.chunk_iterator(500000):
            good = (np.asarray(points.classification)==2) & (np.asarray(points.withheld)==0)
            x,y = transform.transform(np.asarray(points.x)[good],np.asarray(points.y)[good])
            z = np.asarray(points.z)[good]
            inside = (x>=lo[0]) & (x<=hi[0]) & (y>=lo[1]) & (y<=hi[1])
            new_chunks.append(np.column_stack([x[inside],y[inside],z[inside]]))
    new = np.concatenate(new_chunks)
    old_tree, new_tree = cKDTree(old[:,:2]), cKDTree(new[:,:2])
    # Spatially distribute controls; selection is independent of cross-epoch Z.
    bins = np.floor((old[:,:2]-lo)/4).astype(int)
    _, indices = np.unique(bins,axis=0,return_index=True)
    controls = []
    for index in indices:
        centre = old[index,:2]
        nearby = old_tree.query_ball_point(centre,1.5)
        if len(nearby)<12:
            continue
        local = old[nearby]
        design = np.column_stack([local[:,:2]-centre,np.ones(len(local))])
        plane = np.linalg.lstsq(design,local[:,2],rcond=None)[0]
        rms = np.sqrt(np.mean((design@plane-local[:,2])**2))
        slope = np.linalg.norm(plane[:2])
        if rms>.08 or slope>1 or np.linalg.matrix_rank(design)!=3:
            continue
        distance, j = new_tree.query(centre)
        if distance>.3 or water_tree.query(new[j,:2])[0]<=5:
            continue
        delta = new[j,2]-(plane[2]+plane[:2]@(new[j,:2]-centre))
        controls.append(dict(xy=centre.tolist(), gradient=plane[:2].tolist(),
            plane_rms_m=float(rms), horizontal_distance_m=float(distance), residual_m=float(delta)))
    gradients = np.array([c['gradient'] for c in controls])
    residuals = np.array([c['residual_m'] for c in controls])
    shift, condition = fit_offset(gradients,residuals)
    corrected = residuals-np.column_stack([gradients,np.ones(len(gradients))])@shift
    report = dict(schema='raftsim.survey_ground_consistency.v1',
        registered=False, production_promoted=False, original_sha256=old_hash, independent_sha256=expected,
        caveat='Source-classified ground is not a surveyed stable control. Linear apparent offset is NOT applied. Dates, geoid realizations and physical changes remain uncertain.',
        control_selection='class2, withheld excluded, >5m from old water returns, 4m bins, 1.5m plane radius, >=12 points, RMS<=.08m, slope<=1, new XY distance<=.3m; no residual-based trimming',
        control_count=len(controls), old_ground_points=len(old), new_ground_points=len(new),
        apparent_offset_xyz_m=shift.tolist(), design_condition=condition,
        uncorrected_quantiles_m=np.quantile(residuals,[0,.05,.5,.95,1]).tolist(),
        corrected_quantiles_m=np.quantile(corrected,[0,.05,.5,.95,1]).tolist(), controls=controls)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='controls'}))


if __name__=='__main__':
    main()
