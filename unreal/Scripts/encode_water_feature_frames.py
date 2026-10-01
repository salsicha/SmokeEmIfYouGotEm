"""Encode a verified regular sequence of laboratory frames as lossless APNG."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    capture = json.loads(args.capture.read_text())
    if not capture['complete'] or len(capture['frames']) < 2:
        raise ValueError('Require completed native render sequence')
    rows = sorted(capture['frames'], key=lambda row: row['frame'])
    indices = np.array([row['frame'] for row in rows])
    strides = np.diff(indices)
    if not (strides[0] > 0 and np.all(strides == strides[0])):
        raise ValueError('Require regularly spaced, distinct native frames')
    fps = capture['simulation_fps']/int(strides[0])
    images = []
    for row in rows:
        path = Path(row['image'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Rendered frame hash mismatch')
        with Image.open(path) as source:
            images.append(source.convert('RGB'))
    if any(image.size != images[0].size for image in images):
        raise ValueError('Inconsistent native render dimensions')
    durations = np.diff(np.rint(np.arange(len(images)+1)*1000/fps)).astype(int).tolist()
    destination = args.output/'feature.png'
    images[0].save(destination, format='PNG', save_all=True, append_images=images[1:],
                   duration=durations, loop=0, disposal=0, blend=0)
    with Image.open(destination) as decoded:
        if decoded.n_frames != len(images):
            raise ValueError('Missing decoded animation frames')
        for index, image in enumerate(images):
            decoded.seek(index)
            np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')), np.asarray(image))
    differences = [float(np.mean(np.abs(np.asarray(b, float)-np.asarray(a, float))))
                   for a, b in zip(images, images[1:])]
    if any(difference == 0 for difference in differences):
        raise ValueError('Unexpected identical adjacent native frames')
    report = dict(complete=True, accepted=False, frame_count=len(images), playback_fps=fps,
                  duration_seconds=sum(durations)/1000, source_stride=int(strides[0]),
                  first_frame=int(indices[0]), last_frame=int(indices[-1]),
                  native_frames_lossless_decode_verified=True, adjacent_duplicate_frames=0,
                  mean_absolute_frame_changes=differences,
                  source_capture=str(args.capture), source_capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
                  feature_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                  diagnostics_only=bool(capture.get('diagnostics_only') or capture.get('physical_accuracy_accepted') is False
                                        or capture.get('diagnostic_tracer_report_sha256') or capture.get('native_mesh_contact_diagnostic')),
                  surface_extraction=capture.get('surface_extraction', 'Unchanged native mesh'),
                  illumination=capture.get('illumination', {'model': 'previous authored study lighting'}),
                  shared_solids_united=capture.get('shared_solids_united', False),
                  contact_materials_transferred=capture.get('contact_materials_transferred', False),
                  constrained_extraction=capture.get('constrained_extraction', False),
                  geometry_measurement=capture.get('geometry_measurement'),
                  secondary_particles_hidden=capture['secondary_particles_hidden'],
                  secondary_phase_study=capture.get('secondary_phase_study', False),
                  simulation_correction=capture.get('simulation_correction'),
                  secondary_materials=capture.get('secondary_materials'),
                  per_particle_size_variation=capture.get('per_particle_size_variation', False),
                  speed_multiplier=1, seamless_loop=False,
                  model=capture.get('model'),
                  limitations=capture.get('limitations') or ('Native secondary-phase diagnostic; phase placement and optics unaccepted. Preserved liquid with collider-consistent extraction; uncalibrated radius variation and one-way subgrid phases, not resolved bubble films, conserved gas volume, calibrated kinetics or accepted eddy circulation. Playback FPS is not game performance.' if capture.get('secondary_phase_study') else
                              'Derived native surface outside shared authored solids. Not solver mass/contact, foam or hydraulic acceptance; playback FPS is not game performance.' if capture.get('solid_clipped_diagnostic') else
                              'Playback FPS is not game performance. Native cached liquid with labeled diagnostic tracers; not accepted foam or hydraulics.' if capture.get('diagnostic_tracer_report_sha256') else
                              'Native cached feature preview, not physical or visual acceptance; playback FPS is not game performance.'))
    (args.output/'clip.json').write_text(json.dumps(report, indent=2))
    print('VERIFIED_FEATURE_ANIMATION', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
