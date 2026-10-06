import unittest
from water_feature_private_step import bind_owned, global_names

RESOURCE = []
SCALAR = 2.
NESTED = (RESOURCE,)


def operation():
    RESOURCE.append(SCALAR)
    return float(SCALAR)


def absent_branch():
    if FalseFlag:
        return unavailable_resource
    return 4


class PrivateStepTests(unittest.TestCase):
    def test_nested_alias_and_mutable_defaults_rejected(self):
        def nested():
            return NESTED
        with self.assertRaisesRegex(ValueError, 'alias'):
            bind_owned(nested, {'NESTED': NESTED}, {}, {})
        def defaulted(value=RESOURCE):
            return value
        with self.assertRaisesRegex(ValueError, 'defaults'):
            bind_owned(defaulted, {}, {}, {})

    def test_owned_function_changes_private_resource_only(self):
        before = list(RESOURCE)
        fresh = []
        fn, report = bind_owned(operation, {'RESOURCE': fresh, 'SCALAR': SCALAR}, {}, {'float': float})
        self.assertEqual(fn(), 2.)
        self.assertEqual(fresh, [2.])
        self.assertEqual(RESOURCE, before)
        self.assertIs(fn.__code__, operation.__code__)
        self.assertTrue(report['private_globals'])

    def test_live_mutable_alias_rejected(self):
        with self.assertRaisesRegex(ValueError, 'alias'):
            bind_owned(operation, {'RESOURCE': RESOURCE, 'SCALAR': SCALAR}, {}, {'float': float})

    def test_unowned_global_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unowned'):
            bind_owned(operation, {'RESOURCE': []}, {}, {'float': float})

    def test_python_function_cannot_masquerade_as_native(self):
        with self.assertRaisesRegex(ValueError, 'native C'):
            bind_owned(operation, {'RESOURCE': [], 'SCALAR': 2.}, {'fake': lambda: None}, {'float': float})

    def test_ambiguous_native_name_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            bind_owned(operation, {'RESOURCE': [], 'SCALAR': 2.}, {}, {'SCALAR': 3.})

    def test_missing_inactive_globals_are_not_fabricated(self):
        fn, report = bind_owned(absent_branch, {'FalseFlag': False}, {}, {})
        self.assertEqual(fn(), 4)
        self.assertNotIn('unavailable_resource', fn.__globals__)
        self.assertIn('unavailable_resource', report['absent_native_globals'])

    def test_closure_and_attribute_names_not_mistaken_for_globals(self):
        self.assertEqual(global_names(operation), ['RESOURCE', 'SCALAR', 'float'])
        item = []
        def closed():
            return item
        with self.assertRaisesRegex(ValueError, 'closure'):
            global_names(closed)


if __name__ == '__main__':
    unittest.main()
