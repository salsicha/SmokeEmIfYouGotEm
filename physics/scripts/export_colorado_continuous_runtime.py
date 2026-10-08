"""Export screened native water with its existing common-grid terrain.

Does not resample terrain, create a map, register a menu entry or certify a
full-river descent. Partial construction coverage stays explicit.
"""
import argparse
import datetime
import json
import re
import shutil
import struct
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from export_colorado_catalog_runtime import BAND, checked_cook
from export_colorado_continuous_terrain import LandscapeTriangles
from chilko_native_friction import runtime_friction_fields
from native_frame_io import NativeFrameStore


def _registered_geometry(mapping, terrain, grid):
    generic=terrain.get('schema')=='raftsim.continuous_landscape.v1'
    origin_key='horizontal_origin_m' if generic else 'horizontal_origin_epsg6404_m'
    if generic and (terrain.get('river_id')!='chilko_river_bc' or
            terrain.get('horizontal_crs')!='EPSG:3157' or
            terrain.get('vertical_reference')!='CGVD2013 (EPSG:6647)' or
            terrain.get('world_y_sign')!=-1 or
            any(mapping.get(key)!=terrain.get(key) for key in
                ('river_id','horizontal_crs','vertical_reference')) or
            'horizontal_origin_epsg6404_m' in mapping):
        raise ValueError('Water and terrain must share the same geographic frame')
    if (mapping.get('schema') != 'raftsim.curved_river_coordinate_map.v1' or
            mapping.get('world_y_sign') != -1 or
            mapping.get(origin_key) != terrain.get(origin_key) or
            mapping['vertical_datum_m'] != terrain['vertical_datum_m']):
        raise ValueError('Water and terrain must share the same geographic frame')
    origin=np.asarray(terrain.get(origin_key),dtype=float)
    if origin.shape!=(2,) or not np.isfinite(origin).all():
        raise ValueError('Invalid geographic origin')
    points = np.asarray(mapping['points'], dtype=float)
    if points.ndim != 2 or points.shape[1] != 5 or not np.isfinite(points).all():
        raise ValueError('Invalid hydraulic coordinate map')
    if np.any(np.diff(points[:, 0]) <= 0):
        raise ValueError('Nonmonotone hydraulic coordinate map')
    station = grid['origin_x'] + np.arange(grid['nx'])*grid['dx']
    indices = np.searchsorted(points[:, 0], station)
    if np.any(indices >= len(points)) or not np.allclose(points[indices, 0], station, atol=1e-8, rtol=0):
        raise ValueError('Cook is not on the shared hydraulic lattice')
    selected = points[indices]
    if not np.allclose(np.linalg.norm(selected[:, 3:5], axis=1), 1., atol=1e-8, rtol=0):
        raise ValueError('Nonunit hydraulic normal')
    lateral = grid['origin_y'] + np.arange(grid['ny'])*grid['dy']
    return station,selected,lateral,origin


def registered_queries(mapping, terrain, grid):
    station,selected,lateral,origin=_registered_geometry(mapping,terrain,grid)
    xy = selected[None, :, 1:3] + lateral[:, None, None]*selected[None, :, 3:5]
    return station, xy + origin


