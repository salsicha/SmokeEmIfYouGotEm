"""Verify mixed-survey roof positions against immutable original records."""
import hashlib
from pathlib import Path
import numpy as np


def validate_mixed_sources(data, original, manifest, root, origin):
    import laspy
    from pyproj import Transformer
    if 'original_return_index' in data:
        raise ValueError('Ambiguous legacy index in mixed source archive')
    xyz=np.asarray(data['vertices_m'])
    datasets=np.asarray(data['source_dataset']); ids=np.asarray(data['source_point_index'])
    classes=np.asarray(data['source_classification'])
    if xyz.ndim!=2 or xyz.shape[1]!=3 or not np.isfinite(xyz).all():
        raise ValueError('Invalid mixed source vertices')
    if any(a.shape!=(len(xyz),) or not np.issubdtype(a.dtype,np.integer) for a in (datasets,ids,classes)):
        raise ValueError('Integer per-vertex source identities required')
    if not np.isin(datasets,[0,1]).all() or not (datasets==1).any() or (ids<0).any():
        raise ValueError('Unknown mixed source identity')
    if not np.isin(classes,[1,2,10]).all():
        raise ValueError('Excluded mixed source classification')
    expected=np.empty_like(xyz); expected_class=np.empty(len(xyz),dtype=np.uint8)
    old=datasets==0
    if (ids[old]>=len(original['classification'])).any():
        raise ValueError('Original source index out of bounds')
    expected[old]=np.column_stack([original[k][ids[old]] for k in
        ('utm_easting_m','utm_northing_m','navd88_m')])-origin
    expected_class[old]=original['classification'][ids[old]]
    record=manifest['independent_source']; root=Path(root).resolve()
    path=(root/record['path']).resolve()
    if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
        raise ValueError('Changed or out-of-repository independent source')
    if record.get('vertical_adjustment_m')!=0:
        raise ValueError('Unreviewed vertical adjustment')
    with laspy.open(path) as reader:
        crs=reader.header.parse_crs()
        if not crs or not crs.is_compound or [c.to_epsg() for c in crs.sub_crs_list]!=[6339,5703]:
            raise ValueError('Unexpected independent source CRS')
        transform=Transformer.from_crs(6339,32610,always_xy=True)
        for index in np.flatnonzero(~old):
            if ids[index]>=reader.header.point_count:
                raise ValueError('Independent source index out of bounds')
            reader.seek(int(ids[index])); point=reader.read_points(1)
            if len(point)!=1 or int(point.withheld[0]):
                raise ValueError('Missing or withheld independent observation')
            x,y=transform.transform(float(point.x[0]),float(point.y[0]))
            expected[index]=np.array([x,y,float(point.z[0])])-origin
            expected_class[index]=point.classification[0]
    if not np.array_equal(xyz,expected):
        raise ValueError('Mixed candidate moved a captured source vertex')
    if not np.array_equal(classes,expected_class):
        raise ValueError('Mixed candidate relabelled source classification')
    return dict(sha256=record['sha256'],source_vertices=int((~old).sum()),
        horizontal_transform=transform.description,horizontal_accuracy_m=transform.accuracy,
        vertical_adjustment_m=0.,semantic_rock_classification_verified=False)
