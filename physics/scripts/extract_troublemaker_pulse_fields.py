"""Replay original LAZ selection exactly and retain pulse fields by archive ID.

Read-only to every captured source. Return order is acquisition metadata, NOT
ground/rock classification; downstream interpretations must remain explicit.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import sha
from build_troublemaker_dem_rock_cap import ROOT, BASE, RETURNS, RETURNS_SHA, ORIGIN


def last_return_mask(number, total):
    number, total = np.asarray(number), np.asarray(total)
    if number.shape != total.shape or number.ndim != 1 or any(
        not np.issubdtype(a.dtype, np.integer) for a in (number, total)):
        raise ValueError('Matching integer pulse arrays required')
    if np.any(number < 1) or np.any(total < number) or np.any(total > 15):
        raise ValueError('Invalid original pulse numbering')
    return number == total


def run(output):
    import laspy
    from pyproj import Transformer
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp output required')
    if sha(RETURNS) != RETURNS_SHA:
        raise ValueError('Original extracted source changed')
    with np.load(RETURNS, allow_pickle=False) as data:
        original = np.column_stack([data[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])
        classes = data['classification']
    records = json.loads((BASE/'sources/point_cloud/downloads.json').read_text())
    inverse = Transformer.from_crs(32610, 6418, always_xy=True)
    transform = Transformer.from_crs(6418, 32610, always_xy=True)
    bounds = inverse.transform_bounds(ORIGIN[0]-180, ORIGIN[1]-140, ORIGIN[0]+180, ORIGIN[1]+140)
    arrays = {key: [] for key in ('return_number','number_of_returns','point_source_id','gps_time','source_tile_index','source_point_index')}
    cursor = 0
    for tile, record in enumerate(records):
        path = BASE/'sources/point_cloud'/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Original LAZ changed')
        with laspy.open(path) as reader:
            crs = reader.header.parse_crs()
            horizontal = crs.sub_crs_list[0] if crs and crs.is_compound else crs
            if horizontal is None or horizontal.to_epsg() != 6418:
                raise ValueError('Original horizontal CRS changed')
            offset = 0
            for points in reader.chunk_iterator(1_000_000):
                x, y = np.asarray(points.x), np.asarray(points.y)
                take = np.flatnonzero((x>=bounds[0]) & (x<=bounds[2]) & (y>=bounds[1]) & (y<=bounds[3]) & (np.asarray(points.withheld)==0))
                e, n = transform.transform(x[take], y[take])
                xyz = np.column_stack([e,n,np.asarray(points.z)[take]*(1200/3937)])
                crop = (abs(xyz[:,0]-ORIGIN[0])<=180) & (abs(xyz[:,1]-ORIGIN[1])<=140)
                xyz, take = xyz[crop], take[crop]
                end = cursor+len(take)
                if not np.array_equal(xyz, original[cursor:end]) or not np.array_equal(np.asarray(points.classification)[take], classes[cursor:end]):
                    raise ValueError('Original archive ID/XYZ/classification replay mismatch')
                for key in ('return_number','number_of_returns','point_source_id','gps_time'):
                    arrays[key].append(np.asarray(getattr(points,key))[take])
                arrays['source_tile_index'].append(np.full(len(take),tile,np.uint8))
                arrays['source_point_index'].append(take.astype(np.int64)+offset)
                offset += len(points)
                cursor = end
    if cursor != len(original):
        raise ValueError('Incomplete original archive replay')
    arrays = {key:np.concatenate(value) for key,value in arrays.items()}
    keep = last_return_mask(arrays['return_number'],arrays['number_of_returns'])
    output.mkdir()
    path = output/'pulse_fields.npz'
    np.savez_compressed(path,**arrays)
    report = dict(schema='raftsim.original_lidar_pulse_fields.v1', source_returns_sha256=RETURNS_SHA,
        source_tiles=records, archive_count=cursor, exact_archive_order_xyz_classification=True,
        fields_path=path.relative_to(ROOT).as_posix(), fields_sha256=sha(path),
        last_or_only_returns=int(keep.sum()), nonlast_returns=int((~keep).sum()),
        source_modified=False, classification_inferred=False, production_promoted=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_tiles'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args().output)
