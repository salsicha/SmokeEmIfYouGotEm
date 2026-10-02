"""Native plane/orientation/phase and preserved flat-field extraction controls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_native_field_mesh import extract
from water_feature_field_surface import planar_case,interface_residuals,regularize_exact_mesh
from water_feature_flat_metrics import closed_box_phi,mesh_metrics,paired_residuals
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import grid_array


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    reference=json.loads(args.reference.read_text());hashes=dict(reference['dependency_sha256'])
    hashes[str(args.reference.resolve())]=digest(args.reference)
    for name in ('probe_water_feature_field_mesh.py','water_feature_native_field_mesh.py','water_feature_field_surface.py',
            'test_water_feature_field_surface.py','water_feature_flat_metrics.py','probe_water_feature_native_transport.py',
            'probe_water_feature_solver_stages.py'):
        path=Path(__file__).with_name(name);hashes[str(path.resolve())]=digest(path)
    if not reference['complete'] or any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Unchanged prior controls required')
    # This Blender build completes inherited grid bindings during actual host
    # fluid initialization. Initialize the preserved scene READ-ONLY rather
    # than monkey-patching grid classes in an empty factory scene.
    source_root=Path(bpy.data.filepath).resolve().parent
    if source_root.name!='eddy-v2-grid-aligned-modular':raise ValueError('Preserved matched native host initialization required')
    bpy.data.objects['Feature liquid'].modifiers[0].domain_settings.cache_directory=str(source_root/'cache')
    bpy.context.scene.frame_set(192)
    actual,identifier=actual_space((80,21,39))
    actual_before={name:hashlib.sha256(grid_array(actual[f'{name}_s{identifier}'],(80,21,39)).tobytes()).hexdigest()
        for name in ('phi','phiTmp')}
    args.output.mkdir();rows=[];started=time.perf_counter()
    shape=(32,24,24);obstacle=closed_box_phi(shape).astype(np.float32)
    cases=[((0,0,1),12.),((0,0,1),12.3),((.2,0,1),14.),((0,.25,1),14.3),((.15,-.2,1),12.)]
    for case_index,(normal,offset) in enumerate(cases):
        phi,n=planar_case(shape,normal,offset)
        for refinement in (1,2,4):
            path=args.output/f'plane-{case_index}-r{refinement}.obj'
            vertices,triangles,proof=extract(phi,obstacle,refinement,path)
            vertices,triangles,cleanup_proof=regularize_exact_mesh(vertices,triangles)
            base=vertices.astype(float)/refinement+proof['base_coordinate_offset_cells']
            # Independently defined interior free-air vertices; contact edges
            # are NOT used as evidence for the affine-plane accuracy gate.
            interior=np.all((base[:,:2]>4)&(base[:,:2]<np.array(shape[:2])-4),axis=1)&(base[:,2]>4)
            if not interior.any():raise ValueError('Missing independent interior plane mesh')
            distance=np.abs(base[interior]@n-offset)
            if distance.max()>2e-5:raise ValueError('Native plane coordinate/isovalue gate failed: '+str(dict(
                case=case_index,refinement=refinement,maximum_error_cells=float(distance.max()),
                base_extent=[base[interior].min(0).tolist(),base[interior].max(0).tolist()],offset_cells=offset)))
            rows.append(dict(kind='manufactured',case=case_index,normal=n.tolist(),offset_cells=offset,
                refinement=refinement,interior_vertices=int(interior.sum()),maximum_affine_plane_error_cells=float(distance.max()),
                allowance_cells=2e-5,metrics=mesh_metrics(base,triangles,[],.075,.075,shape),
                field_residuals=interface_residuals(phi,obstacle,base,triangles),proof=proof,exact_cleanup=cleanup_proof,obj=str(path.resolve())))
    for control in reference['controls']:
        native=json.loads(Path(control['receipt']).read_text())
        for frame in (0,1,24,48):
            state=native['frames'][frame];phi=np.load(state['fields']['phi']);obstacle=np.load(native['obstacle_array'])
            for refinement in (1,2,4):
                path=args.output/f'{native["radius_policy"]}-m{2*native["subdivision"]}-f{frame}-r{refinement}.obj'
                vertices,triangles,proof=extract(phi,obstacle,refinement,path)
                vertices,triangles,cleanup_proof=regularize_exact_mesh(vertices,triangles)
                base=vertices.astype(float)/refinement+proof['base_coordinate_offset_cells']
                metrics=mesh_metrics(base,triangles,native['columns'],.075,.075,shape)
                paired=paired_residuals(metrics['samples'],state['columns'],native['initial_height_m'])
                supported=[abs(r['mesh_minus_phi_m']) for r in paired if r['mesh_minus_phi_m'] is not None]
                passed=(len(supported)==24 and max(supported)<=1.5e-6 and metrics['maximum_vertex_wall_intrusion_m']<=1.5e-6
                        and not metrics['boundary_edges'] and not metrics['nonmanifold_edges'] and not metrics['exact_zero_area_triangles'])
                # Retain failed geometry gates and finish the entire declared
                # cohort, rather than dropping the difficult radius control.
                rows.append(dict(kind='preserved',control=native['radius_policy'],subdivision=native['subdivision'],frame=frame,
                    geometry_gate_passed=passed,maximum_supported_height_error_m=max(supported) if supported else None,
                    refinement=refinement,metrics=metrics,paired_residuals=paired,proof=proof,exact_cleanup=cleanup_proof,
                    field_residuals=interface_residuals(phi,obstacle,base,triangles),obj=str(path.resolve())))
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Preserved input changed during extraction')
    if any(hashlib.sha256(grid_array(actual[f'{name}_s{identifier}'],(80,21,39)).tobytes()).hexdigest()!=sha
            for name,sha in actual_before.items()):raise ValueError('Live actual host phi fields changed')
    report=dict(complete=True,accepted=False,originals_unchanged=True,rows=rows,dependency_sha256=hashes,
        geometry_qualification_passed=all(r.get('geometry_gate_passed',True) for r in rows),
        live_actual_phi_fields_unchanged=True,
        outputs_sha256={r['obj']:digest(r['obj']) for r in rows},elapsed_s=time.perf_counter()-started,
        scope='Native copied-field extraction only; no new liquid evolution. Free-surface/contact discretization and volume must remain explicit. Not foam or hydraulic acceptance.')
    with (args.output/'field-mesh.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('NATIVE_FIELD_MESH_CONTROLS_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('NATIVE_FIELD_MESH_CONTROLS_FAILED',error,flush=True);raise SystemExit(1)
