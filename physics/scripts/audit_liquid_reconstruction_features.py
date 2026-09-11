"""Controlled free-surface tests, not real-engine motion or photographs."""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_anisotropic_surface import fit_kernels, splat_density, upper_surface, filter_kernels


def sample_volume(amplitude, phase_offset=0):
    # Same seeded particles in each case. Warp vertical columns to prescribe
    # a known volume boundary, rather than using the reconstruction as truth.
    z, y, x = np.meshgrid((np.arange(12)+.5)/12,
                         (np.arange(40)+.5)*.125-2.5,
                         (np.arange(40)+.5)*.125-2.5, indexing='ij')
    points = np.stack((x.ravel(), y.ravel(), z.ravel()), axis=1)
    rng = np.random.default_rng(20260908)
    points[:, :2] += rng.uniform(-.02, .02, (len(points), 2))
    points[:, 2] += rng.uniform(-.01, .01, len(points))
    points[:, 2] *= 1.5+amplitude*np.cos(2*np.pi*points[:, 0]/3)
    points[:, 0] += phase_offset
    return points


def run(output):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    minimum, extent, cells = np.array([-2.5, -2.5, 0]), np.array([5., 5., 2.4]), np.array([50, 50, 24])
    y, x = np.meshgrid((np.arange(50)+.5)*.1-2.5, (np.arange(50)+.5)*.1-2.5, indexing='ij')
    mask = (abs(x) < 1.5) & (abs(y) < 1.5)
    reports, surfaces = {}, {}
    for name, amplitude, shift in [('flat', 0., 0.), ('crest', .2, 0.), ('crest_translated', .2, 1/30)]:
        points = sample_volume(amplitude, shift)
        fit = fit_kernels(points, .4)
        for method in ('anisotropic', 'anisotropic_unshifted', 'anisotropic_prefiltered', 'isotropic'):
            if method == 'anisotropic':
                kernels = fit
            elif method == 'anisotropic_unshifted':
                kernels = dict(fit, centers=points)
            elif method == 'anisotropic_prefiltered':
                kernels = filter_kernels(dict(fit, centers=points), .1)
            else:
                kernels = dict(centers=points,
                    matrix=np.broadcast_to(np.eye(3)/.4, (len(points), 3, 3)),
                    basis=np.broadcast_to(np.eye(3), (len(points), 3, 3)),
                    axes=np.full((len(points), 3), .4))
            density = splat_density(kernels, fit['sample_volumes'], minimum, extent, cells)
            surface = upper_surface(density, minimum, extent)
            key = name+'_'+method
            surfaces[key] = surface
            valid = mask & np.isfinite(surface)
            expected = 1.5+amplitude*np.cos(2*np.pi*(x-shift)/3)
            residual = surface[valid]-expected[valid]
            # Fit the prescribed wavelength without granting phase/height errors
            # a pass. Report mean bias and residual separately from amplitude.
            design = np.stack((np.ones(valid.sum()), np.cos(2*np.pi*(x[valid]-shift)/3),
                               np.sin(2*np.pi*(x[valid]-shift)/3)), axis=1)
            coefficients = np.linalg.lstsq(design, surface[valid], rcond=None)[0]
            reports[key] = dict(particle_count=len(points), missing_interior_columns=int(mask.sum()-valid.sum()),
                height_bias_m=float(residual.mean()), height_error_rms_m=float(np.sqrt(np.mean(residual**2))),
                debiased_height_error_rms_m=float(np.std(residual)),
                fitted_crest_amplitude_m=float(np.linalg.norm(coefficients[1:])),
                expected_crest_amplitude_m=amplitude,
                prescribed_phase_error_component_m=float(coefficients[2]))
    report = dict(cases=reports, simulation_or_renderer_modified=False,
                  real_motion_measured=False, visual_or_physical_acceptance=False)
    np.savez_compressed(output/'surfaces.npz', **surfaces, minimum=minimum, extent=extent, cells=cells)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
