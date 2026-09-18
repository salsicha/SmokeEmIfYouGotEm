"""Source-verified rock extension composed with the original bed-only revision.

Never weakens RegisteredTerrainRevision's fixed-XY, authority-2 contract.
Hydraulics sees the same registered triangles as the candidate geometry; no
evolved water state is transferred. Additional class1 returns remain interpreted.
"""
import json
from pathlib import Path

import numpy as np

from prepare_troublemaker_control_ablation import original_prior_surfaces, sha
from recover_constriction_source_candidate import recover, reconstruct_added_flanks
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_terrain_revision import RegisteredTerrainRevision, load_revision


def source_change_bounds(original, revised, origin):
    """Both old and new triangles matter when registered XY/connectivity moves."""
    if original.xyz.shape != revised.xyz.shape or original.faces.shape != revised.faces.shape:
        raise ValueError('Same registered lattice vertex/face counts required')
    changed = np.any(original.xyz != revised.xyz, axis=1)
    faces = np.any(original.faces != revised.faces, axis=1)
    faces |= np.any(changed[original.faces], axis=1) | np.any(changed[revised.faces], axis=1)
    if not faces.any():
        raise ValueError('Empty source-supported revision')
    positions = np.concatenate((original.xyz[original.faces[faces], :2].reshape(-1, 2),
                                revised.xyz[revised.faces[faces], :2].reshape(-1, 2)))
    return positions.min(axis=0)+origin, positions.max(axis=0)+origin, int(changed.sum())


def verify_extension(installed, candidate, returns, selection, original_prior):
    """Reproduce source selection AND inference; a manifest pass flag is not proof."""
    baseline, controlled = original_prior_surfaces(original_prior)
    prior_cells = original_prior['authority'] == 2
    if not np.array_equal(controlled[prior_cells], original_prior['z_m'][prior_cells]):
        raise ValueError('Original prior reproduction failed')
    expected, added, ids, counts = recover(installed, returns, selection)
    expected, flank = reconstruct_added_flanks(expected, added, baseline)
    if set(expected) != set(candidate) or any(
            expected[k].dtype != candidate[k].dtype or expected[k].shape != candidate[k].shape
            or not np.array_equal(expected[k], candidate[k]) for k in expected):
        raise ValueError('Candidate is not the source-exact declared extension and inferred flank reconstruction')
    # Independent invariants, not just equality with the producer.
    protected = np.isin(installed['authority'], [1, 3, 4])
    for k in ('east_m', 'north_m', 'z_m', 'authority'):
        if not np.array_equal(installed[k][protected], candidate[k][protected]):
            raise ValueError('Original captured source or seam changed')
        if any(not np.array_equal(installed[k][edge], candidate[k][edge])
               for edge in ((0, slice(None)), (-1, slice(None)), (slice(None), 0), (slice(None), -1))):
            raise ValueError('Rapid seam boundary changed')
    xyz = np.column_stack([returns[k][ids] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])
    xyz -= selection['origin_utm_and_vertical_datum_m']
    for axis, key in enumerate(('east_m', 'north_m', 'z_m')):
        if not np.array_equal(candidate[key][added], xyz[:, axis].astype(candidate[key].dtype)):
            raise ValueError('Additional source coordinate changed')
    return dict(added_captured_vertices=int(added.sum()), minimum_source_bin_count=int(counts.min()),
                additional_source_classes={str(int(c)): int(np.count_nonzero(returns['classification'][ids] == c))
                                           for c in np.unique(returns['classification'][ids])},
                inferred_flanks=flank)


class SourceSupportedTerrainRevision:
    # The exact-source sampling operator is shared, not the bed-only validator.
    apply = RegisteredTerrainRevision.apply

    def __init__(self, bed_revision, candidate, origin, datum):
        self.original = bed_revision.original
        self.revised = RegisteredMeshSampler(candidate)
        self.origin = np.asarray(origin, float)
        self.datum = float(datum)
        if (self.origin.shape != (2,) or not np.isfinite(self.origin).all()
                or not np.isfinite(self.datum) or not np.array_equal(self.origin, bed_revision.origin)
                or self.datum != bed_revision.datum):
            raise ValueError('Source-supported revision frame differs')
        self.lower, self.upper, self.changed_vertices = source_change_bounds(self.original, self.revised, self.origin)


