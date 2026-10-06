"""Render independent point-cloud sections; do not fit or modify rock geometry."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
import laspy
import numpy as np
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    work = ROOT/'tmp/troublemaker-independent-lidar-20260925'
    output = work/'anchor-686411-layers-pulses'
    if output.exists():
        raise ValueError('Refusing to overwrite prior inspection')
    source = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/classified_lidar_returns.npz'
    laz = work/'USGS_LPC_CA_SierraNevada_B22_10SFH8396.laz'
    expected = ['7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe',
                '2261adeac1a3ea49cdeaaa038cbb8bba40b2c1ada7f15b0e42e98192957fd96e']
    if [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,laz)] != expected:
        raise ValueError('A source has changed')
    with np.load(source) as old:
        xyz = np.column_stack([old['utm_easting_m'],old['utm_northing_m'],old['navd88_m']])
        target = xyz[686411].copy()
        selected = (abs(xyz[:,:2]-target[:2])<=4).all(axis=1)
        a = np.column_stack([xyz[selected]-target,old['classification'][selected]])
    transform = Transformer.from_crs(6339,32610,always_xy=True)
    chunks = []
    offset = 0
    with laspy.open(laz) as reader:
        crs = reader.header.parse_crs()
        if not crs.is_compound or [c.to_epsg() for c in crs.sub_crs_list] != [6339,5703]:
            raise ValueError('Unexpected independent CRS')
        for points in reader.chunk_iterator(500000):
            x,y = transform.transform(np.asarray(points.x),np.asarray(points.y))
            inside = (abs(x-target[0])<=4)&(abs(y-target[1])<=4)
            idx = np.flatnonzero(inside)
            chunks.append(np.column_stack([x[idx]-target[0],y[idx]-target[1],
                np.asarray(points.z)[idx]-target[2],np.asarray(points.classification)[idx],
                np.asarray(points.return_number)[idx],np.asarray(points.number_of_returns)[idx],
                np.asarray(points.withheld)[idx],offset+idx,np.asarray(points.gps_time)[idx],
                np.asarray(points.point_source_id)[idx],np.asarray(points.scanner_channel)[idx]]))
            offset += len(points)
        if offset != reader.header.point_count:
            raise ValueError('Incomplete independent cloud')
    b = np.concatenate(chunks)
    report = dict(anchor_original_id=686411, anchor_utm_navd88_m=target.tolist(), source_sha256=expected,
        production_promoted=False, correspondence_established=False,
        caveat='Nominal coordinate alignment only. No fitted ground offset applied. 2019 excludes withheld points; 2021 withheld flags retained. Classes are not rock labels.',
        independent_columns=['east_relative_m','north_relative_m','height_relative_m','classification','return_number','number_of_returns','withheld','laz_point_index','gps_time','point_source_id','scanner_channel'],
        independent_points=b.tolist(), original_columns=['east_relative_m','north_relative_m','height_relative_m','classification'],
        original_points=a.tolist(), radial_counts=[], upper_pulse_groups=[])
    for point in b[abs(b[:,2])<=.3]:
        if point[4]!=1 or point[5]<=1:
            continue
        same = b[(b[:,8:11]==point[8:11]).all(axis=1)]
        report['upper_pulse_groups'].append(dict(first_laz_index=int(point[7]),
            declared_returns=int(point[5]), recovered_returns=len(same),
            matching_laz_indices=same[:,7].astype(int).tolist(),
            return_numbers=same[:,4].astype(int).tolist(),
            classifications=same[:,3].astype(int).tolist(),
            height_relative_m=same[:,2].tolist(),
            horizontal_distance_from_first_m=np.linalg.norm(same[:,:2]-point[:2],axis=1).tolist()))
    for radius in [.3,.5,1,2,3]:
        row = dict(radius_m=radius)
        for name, points in [('2019',a),('2021',b)]:
            local = points[np.hypot(points[:,0],points[:,1])<=radius]
            row[name] = dict(count=len(local),near_anchor_height_count=int((abs(local[:,2])<=.3).sum()),
                min_max_height_relative_m=[float(local[:,2].min()),float(local[:,2].max())] if len(local) else None)
        report['radial_counts'].append(row)
    fig, axes = plt.subplots(1,3,figsize=(15,5),layout='constrained')
    for ax, dims, labels in zip(axes,[(0,1),(0,2),(1,2)],
            [('East','North'),('East','Height'),('North','Height')]):
        for points,color,label in [(a,'#0067b1','2019 raw'),(b,'#e07000','2021 raw')]:
            ax.scatter(points[:,dims[0]],points[:,dims[1]],s=5,alpha=.5,c=color,label=label)
        ax.scatter([0],[0],marker='x',s=90,c='black',label='2019 anchor686411')
        ax.set_xlabel(labels[0]+' relative to anchor (m)'); ax.set_ylabel(labels[1]+' relative to anchor (m)')
        ax.grid(alpha=.2); ax.set_aspect('equal',adjustable='box')
    axes[0].legend(fontsize=7)
    fig.suptitle('Troublemaker independent survey layers: 8 m square\nNot registered rock correspondences; no geometry edits')
    output.mkdir()
    fig.savefig(output/'sections.png',dpi=160); plt.close(fig)
    (output/'sections.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(original_count=len(a),independent_count=len(b),radial_counts=report['radial_counts'])))


if __name__=='__main__':
    main()