def registered_query_blocks(mapping,terrain,grid,*,block_cells=262144):
    """Exact original arithmetic, retaining only neighbouring station columns."""
    station,selected,lateral,origin=_registered_geometry(mapping,terrain,grid)
    if not isinstance(block_cells,int) or block_cells<len(lateral):
        raise ValueError('Query block must contain one complete cross-section')
    columns=max(1,block_cells//len(lateral))
    for start in range(0,len(station),columns):
        sl=slice(start,min(start+columns,len(station)))
        xy=selected[None,sl,1:3]+lateral[:,None,None]*selected[None,sl,3:5]
        yield sl,xy+origin


def validate_runtime_geometry(mapping,triangles,grid,frame,bed,*,block_cells=262144):
    station,_,_,_=_registered_geometry(mapping,triangles.manifest,grid)
    error=0.
    for sl,queries in registered_query_blocks(mapping,triangles.manifest,grid,block_cells=block_cells):
        rendered=triangles.sample(queries);source=bed[:,sl]
        if not np.isfinite(rendered).all() or not np.allclose(rendered,source,atol=1e-8,rtol=0):
            raise ValueError('Cook bed differs from encoded shared terrain triangles')
        error=max(error,float(abs(rendered-source).max()))
        if not np.allclose(source.astype('<f4').astype(float),source,atol=.01,rtol=0):
            raise ValueError('Runtime bed precision exceeds one centimetre')
        if not np.all((frame['wet'][:,sl]>.5).any(axis=0)):
            raise ValueError('Dry cross-section interrupts the water corridor')
    return station,error


def write_fields(folder, grid, station, frame, bed, band_id=BAND,*,block_cells=262144):
    """Preserve solved state; serialize the actual native support surface."""
    if not re.fullmatch(r'[A-Za-z0-9_]+',band_id):raise ValueError('Unsafe flow band')
    ny, nx = bed.shape
    if (ny, nx) != (grid['ny'], grid['nx']):
        raise ValueError('Runtime grid shape mismatch')
    if (not isinstance(block_cells,int) or block_cells<max(ny,nx) or
            np.shape(station)!=(nx,) or not np.isfinite(station).all() or
            max(nx,ny*nx)>np.iinfo(np.int32).max):
        raise ValueError('Invalid runtime block, station axis or support field count')
    for key in ('wet','h','u','v','eta'):
        if np.shape(frame[key])!=bed.shape:raise ValueError('Nonfinite or incomplete runtime field')
    rows=max(1,block_cells//nx);columns=max(1,block_cells//ny)
    for start in range(0,ny,rows):
        sl=slice(start,start+rows)
        if not all(np.isfinite(a[sl]).all() for a in (bed,*(frame[k] for k in ('wet','h','u','v','eta')))):
            raise ValueError('Nonfinite or incomplete runtime field')
    # Five NPY fields plus the original station-major support binary. Keep the
    # same disk reserve as frame review before allocating any output files.
    parent=folder.parent
    while not parent.exists():parent=parent.parent
    if shutil.disk_usage(parent).free<ny*nx*26+nx*4+1048576+40*1024**3:
        raise ValueError('Insufficient runtime disk headroom; forty GiB reserve required')
    folder.mkdir(parents=True)
    band = folder/band_id
    band.mkdir()
    arrays = {}
    for name,dtype in [('bed','<f4'),('h','<f4'),('u','<f4'),('v','<f4'),('wet_mask','u1')]:
        path = band/(name+'.npy')
        with path.open('xb') as stream:
            np.lib.format.write_array_header_1_0(stream,dict(descr=np.dtype(dtype).str,
                fortran_order=False,shape=(ny,nx)))
            for start in range(0,ny,rows):
                sl=slice(start,start+rows)
                if name=='bed':array=bed[sl]
                elif name=='h':array=frame['h'][sl]
                elif name=='wet_mask':array=frame['wet'][sl]>.5
                else:array=np.where(frame['wet'][sl]>.5,frame[name][sl],0)
                array=np.ascontiguousarray(array,dtype=dtype)
                if not np.isfinite(array).all():raise ValueError('Nonfinite or incomplete runtime field')
                stream.write(memoryview(array).cast('B'))
        arrays[name] = dict(file=f'{band_id}/{path.name}', sha256=sha(path),
                           shape=[ny, nx], dtype='uint8' if dtype == 'u1' else 'float32')
    baseline = folder/f'support_band_field_{band_id}.bin'
    with baseline.open('xb') as stream:
        stream.write(struct.pack('<IIiiff', 0x52534246, 1, ny, nx, grid['origin_y'], grid['dy']))
        stream.write(struct.pack('<i',nx))
        stream.write(memoryview(np.ascontiguousarray(station,dtype='<f4')).cast('B'))
        # Each component is station-major, not the NPY row-major layout.
        for name,dtype in [('surface','<f4'),('energy','<f4'),('wet','u1')]:
            stream.write(struct.pack('<i',ny*nx))
            for start in range(0,nx,columns):
                sl=(slice(None),slice(start,start+columns));h=frame['h'][sl]
                support_wet=(frame['wet'][sl]>.5)&(h>.05)
                if name=='surface':array=np.where(support_wet,frame['eta'][sl],bed[sl])
                elif name=='wet':array=support_wet
                else:
                    speed=np.hypot(frame['u'][sl],frame['v'][sl])
                    froude=np.where(h>.05,speed/np.sqrt(9.81*np.maximum(h,.05)),0)
                    array=np.clip(.6*np.clip((speed-.5)/2.5,0,1)+.4*np.clip((froude-.5)/.5,0,1),0,1)
                array=np.ascontiguousarray(array.T,dtype=dtype)
                if not np.isfinite(array).all():raise ValueError('Nonfinite runtime support field')
                stream.write(memoryview(array).cast('B'))
    return arrays, dict(file=baseline.name, sha256=sha(baseline))


def export(inputs, cook, review, out, river_id='colorado_river_grand_canyon_rowing'):
    if out.exists():
        raise ValueError('Fresh continuous runtime export required')
    if river_id=='colorado_river_grand_canyon_rowing':
        with NativeFrameStore(inputs.parent) as store:
            return _export(inputs,cook,review,out,river_id,frame_loader=store.load)
    return _export(inputs,cook,review,out,river_id)


def _export(inputs,cook,review,out,river_id,*,frame_loader=None):
    chilko=river_id=='chilko_river_bc'
    if chilko:
        from review_chilko_continuous_cook import checked_cook as checked_chilko
        build,receipt,native,scenario,frame,bed=checked_chilko(inputs,cook,review)
    elif river_id=='colorado_river_grand_canyon_rowing':
        build, receipt, native, scenario, frame, bed = checked_cook(inputs, cook, review,frame_loader=frame_loader)
    else:raise ValueError('Unsupported continuous river')
    band_id=scenario['metadata']['flow_band'] if chilko else BAND
    section_id='chilko_continuous' if chilko else 'colorado_continuous'
    name=scenario['metadata']['scenario_id'] if chilko else build['name']
    terrain_folder = (ROOT/build['continuous_terrain']['manifest']).parent
    for key in ('continuous_terrain', 'shared_hydraulic_frame'):
        if chilko:continue  # checked_chilko already verifies terrain and exact source/grid frame.
        spec = build[key]
        if sha(ROOT/spec['manifest']) != spec['sha256']:
            raise ValueError('Changed common terrain or hydraulic frame')
    triangles = LandscapeTriangles(terrain_folder)
    mapping_path = inputs/'coordinate_map.json'
    mapping = json.loads(mapping_path.read_text())
    if not chilko:
        original_map = (ROOT/build['shared_hydraulic_frame']['manifest']).parent/'coordinate_map.json'
        if mapping != json.loads(original_map.read_text()):
            raise ValueError('Input coordinate map differs from full shared frame')
    grid = scenario['grid']
    station,terrain_error=validate_runtime_geometry(mapping,triangles,grid,frame,bed)
    # These are the existing runtime end-boundary conventions; interior moving
    # windows receive the actual per-cell cooked ghost states.
    inlet = (frame['wet'][:, 0]>.5) & (frame['h'][:, 0] > .05)
    outlet = (frame['wet'][:, -1]>.5) & (frame['h'][:, -1] > .05)
    if not inlet.any() or not outlet.any():
        raise ValueError('Dry runtime boundary')
    boundaries = [dict(edge='west', kind='inflow', stage=float(np.median(frame['eta'][inlet, 0])),
                      velocity=[float(np.median(frame[k][inlet, 0])) for k in ('u', 'v')]),
                  dict(edge='east', kind='outflow', stage=float(np.median(frame['eta'][outlet, -1]))),
                  dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    terrain_bytes=sum((terrain_folder[c['heightfield']]).stat().st_size for c in triangles.manifest['chunks'])
    required=grid['ny']*grid['nx']*26+grid['nx']*4+terrain_bytes+mapping_path.stat().st_size+1048576
    parent=out.parent
    while not parent.exists():parent=parent.parent
    if shutil.disk_usage(parent).free<required+40*1024**3:
        raise ValueError('Insufficient runtime terrain/field disk headroom; forty GiB reserve required')
    out.mkdir(parents=True)
    fields = out/'cooked_flow_fields'
    arrays, baseline = write_fields(fields, grid, station, frame, bed, band_id)
    solver = dict(native, binary_sha256=receipt['solver_sha256'],
                  runtime_crop_boundary_mode='cooked_ghost', fixed_dt_s=scenario['fixed_dt'])
    solver.pop('frames', None)
    manifest = dict(schema='raftsim.cooked_flow_fields.v1', generator=Path(__file__).name,
        generated_on=datetime.date.today().isoformat(), river_id=river_id,
        rapid_name=name, section_id=section_id, source_elevation_datum_m=0.,
        grid=dict(nx=grid['nx'], ny=grid['ny'], dx_m=grid['dx'], dy_m=grid['dy'],
                  origin_x_m=grid['origin_x'], origin_y_m=grid['origin_y'],
                  layout='row_major_c_order', downstream_axis='+x'), solver=solver,
        bands=[dict(band_id=band_id, directory=band_id, scenario_id=native['scenario_id'],
            **runtime_friction_fields(scenario),
            discharge_target_m3s=receipt['statistics']['exact_face_discharge_target_m3s'],
            discharge_target_cfs=receipt['statistics']['exact_face_discharge_target_m3s']/0.028316846592 if chilko else 8000., runtime_boundaries=boundaries, arrays=arrays,
            presentation_baseline=baseline,
            convergence=dict(construction_screen_passed=True, **receipt['statistics']))],
        provenance=dict(continuous_terrain=build['continuous_terrain'],
                        shared_hydraulic_frame=build.get('shared_hydraulic_frame'),
                        source_inputs=build.get('source_inputs', []),
                        native_continuation=build.get('native_continuation'),
                        bed_edit_warm_start=build.get('bed_edit_warm_start'),
                        input_build_report_sha256=sha(inputs/'build_report.json'),
                        construction_review_sha256=sha(review)),
        runtime_boundary_note='Only original reach ends use median solved stage/velocity; interior moving crops use cooked ghosts.',
        engine_validated=False, class_match='not_established')
    (fields/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    terrain = out/'terrain'; terrain.mkdir()
    shutil.copyfile(terrain_folder/'manifest.json', terrain/'manifest.json')
    for chunk in triangles.manifest['chunks']:
        shutil.copyfile(terrain_folder/chunk['heightfield'], terrain/chunk['heightfield'])
    shutil.copyfile(mapping_path, out/'coordinate_map.json')
    field_path = (fields/'manifest.json').relative_to(ROOT).as_posix()
    stream = dict(schema='raftsim.south_fork.moving_water_streaming.v1',
        full_reach_transit_seed=dict(cooked_fields_manifest=field_path,
                                    cooked_fields_manifest_sha256=sha(fields/'manifest.json')),
        windows=[dict(window_id=section_id, cooked_fields_manifest=field_path,
                      station_range_m=[float(station[0]), float(station[-1])])],
        moving_window=dict(station_extent_m=480., lateral_extent_m=(grid['ny']-1)*grid['dy'], advance_m=80.),
        settled_hydraulics=True, procedural_reference_field=False,
        full_river_coverage=False)
    (out/'moving_water_streaming.json').write_text(json.dumps(stream, indent=2)+'\n')
    shutil.copyfile(review, out/'construction_review.json')
    result = dict(schema='raftsim.continuous_runtime_candidate.v1' if chilko else 'raftsim.colorado_continuous_runtime_candidate.v1',
        river_id=river_id,
        source_inputs=inputs.relative_to(ROOT).as_posix(), source_cook=cook.relative_to(ROOT).as_posix(),
        source_review_sha256=sha(review), source_core_interval_m=None if chilko else build['source_core_interval_m'],
        hydraulic_station_range_m=[float(station[0]), float(station[-1])],
        terrain_solver_bed_max_error_m=terrain_error,
        files_sha256={p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*') if p.is_file()},
        limitations=['Construction screening is not boat, shoreline animation or performance acceptance.',
                     'Full geographic coordinate coverage does not imply full terrain or water coverage.',
                     'No vegetation placement or measured rapid obstacle claims in this export.'],
        full_river_coverage=False, playable_map_created=False, engine_validated=False, accepted=False)
    (out/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('inputs', 'cook', 'review', 'out'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--river-id',choices=['colorado_river_grand_canyon_rowing','chilko_river_bc'],default='colorado_river_grand_canyon_rowing')
    args = parser.parse_args()
    result = export(*(getattr(args, key).resolve() for key in ('inputs', 'cook', 'review', 'out')),river_id=args.river_id)
    print(json.dumps({k: v for k, v in result.items() if k != 'files_sha256'}, indent=2))
