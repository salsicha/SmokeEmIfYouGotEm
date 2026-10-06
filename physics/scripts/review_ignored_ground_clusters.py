"""Dated imagery and original-return context, not a geometry promotion.

Review only clusters of at least two of the 17 observations, each with three
classified-ground peers, connected within 4 m. These are explicit diagnostic
selection parameters, not measured rock boundaries or semantic rock labels.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_eldorado_ignored_ground import ROOT, SOURCE, SOURCE_SHA
from south_fork_rock_union import sha
from build_troublemaker_dem_rock_cap import BASE, PARENT, PARENT_SHA, ORIGIN
from south_fork_registered_mesh import RegisteredMeshSampler


def clusters(rows, radius=4.):
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError('Positive finite cluster radius required')
    ids = [r['original_return_index'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate original indices')
    selected = sorted((r for r in rows if r['classified_ground_peer_count'] >= 3),
                      key=lambda r: r['original_return_index'])
    result = []
    while selected:
        component = [selected.pop(0)]
        for row in component:
            near = [r for r in selected if np.linalg.norm(
                np.array(r['source_utm_navd88_m'][:2])-row['source_utm_navd88_m'][:2]) <= radius]
            component.extend(near)
            selected = [r for r in selected if r not in near]
        if len(component) >= 2:
            result.append(sorted(component, key=lambda r: r['original_return_index']))
    return result


def main(output):
    from shapely.geometry import Polygon
    from shapely import intersects_xy
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp directory required')
    screen_path = ROOT/'docs/reconstruction-review-2026-09-07/south-fork-ignored-ground-registered-screen.json'
    atlas_path = BASE/'sources/rapid_atlas/troublemaker/manifest.json'
    atlas = json.loads(atlas_path.read_text())
    image_path = ROOT/atlas['image_path']
    protected = {p:sha(p) for p in (SOURCE, PARENT, screen_path, atlas_path, image_path)}
    if sha(SOURCE) != SOURCE_SHA or sha(PARENT) != PARENT_SHA or sha(image_path) != atlas['image_sha256']:
        raise ValueError('Source identity mismatch')
    if atlas['source_raster_ids'] != [21979] or atlas['source_metadata'][0]['acquisition_date'] != 1658361600000:
        raise ValueError('Expected locked 2022-07-21 source')
    extent = atlas['actual_returned_extent']
    if extent['spatialReference']['latestWkid'] != 32610:
        raise ValueError('Unexpected image coordinate system')
    bounds = [extent[k] for k in ('xmin','xmax','ymin','ymax')]
    image = plt.imread(image_path)
    with np.load(SOURCE, allow_pickle=False) as source:
        xyz = np.column_stack([source[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])
        classes = source['classification'].copy()
    with np.load(PARENT, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
        grid = np.stack([mesh['east_m'],mesh['north_m']],axis=-1)
        perimeter = np.concatenate([grid[0],grid[1:,-1],grid[-1,-2::-1],grid[-2:0:-1,0]])+ORIGIN[:2]
        footprint = Polygon(perimeter)
        if not footprint.is_valid: raise ValueError('Invalid registered boundary')
    groups = clusters(json.loads(screen_path.read_text())['rows'])
    if not groups:
        raise ValueError('No supported clusters')
    output.mkdir()
    reports = []
    for group in groups:
        ids = np.array([r['original_return_index'] for r in group])
        if not np.array_equal(xyz[ids], [r['source_utm_navd88_m'] for r in group]):
            raise ValueError('Changed original coordinates')
        center = xyz[ids,:2].mean(axis=0)
        roi = [center[0]-10,center[0]+10,center[1]-10,center[1]+10]
        if not (bounds[0] <= roi[0] < roi[1] <= bounds[1] and bounds[2] <= roi[2] < roi[3] <= bounds[3]):
            raise ValueError('Review window outside actual returned imagery')
        local = np.flatnonzero((np.abs(xyz[:,:2]-center) <= 10).all(axis=1))
        ground = local[np.isin(classes[local], [2,20])]
        inside = intersects_xy(footprint,*xyz[ground,:2].T)
        uncovered = ground[~inside]
        ground = ground[inside]
        base = sampler.sample(*(xyz[ground,:2]-ORIGIN[:2]).T)+ORIGIN[2]
        if not np.isfinite(base).all():
            raise ValueError('Incomplete registered-base coverage')
        residual = xyz[ground,2]-base
        fig, axes = plt.subplots(1,3,figsize=(15,5),layout='constrained')
        axes[0].imshow(image, extent=bounds, origin='upper', interpolation='nearest')
        axes[0].set_title('Locked NAIP 2022-07-21 (0.6 m source)')
        for point in xyz[ids]:
            axes[0].add_patch(Circle(point[:2],3,fill=False,color='yellow',linestyle='--',linewidth=.7))
        for cl,color in ((1,'gray'),(2,'green'),(20,'orange'),(9,'blue')):
            points=local[classes[local]==cl]
            axes[1].scatter(*xyz[points,:2].T,s=6,c=color,label=f'class {cl}')
        axes[1].legend(fontsize=8)
        axes[1].set_title('Original classes (not rock semantics)')
        dots=axes[2].scatter(*xyz[ground,:2].T,c=residual,s=10,cmap='coolwarm',vmin=-1,vmax=1)
        fig.colorbar(dots,ax=axes[2],label='Ground return minus registered BASE (m)',shrink=.65)
        axes[2].set_title('Base only, not current collision union')
        axes[2].scatter(*xyz[uncovered,:2].T,s=7,c='gray',marker='x',label='Outside registered mesh')
        axes[2].legend(fontsize=7)
        for ax in axes:
            ax.scatter(*xyz[ids,:2].T,marker='+',s=110,c='magenta',linewidths=1)
            for i,point in zip(ids,xyz[ids]):
                ax.annotate(str(i),point[:2],xytext=(4,5),textcoords='offset points',fontsize=7,color='magenta')
            ax.set(xlim=roi[:2],ylim=roi[2:],aspect='equal')
            ax.ticklabel_format(useOffset=False,style='plain')
            ax.tick_params(axis='x',labelrotation=30)
        fig.suptitle('20 m context; dashed 3 m registration sensitivity, not a confidence bound or measured outline',fontsize=10)
        name=f'cluster-{ids[0]}'
        fig.savefig(output/(name+'.png'),dpi=150)
        plt.close(fig)
        values,counts=np.unique(classes[local],return_counts=True)
        reports.append(dict(ids=ids.tolist(),bbox_utm32610_m=roi,
            image_window_covered=True, source_class_counts={str(int(v)):int(n) for v,n in zip(values,counts)},
            outside_registered_mesh_original_indices=uncovered.tolist(),
            ground_returns=[dict(original_return_index=int(i),xyz_m=p.tolist(),classification=int(cl),
                registered_base_m=float(b),residual_m=float(d))
                for i,p,cl,b,d in zip(ground,xyz[ground],classes[ground],base,residual)],
            figure=name+'.png',figure_sha256=sha(output/(name+'.png'))))
    for path,digest in protected.items():
        if sha(path)!=digest: raise ValueError('Changed protected source')
    report=dict(schema='raftsim.ignored_ground_cluster_review.v1',clusters=reports,
        protected_inputs={p.relative_to(ROOT).as_posix():d for p,d in protected.items()},
        image_date='2022-07-21',image_source_resolution_m=.6,export_pixel_spacing_m=(bounds[1]-bounds[0])/image.shape[1],
        registration_sensitivity_m=3., geometry_modified=False,semantic_rock_labels_verified=False,
        playable_changed=False, scope=__doc__)
    with (output/'report.json').open('x') as f: json.dump(report,f,indent=2,allow_nan=False)
    print(json.dumps(dict(output=str(output),clusters=[r['ids'] for r in reports])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
