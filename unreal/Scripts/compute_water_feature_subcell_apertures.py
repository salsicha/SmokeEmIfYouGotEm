"""Geometric all-face aperture construction from pinned actual closed meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from water_feature_subcell_geometry import face_apertures


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    source = json.loads(args.inputs.read_text())
    hashes = {**source['dependency_sha256'], **source['outputs_sha256'],
        str(args.inputs.resolve()): digest(args.inputs), str(Path(__file__).resolve()): digest(__file__)}
    helper = Path(__file__).with_name('water_feature_subcell_geometry.py'); hashes[str(helper.resolve())] = digest(helper)
    if not source['complete'] or any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned source export changed')
    meshes = {m['name']: (np.load(m['vertices'], allow_pickle=False), np.load(m['triangles'], allow_pickle=False))
              for m in source['meshes']}
    args.output.mkdir(); started = time.perf_counter()

    def progress(axis, index):
        if index % 10 == 0:
            print('GEOMETRIC_APERTURE_PLANE', axis, index, 'seconds', time.perf_counter()-started, flush=True)

    arrays, planes = face_apertures(meshes, source['shape'], source['origin_m'], source['cell_m'], progress)
    files = []; outputs = {}; statistics = []
    h = source['cell_m']
    for axis, area in enumerate(arrays):
        path = args.output/f'open-area-axis-{axis}.npy'
        with path.open('xb') as stream:
            np.save(stream, area, allow_pickle=False)
        files.append(str(path.resolve())); outputs[str(path.resolve())] = digest(path)
        statistics.append(dict(axis=axis, shape=area.shape, faces=area.size, fully_blocked=int(np.count_nonzero(area == 0)),
            fully_open=int(np.count_nonzero(area == h*h)), cut_faces=int(np.count_nonzero((area > 0) & (area < h*h))),
            minimum_open_area_m2=float(area.min()), maximum_open_area_m2=float(area.max())))
    report = dict(complete=True, accepted=False, frame=source['frame'], shape=source['shape'],
        origin_m=source['origin_m'], cell_m=h, construction_seconds=time.perf_counter()-started,
        meshes=source['meshes'], arrays=files, face_statistics=statistics, plane_sections=planes,
        dependency_sha256=hashes, outputs_sha256=outputs, input_vertices_moved=False,
        physical_area_units='m^2', native_storage_mapping='Lower face component: full area array at indices [0:N] / cell_m^2',
        scope='Only exact triangle/plane union areas; no native pressure, trajectory contact, mass budget, surface or visible acceptance')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Input preservation failed')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('GEOMETRIC_APERTURES_COMPLETE', statistics, report['construction_seconds'], flush=True)


if __name__ == '__main__':
    main()
