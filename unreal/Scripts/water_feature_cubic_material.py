"""Experimental richer 3D material geometry/velocity with local linear pressure.

Reuses the frozen space-time impulse integrator, NOT its quadratic basis.
Twenty-node conforming cubic geometry, full eighth-order Gauss material mass,
degree-six determinant certificates. No assertion of fluid inf-sup stability,
local exact density, feature acceptance, topology changes or source handling.
"""
from itertools import product
import math
import numpy as np
from water_feature_moving_tetra import MovingLiquid, quadrature, basis as quadratic_basis


def lattice(degree):
    vertices = [tuple(degree if i == j else 0 for i in range(4)) for j in range(4)]
    rest = [a for a in product(range(degree+1), repeat=4) if sum(a) == degree and a not in vertices]
    return np.array(vertices+rest, int)


def cubic_basis(bary):
    l = np.asarray(bary, float); alpha = lattice(3)
    gradients = np.array([[-1., -1., -1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    N = np.ones((len(l), len(alpha))); d = np.zeros((len(l), len(alpha), 3))
    for ni, powers in enumerate(alpha):
        factors = []; directions = []
        for axis, count in enumerate(powers):
            for j in range(count):
                factors.append((3*l[:, axis]-j)/(count-j))
                directions.append(3*gradients[axis]/(count-j))
        N[:, ni] = np.prod(factors, axis=0)
        for i, direction in enumerate(directions):
            other = np.prod([f for j, f in enumerate(factors) if j != i], axis=0)
            d[:, ni] += other[:, None]*direction
    return N, d


def determinant_certificate():
    alpha = lattice(6); bary = alpha/6
    matrix = np.array([[math.factorial(6)/math.prod(math.factorial(int(p)) for p in a)
                        *math.prod(float(l[i])**int(a[i]) for i in range(4)) for a in alpha] for l in bary])
    return bary, np.linalg.inv(matrix)


class CubicMaterial(MovingLiquid):
    def __init__(self, vertices, tetrahedra, density=1000., maximum_velocity_nodes=1200, pressure_degree=1):
        v = np.asarray(vertices, float); t = np.asarray(tetrahedra)
        if (v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all() or t.ndim != 2 or t.shape[1] != 4
                or not np.issubdtype(t.dtype, np.integer) or len(t) == 0 or np.any(t < 0) or np.any(t >= len(v))
                or not np.isfinite(density) or density <= 0 or len({tuple(sorted(x)) for x in t}) != len(t)):
            raise ValueError('Finite conforming material topology required')
        t = t.copy(); determinants = np.linalg.det(v[t[:, 1:]]-v[t[:, :1]])
        if np.any(determinants == 0):
            raise ValueError('Degenerate material cell, not removed')
        reversed_cells = determinants < 0; t[reversed_cells, 2:4] = t[reversed_cells, 3:1:-1]
        nodes = list(v.copy()); shared = {((i, 3),): i for i in range(len(v))}; cells = []
        for tet in t:
            ids = []
            for powers in lattice(3):
                key = tuple(sorted((int(vertex), int(weight)) for vertex, weight in zip(tet, powers) if weight))
                if key not in shared:
                    shared[key] = len(nodes); pos = powers@v[tet]/3
                    # Exact authored planar support: do not miss a wall because
                    # an equivalent rational sum rounded one ULP differently.
                    support = v[tet[powers > 0]]
                    for axis in range(3):
                        if np.all(support[:, axis] == support[0, axis]):
                            pos[axis] = support[0, axis]
                    nodes.append(pos)
                ids.append(shared[key])
            cells.append(ids)
        if len(nodes) > maximum_velocity_nodes:
            raise ValueError('Bounded cubic prototype size exceeded')
        if pressure_degree not in (1, 2):
            raise ValueError('Explicit linear/quadratic local pressure experiment required')
        self.pressure_degree = pressure_degree; self.pressure_shapes = 4 if pressure_degree == 1 else 10
        self.positions = np.array(nodes); self.cells = np.array(cells); self.vertex_cells = t
        self.pressure_mode = 'discontinuous_p'+str(pressure_degree); self.pressure_nodes = self.pressure_shapes*len(t)
        self.pressure_cells = np.arange(self.pressure_nodes).reshape(-1, self.pressure_shapes)
        self.density = float(density); self._cached_free = None
        self.bary, self.weights = quadrature(8); self.N, self.grad = cubic_basis(self.bary)
        self.pressure_basis = self.bary if pressure_degree == 1 else quadratic_basis(self.bary)[0]
        self.cert_bary, self.cert_inverse = determinant_certificate(); _, self.cert_grad = cubic_basis(self.cert_bary)
        self.velocities = np.zeros_like(self.positions); self.steps = 0
        self.initialize_material(self.positions); self.fixed = np.zeros_like(self.positions, bool)

    def divergence_matrix(self, positions):
        from water_feature_moving_tetra import geometry_jacobian
        _, cof = geometry_jacobian(positions, self.cells, self.grad)
        local = np.einsum('q,qi,qjb,tqab->tija', self.weights, self.pressure_basis, self.grad, cof, optimize=True)
        result = np.zeros((self.pressure_nodes, 3*len(self.positions)))
        for ci, ids in enumerate(self.cells):
            dofs = (3*ids[:, None]+np.arange(3)).ravel()
            result[np.ix_(self.pressure_cells[ci], dofs)] += local[ci].reshape(self.pressure_shapes, 60)
        return result

    def step(self, *args, **kwargs):
        # The frozen integrator's local-pressure branch is shape-agnostic but
        # named for its original P1 caller. Use that branch with ALL actual
        # rows, restore the true external space label even on atomic failure.
        true_mode = self.pressure_mode; self.pressure_mode = 'discontinuous_p1'
        try:
            pressure, proof = super().step(*args, **kwargs)
        finally:
            self.pressure_mode = true_mode
        proof['pressure_mode'] = true_mode; proof['pressure_degree'] = self.pressure_degree
        return pressure, proof


def barycentric_split(vertices, tetrahedra):
    """Author a conforming four-tetra split of every original straight cell.

    A topology choice for NEW controls, not remeshing a moving checkpoint.
    Shared original faces are unchanged; no new face cracks or cell deletion.
    No curved/material stability claim follows from the straight-mesh pattern.
    """
    v = np.asarray(vertices, float); t = np.asarray(tetrahedra, int); nodes = list(v.copy()); cells = []
    for tet in t:
        center = len(nodes); nodes.append(v[tet].mean(axis=0))
        for opposite in range(4):
            corners = [int(tet[j]) for j in range(4) if j != opposite]
            cells.append([center, *corners])
    return np.array(nodes), np.array(cells)
