import numpy as np
import pytest
from total_depth_pressure import pressure_correction, wet_pairs
from finite_depth_pressure_reference import LENGTHS, WEIGHTS, response


def test_coupled_emergent_lake_stays_at_rest():
    from total_depth_bank_replay import advance
    bed = np.broadcast_to(np.arange(13)*.25, (5, 13)).copy()
    state = np.zeros((*bed.shape, 3)); state[..., 0] = np.maximum(0, 2-bed)
    final, stats = advance(state, bed, .5, .2, second_order=True, dispersive=True)
    np.testing.assert_allclose(final, state, atol=2e-14, rtol=0)
    assert abs(stats['volume_error_m3']) < 1e-13


@pytest.mark.parametrize('wavelength', [2., 4., 12.])
def test_coupled_small_wave_keeps_finite_depth_phase(wavelength):
    from total_depth_bank_replay import advance
    count, mean_depth, amplitude, current = 128, 1.5, 1e-5, .4
    dx = 4*wavelength/count
    x = (np.arange(count)+.5)*dx
    k = 2*np.pi/wavelength
    c = np.sqrt(9.81*np.tanh(k*mean_depth)/k)
    eta = amplitude*np.cos(k*x)
    h = mean_depth+eta
    state = np.stack((h, current*h+c*eta, np.zeros_like(h)), axis=-1)[None]
    seconds = wavelength/(c+current)
    final, stats = advance(state, np.zeros((1, count)), dx, seconds,
        second_order=True, periodic=True, dispersive=True)
    initial_mode = np.sum(eta*np.exp(-1j*k*x))
    final_mode = np.sum((final[0, :, 0]-mean_depth)*np.exp(-1j*k*x))
    phase_error = abs(np.angle(final_mode/initial_mode))/(2*np.pi)
    amplitude_ratio = abs(final_mode/initial_mode)
    assert phase_error < .03
    assert .9 < amplitude_ratio < 1.1
    assert abs(stats['volume_error_m3']) < 1e-11


def test_pressure_matches_independent_dense_system_on_variable_bed():
    y, x = np.mgrid[:5, :7]
    h = .5+.2*x+.1*y
    bed = .125*x+.0625*y
    h[:, 3] = 0
    actual, pairs = pressure_correction(h, bed, .5)
    size = h.size
    matrices = np.broadcast_to(np.eye(size), (2, size, size)).copy()
    surface = (h+bed).ravel()
    for yy in range(h.shape[0]):
        for xx in range(h.shape[1]):
            i = yy*h.shape[1]+xx
            for component, (dx, dy) in enumerate(((1, 0), (0, 1))):
                for sign in (-1, 1):
                    xxx, yyy = xx+sign*dx, yy+sign*dy
                    if not (0 <= xxx < h.shape[1] and 0 <= yyy < h.shape[0]): continue
                    py, px = (yy, xx) if sign == 1 else (yyy, xxx)
                    if not pairs[component][py, px]: continue
                    j = yyy*h.shape[1]+xxx
                    weight = LENGTHS*(h[yy, xx]/.5)**2
                    matrices[:, i, i] += weight
                    matrices[:, i, j] -= weight
    direct = np.stack([np.linalg.solve(a, surface)-surface for a in matrices])
    np.testing.assert_allclose(actual.ravel(), WEIGHTS@direct, atol=3e-5, rtol=0)


def test_emergent_lake_and_disconnected_pools_have_zero_correction():
    bed = np.broadcast_to(np.arange(13)*.25, (5, 13)).copy()
    h = np.maximum(0, 2-bed)
    actual, _ = pressure_correction(h, bed, .5)
    np.testing.assert_array_equal(actual, np.zeros_like(h))
    bed[:, 4] = 8
    h[:, 4] = 0
    h[:, 5:] = np.maximum(0, 2.5-bed[:, 5:])
    actual, _ = pressure_correction(h, bed, .5)
    np.testing.assert_array_equal(actual, np.zeros_like(h))


def test_vertical_datum_and_zero_depth_are_not_pressure_parameters():
    x = np.arange(32)
    h = (1e-12*(2+np.cos(2*np.pi*x/32)))[None]
    a, _ = pressure_correction(h, np.zeros_like(h), .5, periodic=True)
    b, _ = pressure_correction(h, np.full_like(h, 1e6), .5, periodic=True)
    np.testing.assert_array_equal(a, b)
    dry, _ = pressure_correction(np.zeros((3, 4)), np.ones((3, 4)), .5)
    np.testing.assert_array_equal(dry, np.zeros_like(dry))


def test_linear_response_matches_rational_finite_depth_symbol():
    count, dx, mean_depth = 256, .25, 1.5
    for mode in (2, 8, 24):
        x = np.arange(count)
        amplitude = 1e-7
        wave = amplitude*np.cos(2*np.pi*mode*x/count)
        h = (mean_depth+wave)[None]
        actual, _ = pressure_correction(h, np.zeros_like(h), dx, periodic=True)
        kh = mean_depth*2*np.sin(np.pi*mode/count)/dx
        expected = (response(kh)-1)*wave
        np.testing.assert_allclose(actual[0], expected, atol=1e-11, rtol=0)


def test_graph_does_not_connect_water_through_emergent_bed_step():
    h = np.array([[1., .1]])
    bed = np.array([[0., 2.]])
    pair = wet_pairs(h, bed)[0]
    assert not np.any(pair)


def test_supplied_reconstructed_closed_face_blocks_pressure_exchange():
    h = np.array([[1., 1.5, 2.]])
    bed = np.zeros_like(h)
    pairs = [np.zeros_like(h, dtype=bool), np.zeros_like(h, dtype=bool)]
    actual, _ = pressure_correction(h, bed, .5, pairs=pairs)
    np.testing.assert_array_equal(actual, np.zeros_like(h))


def test_supplied_graph_cannot_leak_through_dry_or_exterior_cells():
    h = np.array([[1., 0., 2.]])
    bed = np.zeros_like(h)
    with pytest.raises(ValueError, match='dry cell'):
        pressure_correction(h, bed, .5, pairs=[np.array([[True, False, False]]), np.zeros_like(h, dtype=bool)])
    with pytest.raises(ValueError, match='physical domain'):
        pressure_correction(np.ones_like(h), bed, .5, pairs=[np.array([[False, False, True]]), np.zeros_like(h, dtype=bool)])


def test_invalid_supplied_graph_shape_is_rejected():
    with pytest.raises(ValueError, match='wet graph'):
        pressure_correction(np.ones((2, 3)), np.zeros((2, 3)), .5,
            pairs=[np.zeros((2, 2), dtype=bool), np.zeros((2, 3), dtype=bool)])


@pytest.mark.parametrize('depth,bed,dx,iterations', [([[-1]], [[0]], .5, 40),
    ([[1]], [[np.nan]], .5, 40), ([[1]], [[0]], 0, 40), ([[1]], [[0]], .5, 0)])
def test_invalid_pressure_inputs_fail(depth, bed, dx, iterations):
    with pytest.raises(ValueError): pressure_correction(depth, bed, dx, iterations)
