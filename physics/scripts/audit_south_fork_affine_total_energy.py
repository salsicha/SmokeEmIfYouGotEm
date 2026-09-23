"""Qualify original-source gravity and compose hash-certified kinetic time work.

No pressure system is rebuilt or solved. The completed kinetic pullback is an
explicit prerequisite, not replaced by a stored success flag. This is neither
a conservative force/transport step nor a native/playable solver acceptance.
"""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys
import time

import numpy as np

from audit_south_fork_affine_front_variation import (
    check_coverage, digest, exact, numeric, pairs, source_trace, verify_protected)
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip, _integrate
from subcell_affine_front_total_energy import affine_front_potential


def branch_potential(fan, fragments, time, datum=0):
    """Direct h^2/2+(z-datum)h quadrature, independent of depth/spatial moments.

    Moving-interface terms cancel at the continuous head and vanish at the dry
    front. The remaining rate is g*(h+z-datum)*h_t on each original branch.
    """
    t, datum = F(time), F(datum)
    if t <= 0:
        raise ValueError('Positive moving-front time required')
    head, front, linear, _, _ = fan._profile(t)
    acceleration = fan.gravity*sum(n*s for n, s in zip(fan.normal, fan.gradient))
    linear_rate = lambda p: fan._coordinate(p)/(t*t)-acceleration/2
    bed = lambda p: p[2]-datum
    energy = rate = fan.zero
    for fragment in fragments:
        wet = _clip(fragment.polygon, lambda p: fan._coordinate(p)-head, False)
        varying = _clip(_clip(fragment.polygon, lambda p: fan._coordinate(p)-head, True),
                        lambda p: fan._coordinate(p)-front, False)
        for polygon, variable in ((wet, False), (varying, True)):
            c = 1/(9*fan.gravity*fan.norm2) if variable else fan.depth
            forms = [linear, linear] if variable else []
            for i in range(1, len(polygon)-1):
                triangle = polygon[0], polygon[i], polygon[i+1]
                integrate = lambda fs: _integrate(triangle, fs, fan.zero)
                energy += fan.gravity*(c*c*integrate(forms+forms)/2+c*integrate(forms+[bed]))
                if variable:
                    rate += 2*fan.gravity*c*(c*integrate([linear]*3+[linear_rate])
                                             +integrate([linear, linear_rate, bed]))
    return energy, rate


def contract(gradients, directions, zero):
    if len(gradients) != len(directions) or any(len(a) != len(b) for a, b in zip(gradients, directions)):
        raise ValueError('Original primitive derivative dimensions changed')
    return sum((numeric(x)*numeric(y) for a, b in zip(gradients, directions) for x, y in zip(a, b)), zero)


def check_total(trace, fan, time, saved, pullback, datum=0):
    """Only call with the CLI's hash-certified saved kinetic records."""
    g = trace.geometry
    potential = affine_front_potential(g, datum)
    moment_rates = [g.forms[i]['depth_moment_rates'] for i in g.active]
    spatial_rates = [g.forms[i]['depth_spatial_moment_rates'] for i in g.active]
    depth_work = contract(potential['gradients']['moments'], moment_rates, g.zero)
    spatial_work = contract(potential['gradients']['spatial'], spatial_rates, g.zero)
    direct_energy, direct_rate = branch_potential(fan, g.fragments, time, datum)
    if potential['energy'] != direct_energy or depth_work+spatial_work != direct_rate:
        raise ValueError('Original gravity energy or rate disagrees with branch quadrature')
    works = {}
    for coordinate in ('physical', 'canonical'):
        old = pullback[coordinate+'_time_work']
        grad = pullback['primitive_gradients'][coordinate]
        momentum_rate = saved['physical_momentum_rate'] if coordinate == 'physical' else saved['result']['canonical_momentum_rate']
        reconstructed = dict(
            momentum_work=contract(grad['momentum'], momentum_rate, g.zero),
            depth_moment_work=contract(grad['moments'], moment_rates, g.zero),
            bed_gradient_work=contract(grad['slopes'], [(0, 0)]*len(g.active), g.zero),
            face_column_work=contract(grad['columns'], [f['column_normal_rate'] for f in g.faces], g.zero),
            boundary_flux_work=contract([grad['boundary_flux']],
                                       [[f['outward_mass_flux_rate'] for f in trace.boundary_faces]], g.zero))
        if any(value != numeric(old[key]) for key, value in reconstructed.items()):
            raise ValueError('Certified kinetic primitive work changed')
        kinetic_rate = sum(reconstructed.values(), g.zero)
        if kinetic_rate != numeric(old['energy_direction']) or kinetic_rate != numeric(saved['result']['kinetic_energy_rate']):
            raise ValueError('Certified kinetic rate changed')
        reconstructed['depth_moment_work'] += depth_work
        reconstructed.update(spatial_moment_work=spatial_work, bed_height_work=g.zero)
        reconstructed.update(energy_direction=kinetic_rate+direct_rate,
                             kinetic_energy_direction=kinetic_rate, potential_energy_direction=direct_rate)
        works[coordinate+'_time_work'] = reconstructed
    if works['physical_time_work']['energy_direction'] != works['canonical_time_work']['energy_direction']:
        raise ValueError('Momentum coordinates disagree')
    kinetic_energy = numeric(saved['result']['kinetic_energy'])
    return dict(**works, kinetic_energy=kinetic_energy, potential_energy=direct_energy,
                total_energy=kinetic_energy+direct_energy, energy_datum=F(datum),
                exact_original_branch_gravity_and_composed_time_work=True,
                pressure_solve_performed=False, conservative_force_or_open_boundary_or_gameplay_accepted=False)


