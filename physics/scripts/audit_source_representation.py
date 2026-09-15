"""Compare exact source representation with independent rational integrals."""
from fractions import Fraction as F
import math
import numpy as np

from subcell_exact_geometry import SourceRelativeStorage, cell_fragments
from subcell_exact_source_faces import triangle_cut
from subcell_pressure_kinetic_geometry import local_form
from triangle_cell_storage import projected_areas


def audit_representation(sampler, origin, shape, spacing, volumes):
    volumes = np.asarray(volumes, float)
    if (len(shape) != 2 or any(int(n) != n or n < 1 for n in shape)
            or volumes.size != math.prod(shape) or not np.isfinite(volumes).all() or (volumes < 0).any()):
        raise ValueError('One finite nonnegative volume per requested source cell required')
    records = []
    for index, volume in enumerate(volumes.ravel()):
        row, col = divmod(index, shape[1])
        center = np.asarray(origin)+np.asarray(spacing)*[col, row]
        fragments = cell_fragments(sampler, center, spacing)
        storage = SourceRelativeStorage(fragments)
        collapsed = sum(int(np.sum(projected_areas(np.asarray(f.triangles, float)) == 0)) for f in fragments)
        face_count = 0
        for fragment in fragments:
            for axis in (0, 1):
                for sign in (-1, 1):
                    actual = fragment.face(axis, sign*F(float(spacing[axis]))/2)
                    expected = triangle_cut(sampler.xyz[sampler.faces[fragment.source_id]], center, spacing, axis, sign)
                    if (actual is None) != (expected is None):
                        raise ValueError('Exact storage and independent source face topology disagree')
                    if actual is not None:
                        if not np.array_equal(np.asarray(actual, float), expected):
                            raise ValueError('Exact storage and independent source face coordinates disagree')
                        face_count += 1
        record = dict(parent=index, source_fragments=len(fragments), triangles=len(storage.areas),
                      positive_fragments_with_degenerate_float_projection=collapsed, exact_source_faces=face_count,
                      exact_coverage_passed=True, original_face_equality_passed=True, volume=float(volume))
        if volume > 0:
            form = local_form(storage, volume)
            stage = storage.source_datum+F(form['stage_offset'])
            moments = [F(0)]*4
            gram = [[F(0) for _ in range(3)] for _ in range(3)]
            for fragment in fragments:
                m = fragment.depth_moments(stage)
                moments = [a+b for a, b in zip(moments, m)]
                gram[0][0] += m[3]
                for a in range(2):
                    gram[0][a+1] -= F(3, 2)*m[2]*fragment.gradient[a]
                    gram[a+1][0] -= F(3, 2)*m[2]*fragment.gradient[a]
                    for b in range(2):
                        gram[a+1][b+1] += 3*m[1]*fragment.gradient[a]*fragment.gradient[b]
            expected_gram = np.asarray(gram, float)
            record.update(relative_volume_error=abs(float(moments[1])-volume)/volume,
                scaled_kinetic_gram_error=float(np.max(abs(form['gram']-expected_gram))/max(1., np.max(abs(expected_gram)))),
                scaled_moment_error=float(np.max(abs(form['depth_moments']-np.asarray(moments, float)))
                                          /max(1., max(map(float, moments)))))
        elif volume < 0:
            raise ValueError('Negative actual source volume')
        records.append(record)
    positive = [r for r in records if r['volume'] > 0]
    maximum = lambda key: max((r[key] for r in positive), default=0.)
    errors = {key: maximum(key) for key in ('relative_volume_error', 'scaled_kinetic_gram_error', 'scaled_moment_error')}
    return dict(exact_representation_controls_passed=all(v < 1e-10 for v in errors.values()),
        total_cells=len(records), positive_cells=len(positive),
        exact_source_faces=sum(r['exact_source_faces'] for r in records),
        positive_fragments_with_degenerate_float_projection=sum(r['positive_fragments_with_degenerate_float_projection'] for r in records),
        maximum_errors=errors, records=records,
        evolving_storage_or_topology_or_full_physics_or_gameplay_accepted=False,
        scope='Exact original-source polygons, area, slopes and relative metric controls. '
              'Current evolving pools still use the old float-vertex storage and float datum/face API.')
