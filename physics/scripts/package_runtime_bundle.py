"""Freeze the exact saved-scene runtime dependency closure, without recooking.

Payloads are content-addressed but staged at their existing logical paths. This
preserves every JSON/NumPy byte and saved actor binding; tmp-prefixed logical
names no longer require a developer's tmp directory. This is not acceptance of
the physical state, visual result, or source bathymetry.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import posixpath
import shutil


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def logical_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('Portable repository-relative path required')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('Canonical repository-relative path required')
    return value


def relative_dependency(parent, value):
    if not isinstance(value, str) or '\\' in value or ':' in value or value.startswith('/'):
        raise ValueError('Relative manifest dependency required')
    return logical_path(posixpath.normpath(posixpath.join(posixpath.dirname(parent), value)))


def validate_coordinate_map(data):
    def finite(value):
        return type(value) in (int, float) and math.isfinite(value)
    if data.get('world_y_sign', 1) not in (-1, 1):
        raise ValueError('Coordinate reflection must match native convention')
    schema = data.get('schema')
    if schema == 'raftsim.cartesian_water_coordinate_map.v1':
        bounds = data.get('hydraulic_bounds_m')
        if ('world_y_sign' not in data or not finite(data.get('vertical_datum_m')) or
            not isinstance(bounds, list) or len(bounds) != 4 or not all(map(finite, bounds)) or
            bounds[0] >= bounds[2] or bounds[1] >= bounds[3]):
            raise ValueError('Complete Cartesian coordinate map required')
    elif schema == 'raftsim.curved_river_coordinate_map.v1':
        points = data.get('points')
        if not isinstance(points, list) or len(points) < 2:
            raise ValueError('Complete curved coordinate map required')
        previous = -math.inf
        for point in points:
            if (not isinstance(point, list) or len(point) != 5 or not all(map(finite, point)) or
                point[0] <= previous or math.hypot(point[3], point[4]) == 0):
                raise ValueError('Invalid curved coordinate point')
            previous = point[0]
    else:
        raise ValueError('Unsupported coordinate-map schema')


class Closure:
    def __init__(self, root, payloads=None):
        self.root = Path(root).resolve()
        self.payloads = payloads
        self.files = {}
        self.case_names = {}
        self.visited = set()

    def add(self, name, expected=None):
        name = logical_path(name)
        if PurePosixPath(name).suffix not in ('.json', '.npy'):
            raise ValueError('Only runtime JSON/NumPy payloads may be bundled')
        other = self.case_names.setdefault(name.casefold(), name)
        if other != name:
            raise ValueError('Case-colliding runtime paths')
        if name not in self.files:
            source = self.payloads[name] if self.payloads is not None else name
            path = (self.root/logical_path(source)).resolve()
            if not path.is_relative_to(self.root):
                raise ValueError('Runtime dependency escapes source root')
            self.files[name] = dict(path=path, sha256=sha(path), size_bytes=path.stat().st_size)
        if expected is not None and self.files[name]['sha256'] != expected:
            raise ValueError('Runtime dependency hash mismatch: '+name)
        return self.files[name]['path']

    def document(self, name, schema, expected=None):
        path = self.add(name, expected)
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if value.get('schema') != schema:
            raise ValueError('Unexpected runtime schema: '+name)
        return value

    def atlas(self, name, expected):
        self.add(name, expected)
        if ('atlas', name) in self.visited:
            return
        self.visited.add(('atlas', name))
        atlas = self.document(name, 'raftsim.cartesian_state_atlas.v1')
        if not {'bed', 'h', 'u', 'v'}.issubset(atlas['arrays']):
            raise ValueError('Incomplete shared hydraulic state')
        for meta in atlas['arrays'].values():
            self.add(relative_dependency(name, meta['file']), meta['sha256'])

    def fields(self, name):
        if ('fields', name) in self.visited:
            return
        self.visited.add(('fields', name))
        fields = self.document(name, 'raftsim.cooked_flow_fields.v1')
        if not fields['bands']:
            raise ValueError('Empty field bands')
        for band in fields['bands']:
            if not {'bed', 'captured_water_mask'}.issubset(band['arrays']):
                raise ValueError('Incomplete source terrain fields')
            for meta in band['arrays'].values():
                self.add(relative_dependency(name, meta['file']), meta['sha256'])
            shared = band['shared_cartesian_state']
            self.atlas(relative_dependency(name, shared['manifest']), shared['sha256'])

    def collect(self, entrypoints):
        required = {'streaming_manifest', 'initial_fields_manifest',
                    'hydraulic_coordinate_map', 'route_coordinate_map'}
        if set(entrypoints) != required:
            raise ValueError('Complete saved-scene entrypoints required')
        stream = self.document(entrypoints['streaming_manifest'], 'raftsim.cartesian_water_streaming.v1')
        if not stream['windows']:
            raise ValueError('Empty streaming coverage')
        for row in stream['windows']:
            self.fields(logical_path(row['cooked_fields_manifest']))
        self.fields(logical_path(entrypoints['initial_fields_manifest']))
        # Native coordinate loader reads each complete JSON document. Its
        # provenance references are evidence, not runtime array dependencies.
        for key in ('hydraulic_coordinate_map', 'route_coordinate_map'):
            data = json.loads(self.add(entrypoints[key]).read_text(encoding='utf-8-sig'))
            validate_coordinate_map(data)
        return self.files


def verify_bundle(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder/'manifest.json').read_text())
    if manifest.get('schema') != 'raftsim.runtime_data_bundle.v1':
        raise ValueError('Runtime bundle schema required')
    files = manifest['files']
    if not files or len({row['destination'].casefold() for row in files}) != len(files):
        raise ValueError('Unique nonempty runtime destinations required')
    payloads = {}
    for row in files:
        name, source = logical_path(row['destination']), logical_path(row['source'])
        expected_source = 'files/'+row['sha256']+PurePosixPath(name).suffix
        if source != expected_source:
            raise ValueError('Content-addressed source identity required')
        path = (folder/source).resolve()
        if not path.is_relative_to(folder) or sha(path) != row['sha256'] or path.stat().st_size != row['size_bytes']:
            raise ValueError('Bundled payload changed')
        payloads[name] = source
    closure = Closure(folder, payloads)
    closure.collect(manifest['entrypoints'])
    if set(closure.files) != set(payloads):
        raise ValueError('Bundle must contain exactly the runtime dependency closure')
    return manifest


def verify_staged(folder, data_root):
    """Verify the real UBT/package tree, without falling back to source files."""
    manifest = verify_bundle(folder)
    data_root = Path(data_root).resolve()
    for row in manifest['files']:
        path = (data_root/row['destination']).resolve()
        if not path.is_relative_to(data_root) or sha(path) != row['sha256'] or path.stat().st_size != row['size_bytes']:
            raise ValueError('Staged runtime payload changed: '+row['destination'])
    closure = Closure(data_root)
    closure.collect(manifest['entrypoints'])
    if set(closure.files) != {row['destination'] for row in manifest['files']}:
        raise ValueError('Staged runtime closure differs from source bundle')
    return dict(schema='raftsim.staged_runtime_bundle_audit.v1', passed=True,
        bundle_manifest_sha256=sha(Path(folder)/'manifest.json'), data_root=str(data_root),
        files_verified=len(manifest['files']), bytes_verified=sum(row['size_bytes'] for row in manifest['files']),
        external_source_fallback_used=False, physical_acceptance=False, packaged_execution_verified=False)


def prepare(root, bindings_path, output):
    root, bindings_path, output = Path(root).resolve(), Path(bindings_path).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError('Fresh in-repository bundle directory required')
    bindings = json.loads(bindings_path.read_text())
    if bindings.get('schema') != 'raftsim.saved_runtime_bindings.v1' or bindings.get('saved_assets') is not False:
        raise ValueError('Read-only native saved-scene inventory required')
    source_assets = []
    for package, digest, suffix in [(bindings['level'], bindings['map_sha256'], '.umap')]+[
            (row['package'], row['sha256'], '.uasset') for row in bindings['bindings'].values()]:
        if not package.startswith('/Game/'):
            raise ValueError('Project scene binding required')
        name = logical_path('unreal/Content/'+package[6:]+suffix)
        path = (root/name).resolve()
        if not path.is_relative_to(root) or sha(path) != digest:
            raise ValueError('Saved scene changed since native inventory')
        source_assets.append(dict(path=name, sha256=digest))
    closure = Closure(root)
    closure.collect(bindings['entrypoints'])
    # No output exists until all inputs and their transitive hashes pass.
    output.mkdir(parents=True)
    (output/'files').mkdir()
    rows = []
    for name, record in sorted(closure.files.items()):
        source = 'files/'+record['sha256']+PurePosixPath(name).suffix
        target = output/source
        if not target.exists():
            shutil.copyfile(record['path'], target)
        if sha(target) != record['sha256']:
            raise ValueError('Copied runtime bytes changed')
        rows.append(dict(destination=name, source=source, sha256=record['sha256'], size_bytes=record['size_bytes']))
    manifest = dict(schema='raftsim.runtime_data_bundle.v1', entrypoints=bindings['entrypoints'],
        saved_scene_assets=source_assets, native_bindings_sha256=sha(bindings_path), files=rows,
        payload_bytes_unchanged=True, saved_scene_unchanged=True, physical_acceptance=False,
        settled_hydraulics=False, visual_acceptance=False, packaged_execution_verified=False)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    verify_bundle(output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--bindings', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--staged-root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.verify_only and not args.staged_root and args.bindings is None:
        parser.error('--bindings is required when creating a bundle')
    if args.report and args.report.exists():
        parser.error('Fresh report required')
    if args.staged_root:
        result = verify_staged(args.output, args.staged_root)
    else:
        bundle = verify_bundle(args.output) if args.verify_only else prepare(args.root, args.bindings, args.output)
        result = dict(files=len(bundle['files']), logical_bytes=sum(row['size_bytes'] for row in bundle['files']),
                      physical_acceptance=False, verified_dependency_closure=True)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
