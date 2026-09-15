"""Compare exact source representation with independent rational integrals."""
from fractions import Fraction as F
import math
import numpy as np

from subcell_exact_geometry import SourceRelativeStorage, cell_fragments
from subcell_exact_source_faces import triangle_cut
from subcell_pressure_kinetic_geometry import local_form
from triangle_cell_storage import projected_areas
from subcell_source_face_section import fragment_section
from subcell_wet_connectivity import components
from subcell_wet_pool_pressure import harmonic_area


def audit_representation(sampler, origin, shape, spacing, volumes):
    volumes = np.asarray(volumes, float)
    if (len(shape) != 2 or any(int(n) != n or n < 1 for n in shape)
            or volumes.size != math.prod(shape) or not np.isfinite(volumes).all() or (volumes < 0).any()):
        raise ValueError('One finite nonnegative volume per requested source cell required')
    records, source_cells = [], []
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
        source_cells.append((fragments, storage, storage.relative_stage_for_volume(volume)))
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
            graph = components(sampler, storage, center, spacing, form['stage_offset'])
            force = storage.hydrostatic_bed_force(form['stage_offset'], relative=True)
            face_moment_error = 0.
            for axis in (0, 1):
                for sign in (-1, 1):
                    section = fragment_section(fragments, axis, sign*F(float(spacing[axis]))/2)
                    actual = section.moments(form['stage_offset'], storage.source_datum)
                    expected = [F(0)]*3
                    for (low, high), (start, end) in zip(section.source_levels, section.source_segments):
                        a, b = stage-low, stage-high
                        width = end[0]-start[0]
                        if a <= 0:
                            continue
                        if b < 0:
                            width *= a/(high-low)
                            b = F(0)
                        expected[0] += width*(a+b)/2
                        expected[1] += width*(a*a+a*b+b*b)/3
                        expected[2] += width
                    face_moment_error = max(face_moment_error,
                        float(np.max(abs(np.asarray(actual)-np.asarray(expected, float)))/max(1., max(map(float, expected)))))
                    force[axis] -= sign*.5*9.81*actual[1]
            record.update(exact_frame_component_count=graph['component_count'],
                          partial_lake_force_residual=float(np.max(abs(force))),
                          scaled_face_moment_error=face_moment_error)
        elif volume < 0:
            raise ValueError('Negative actual source volume')
        records.append(record)
    positive = [r for r in records if r['volume'] > 0]
    maximum = lambda key: max((r[key] for r in positive), default=0.)
    shared_faces, shared_columns = 0, []
    for index, (fragments, storage, height) in enumerate(source_cells):
        row, col = divmod(index, shape[1])
        for axis, neighbor in ((0, index+1 if col+1 < shape[1] else None),
                               (1, index+shape[1] if row+1 < shape[0] else None)):
            if neighbor is None:
                continue
            other, other_storage, other_height = source_cells[neighbor]
            first = fragment_section(fragments, axis, F(float(spacing[axis]))/2)
            second = fragment_section(other, axis, -F(float(spacing[axis]))/2)
            first.verify_shared(second)
            shared_columns.append(harmonic_area(first, height, other_height,
                                               storage.source_datum, other_storage.source_datum))
            shared_faces += 1
    errors = {key: maximum(key) for key in ('relative_volume_error', 'scaled_kinetic_gram_error', 'scaled_moment_error',
                                          'partial_lake_force_residual', 'scaled_face_moment_error')}
    return dict(exact_representation_controls_passed=all(v < 1e-10 for v in errors.values()),
        total_cells=len(records), positive_cells=len(positive),
        exact_source_faces=sum(r['exact_source_faces'] for r in records),
        exact_frame_wet_components=sum(r.get('exact_frame_component_count', 0) for r in records),
        exact_shared_cartesian_faces=shared_faces,
        positive_shared_harmonic_columns=sum(v > 0 for v in shared_columns),
        positive_fragments_with_degenerate_float_projection=sum(r['positive_fragments_with_degenerate_float_projection'] for r in records),
        maximum_errors=errors, records=records,
        evolving_storage_or_topology_or_full_physics_or_gameplay_accepted=False,
        scope='Exact original-source polygons, area, slopes, relative storage/face moments, partial-lake '
              'balance, source connectivity and shared column controls. Current evolving pools still '
              'use the old float-vertex storage and float datum/face API; no exact-frame pressure graph evolution.')
