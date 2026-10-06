"""Compare cached stages at identical world XY, not different screenshot pixels.

Diagnostic only. Independent runs may have different source ages, flow states,
bed hypotheses and raft trajectories. This is not an isolated bed experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_carrier_camera_rays import probe
from audit_submitted_carrier_shape import (
    SOURCE_FIELDS_V2, VERTEX_FIELDS, gradients, raw_stage, read_table, summarize,
)


def validate_source(meta, source):
    nx, ny = meta['source_nx'], meta['source_ny']
    if (meta.get('schema') != 'raftsim.submitted_carrier_shape.v2' or
            type(nx) is not int or type(ny) is not int or nx < 2 or ny < 2 or
            meta['world_y_sign'] not in (-1, 1) or source.shape != (nx*ny, 8) or
            not np.isfinite(source).all() or
            not np.array_equal(source[:, 0], np.arange(nx*ny)) or
            not np.isin(source[:, 3], [0, 1]).all() or np.any(source[:, 5] < 0)):
        raise ValueError('Complete finite ordered source lattice required')
    # Also validate uniform XY and row ordering, including an all-missing probe run.
    raw_stage(source[:1, 1:3]*[1, meta['world_y_sign']], source, nx, ny, meta['world_y_sign'])


def compare(reference_meta, reference_source, rays, candidate_meta, candidate_source):
    for meta, source in ((reference_meta, reference_source), (candidate_meta, candidate_source)):
        validate_source(meta, source)
    if reference_meta['world_y_sign'] != candidate_meta['world_y_sign']:
        raise ValueError('Matching registered world/field Y conventions required')
    for key in ('game_frame', 'world_seconds', 'detail_sequence'):
        if rays[key] != reference_meta[key]:
            raise ValueError('Reference ray/source epoch mismatch')
    rows = []
    for ray in rays['probes']:
        row = dict(pixel=ray['pixel'], reference_triangle=None, comparison_available=False)
        hit = ray['hit']
        if hit is None:
            row['reason'] = 'No reference CPU triangle on this camera ray'
            rows.append(row)
            continue
        points = np.asarray(hit['vertices_world_m'], dtype=float)
        if points.shape != (3, 3) or not np.isfinite(points).all():
            raise ValueError('Original finite reference triangle required')
        row.update(reference_triangle=hit['triangle'], world_xy_m=points[:, :2].tolist(),
                   reference_displayed_slope_degrees=hit['slope_degrees'])
        available = True
        for name, meta, source in (('reference', reference_meta, reference_source),
                                    ('candidate', candidate_meta, candidate_source)):
            values, valid = raw_stage(points[:, :2], source, meta['source_nx'],
                                     meta['source_ny'], meta['world_y_sign'])
            row[name] = dict(fully_wet_source_vertices=valid.tolist())
            if valid.all():
                gradient = gradients(points[None, :, :2], values[None])[0]
                row[name].update(stage_m=values.tolist(), gradient_world_xy=gradient.tolist(),
                    slope_degrees=float(np.degrees(np.arctan(np.linalg.norm(gradient)))))
            else:
                available = False
        row['comparison_available'] = available
        if available:
            row['candidate_minus_reference_stage_m'] = (
                np.asarray(row['candidate']['stage_m'])-row['reference']['stage_m']).tolist()
        else:
            row['reason'] = 'Outside or not fully wet/available/connected; no extrapolation'
        rows.append(row)
    return dict(schema='raftsim.same_xy_carrier_sources.v1', accepted=False,
        reference_epoch={k: reference_meta[k] for k in ('game_frame', 'world_seconds', 'detail_sequence')},
        candidate_epoch={k: candidate_meta[k] for k in ('game_frame', 'world_seconds', 'detail_sequence')},
        probes=rows, comparable_probes=sum(r['comparison_available'] for r in rows),
        limitations='Same world XY of original reference CPU triangles, not candidate camera pixels or candidate rendered triangles. Piecewise A-D cached-source interpolation only on fully wet cells. Different run/source ages, evolving flow and inferred bed may all contribute; not an isolated bed effect, measured bathymetry, GPU visibility, physics, visual, FPS or release acceptance.')


def load_capture(path):
    paths = [path]+[Path(str(path)+suffix) for suffix in ('.vertices.csv', '.triangles.csv', '.source.csv', '.normals.csv')]
    meta = json.loads(path.read_text(encoding='utf-8-sig'))
    tables = [read_table(p, fields) for p, fields in zip(paths[1:], (
        VERTEX_FIELDS, ['a', 'b', 'c'], SOURCE_FIELDS_V2, ['id', 'normal_x', 'normal_y', 'normal_z']))]
    summarize(meta, *tables[:3], 30.)
    return meta, tables, paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference', type=Path)
    p.add_argument('view', type=Path)
    p.add_argument('candidate', type=Path)
    p.add_argument('--pixel', nargs=2, type=float, action='append', required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    a, at, ap = load_capture(args.reference)
    b, bt, bp = load_capture(args.candidate)
    view = json.loads(args.view.read_text(encoding='utf-8-sig'))
    rays = probe(a, view, *at, args.pixel)
    result = compare(a, at[2], rays, b, bt[2])
    result['input_sha256'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in ap+bp+[args.view]}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
