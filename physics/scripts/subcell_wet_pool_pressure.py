"""Two original pressure poles on a fixed, source-topological wet-pool graph.

The harmonic shared column reduces exactly to the original flat D_h weights.
Exact local kinetic factors retain source depth/slope variation. Dry pools are
absent; reflecting exterior faces are explicit. This static operator does NOT
derive nonlinear bed-force work, moving topology, wetting, time or gameplay.
"""
import math
import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from pressure_cg_range_reference import solve as range_cg
from triangle_face_section import TriangleFaceSection


def harmonic_area(segment, left_height, right_height, left_datum, right_datum):
    """Integral 2*hL*hR/(hL+hR) over the common positive wet interval.

    Exact logarithmic antiderivative, with a convergent numerical series only
    to avoid log1p subtraction cancellation. No dry-depth threshold is used.
    """
    segment = np.asarray(segment, float)
    if segment.shape != (2, 2) or not np.isfinite(segment).all():
        raise ValueError('Finite shared face segment required')
    width = segment[1, 0]-segment[0, 0]
    if width <= 0 or not np.isfinite([left_height, right_height, left_datum, right_datum]).all():
        raise ValueError('Positive face length and finite relative stages required')
    delta = math.fsum((right_datum, -left_datum, right_height, -left_height))
    if delta < 0:
        left_height, right_height, left_datum, right_datum = right_height, left_height, right_datum, left_datum
        delta = -delta
    low, high = np.sort(segment[:, 1])
    b = math.fsum((left_height, left_datum, -float(low)))
    if b <= 0:
        return 0.
    a = math.fsum((left_height, left_datum, -float(high)))
    if a < 0:
        width *= b/(high-low)
        a = 0.
    if delta == 0:
        return width*.5*(a+b)
    span = b-a
    at_a = 2*a/(1+a/(a+delta)) if a > 0 else 0.
    if span == 0:
        return width*at_a
    denominator = 2*a+delta
    z = 2*span/denominator
    ratio = delta/denominator
    if z < .01:
        # (z-log1p(z))/z^2 = sum (-z)^k/(k+2).
        # At z<.01 twelve terms leave <1e-25 absolute truncation error.
        series = sum((-z)**k/(k+2) for k in range(12))
        correction = ratio*ratio*span*series
    else:
        log_ratio = math.log1p(z)/z if math.isfinite(z) else 0.
        correction = .5*ratio*ratio*denominator*(1-log_ratio)
    result = width*(at_a+.5*span+correction)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Shared harmonic column exceeds represented range')
    return result


def shared_subsegments(left, right):
    """Intersect labelled source face pieces without joining point contacts."""
    for li, a in left:
        for ri, b in right:
            low, high = max(a[0, 0], b[0, 0]), min(a[1, 0], b[1, 0])
            if high <= low:
                continue
            t = np.array([low, high])
            za = a[0, 1]+(a[1, 1]-a[0, 1])*(t-a[0, 0])/(a[1, 0]-a[0, 0])
            zb = b[0, 1]+(b[1, 1]-b[0, 1])*(t-b[0, 0])/(b[1, 0]-b[0, 0])
            # Same coverage tolerance as the existing source-face verifier;
            # coordinates are not welded or displaced to satisfy this check.
            if not np.allclose(za, zb, atol=1e-9, rtol=0):
                raise ValueError('Pool owners disagree on original shared terrain')
            yield li, ri, np.column_stack((t, za))


