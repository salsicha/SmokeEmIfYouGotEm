"""Guard interpreted-bed previews against mismatched fields and provenance."""
from dataclasses import replace
from pathlib import Path
import json
import runpy
import sys
from types import SimpleNamespace

import numpy as np


def module():
    scripts = Path(__file__).resolve().parents[1] / 'scripts'
    sys.path.insert(0, str(scripts))
    try:
        return runpy.run_path(str(scripts / 'export_troublemaker_review_fields.py'))
    finally:
        sys.path.pop(0)


def test_review_accepts_only_matching_original_or_declared_throat_bed():
    from raftsim.scenario2_5d import read_scenario2_5d_package
    helpers = module()
    root = Path(__file__).resolve().parents[2]
    base = read_scenario2_5d_package(root / 'physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/troublemaker/scenario/median_runnable')
    validate = helpers['validate_review_scenario']
    validate(base, base)
    candidate = helpers['interpreted_throat'](base, 12.)
    validate(base, candidate)
    connected = helpers['bank_connected_throat'](base, 12.)
    validate(base, connected)
    changed_bed = candidate.bed.copy()
    changed_bed[0, 0] += .1
    changed_datum = replace(candidate.metadata, provenance={**candidate.metadata.provenance,
        'source_elevation_datum_m': candidate.metadata.provenance['source_elevation_datum_m'] + .1})
    invalid = [replace(candidate, bed=changed_bed),
               replace(connected, metadata=candidate.metadata),
               replace(candidate, metadata=connected.metadata),
               replace(candidate, metadata=replace(candidate.metadata, provenance={
                   **candidate.metadata.provenance, 'experimental_throat_shoulders': 'unknown'})),
               replace(candidate, grid=replace(candidate.grid, origin_x=candidate.grid.origin_x+1)),
               replace(candidate, metadata=changed_datum),
               replace(candidate, metadata=replace(candidate.metadata, river_id='another_river')),
               replace(candidate, metadata=replace(candidate.metadata, flow_band='low_runnable')),
               replace(candidate, boundaries=(replace(candidate.boundaries[0], stage=3.), *candidate.boundaries[1:]))]
    for other in invalid:
        try:
            validate(base, other)
        except ValueError:
            pass
        else:
            raise AssertionError('incompatible preview scenario was accepted')
    assert np.array_equal(candidate.bed, helpers['interpreted_throat'](base, 12.).bed)


def test_source_manifest_must_contain_frame_and_match_solver_mode():
    validate = module()['validate_solver_manifest']
    parent = Path(__file__).resolve().parent
    data = dict(frames=['frame.csv'], solver_mode='finite_volume', boundary_mode='scenario',
                spatial_order=2, flux_scheme='hll', disable_fixture_calibrations=True,
                preserve_initial_mass=False, experimental_west_discharge_m3s=45.30695)
    fake_path = SimpleNamespace(parent=parent, read_text=lambda: json.dumps(data))
    assert validate(parent / 'frame.csv', fake_path)['experimental_west_discharge_m3s'] == 45.30695
    invalid = [(parent / 'wrong.csv', data),
               (parent / 'frame.csv', {**data, 'spatial_order': 1}),
               (parent / 'frame.csv', {**data, 'preserve_initial_mass': True}),
               (parent / 'frame.csv', {**data, 'disable_fixture_calibrations': False})]
    for frame, content in invalid:
        fake_path.read_text = lambda: json.dumps(content)
        try:
            validate(frame, fake_path)
        except ValueError:
            pass
        else:
            raise AssertionError('incompatible or unrelated source manifest accepted')
