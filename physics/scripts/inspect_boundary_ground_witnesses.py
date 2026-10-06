"""Inspect five captured lower witnesses; do not replace or relabel roof points."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from shapely.geometry import Point, Polygon
from shapely import union_all
from build_troublemaker_dem_rock_cap import ROOT, BASE, ORIGIN
from south_fork_rock_union import sha


def main():
    audit_path=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup/boundary-lower-bin-witnesses.json'
    audit=json.loads(audit_path.read_text())
    cap_path=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925/mixed_survey_rock_cap.npz'
    if sha(cap_path)!=audit['cap_sha256']:raise ValueError('Changed cap')
    source=BASE/'full_reach/source_matched_20260917/rock_cap_manifest.json'
    # Use the retained registered-image identities from the original construction.
    if not source.exists():
        raise ValueError('Missing installed source manifest')
    manifest=json.loads(source.read_text())
    image_path=BASE/'sources/troublemaker_naip.png'
    meta_path=BASE/'sources/troublemaker_naip_export.json'
    if sha(image_path)!=manifest['source_naip_sha256'] or sha(meta_path)!=manifest['source_naip_export_sha256']:
        raise ValueError('Changed registered imagery')
    meta=json.loads(meta_path.read_text());extent=meta['extent']
    if extent['spatialReference']['latestWkid']!=32610:raise ValueError('Unexpected frame')
    image=plt.imread(image_path)
    bounds=[extent['xmin']-ORIGIN[0],extent['xmax']-ORIGIN[0],extent['ymin']-ORIGIN[1],extent['ymax']-ORIGIN[1]]
    with np.load(cap_path) as cap:
        vertices=cap['vertices_m'];faces=cap['triangles'];edges=cap['boundary_edges']
        source_ids=cap['source_point_index'];classes=cap['source_classification']
    footprint=union_all([Polygon(t) for t in vertices[faces,:2]])
    rows=[r.copy() for r in audit['witnesses'] if r['classification']==2 and r['excluded_by_clearance']]
    if len(rows)!=5:raise ValueError('Expected five ground witnesses')
    output=ROOT/'tmp/boundary-ground-witness-review-20260925'
    if output.exists():raise ValueError('Fresh output required')
    fig,axes=plt.subplots(1,5,figsize=(16,4),layout='constrained')
    for ax,row in zip(axes,rows):
        index=row['vertex'];p=vertices[index];q=np.array(row['source_xyz_m'])
        incident=faces[np.any(faces==index,axis=1)]
        hypothetical=vertices.copy();hypothetical[index]=q
        xyz=hypothetical[incident];cross=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
        row.update(upper_source_index=int(source_ids[index]),upper_classification=int(classes[index]),
            lower_inside_roof=bool(footprint.covers(Point(q[:2]))),incident_faces=len(incident),
            replacement_flipped_or_degenerate_faces=int((cross[:,2]<=0).sum()),
            replacement_max_edge_m=float(np.linalg.norm(xyz[:,:,:2]-np.roll(xyz[:,:,:2],1,axis=1),axis=2).max()))
        ax.imshow(image,extent=bounds,origin='upper',interpolation='nearest')
        ax.add_collection(LineCollection(vertices[edges,:2],colors='cyan',linewidths=.7))
        ax.plot(p[0],p[1],'rx',label='Upper selected')
        ax.plot(q[0],q[1],'y+',label='Ground witness')
        ax.set(xlim=(p[0]-2,p[0]+2),ylim=(p[1]-2,p[1]+2),title=str(row['source_index']))
        ax.set_aspect('equal')
    axes[0].legend(fontsize=6)
    fig.suptitle('Registered NAIP context, 4 m windows; not measured outlines or point classification')
    output.mkdir();fig.savefig(output/'context.png',dpi=120);plt.close(fig)
    report=dict(audit_sha256=sha(audit_path),cap_sha256=sha(cap_path),image_sha256=sha(image_path),
        registration_uncertainty_m=manifest.get('registration_uncertainty_m'),
        geometry_modified=False,acceptance=False,targets=rows)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
