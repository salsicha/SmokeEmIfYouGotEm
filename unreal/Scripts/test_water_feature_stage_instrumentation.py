"""Check observation insertion preserves operation order and nested branches."""
import ast
from pathlib import Path
import unittest

from water_feature_stage_instrumentation import Instrument


class RemoveCaptures(ast.NodeTransformer):
    def visit_Expr(self, node):
        if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                and node.value.func.id == 'capture'):
            return None
        return node


class InstrumentTests(unittest.TestCase):
    def check_roundtrip(self, source, identifier):
        original = ast.parse(source)
        instrument = Instrument(identifier)
        transformed = instrument.visit(ast.parse(source))
        ast.fix_missing_locations(transformed)
        compile(transformed, '<instrumented>', 'exec')
        stripped = RemoveCaptures().visit(transformed)
        self.assertEqual(ast.dump(original), ast.dump(stripped))
        return instrument

    def test_nested_calls_and_other_function_untouched(self):
        source = '''
def liquid_step_2():
    mantaMsg('step')
    phi.advect()
    if pressure:
        solvePressure()
    for particle in particles:
        update(particle)
    x = value()
    return x
def unrelated():
    other()
'''
        instrument = self.check_roundtrip(source, '2')
        self.assertEqual(instrument.labels, ['01: phi.advect()'])

    def test_executable_call_order_is_identical(self):
        source = '''
def liquid_step_9():
    operation('advection')
    if enabled:
        operation('pressure')
    operation('resample')
'''
        for enabled in (False, True):
            baseline, observed, captures = [], [], []
            original_space = dict(operation=baseline.append, enabled=enabled)
            observed_space = dict(operation=observed.append, enabled=enabled, capture=captures.append)
            exec(source, original_space)
            transformed = Instrument('9').visit(ast.parse(source))
            ast.fix_missing_locations(transformed)
            exec(compile(transformed, '<instrumented>', 'exec'), observed_space)
            original_space['liquid_step_9']()
            observed_space['liquid_step_9']()
            self.assertEqual(observed, baseline)
            self.assertEqual(len(captures), 3)

    def test_current_export_preserves_body(self):
        path = Path(__file__).resolve().parents[2]/'tmp/water-feature-lab/froth-jet-v6-solver-export-probe-v2/cache/script/liquid_script.py'
        if not path.exists():
            self.skipTest('Preserved local export unavailable; synthetic tests still run')
        source = path.read_text().split('## MAIN', 1)[0]
        instrument = self.check_roundtrip(source, '2')
        self.assertTrue(any('.join(' in label for label in instrument.labels))
        self.assertTrue(any('adjustNumber(' in label for label in instrument.labels))


if __name__ == '__main__':
    unittest.main()
