"""Small conforming-liquid RT0/P0 gravity/pressure impulse reference.

Explicit tetrahedra and liquid boundary facets; no buried-center ghost distances,
area/dual-volume substitutions or mass lumping. Dense, bounded reference only:
not a scalable river solver, advection, viscosity or a completed liquid simulator.
"""
from itertools import permutations
import numpy as np


def tank_mesh(n, length=(1., .6, .5), bed_rise=0.):
    """Authored liquid slab: exact planar inclined bed and horizontal top.

    Six consistently oriented Freudenthal tetrahedra per logical cube.
    The vertical map creates nonuniform volumes, not a voxelized staircase.
    """
    if not isinstance(n, int) or not 1 <= n <= 8:
        raise ValueError('Bounded positive integer tank refinement required')
    length = np.asarray(length, float)
    if length.shape != (3,) or not np.isfinite(length).all() or np.any(length <= 0) or not 0 <= bed_rise < length[2]:
        raise ValueError('Positive tank dimensions and strictly submerged bed required')
    grid = np.indices((n+1,)*3).reshape(3, -1).T/n
    vertices = grid*length
    bed = bed_rise*grid[:, 0]
    vertices[:, 2] = bed+grid[:, 2]*(length[2]-bed)
    ids = np.arange(len(vertices)).reshape((n+1,)*3); cells = []
    for key in np.ndindex((n,)*3):
        for order in permutations(range(3)):
            pos = np.array(key); tet = [ids[tuple(pos)]]
            for axis in order:
                pos = pos.copy(); pos[axis] += 1; tet.append(ids[tuple(pos)])
            cells.append(tet)
    return vertices, np.asarray(cells, int)


