"""Find same-bin lower source witnesses at artificial cap closures, not rock labels."""
import json
import numpy as np
from build_troublemaker_dem_rock_cap import ROOT, RETURNS, RETURNS_SHA, ORIGIN
from south_fork_rock_union import sha


def lower_bin_witnesses(vertices, xyz, classes, residual, cell_m=.5):
    vertices, xyz = np.asarray(vertices), np.asarray(xyz)
    if cell_m <= 0 or not np.isfinite(cell_m):
        raise ValueError('Positive finite bin size required')
    if not np.isfinite(vertices).all():
        raise ValueError('Finite candidate coordinates required')
    valid = np.isfinite(xyz).all(axis=1) & np.isfinite(residual) & np.isin(classes, [1, 2, 20])
    bins = {}
    for i in np.flatnonzero(valid):
        key = tuple(np.floor(xyz[i, :2] / cell_m).astype(np.int64))
        old = bins.get(key)
        if old is None or (xyz[i, 2], i) < (xyz[old, 2], old):
            bins[key] = int(i)
    rows = []
    for vertex, p in enumerate(vertices):
        index = bins.get(tuple(np.floor(p[:2] / cell_m).astype(np.int64)))
        if index is None or p[2] - xyz[index, 2] <= .5:
            continue
        rows.append(dict(vertex=vertex, source_index=index,
            source_xyz_m=xyz[index].tolist(), classification=int(classes[index]),
            vertical_separation_m=float(p[2]-xyz[index, 2]),
            horizontal_separation_m=float(np.linalg.norm(p[:2]-xyz[index, :2])),
            original_dem_residual_m=float(residual[index]),
            excluded_by_clearance=bool(residual[index] <= .3)))
    return rows


def main():
    cap_path=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925/mixed_survey_rock_cap.npz'
    output=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/boundary-lower-bin-witnesses.json'
    if output.exists(): raise ValueError('Fresh output required')
    if sha(RETURNS)!=RETURNS_SHA or sha(cap_path)!='7d1031602413e0dae311574f6b6d03e1542917bf2b9893a5c911875f84404d62':
        raise ValueError('Source identity mismatch')
    with np.load(cap_path) as cap:
        ids=np.unique(cap['boundary_edges']); vertices=cap['vertices_m'][ids]
        gaps=vertices[:,2]-cap['retained_parent_height_m'][ids]
    with np.load(RETURNS) as data:
        xyz=np.column_stack([data[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-ORIGIN
        rows=lower_bin_witnesses(vertices,xyz,data['classification'],data['height_above_flattened_surface_m'])
    for row in rows:
        local=row['vertex'];row['vertex']=int(ids[local]);row['cap_xyz_m']=vertices[local].tolist()
        row['cap_parent_gap_m']=float(gaps[local])
    result=dict(cap_sha256=sha(cap_path),source_sha256=RETURNS_SHA,boundary_vertices=len(ids),
        lower_witness_count=len(rows),clearance_excluded_count=sum(r['excluded_by_clearance'] for r in rows),
        interpretation='Same bin is not a point correspondence or proof of rock; no coordinates moved or observations removed.',
        playable_integrated=False,witnesses=rows)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='witnesses'},indent=2))


if __name__=='__main__':main()
