"""Verify an identical-source engine geometry A/B, without granting visual acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def verify_computed_surface(source,manifest,binding_directory):
    """Independently check saved GPU bytes, not only the engine's pass flag."""
    scalar=source/'input_phi.r32f'
    actual_path=binding_directory/'gpu_surface.rgba16f'
    expected_path=source/'surface.rgba16f'
    if not scalar.is_file() or not actual_path.is_file():
        return False
    if hashlib.sha256(scalar.read_bytes()).hexdigest()!=manifest.get('input_scalar_sha256'):
        return False
    expected=np.fromfile(expected_path,dtype='<f2')
    actual=np.fromfile(actual_path,dtype='<f2')
    count=int(np.prod(manifest['grid_cells']))
    if actual.size!=count*4 or expected.size!=actual.size or scalar.stat().st_size!=count*4:
        return False
    actual=actual.reshape(-1,4).astype(float)
    expected=expected.reshape(-1,4).astype(float)
    return bool(np.isfinite(actual).all() and
                np.array_equal(actual[:,0]<0,expected[:,0]<0) and
                np.max(abs(actual[:,0]-expected[:,0]))<=.1 and
                np.array_equal(actual[:,1:],expected[:,1:]))


def audit(directory):
    capture=json.loads((directory/'capture.json').read_text())
    snapshot=capture['surface_snapshot']
    sources=[Path(snapshot['baseline_source']),Path(snapshot['source'])]
    manifests=[json.loads((p/'report.json').read_text()) for p in sources]
    bindings=[json.loads((directory/p/'binding.json').read_text()) for p in ('baseline_binding','snapshot_binding')]
    materials=[json.loads((directory/f'optics_{i:02d}_particles.json').read_text())['runtime_materials'] for i in range(2)]
    if any(len(m)!=1 for m in materials):
        raise ValueError('One actual runtime material per image required')
    a,b=[m[0] for m in materials]
    same_source=manifests[0]['particle_capture_sha256']==manifests[1]['particle_capture_sha256']==snapshot['same_particle_capture_sha256']
    source_bytes_verified=all(hashlib.sha256((p/'surface.rgba16f').read_bytes()).hexdigest()==m['texture_sha256'] for p,m in zip(sources,manifests))
    computed_bytes_verified=all(not binding.get('gpu_reconstruction_executed',False) or
                               verify_computed_surface(source,manifest,directory/subdir)
                               for source,manifest,binding,subdir in zip(sources,manifests,bindings,('baseline_binding','snapshot_binding')))
    same_optics=a['vectors']==b['vectors'] and a['scalars']==b['scalars']
    binding_verified=all(binding.get('gpu_result_verified',binding.get('gpu_upload_readback_exact',False)) and binding['material_binding_verified'] and
                         material['textures']['VolumeTex']==binding['bound_texture'] and
                         Path(binding['source_directory']).resolve()==source.resolve()
                         for binding,material,source in zip(bindings,(a,b),sources))
    controls=[c['optics_control'] for c in capture['captures'] if c['name'].startswith('optics_')]
    if len(controls)!=2:
        raise ValueError('Exactly two optical control captures required')
    same_controls=all(c['simulation_frozen'] and c['camera_fixed'] and c['foam_strength']==0 for c in controls)
    same_controls &= all(controls[0][key]==controls[1][key] for key in ('opacity','exposure_bias','scattering_coefficient_per_cm','roughness'))
    images=[np.array(Image.open(directory/f'optics_{i:02d}.png').convert('RGB')) for i in range(2)]
    if images[0].shape!=images[1].shape:
        raise ValueError('Image dimensions differ')
    delta=np.abs(images[0].astype(float)-images[1])
    verified=capture['complete'] and capture['error'] is None and same_source and source_bytes_verified and computed_bytes_verified and same_optics and same_controls and binding_verified
    return dict(geometry_ab_verified=bool(verified),same_particle_capture=same_source,
                source_bytes_verified=source_bytes_verified,identical_material_uniforms=same_optics,
                computed_gpu_bytes_independently_verified=computed_bytes_verified,
                identical_optical_controls=bool(same_controls),actual_gpu_texture_bindings_verified=binding_verified,
                changed_pixels_above_two_levels=int((delta.max(axis=-1)>2).sum()),
                decoded_image_sha256=[hashlib.sha256(i.tobytes()).hexdigest() for i in images],
                capture_wall_seconds=capture['wall_seconds'],not_a_frame_rate_measurement=True,
                offline_source_input=True,
                gpu_distance_reconstruction_executed=bool(bindings[1].get('gpu_reconstruction_executed',False)),
                gpu_distance_cpu_max_error_cm=bindings[1].get('gpu_cpu_max_error_cm'),
                offline_reconstruction_only=not bindings[1].get('gpu_reconstruction_executed',False),
                live_reconstruction_implemented=False,
                physical_or_visual_acceptance=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result=audit(args.directory)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['geometry_ab_verified'] else 1)
