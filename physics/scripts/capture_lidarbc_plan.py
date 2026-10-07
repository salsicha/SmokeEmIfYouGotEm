"""Serial, resumable acquisition of a reviewed corridor's bounded DEM requests.

Completed captures are reused only after validating their identity and pixels.
Empty native windows are recorded as missing terrain, never filled or retried
automatically. Other incomplete/failed captures are preserved and stop the run.
This acquires source evidence only; it does not place rapids or accept a map.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from capture_lidarbc_window import capture, validate_catalogue, validate_window
from mosaic_lidarbc_crops import CRS, VERTICAL, sha
from plan_lidarbc_corridor_capture import capture_window


def checked_plan(path):
    plan = json.loads(path.read_text())
    if (plan.get('schema') != 'raftsim.lidarbc_continuous_capture_plan.v1' or
            sha(Path(plan['route'])) != plan['route_sha256'] or
            sha(path.parent/'catalogue.json') != plan['catalogue_sha256']):
        raise ValueError('Changed or unsupported source inventory')
    tiles = {t['filename']: t for t in plan['accepted_headers']}
    cells = {tuple(c['cell']): c for c in plan['cells']}
    requests = plan['capture_requests']
    if not requests or len(requests) > 4096 or len(cells) != len(plan['cells']):
        raise ValueError('Invalid request count or duplicate grid cell')
    seen = set()
    for request in requests:
        tile = tiles[request['tile']]
        cell = cells[tuple(request['cell'])]
        if validate_catalogue(tile['catalogue_attributes'], tile['filename']) != tile['url']:
            raise ValueError('Changed source URL')
        expected = capture_window(cell['bounds'], tile['raster_bounds'])
        if list(validate_window(request['window_utm'])) != expected:
            raise ValueError('Capture request differs from native intersection')
        key = (tuple(request['cell']), request['tile'])
        if key in seen:
            raise ValueError('Duplicate capture request')
        seen.add(key)
    return plan


def checked_crop(path, request):
    meta = json.loads(path.with_suffix('.json').read_text())
    if (meta.get('schema') != 'raftsim.lidarbc_dem_crop.v1' or
            meta['npz_sha256'] != sha(path) or meta['crs'] != CRS or
            meta['vertical'] != VERTICAL or meta['cell_m'] != 1. or
            meta['window_utm'] != request['window_utm'] or
            len(meta['tiles']) != 1 or meta['tiles'][0]['file'] != request['tile'] or
            meta['catalogue_sha256'] != sha(path.with_suffix('.catalog.json'))):
        raise ValueError('Existing crop does not match the request and provenance')
    tile = meta['tiles'][0]
    if validate_catalogue(tile['source_catalogue_attributes'], request['tile']) != tile['url']:
        raise ValueError('Existing crop source URL differs')
    x0, y0, x1, y1 = validate_window(request['window_utm'])
    with np.load(path, allow_pickle=False) as source:
        data = source['height_m']
        finite = np.isfinite(data)
        if (data.dtype != np.float32 or data.shape != (y1-y0, x1-x0) or
                list(data.shape) != meta['shape'] or float(source['cell_m']) != 1. or
                float(source['x0']) != x0 or float(source['y_top']) != y1 or
                np.isinf(data).any() or not finite.any() or
                int((~finite).sum()) != meta['missing_pixels'] or
                abs(float(finite.mean())-meta['valid_share']) > 1e-12):
            raise ValueError('Existing native pixels disagree with capture receipt')
    return meta


def acquire(plan_path, out, max_new=1):
    if type(max_new) is not int or not 1 <= max_new <= 4096:
        raise ValueError('Positive bounded capture count required')
    plan = checked_plan(plan_path)
    identity = dict(plan_sha256=sha(plan_path), route_sha256=plan['route_sha256'])
    out.mkdir(parents=True, exist_ok=True)
    # Exclusive lock protects the output collection from duplicate acquisitions.
    lock = out/'capture.lock'
    with lock.open('x'):
        pass
    try:
        identity_path = out/'plan_identity.json'
        if identity_path.exists():
            if json.loads(identity_path.read_text()) != identity:
                raise ValueError('Output collection belongs to a different plan')
        else:
            if any(p.name != lock.name for p in out.iterdir()):
                raise ValueError('Existing collection has no verified plan identity')
            with identity_path.open('x') as stream:
                json.dump(identity, stream, indent=2)
        completed, empty, started = [], [], 0
        for i, request in enumerate(plan['capture_requests']):
            path = out/f'request_{i:04d}.npz'
            missing_path = path.with_suffix('.missing.json')
            if missing_path.exists():
                missing = json.loads(missing_path.read_text())
                if (missing.get('request') != request or path.exists() or
                        missing.get('catalogue_sha256') != sha(path.with_suffix('.catalog.json')) or
                        missing.get('reason') != 'native_window_has_no_valid_pixels'):
                    raise ValueError('Changed missing-data receipt')
                empty.append(i)
                continue
            if path.exists():
                checked_crop(path, request)
                completed.append(i)
                continue
            if path.with_suffix('.json').exists() or path.with_suffix('.catalog.json').exists():
                raise ValueError(f'Incomplete capture preserved at {path}; inspect before retrying')
            if started >= max_new:
                continue
            started += 1
            print(f'REQUEST {i+1}/{len(plan["capture_requests"])} {request["tile"]}', flush=True)
            try:
                capture(request['tile'], request['window_utm'], path)
            except ValueError as error:
                if str(error) != 'Native tile has no valid pixels in the requested window':
                    raise
                missing = dict(request=request, reason='native_window_has_no_valid_pixels',
                               catalogue_sha256=sha(path.with_suffix('.catalog.json')))
                with missing_path.open('x') as stream:
                    json.dump(missing, stream, indent=2)
                empty.append(i)
                continue
            checked_crop(path, request)
            completed.append(i)
        return dict(requests=len(plan['capture_requests']), completed=len(completed),
                    empty_native_requests=empty, new_requests_started=started,
                    pending=len(plan['capture_requests'])-len(completed)-len(empty),
                    source_acquisition_complete=len(completed)+len(empty)==len(plan['capture_requests']),
                    full_corridor_valid_pixels_verified=False, playable_acceptance=False)
    finally:
        lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-new', type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(acquire(args.plan, args.out, args.max_new), indent=2))
