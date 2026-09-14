import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import observe_reconstructed_history as observed


class ObservationTests(unittest.TestCase):
    def test_metrics_do_not_change_state_and_keep_tiny_wet_cell(self):
        state = np.zeros((2, 2, 3)); state[0, 0] = [1e-100, 3e-98, 4e-98]
        before = state.tobytes(); rate = np.zeros_like(state)
        metrics = observed.cell_metrics(state, np.zeros((2, 2)), rate, rate[..., 1:])
        self.assertEqual(metrics['wet_cells'], 1)
        self.assertAlmostEqual(metrics['maximum_speed_mps'], 500.)
        self.assertEqual(metrics['fastest_cells'][0]['yx'], [0, 0])
        self.assertEqual(state.tobytes(), before)

    def test_wrapper_returns_identical_objects_and_restores_bindings(self):
        state = np.ones((2, 2, 3)); bed = np.zeros((2, 2))
        force = np.zeros((2, 2, 2)); result = (np.zeros_like(state), .01)
        callbacks, events = [], []
        def pressure(*args, **kwargs): return force, [{'iterations': 40}]
        def rate(*args, **kwargs):
            observed.bank.nonlinear_pressure_force()
            return result
        def advance(s, b, seconds, **kwargs):
            self.assertEqual(seconds, .01)
            self.assertIs(observed.bank.rate(s, b, .5), result)
            kwargs['on_step'](s, s, dict(elapsed_s=.01, step_s=.01))
            return s, dict(completed=True)
        with tempfile.TemporaryDirectory() as directory:
            observer = observed.Observer(Path(directory), events.append, .1)
            with patch.multiple(observed.bank, rate=rate, nonlinear_pressure_force=pressure, advance=advance):
                with observer.installed():
                    value, _ = observed.bank.advance(state, bed, .01, on_step=lambda *args: callbacks.append(args))
                    self.assertIs(value, state)
                self.assertIs(observed.bank.rate, rate)
                self.assertIs(observed.bank.nonlinear_pressure_force, pressure)
                self.assertIs(observed.bank.advance, advance)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(observer.rate_count, 1)
            self.assertEqual(observer.accepted_count, 1)
            self.assertEqual([e['event'] for e in events], ['observed_trial_rate', 'observed_accepted_state'])
            for event in events:
                with np.load(event['snapshot']['path']) as archive:
                    np.testing.assert_array_equal(archive['state'], state)

    def test_error_restores_bindings(self):
        bindings = observed.bank.rate, observed.bank.nonlinear_pressure_force, observed.bank.advance
        with tempfile.TemporaryDirectory() as directory:
            observer = observed.Observer(Path(directory), lambda event: None, 0.)
            with self.assertRaisesRegex(RuntimeError, 'test'):
                with observer.installed(): raise RuntimeError('test')
        self.assertEqual(bindings, (observed.bank.rate, observed.bank.nonlinear_pressure_force, observed.bank.advance))


if __name__ == '__main__': unittest.main()
