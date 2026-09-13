"""Compare the pre-pressure live interface with same-step native P2G particles.

This does not label out-of-interface particles as spray, change their positions,
or claim surface volume/visual acceptance. Positive phi is a scalar value, not a
geometric distance: the transported field is not a signed-distance function.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_interface import audit
from audit_liquid_native_handoff import read
from liquid_volume_interface import sample_centred
from liquid_dataset import resolve
from south_fork_registered_mesh import RegisteredMeshSampler
from diagnose_liquid_volume_interface import bed_clearance
from diagnose_liquid_regional_advection import validate_transport_sources


def diagnose(directory):
    directory = Path(directory).resolve()
    transport = audit(directory)
    report = json.loads((directory/'stages.json').read_text())
    unified=report.get('native_unified_transport_requested',False)
    if unified:validate_transport_sources(directory)
    dataset = resolve(report)
    with np.load(dataset['mesh']) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    results, sources = [], {'stages.json':hashlib.sha256((directory/'stages.json').read_bytes()).hexdigest()}
    for record, pair in zip(report['native_transfer_packet'], report['native_interface_transport']['regions']):
        cells = np.asarray(record['cells'])
        spacing = np.asarray(record['extent_cm'])/cells
        phi = np.fromfile(directory/pair['before'], dtype='<f4').reshape(tuple(cells[::-1]))
        points = read(directory, record, 'positions', (record['particle_count'], 4)).view('<f4')[:, :3].astype(float)
        if not np.isfinite(points).all():
            raise ValueError('Nonfinite current particle positions')
        axes = np.asarray([record['world_axis_x'], record['world_axis_y'], [0,0,1]])
        if not np.allclose(axes@axes.T, np.eye(3), atol=1e-9, rtol=0):
            raise ValueError('Orthonormal native frame required')
        local = (points-np.asarray(record['world_origin_cm']))@axes.T
        local[:, :2] += np.asarray(record['extent_cm'])[:2]/2
        if unified:
            frame=np.asarray(record['advection_unit_to_world'],dtype='<f4').reshape(4,4).astype(float)
            offset=points.astype('<f4').astype(float)-frame[3,:3]
            products=offset[:,None,:]*frame[None,:3,:3]
            squares=frame[:3,:3]**2
            unit=(((products[:,:,0]+products[:,:,1])+products[:,:,2])/
                  ((squares[:,0]+squares[:,1])+squares[:,2])).astype('<f4')
            q=(unit*cells.astype('<f4')-np.float32(.5)).astype(float)
            local=(q+.5)*spacing
        sampled, valid = sample_centred(phi, local, spacing)
        outside = valid & (sampled>0)
        results.append(dict(region_id=record['region_id'], particles=len(points),
                            invalid_stencils=int((~valid).sum()), outside_interface=int(outside.sum()),
                            largest_positive_scalar_cm=float(sampled[valid].max(initial=0)),
                            bed_clearance_bins=bed_clearance(points, outside, sampler)))
        for name in (record['positions'], pair['before']):
            path = (directory/name).resolve()
            if path.parent != directory:
                raise ValueError('Coverage input escapes capture')
            sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    particles = sum(r['particles'] for r in results)
    outside = sum(r['outside_interface'] for r in results)
    bins = [{**results[0]['bed_clearance_bins'][i],
             **{k:sum(r['bed_clearance_bins'][i][k] for r in results)
                for k in ('all_particles', 'outside_candidate')}} for i in range(6)]
    return dict(native_p2g_step=report['native_transfer_packet_step'], particles=particles,
                invalid_stencils=sum(r['invalid_stencils'] for r in results),
                outside_interface=outside, outside_fraction=outside/particles,
                largest_positive_scalar_cm=max(r['largest_positive_scalar_cm'] for r in results),
                bed_clearance_bins=bins, regions=results,
                pressure_coupled=transport['pressure_coupled'], source_files_sha256=sources,
                pairing='P2G positions and BEFORE '+transport['velocity_stage']+' transport scalar from the same native step',
                coordinate_contract='double-float-demote-v1' if unified else 'survey-orthogonal-frame',
                positive_scalar_is_not_geometric_distance=True,
                outside_particles_not_reclassified_as_spray=True,
                physical_visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = diagnose(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('regions','source_files_sha256')}, indent=2))