class LiquidTetrahedra:
    def __init__(self, vertices, tetrahedra, density=1000., maximum_faces=1200):
        v = np.asarray(vertices, float); t = np.asarray(tetrahedra)
        if (v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all() or t.ndim != 2 or t.shape[1] != 4
                or not np.issubdtype(t.dtype, np.integer) or len(t) == 0 or np.any(t < 0) or np.any(t >= len(v))
                or not np.isfinite(density) or density <= 0):
            raise ValueError('Finite positive-density tetrahedral liquid required')
        if len({tuple(sorted(row)) for row in t}) != len(t):
            raise ValueError('Repeated liquid tetrahedron')
        self.vertices = v.copy(); self.tetrahedra = t.astype(int).copy(); self.density = float(density)
        xyz = v[t]; edges = xyz[:, 1:]-xyz[:, :1]
        signed = np.linalg.det(edges)/6
        if np.any(signed == 0) or not np.isfinite(signed).all():
            raise ValueError('Degenerate tetrahedron: no small-volume deletion permitted')
        reverse = signed < 0
        self.tetrahedra[reverse, 2:4] = self.tetrahedra[reverse, 3:1:-1]
        xyz = v[self.tetrahedra]; self.volumes = np.abs(signed); self.centroids = xyz.mean(axis=1)
        table = {}; faces = []; owners = []; cell_faces = []; signs = []
        normals = []; areas = []
        for ci, tet in enumerate(self.tetrahedra):
            local = []; orientation = []
            for opposite in range(4):
                key = tuple(sorted(np.delete(tet, opposite)))
                a, b, c = v[list(key)]; av = np.cross(b-a, c-a)/2
                if np.dot(av, v[tet[opposite]]-a) > 0:
                    av = -av
                area = np.linalg.norm(av)
                if area == 0:
                    raise ValueError('Degenerate face')
                if key not in table:
                    fi = len(faces); table[key] = fi; faces.append(key); owners.append([ci]); normals.append(av/area); areas.append(area)
                    sign = 1
                else:
                    fi = table[key]
                    if len(owners[fi]) != 1 or np.dot(normals[fi], av/area) > -1+1e-10:
                        raise ValueError('Nonmanifold or overlapping same-side face')
                    owners[fi].append(ci); sign = -1
                local.append(fi); orientation.append(sign)
            cell_faces.append(local); signs.append(orientation)
        if len(faces) > maximum_faces:
            raise ValueError('Dense prototype size bound exceeded; use scalable assembly before larger meshes')
        self.faces = np.asarray(faces, int); self.owners = owners
        self.cell_faces = np.asarray(cell_faces, int); self.signs = np.asarray(signs, float)
        self.normals = np.asarray(normals); self.areas = np.asarray(areas)
        self.face_centroids = v[self.faces].mean(axis=1)
        self.boundary = np.array([len(owner) == 1 for owner in owners])
        nf = len(faces); self.B = np.zeros((len(t), nf)); self.M = np.zeros((nf, nf))
        # Exact degree-two tetrahedral moments. Use relative coordinates so a
        # translated tiny cell is not obtained by subtracting two huge moments.
        relative = xyz-self.centroids[:, None, :]
        variance_trace = np.sum(relative*relative, axis=(1, 2))/20
        local_mass = density/(9*self.volumes[:, None, None])*(
            variance_trace[:, None, None]+np.einsum('tik,tjk->tij', relative, relative))
        self.local_mass = local_mass
        for ci, ids in enumerate(self.cell_faces):
            s = self.signs[ci]; self.B[ci, ids] = s
            self.M[np.ix_(ids, ids)] += local_mass[ci]*s[:, None]*s[None, :]

    def uniform_flux(self, velocity):
        u = np.asarray(velocity, float)
        if u.shape != (3,) or not np.isfinite(u).all():
            raise ValueError('Finite metric velocity required')
        return self.areas*(self.normals@u)

    def velocity_at_vertices(self, flux):
        """One-sided cell velocities, not an invented unique tangential trace."""
        q = self._flux(flux)
        local = q[self.cell_faces]*self.signs
        xyz = self.vertices[self.tetrahedra]
        basis = (xyz[:, :, None, :]-xyz[:, None, :, :])/(3*self.volumes[:, None, None, None])
        return np.einsum('tijc,tj->tic', basis, local)

    def _flux(self, flux):
        q = np.asarray(flux, float)
        if q.shape != (len(self.faces),) or not np.isfinite(q).all():
            raise ValueError('Finite oriented physical face flux required')
        return q

    def step(self, flux, dt, gravity, prescribed, flux_tolerance=1e-11, momentum_tolerance=1e-9):
        """Gravity plus pressure on FIXED geometry; no interface transport.

        Prescribed boundary fluxes (including solid walls) in m3/s. All other
        external faces have zero ambient pressure, including free liquid faces.
        Each connected liquid component must reach a free-pressure face.
        """
        old = self._flux(flux); g = np.asarray(gravity, float)
        if (not np.isfinite(dt) or dt <= 0 or g.shape != (3,) or not np.isfinite(g).all()
                or not np.isfinite([flux_tolerance, momentum_tolerance]).all()
                or flux_tolerance <= 0 or momentum_tolerance <= 0):
            raise ValueError('Positive physical step/tolerances and finite gravity required')
        fixed = np.zeros(len(old), bool); values = np.zeros(len(old))
        for index, value in prescribed.items():
            if (not isinstance(index, (int, np.integer)) or not 0 <= index < len(old)
                    or not self.boundary[index] or not np.isfinite(value)):
                raise ValueError('Prescribed flux must be on a physical boundary')
            fixed[index] = True; values[index] = value
        free = ~fixed; free_boundary = free & self.boundary
        reached = set(int(self.owners[i][0]) for i in np.flatnonzero(free_boundary)); stack = list(reached)
        while stack:
            ci = stack.pop()
            for fi in self.cell_faces[ci]:
                for other in self.owners[fi]:
                    if other not in reached:
                        reached.add(other); stack.append(other)
        if len(reached) != len(self.tetrahedra):
            raise ValueError('Closed pressure component: explicit compatibility/gauge handling required, not hidden anchoring')
        force = np.zeros(len(old))
        for ci, ids in enumerate(self.cell_faces):
            local = self.density/3*((self.centroids[ci]-self.vertices[self.tetrahedra[ci]])@g)
            force[ids] += self.signs[ci]*local
        rhs_full = self.M@old+dt*force
        predicted = np.linalg.solve(self.M, rhs_full)
        mf = self.M[np.ix_(free, free)]; bf = self.B[:, free]
        rhs = rhs_full[free]-self.M[np.ix_(free, fixed)]@values[fixed]
        constraint = -self.B[:, fixed]@values[fixed]
        system = np.block([[mf, -bf.T], [bf, np.zeros((len(self.B), len(self.B)))]])
        solution = np.linalg.solve(system, np.concatenate((rhs, constraint)))
        new = values.copy(); new[free] = solution[:free.sum()]; impulse = solution[free.sum():]
        flux_residual = self.B@new
        reaction = self.M@new-rhs_full-self.B.T@impulse
        if np.max(np.abs(flux_residual)) > flux_tolerance or np.max(np.abs(reaction[free])) > momentum_tolerance:
            raise ValueError('Fresh coupled constraint/momentum residual fails; no clipping or RHS fitting')
        energy = lambda q: float(q@self.M@q/2)
        loss = energy(new-predicted)
        boundary_work = float(new[fixed]@reaction[fixed])
        closure = energy(new)-energy(predicted)+loss-boundary_work-float(impulse@flux_residual)
        speeds = np.linalg.norm(self.velocity_at_vertices(new), axis=-1)
        inradius = 3*self.volumes/self.areas[self.cell_faces].sum(axis=1)
        proof = dict(volume_m3=float(self.volumes.sum()), mass_kg=float(self.density*self.volumes.sum()),
            dt_seconds=float(dt), maximum_cell_flux_residual_m3_s=float(np.max(np.abs(flux_residual))),
            maximum_divergence_per_second=float(np.max(np.abs(flux_residual/self.volumes))),
            maximum_free_momentum_residual=float(np.max(np.abs(reaction[free]))),
            maximum_prescribed_flux_error_m3_s=float(np.max(np.abs(new[fixed]-values[fixed]))) if fixed.any() else 0.,
            domain_boundary_flux_m3_s=float(new[self.boundary].sum()),
            free_surface_flux_m3_s=float(new[free_boundary].sum()), prescribed_flux_m3_s=float(new[fixed].sum()),
            kinetic_before_j=energy(old), kinetic_predictor_j=energy(predicted), kinetic_after_j=energy(new),
            projection_metric_loss_j=loss, prescribed_boundary_work_j=boundary_work,
            energy_identity_error_j=closure, maximum_cell_vertex_speed_m_s=float(speeds.max()),
            maximum_inradius_courant=float(np.max(dt*speeds.max(axis=1)/inradius)),
            tetrahedra=len(self.tetrahedra), faces=len(old), free_pressure_boundary_faces=int(free_boundary.sum()),
            geometry_advanced=False, accepted=False)
        return new, impulse/dt, proof
