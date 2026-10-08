"""Fail-closed source preflight, without importing or launching Unreal."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class BufferContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        helper = types.ModuleType('install_futaleufu_continuous_canopy')
        for key, value in dict(ROOT=root, LEVEL='test', MAP=root/'map', load_world=None,
                               original_files=None, sha=sha).items():
            setattr(helper, key, value)
        path = Path(__file__).resolve().parents[1]/'update_futaleufu_native_buffers.py'
        spec = importlib.util.spec_from_file_location('buffer_contract_test_target', path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'unreal': types.ModuleType('unreal'), helper.__name__: helper}):
            spec.loader.exec_module(self.module)
        self.module.OLD.mkdir(parents=True)
        self.module.NEW.mkdir(parents=True)
        chunks = []
        for i in range(800):
            name = '%d.png' % i
            for folder in (self.module.OLD, self.module.NEW):
                (folder/name).write_bytes(bytes([i % 256]))
            chunks.append(dict(chunk=[i, 0], heightfield=name, sha256=sha(self.module.OLD/name),
                               world_northwest_xy_cm=[i*25200, -25200]))
        old = dict(landscape=dict(actor_z_cm=105001.831), chunks=chunks)
        new = json.loads(json.dumps(old))
        for c in new['chunks'][:9]:
            p = self.module.NEW/c['heightfield']
            p.write_bytes(b'changed'+p.read_bytes())
            c['sha256'] = sha(p)
        self.old, self.new = old, new
        self.pin()

    def pin(self):
        for folder, data, attr in ((self.module.OLD, self.old, 'OLD_SHA'), (self.module.NEW, self.new, 'NEW_SHA')):
            p = folder/'manifest.json'
            p.write_text(json.dumps(data))
            setattr(self.module, attr, self.module.sha(p))

    def test_exact_changed_set_and_unchanged_extent(self):
        result = self.module.source_contract()
        self.assertEqual(9, len(result['chunks']))
        self.assertEqual(791, result['unchanged_source_chunks'])
        self.assertFalse(self.module.OUT.exists())

    def test_modified_png_is_rejected_before_any_write(self):
        (self.module.NEW/'700.png').write_bytes(b'bad')
        with self.assertRaisesRegex(RuntimeError, 'Changed source PNG'):
            self.module.source_contract()
        self.assertFalse(self.module.OUT.exists())

    def test_shifted_geometry_is_rejected(self):
        self.new['chunks'][0]['world_northwest_xy_cm'][0] += 100
        self.pin()
        with self.assertRaisesRegex(RuntimeError, 'registration changed'):
            self.module.source_contract()

    def test_changed_manifest_is_rejected(self):
        with (self.module.NEW/'manifest.json').open('a') as f:
            f.write(' ')
        with self.assertRaisesRegex(RuntimeError, 'manifest changed'):
            self.module.source_contract()


if __name__ == '__main__':
    unittest.main()
