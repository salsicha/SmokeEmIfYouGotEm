"""Explicit inferred-roof contract, separate from immutable captured returns."""
import json
from pathlib import Path
import numpy as np

from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


def validate_envelope_arrays(original, envelope, floor):
    roof = np.asarray(original['vertices_m'])
    solid = np.asarray(envelope['solid_vertices_m'])
    if (solid.shape != original['solid_vertices_m'].shape or not np.isfinite(solid).all() or
            not np.array_equal(solid[:, :2], original['solid_vertices_m'][:, :2]) or
            not np.array_equal(solid[len(roof):], original['solid_vertices_m'][len(roof):])):
        raise ValueError('Envelope changed XY, floor or array layout')
    active = solid[:len(roof)].copy()
    if np.any(active[:, 2] > roof[:, 2]) or np.any(active[:, 2] <= floor):
        raise ValueError('Envelope must be lower-only and remain above its floor')
    if np.array_equal(active, roof):
        raise ValueError('Empty interpreted envelope')
    for name in ('solid_triangles', 'solid_face_kind'):
        if not np.array_equal(envelope[name], original[name]):
            raise ValueError('Envelope changed solid topology or face authority')
    vertices, faces, kinds, _ = close_cap_below_retained_terrain(active, original['triangles'], floor)
    if not (np.array_equal(vertices, solid) and np.array_equal(faces, envelope['solid_triangles']) and
            np.array_equal(kinds, envelope['solid_face_kind'])):
        raise ValueError('Envelope roof and collision solid differ')
    if (not np.array_equal(envelope['roof_original_z_m'], roof[:, 2]) or
            not np.array_equal(envelope['roof_lowered_m'], roof[:, 2]-active[:, 2])):
        raise ValueError('Envelope original-return/lowering receipt differs')
    return active


def load_interpreted_envelope(path, root, cap_manifest, cap_path, cap, floor, origin):
    from south_fork_rock_union import sha
    root = Path(root).resolve()
    path = Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Envelope descriptor outside project')
    record = json.loads(path.read_text())
    if (record.get('schema') != 'raftsim.inferred_rock_envelope_union_source.v1' or
            record.get('faces_measured') is not False or record.get('captured_returns_modified') is not False):
        raise ValueError('Explicit inferred-envelope authority required')
    if record.get('origin_utm_and_vertical_datum_m') != list(origin):
        raise ValueError('Envelope source frame mismatch')
    dependencies = {}
    for key in ('source_cap_manifest', 'envelope_file', 'build_receipt'):
        source = (root/record[key]).resolve()
        if not source.is_relative_to(root) or sha(source) != record[key+'_sha256']:
            raise ValueError('Envelope dependency changed: '+key)
        dependencies[key] = source
    if dependencies['source_cap_manifest'] != Path(cap_manifest).resolve():
        raise ValueError('Envelope belongs to a different captured roof')
    build = json.loads(dependencies['build_receipt'].read_text())
    if (build.get('schema') != 'raftsim.troublemaker_rock_envelope.v2' or
            build.get('source_cap_sha256') != sha(cap_path) or
            build.get('output_sha256') != record['envelope_file_sha256'] or
            build.get('faces_measured') is not False or build.get('captured_returns_modified') is not False):
        raise ValueError('Envelope construction receipt/source mismatch')
    with np.load(cap_path, allow_pickle=False) as original, np.load(dependencies['envelope_file'], allow_pickle=False) as envelope:
        active = validate_envelope_arrays(original, envelope, floor)
        changed = int(np.count_nonzero(active[:,2] != original['vertices_m'][:,2]))
    if changed != build['vertices_changed'] or len(active) != build['roof_vertices']:
        raise ValueError('Envelope construction counts differ')
    identity = dict(descriptor=path.relative_to(root).as_posix(),descriptor_sha256=sha(path),
        envelope_file=record['envelope_file'],envelope_sha256=record['envelope_file_sha256'],
        build_receipt=record['build_receipt'],build_receipt_sha256=record['build_receipt_sha256'],
        source_cap_sha256=cap['cap_sha256'],changed_roof_vertices=changed,
        faces_measured=False,captured_returns_modified=False,
        old_hydraulic_constraints_not_equivalence_proof=True)
    return active, identity