def piecewise_column_integral(partition, first, second=None):
    """Independent knot sweep for differing stages of same-cell pool traces.

    Unlike a scalar parent stage, this remains meaningful when distinct pools
    are independently perturbed. Multiple pool owners of one interval are
    rejected. Same-pool trace overlaps are unioned ONLY in this coverage oracle;
    the original geometry/operator remains unchanged and its overlap error is
    measured against this integral.
    """
    pieces = first+(second if second is not None else [])
    if not pieces:
        return 0.
    knots = set(float(x) for _, segment in pieces for x in segment[:, 0])
    for index, segment in pieces:
        form = partition.pools[index]['form']
        depths = [math.fsum((form['stage_offset'], form['datum'], -float(z))) for z in segment[:, 1]]
        if (depths[0] < 0 < depths[1]) or (depths[1] < 0 < depths[0]):
            knots.add(float(segment[0, 0]+(segment[1, 0]-segment[0, 0])*depths[0]/(depths[0]-depths[1])))
    knots = sorted(knots)
    total = 0.
    for low, high in zip(knots, knots[1:]):
        def owner(segments):
            # No representable midpoint need exist between adjacent float knots.
            candidates = [(index, segment) for index, segment in segments
                          if segment[0, 0] <= low and high <= segment[1, 0]]
            # A component's source triangle can have dry face portions. Those
            # portions do not own pressure, including at a dry rock ridge where
            # separately clipped traces overlap by one representable interval.
            candidates = [(i, s) for i, s in candidates
                          if any(math.fsum((partition.pools[i]['form']['stage_offset'],
                                            partition.pools[i]['form']['datum'], -float(z))) > 0
                                 for z in np.interp([low, high], s[:, 0], s[:, 1]))]
            if len(candidates) > 1:
                heights = [np.interp([low, high], s[:, 0], s[:, 1]) for _, s in candidates]
                # Existing source-face agreement tolerance; no geometry welding.
                if (len(set(i for i, _ in candidates)) != 1
                        or any(not np.allclose(z, heights[0], atol=1e-9, rtol=0) for z in heights[1:])):
                    raise ValueError(f'Multiple incompatible pool traces on interval {low!r}, {high!r}: '
                                     f'{[(i, s.tolist()) for i, s in candidates]}')
            return candidates[0] if candidates else None
        left = owner(first)
        right = owner(second) if second is not None else left
        if left is None or right is None:
            continue
        index, segment = left
        t = np.array([low, high])
        z = segment[0, 1]+(segment[1, 1]-segment[0, 1])*(t-segment[0, 0])/(segment[1, 0]-segment[0, 0])
        clipped = np.column_stack((t, z))
        lp, rp = partition.pools[index]['form'], partition.pools[right[0]]['form']
        if second is None:
            total += TriangleFaceSection([clipped], [low, high]).moments(lp['stage_offset'], lp['datum'])[0]
        else:
            total += harmonic_area(clipped, lp['stage_offset'], rp['stage_offset'], lp['datum'], rp['datum'])
    return total


def uniform_parent_stage(partition, parent):
    pools = [partition.pools[i] for i in partition.parent_pools[parent]]
    return pools and all(p['parent_stage_offset'] == pools[0]['parent_stage_offset'] for p in pools)


