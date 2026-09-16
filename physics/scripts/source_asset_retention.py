"""Resolve only explicitly proven metadata-only CPU-retention asset revisions.

Historical import hashes stay immutable. A changed package is accepted only
against the versioned before/after receipt and its exact current package hash.
This does not waive source geometry or native collision identity checks.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT/'docs/reconstruction-review-2026-09-07/ground-cpu-retention-v1.json'
IDENTITY = ('format', 'collision_lod', 'collision_trace_flag', 'collision_source_sha256',
            'triangle_count', 'provider_vertex_count', 'flip_normals')


def retained_asset_digest(path, original_digest, *, root=ROOT, receipt=RECEIPT):
    path, root = Path(path).resolve(), Path(root).resolve()
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual == original_digest:
        return actual
    document = json.loads(Path(receipt).read_text())
    if document.get('schema') != 'raftsim.ground_cpu_retention.v1' or not document.get('completed'):
        raise ValueError('Complete CPU-retention provenance required')
    rows = [row for row in document['assets']
            if row.get('asset', '').startswith('/Game/') and
            (root/'unreal/Content'/(row['asset'][6:]+'.uasset')).resolve() == path]
    if len(rows) != 1:
        raise ValueError('Exactly one matching source package revision required')
    row = rows[0]
    if row['original_asset_sha256'] != original_digest or row['retained_asset_sha256'] != actual:
        raise ValueError('Current package is not the proven CPU-retention revision')
    before, after = row['before'], row['after']
    if not row.get('native_source_unchanged') or not before.get('available') or not after.get('available') or not after.get('allow_cpu_access'):
        raise ValueError('Native CPU source was not retained')
    if any(key not in before or key not in after or before[key] != after[key] for key in IDENTITY):
        raise ValueError('Native source identity changed')
    if len(before['collision_source_sha256']) != 64 or before['triangle_count'] <= 0:
        raise ValueError('Complete native geometry evidence required')
    return actual
