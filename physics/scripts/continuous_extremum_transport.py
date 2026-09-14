"""Continuous-envelope research mass limiter, NOT smooth pressure energy.

Take the magnitude envelope of conventional MC and the curvature-limited EP
candidate instead of switching abruptly between them at a wide-extremum
predicate. Both candidates share the centered-slope sign and cap. This retains
MC where it is the stronger slope, including the exact EP jump counterexample.

At strictly positive connected support the min/max envelope is continuous in
its inputs. It is NOT C1, and does not fix the pressure-energy gradient's jumps.
Exact dry-support changes and full shock/entropy behavior remain unqualified.
"""
from fractions import Fraction as F
import numpy as np
from extremum_preserving_transport import ExtremumPreservingTransport


def continuous_slope(value,axis,other=None):
    back=value-np.roll(value,1,axis);front=np.roll(value,-1,axis)-value
    if other is not None:
        back+=other-np.roll(other,1,axis);front+=np.roll(other,-1,axis)-other
    center=.5*(back+front);curve=front-back;sign=np.sign(curve)
    curvature=np.minimum(abs(curve),np.minimum(
        np.maximum(sign*(back-np.roll(back,1,axis)),0),
        np.maximum(sign*(np.roll(front,-1,axis)-front),0)))
    same=((back>0)&(front>0))|((back<0)&(front<0))
    mc=np.where(same,2*np.minimum(abs(back),abs(front)),0)
    edge=np.where(sign*np.sign(center)<0,abs(back),abs(front))
    ep=np.minimum(1.875*curvature,2*edge)
    return np.sign(center)*np.minimum(abs(center),np.maximum(mc,ep))


def exact_continuous_slope(values):
    mm,m,c,p,pp=values;back=c-m;front=p-c
    center=(back+front)/2;curve=front-back
    sign=lambda x: 1 if x>0 else -1 if x<0 else 0
    s=sign(curve)
    curvature=min(abs(curve),max(s*(back-(m-mm)),0),max(s*((pp-p)-front),0))
    mc=2*min(abs(back),abs(front)) if back*front>0 else F(0)
    edge=abs(back) if s*center<0 else abs(front)
    ep=min(F(15,8)*curvature,2*edge)
    return sign(center)*min(abs(center),max(mc,ep))


class ContinuousExtremumTransport(ExtremumPreservingTransport):
    slope=staticmethod(continuous_slope)
    exact_limiter=staticmethod(exact_continuous_slope)