def load_source_revision(manifest_path, root, original_path, origin, datum):
    root = Path(root).resolve()
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_relative_to(root):
        raise ValueError('Source-supported revision manifest escapes project')
    record = json.loads(manifest_path.read_text())
    if record.get('schema') != 'raftsim.source_supported_terrain_revision.v1':
        raise ValueError('Explicit source-supported revision schema required')
    if record.get('state_transfer_permitted') is not False or record.get('production_promoted') is not False:
        raise ValueError('Only an unpromoted fresh-state candidate is allowed')
    def dependency(key):
        item = record[key]
        path = (root/item['path']).resolve()
        if not path.is_relative_to(root) or sha(path) != item['sha256']:
            raise ValueError('Source-supported revision dependency changed or escaped project: '+key)
        return path
    paths = {k: dependency(k) for k in ('bed_revision', 'candidate_manifest', 'candidate_mesh',
                                       'source_returns', 'selection', 'original_prior', 'source_naip', 'source_naip_export')}
    bed_record = json.loads(paths['bed_revision'].read_text())
    if bed_record.get('schema') != 'raftsim.captured_rock_xy_mesh_candidate.v1':
        raise ValueError('Only one original bed-only revision may precede the source extension')
    bed = load_revision(paths['bed_revision'], root, original_path, origin, datum)
    candidate_record = json.loads(paths['candidate_manifest'].read_text())
    selection = json.loads(paths['selection'].read_text())
    if (candidate_record.get('schema') != 'raftsim.constriction_source_candidate.v1'
            or candidate_record['parent_mesh_sha256'] != bed.identity['revised_geometry_sha256']
            or candidate_record['mesh_sha256'] != sha(paths['candidate_mesh'])
            or (root/candidate_record['mesh_path']).resolve() != paths['candidate_mesh']
            or candidate_record['selection_sha256'] != sha(paths['selection'])
            or candidate_record['original_returns_sha256'] != sha(paths['source_returns'])
            or not candidate_record.get('additional_flank_interpolation')):
        raise ValueError('Candidate identity chain differs from original bed/source revision')
    if (selection.get('schema') != 'raftsim.interpreted_source_selection.v1'
            or selection['origin_utm_and_vertical_datum_m'] != [*origin, datum]
            or selection['source_mesh_sha256'] != bed.identity['revised_geometry_sha256']
            or selection['original_returns_sha256'] != sha(paths['source_returns'])
            or selection['source_naip_sha256'] != sha(paths['source_naip'])
            or selection['source_naip_export_sha256'] != sha(paths['source_naip_export'])):
        raise ValueError('Interpreted selection source/frame mismatch')
    # The floor must be the exact historical input of the verified bed ablation,
    # not a newly supplied low surface that makes an extension easier to accept.
    old_inputs = bed_record.get('control_ablation', {}).get('source_sha256', {})
    matched = [digest for name, digest in old_inputs.items()
               if (root/name).resolve() == paths['original_prior']]
    if matched != [sha(paths['original_prior'])]:
        raise ValueError('Original inference floor is not the retained bed-ablation source')
    def load(path):
        with np.load(path, allow_pickle=False) as data:
            return {k: data[k] for k in data.files}
    installed = load(root/bed_record['mesh_path'])
    candidate = load(paths['candidate_mesh'])
    proof = verify_extension(installed, candidate, load(paths['source_returns']), selection, load(paths['original_prior']))
    revision = SourceSupportedTerrainRevision(bed, candidate, origin, datum)
    revision.identity = dict(schema='raftsim.registered_source_supported_terrain_revision.v1',
        manifest=manifest_path.relative_to(root).as_posix(), manifest_sha256=sha(manifest_path),
        original_geometry_sha256=bed.identity['original_geometry_sha256'],
        revised_geometry_sha256=sha(paths['candidate_mesh']), mesh_path=paths['candidate_mesh'].relative_to(root).as_posix(),
        inherited_bed_revision=bed.identity, source_dependencies=record,
        changed_vertices=revision.changed_vertices, captured_vertices_unchanged=True,
        registered_xy_and_topology_unchanged=False, rapid_seam_boundary_unchanged=True,
        additional_source_classification_is_interpreted=True,
        measured_bathymetry=False, state_transfer_permitted=False, **proof)
    return revision