class WetPoolPressureSystem:
    def __init__(self, partition, length):
        if not np.isfinite(length) or length <= 0 or not partition.pools:
            raise ValueError('Positive pressure pole and nonempty wet-pool graph required')
        self.partition, self.length = partition, float(length)
        self.h = np.array([pool['volume'] for pool in partition.pools])[:, None]
        self.root = np.sqrt(self.h[:, 0])
        self.row_maps = [dict() for _ in partition.pools]
        self.connections, self.walls = [], []
        self.maximum_shared_column_partition_error = 0.
        self.maximum_wall_column_partition_error = 0.
        def add(row, column, value):
            entry = self.row_maps[row]
            entry[column] = entry.get(column, 0.)+value
        for left, right, axis, section in partition.patch.faces:
            if left >= 0 and right >= 0:
                first = partition.boundary_segments(left, axis, 1)
                second = partition.boundary_segments(right, axis, -1)
                total_area = 0.
                for li, ri, segment in shared_subsegments(first, second):
                    lp, rp = partition.pools[li], partition.pools[ri]
                    area = harmonic_area(segment, lp['form']['stage_offset'], rp['form']['stage_offset'],
                                         lp['form']['datum'], rp['form']['datum'])
                    if area == 0:
                        continue
                    total_area += area
                    self.connections.append(dict(left=li, right=ri, axis=axis, area=area))
                    for owner in (li, ri):
                        weight = area/(2*self.h[owner, 0])
                        add(owner, 2*ri+axis, weight)
                        add(owner, 2*li+axis, -weight)
                expected = piecewise_column_integral(partition, first, second)
                self.maximum_shared_column_partition_error = max(self.maximum_shared_column_partition_error,
                    abs(total_area-expected)/max(1., expected))
                if uniform_parent_stage(partition, left) and uniform_parent_stage(partition, right):
                    lp = partition.pools[partition.parent_pools[left][0]]
                    rp = partition.pools[partition.parent_pools[right][0]]
                    expected = sum(harmonic_area(segment, lp['parent_stage_offset'], rp['parent_stage_offset'],
                                                lp['parent_datum'], rp['parent_datum']) for segment in section.segments)
                self.maximum_shared_column_partition_error = max(self.maximum_shared_column_partition_error,
                    abs(total_area-expected)/max(1., expected))
            else:
                parent, sign = (right, -1) if left < 0 else (left, 1)
                total_area = 0.
                for owner, segment in partition.boundary_segments(parent, axis, sign):
                    pool = partition.pools[owner]
                    part = TriangleFaceSection([segment], segment[:, 0])
                    area = part.moments(pool['form']['stage_offset'], pool['form']['datum'])[0]
                    if area == 0:
                        continue
                    total_area += area
                    add(owner, 2*owner+axis, -sign*area/self.h[owner, 0])
                    self.walls.append(dict(owner=owner, axis=axis, sign=sign, area=area))
                expected = piecewise_column_integral(partition, partition.boundary_segments(parent, axis, sign))
                self.maximum_wall_column_partition_error = max(self.maximum_wall_column_partition_error,
                    abs(total_area-expected)/max(1., expected))
                if uniform_parent_stage(partition, parent):
                    pool = partition.pools[partition.parent_pools[parent][0]]
                    expected = section.moments(pool['parent_stage_offset'], pool['parent_datum'])[0]
                self.maximum_wall_column_partition_error = max(self.maximum_wall_column_partition_error,
                    abs(total_area-expected)/max(1., expected))
        # Newly activated source regions can meet inside a Cartesian cell.
        # Retain their actual oblique normal; no forced common pool level.
        for face in partition.internal_faces:
            li, ri = face['left'], face['right']
            if li is None or ri is None:
                continue
            lf, rf = partition.pools[li]['form'], partition.pools[ri]['form']
            area = harmonic_area(face['segment'], lf['stage_offset'], rf['stage_offset'], lf['datum'], rf['datum'])
            if area == 0:
                continue
            self.connections.append(dict(left=li, right=ri, axis=None, normal=face['normal'], area=area,
                                         internal_source_edge=face['edge_vertex_ids']))
            for owner in (li, ri):
                for axis, normal in enumerate(face['normal']):
                    weight = area*normal/(2*self.h[owner, 0])
                    add(owner, 2*ri+axis, weight)
                    add(owner, 2*li+axis, -weight)
        rows, columns, coefficients = [], [], []
        for row, mapping in enumerate(self.row_maps):
            for column, coefficient in mapping.items():
                if coefficient != 0:
                    rows.append(row); columns.append(column); coefficients.append(coefficient)
        self.rows, self.columns = np.asarray(rows, int), np.asarray(columns, int)
        self.coefficients = np.asarray(coefficients)
        # Source subdivision introduces tightly coupled same-parent unknowns.
        # Precondition their exact principal blocks, without coalescing states
        # or changing A. Ordinary disconnected-pool graphs retain the old 2x2
        # path exactly. Only actual common-wet internal edges form a group.
        adjacency = {}
        for face in self.connections:
            if face.get('internal_source_edge'):
                li, ri = face['left'], face['right']
                adjacency.setdefault(li, set()).add(ri)
                adjacency.setdefault(ri, set()).add(li)
        groups, remaining = [], set(adjacency)
        while remaining:
            pending, found = [min(remaining)], set()
            while pending:
                index = pending.pop()
                if index in found:
                    continue
                found.add(index)
                pending.extend(adjacency[index]-found)
            remaining -= found
            groups.append(sorted(found))
        group_for = {pool: (g, i) for g, group in enumerate(groups) for i, pool in enumerate(group)}
        group_matrices = [np.eye(2*len(group)) for group in groups]
        self.diagonal = np.ones((len(self.h), 2))
        self.off_diagonal = np.zeros(len(self.h))
        for index, pool in enumerate(partition.pools):
            mapping = self.row_maps[index]
            columns = sorted(set(mapping) | {2*index, 2*index+1})
            jet_map = np.zeros((3, len(columns)))
            for j, column in enumerate(columns):
                jet_map[0, j] = mapping.get(column, 0.)/self.root[column//2]
                if column//2 == index:
                    jet_map[1+column%2, j] = 1/self.root[index]
            matrix = pool['form']['factor']@jet_map
            for group in set(group_for[c//2][0] for c in columns if c//2 in group_for):
                selected = [(j, 2*group_for[c//2][1]+c%2) for j, c in enumerate(columns)
                            if c//2 in group_for and group_for[c//2][0] == group]
                j, k = zip(*selected)
                local = matrix[:, j]
                group_matrices[group][np.ix_(k, k)] += self.length*(local.T@local)
            for j, column in enumerate(columns):
                self.diagonal[column//2, column%2] += self.length*float(matrix[:, j]@matrix[:, j])
                if column%2 == 0 and column+1 in columns:
                    k = columns.index(column+1)
                    self.off_diagonal[column//2] += self.length*float(matrix[:, j]@matrix[:, k])
        if not np.isfinite(self.coefficients).all() or not np.isfinite(self.diagonal).all():
            raise ValueError('Wet-pool operator exceeds represented range')
        self.source_blocks = [(np.array(group, int), np.linalg.cholesky(matrix))
                              for group, matrix in zip(groups, group_matrices)]

    def _vector(self, value):
        value = np.asarray(value, float)
        if value.shape != (len(self.h), 1, 2) or not np.isfinite(value).all():
            raise ValueError('Finite normalized wet-pool vector required')
        return value

    def divergence(self, velocity):
        velocity = np.asarray(velocity, float).reshape(len(self.h), 2)
        return np.bincount(self.rows, weights=self.coefficients*velocity.ravel()[self.columns], minlength=len(self.h))

    def divergence_transpose(self, scalar):
        scalar = np.asarray(scalar, float)
        return np.bincount(self.columns, weights=self.coefficients*scalar[self.rows],
                           minlength=2*len(self.h)).reshape(-1, 2)

    def factor_action(self, q):
        velocity = self._vector(q)[:, 0]/self.root[:, None]
        jet = np.column_stack((self.divergence(velocity), velocity))
        return [pool['form']['factor']@jet[i] for i, pool in enumerate(self.partition.pools)]

    def factor_transpose(self, values):
        jet = np.array([pool['form']['factor'].T@value for pool, value in zip(self.partition.pools, values)])
        result = self.divergence_transpose(jet[:, 0])+jet[:, 1:]
        return (result/self.root[:, None])[:, None, :]

    def apply(self, q):
        q = self._vector(q)
        return q+self.length*self.factor_transpose(self.factor_action(q))

    def precondition(self, residual, scheme='block'):
        r = self._vector(residual)[:, 0]
        if scheme not in ('block', 'source-block'):
            raise ValueError('Only local 2x2 or connected source-region block preconditioning is implemented')
        a, b = self.diagonal.T
        ratio = self.off_diagonal/a
        schur = b-self.off_diagonal*ratio
        if (schur <= 0).any() or not np.isfinite(schur).all():
            raise ValueError('Invalid wet-pool pressure block')
        second = (r[:, 1]-ratio*r[:, 0])/schur
        first = r[:, 0]/a-ratio*second
        result = np.stack((first, second), axis=-1)
        if scheme == 'source-block':
            for indices, cholesky in self.source_blocks:
                result[indices] = np.linalg.solve(cholesky.T,
                    np.linalg.solve(cholesky, r[indices].ravel())).reshape(-1, 2)
        return result[:, None, :]

    def solve(self, rhs):
        scheme = 'source-block' if self.source_blocks else 'block'
        value, stats = range_cg(self, self._vector(rhs), 40, preconditioner=scheme)
        return value, dict(stats, preconditioner=scheme)


def response(partition, rhs):
    result = (1-float(np.sum(WEIGHTS)))*np.asarray(rhs, float)
    poles = []
    for length, weight in zip(LENGTHS, WEIGHTS):
        system = WetPoolPressureSystem(partition, float(length))
        value, stats = system.solve(rhs)
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original 40-CG wet-pool pressure residual gate failed')
        result += weight*value
        poles.append(dict(length=float(length), weight=float(weight), **stats))
    return dict(value=result, poles=poles, static_pressure_only=True,
        nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
