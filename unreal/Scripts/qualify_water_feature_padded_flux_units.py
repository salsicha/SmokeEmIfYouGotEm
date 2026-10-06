"""Correct diagnostic-only velocity units and re-integrate EVERY source face.

Never changes cached velocities/geometry. The earlier volume report used
display-API velocity normalization (1/80), not physical MAC units. Its volume
integrals are unaffected; its section mps/m3s labels must not be used as-is.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import openvdb

sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_plane_flux import partial_face_flux
from water_feature_cache_stages import decode_configuration


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--calibration',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    report=json.loads(args.input.read_text());cal=json.loads(args.calibration.read_text())
    hashes=dict(report['dependency_sha256'])
    for p in (Path(__file__),args.input,args.calibration,Path(__file__).with_name('water_feature_plane_flux.py'),
        Path(__file__).with_name('water_feature_cache_stages.py')):hashes[str(p.resolve())]=digest(p)
    if not report['complete'] or report['accepted'] or not cal['passed'] or cal['simulation_method']!='FLIP':
        raise ValueError('Complete unaccepted paired native report and FLIP unit reference required')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned native evidence changed')
    checks=[]
    for control in report['controls']:
        root=Path(control['root']);h=control['cell_m'];shape=tuple(control['shape'])
        # C01 uses0.1*25*timescale/fps per frame; physical grid displacement
        # is h per native cell. Existing affine native-advection controls
        # validate the cell/time convention independently of the flume flow.
        state=json.loads((root/'domain-settings.json').read_text())
        if shape!=(80,21,42) or h!=.075 or state['time_scale']!=1 or state['simulation_method']!='FLIP':
            raise ValueError('Matched native cell/time convention required')
        scale=h*2.5;factor=scale/(1/80)
        inferred=cal['inferred_raw_velocity_to_mps']/cal['resolution']
        if abs(inferred-scale)/scale>.01 or cal['resolution']!=80 or cal['fps']!=24:
            raise ValueError('Independent unit reference does not support cell/time scale')
        control['physical_mac_velocity_scale_mps_per_native_unit']=scale
        control['fractional_clearance_cells']=state['fractions_distance'] if state['use_fractions'] else None
        for row in control['frames']:
            data=root/'cache'/'data'/f'fluid_data_{row["frame"]:04d}.vdb';arrays={}
            config=decode_configuration((root/'cache'/'config'/f'config_{row["frame"]:04d}.uni').read_bytes())
            if config['resolution']!=list(shape):raise ValueError('Native shape changed')
            for name,vector in (('phi',False),('phi_obstacle',False),('velocity',True)):
                a=np.empty((*shape,3) if vector else shape,np.float32);g=openvdb.read(str(data),name);g.copyToArray(a)
                arrays[name]=a
            for section in row['sections']:
                x=section['native_x_face_index']
                phi=(arrays['phi'][x-1].astype(float)+arrays['phi'][x])/2
                obs=(arrays['phi_obstacle'][x-1].astype(float)+arrays['phi_obstacle'][x])/2
                v=arrays['velocity'][x,:,:,0].astype(float)*scale
                for estimate in section['estimates']:
                    for key in ('signed_positive_x_flux_m3s','positive_x_only_flux_m3s','negative_x_only_flux_m3s','mean_x_velocity_mps'):
                        if estimate[key] is not None:estimate[key]*=factor
                    fresh=partial_face_flux(phi,obs,v,(h,h),estimate['subdivisions'])
                    pairs=(('signed_positive_x_flux_m3s','signed_downward_flux_m3s'),
                        ('positive_x_only_flux_m3s','downward_only_flux_m3s'),
                        ('negative_x_only_flux_m3s','upward_only_flux_m3s'),
                        ('mean_x_velocity_mps','mean_downward_velocity_mps'))
                    errors=[]
                    for dst,src in pairs:
                        if (estimate[dst] is None)!=(fresh[src] is None):raise ValueError('Face support changed')
                        if estimate[dst] is not None:errors.append(abs(estimate[dst]-fresh[src]))
                    error=max(errors,default=0.)
                    if error>1e-12:raise ValueError('Physical-unit face re-integration mismatch')
                    checks.append(dict(label=control['label'],frame=row['frame'],x_face=x,
                        subdivisions=estimate['subdivisions'],maximum_reintegration_error=error))
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Source changed during unit qualification')
    report.update(dependency_sha256=hashes,diagnostic_unit_correction=True,section_units_qualified=True,
        supersedes_section_units_in=str(args.input.resolve()),original_phi_volumes_unchanged=True,
        corrected_mac_velocity_scale_mps_per_native_unit=.1875,old_unqualified_scale=1/80,
        exact_clock_based_scale_not_fitted_to_flume=True,all_face_reintegration_checks=checks,
        independent_reference_inferred_scale=cal['inferred_raw_velocity_to_mps']/80,
        caveats=report['caveats']+'Earlier section mps/m3s units were wrong by15x; use this corrected report. Native display velocities are not already physical mps. Reference calibration verifies the same build/cell/time convention, NOT the padded/fractional full hydraulics.',
        unit_qualification_scope=__doc__)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('PADDED_MAC_UNITS_QUALIFIED',len(checks),.1875,max(c['maximum_reintegration_error'] for c in checks),flush=True)


if __name__=='__main__':main()
