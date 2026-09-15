"""Independent face/bed-source assembly for smooth periodic metric forces.

No source is computed by subtracting a flux from the final momentum rate.
Each source comes from original cut coefficients, their time derivatives,
the physical bed gradient, or the explicit symmetric bed Hessian term.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class Ledger:
    faces: list
    bed: np.ndarray

    def __add__(self, other):
        return Ledger([a+b for a, b in zip(self.faces, other.faces)], self.bed+other.bed)

    def __mul__(self, scalar):
        return Ledger([scalar*f for f in self.faces], scalar*self.bed)

    def action(self, dx):
        return self.bed+sum((f-np.roll(f, 1, axis))/dx for f, axis in zip(self.faces, (1, 0)))


def zero(g):
    return Ledger([np.zeros((*g.h.shape, 2)) for _ in range(2)], np.zeros((*g.h.shape, 2)))


def traction(g, p, b, *, tangent=None):
    result = zero(g)
    for j, (axis, edge) in enumerate(zip((1, 0), g.edges)):
        right_p, right_b = np.roll(p, -1, axis), np.roll(b, -1, axis)
        if tangent is None:
            face = edge['other']*edge['aa']*p+edge['own']*edge['ab']*right_p
            face += edge['shared_b']*(right_b-b)
            bed = (-edge['aa']+np.roll(edge['ab'], 1, axis)+edge['local_p'])*p/g.dx
            bed += edge['physical_b']*b
        else:
            rate = tangent.edges[j]
            face = (rate['other']*edge['aa']+edge['other']*rate['aa'])*p
            face += (rate['own']*edge['ab']+edge['own']*rate['ab'])*right_p
            face += rate['shared_b']*(right_b-b)
            bed = (-rate['aa']+np.roll(rate['ab'], 1, axis))*p/g.dx
        result.faces[j][..., j] = face
        result.bed[..., j] = bed
    return result


def factor_transpose(g, value, *, bottom=False, tangent=None):
    if tangent is None:
        return traction(g, np.zeros_like(value) if bottom else -g.h*value,
                        value if bottom else -1.5*value)
    result = traction(g, np.zeros_like(value) if bottom else -g.h*value,
                      value if bottom else -1.5*value, tangent=tangent)
    if not bottom:
        result = result+traction(g, -tangent.mass_rate*value, np.zeros_like(value))
    return result


def gram(factors, value):
    g, h = factors.system.geometry, factors.h
    return (factor_transpose(g, h*factors.action(value))
            +factor_transpose(g, h*factors.action(value, bottom=True), bottom=True)*.75)


def gram_rate(factors, value):
    g, h, t = factors.system.geometry, factors.h, factors.tangent
    result = zero(g)
    for bottom, weight in ((False, 1.), (True, .75)):
        a = factors.action(value, bottom=bottom)
        result = result+(factor_transpose(g, h*a, bottom=bottom, tangent=t)
                         +factor_transpose(g, t.mass_rate*a+h*factors.rate(value, bottom=bottom),
                                           bottom=bottom))*weight
    return result


def commutator(factors, value):
    g, h, t = factors.system.geometry, factors.h, factors.tangent
    result = zero(g)
    for bottom, weight in ((False, .5), (True, .375)):
        result = result+(factor_transpose(g, h*factors.rate(value, bottom=bottom), bottom=bottom)
                         +factor_transpose(g, h*factors.action(value, bottom=bottom),
                                           bottom=bottom, tangent=t)*-1.)*weight
    return result


def tensor(g, c, s, value, *, include_hessian=True):
    # Independent face representation of centered divergence. The cell tensor
    # is averaged to each face; its face divergence equals the centered action.
    derivative = lambda a, j: (np.roll(a, -1, 1-j)-np.roll(a, 1, 1-j))/(2*g.dx)
    jac = [[derivative(value[..., i], j) for j in range(2)] for i in range(2)]
    trace = jac[0][0]+jac[1][1]
    result = zero(g)
    for j in range(2):
        for i in range(2):
            stress = c*(jac[j][i]+(trace if i == j else 0.))
            result.faces[j][..., i] = .5*(stress+np.roll(stress, -1, 1-j))
            if include_hessian:
                result.bed[..., i] += s*derivative(derivative(g.bed, j), i)*value[..., j]
    return result
