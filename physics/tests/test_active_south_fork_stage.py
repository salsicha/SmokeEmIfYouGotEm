import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_active_south_fork_stage import RULES, selected_bundle


class ActiveBundleTests(unittest.TestCase):
    def select(self, rules):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / RULES
            path.parent.mkdir(parents=True)
            path.write_text(rules)
            return selected_bundle(root).relative_to(root.resolve()).as_posix()

    def test_current_selection_not_historical_comment(self):
        old = 'StageVerifiedRuntimeBundle(RepoRoot, "physics/data/runtime_bundles/south_fork_old", RuntimeDestinations);'
        new = 'StageVerifiedRuntimeBundle(RepoRoot,\n "physics/data/runtime_bundles/south_fork_new", RuntimeDestinations);'
        self.assertEqual(self.select('// ' + old + '\n/* ' + old + ' */\n' + new),
                         'physics/data/runtime_bundles/south_fork_new')

    def test_missing_or_ambiguous_selection_fails(self):
        call = 'StageVerifiedRuntimeBundle(RepoRoot, "physics/data/runtime_bundles/south_fork_new", RuntimeDestinations);'
        for rules in ('', call + call):
            with self.assertRaisesRegex(ValueError, 'Exactly one'):
                self.select(rules)

    def test_escape_and_non_south_fork_selection_fail(self):
        for name in ('../outside', 'physics/data/runtime_bundles/other'):
            with self.assertRaises(ValueError):
                self.select(f'StageVerifiedRuntimeBundle(RepoRoot, "{name}", RuntimeDestinations);')


if __name__ == '__main__':
    unittest.main()
