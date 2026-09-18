"""Seal and validate the source-supported constriction revision dependency chain."""
import argparse
import json
from pathlib import Path

from prepare_troublemaker_control_ablation import sha
from south_fork_terrain_revision import load_revision

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def prepare(candidate_dir, output):
    candidate_dir, output = candidate_dir.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp descriptor required')
    candidate = json.loads((candidate_dir/'manifest.json').read_text())
    paths = dict(bed_revision=BASE/'full_reach/source_matched_20260917/bed_revision_manifest.json',
                 candidate_manifest=candidate_dir/'manifest.json', candidate_mesh=candidate_dir/'registered_mesh_source.npz',
                 source_returns=BASE/'troublemaker/classified_lidar_returns.npz',
                 selection=ROOT/candidate['selection_path'],
                 original_prior=BASE/'troublemaker/geometry_candidate/engine_mesh_source.npz',
                 source_naip=BASE/'sources/troublemaker_naip.png', source_naip_export=BASE/'sources/troublemaker_naip_export.json')
    record = dict(schema='raftsim.source_supported_terrain_revision.v1', state_transfer_permitted=False,
                  production_promoted=False, **{k: dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p)) for k, p in paths.items()})
    output.write_text(json.dumps(record, indent=2)+'\n')
    cap = json.loads((BASE/'full_reach/source_matched_20260917/rock_cap_manifest.json').read_text())
    origin = cap['origin_utm_and_vertical_datum_m']
    revision = load_revision(output, ROOT, ROOT/cap['source_mesh_path'], origin[:2], origin[2])
    return revision.identity


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.output), indent=2))
