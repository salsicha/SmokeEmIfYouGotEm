"""Run unchanged physical/operator controls with the isolated scalar derivative.

These tests are not full river history, native execution, or gameplay acceptance.
Run each mode in a fresh process; never install this override in a live replay.
"""
import argparse
from contextlib import nullcontext
from pathlib import Path
import pytest
from difference_scalar_gradient_reference import difference_scalar_gradients
from reconstructed_pressure_geometry import ReconstructedPressureGeometry

SUITES = (
    'test_reconstructed_pressure_geometry.py',
    'test_reconstructed_pressure_rates.py',
    'test_reconstructed_acceleration_system.py',
    'test_reconstructed_nonlinear_pressure.py',
    'test_shared_bottom_pressure_geometry.py',
    'test_reconstructed_pressure_boundary.py',
    'test_directional_pressure_geometry.py',
    'test_reconstructed_solitary_residual.py',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('original', 'candidate'), required=True)
    parser.add_argument('--junitxml', type=Path, required=True)
    args = parser.parse_args()
    if args.junitxml.exists():
        raise FileExistsError(args.junitxml)
    directory = Path(__file__).resolve().parent
    original = ReconstructedPressureGeometry.scalar_gradient
    context = difference_scalar_gradients() if args.mode == 'candidate' else nullcontext()
    print(f'Unchanged control suites; scalar mode={args.mode}. No full-history/native/gameplay acceptance.')
    with context:
        result = pytest.main([str(directory / name) for name in SUITES]
                             + ['-q', f'--junitxml={args.junitxml.resolve()}'])
    assert ReconstructedPressureGeometry.scalar_gradient is original
    return int(result)


if __name__ == '__main__':
    raise SystemExit(main())