def check_pullback_coverage(source, replay, pullback):
    check_coverage(source, replay)
    if (pullback['schema'] != 'raftsim.south_fork.affine_front_variation.v1'
            or pullback['exact_source_pullbacks_passed'] is not True
            or len(pullback['records']) != len(replay['records'])):
        raise ValueError('Complete qualified kinetic pullback required')
    for old, new in zip(replay['records'], pullback['records']):
        if new['index'] != old['index'] or new['tested'] is not old['tested']:
            raise ValueError('Pullback coverage/order changed')
        if not old['tested']:
            if new != old:
                raise ValueError('Unsupported original source changed')
        elif new['source_id'] != old['result']['source_id']:
            raise ValueError('Pullback source identity changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('pullback', 'replay', 'source', 'report'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--pullback-sha256', required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.pullback) != args.pullback_sha256:
        raise ValueError('Qualified kinetic pullback changed')
    pullback, replay, source = (json.loads(p.read_text()) for p in (args.pullback, args.replay, args.source))
    protected = dict(pullback['protected_sha256'])
    for path, sha in pullback['implementation_sha256'].items():
        if path in protected and protected[path] != sha:
            raise ValueError('Conflicting protected hash')
        protected[path] = sha
    protected[str(args.pullback.resolve())] = args.pullback_sha256
    for path in (args.source, args.replay):
        if str(path.resolve()) not in protected or digest(path) != protected[str(path.resolve())]:
            raise ValueError('Original source and replay must remain hash-bound')
    verify_protected(protected, {})
    check_pullback_coverage(source, replay, pullback)
    scripts = Path(__file__).resolve().parent
    implementation = {str(Path(m.__file__).resolve()): digest(m.__file__) for m in tuple(sys.modules.values())
                      if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts}
    mesh_path, = [p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    rows = []
    for record, saved, old in zip(source['records'], replay['records'], pullback['records']):
        if not saved['tested']:
            rows.append(saved)
            continue
        started = time.perf_counter()
        trace = source_trace(record, sampler)
        point, normal = (tuple(map(exact, record[k])) for k in ('point', 'normal'))
        depth = exact(record['local_depth'])
        fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                          exact(record['original_bed']), tuple(map(exact, record['original_gradient'])),
                          exact(record['whole']['volume']['radicand'])/(depth*sum(n*n for n in normal)))
        result = check_total(trace, fan, exact(record['time_increment']), saved['result'], old['result'])
        rows.append(dict(index=saved['index'], source_id=record['source_id'], tested=True, result=result))
        print(json.dumps(dict(index=saved['index'], phase='passed', seconds=time.perf_counter()-started)), flush=True)
    verify_protected({**protected, **implementation}, {})
    result = dict(schema='raftsim.south_fork.affine_total_energy.v1', protected_sha256=protected,
                  implementation_sha256=implementation, records=rows, exact_source_total_energy_checks_passed=True,
                  conservative_force_or_open_boundary_or_gameplay_accepted=False, scope=__doc__)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False,
                  default=lambda v: v.record() if isinstance(v, Radical) else json_default(v))


if __name__ == '__main__':
    main()
