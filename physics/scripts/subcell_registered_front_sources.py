"""Recover a conditional front's ORIGINAL registered terrain triangles.

The water-state audit block is not a terrain boundary. Search the complete
registered mesh using outward-rounded broad-phase bounds, then retain exact
binary-source rationals for ownership and flux. No clamp, fill or extrapolation.
This source index says nothing about water state outside the inspected block.
"""
from fractions import Fraction as F
import math

import numpy as np

from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_exact_geometry import SourceFragment


class RegisteredFrontSources:
    def __init__(self, sampler):
        if not isinstance(sampler,RegisteredMeshSampler):
            raise ValueError('Validated original registered mesh required')
        # Own an immutable geometry epoch: caller edits cannot stale a cached
        # exact triangle while silently changing its broad-phase bounds.
        self._triangles = np.array(sampler.xyz[sampler.faces],dtype=float,copy=True)
        self._triangles.setflags(write=False)
        self._low = self._triangles[:,:,:2].min(axis=1)
        self._high = self._triangles[:,:,:2].max(axis=1)
        self._low.setflags(write=False)
        self._high.setflags(write=False)
        self._exact = {}

    def _fragment(self, source_id):
        if source_id not in self._exact:
            xyz = tuple(tuple(F(float(v)) for v in p) for p in self._triangles[source_id])
            a,b = (tuple(p[j]-xyz[0][j] for j in range(3)) for p in xyz[1:])
            determinant = a[0]*b[1]-a[1]*b[0]
            if determinant == 0:
                raise ValueError('Degenerate original terrain triangle')
            gradient = ((a[2]*b[1]-b[2]*a[1])/determinant,
                        (a[0]*b[2]-b[0]*a[2])/determinant)
            self._exact[source_id] = SourceFragment(source_id,xyz,gradient)
        return self._exact[source_id]

    def fragments(self, sweep):
        """Conservative candidates for the complete ray, not a guessed halo.

        One nextafter step outward encloses exact rational bounds rounded to
        binary64, including sub-ulp/sub-float displacements. It enlarges ONLY
        the search; no returned vertex, front point or ownership is moved.
        Every original face is checked, so registered lattice offsets cannot
        exclude an owner. Exact ownership rejects broad-phase false positives.
        """
        endpoints = (sweep.edge[0][:2],tuple(sweep.edge[0][j]+sweep.velocity[j]*sweep.time_root**3
                                           for j in range(2)))
        low,high = [],[]
        for axis in range(2):
            values = [p[axis] for p in endpoints]
            try:
                a,b = float(min(values)),float(max(values))
            except OverflowError as exc:
                raise ValueError('Ray exceeds represented mesh-search range; no clamping') from exc
            if not math.isfinite(a) or not math.isfinite(b):
                raise ValueError('Finite represented mesh-search bounds required')
            low.append(np.nextafter(a,-np.inf))
            high.append(np.nextafter(b,np.inf))
        indices = np.flatnonzero(np.all(self._high>=low,axis=1)&np.all(self._low<=high,axis=1))
        return {int(i):self._fragment(int(i)) for i in indices}
