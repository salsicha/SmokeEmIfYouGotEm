"""Bind source-extension probes to the currently installed physical union.

The historical height-only preview contract remains untouched. This descriptor
compares an installed source-matched union with a fresh-state source hypothesis.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_constriction_native_geometry import ROOT, BASE
from prepare_south_fork_union_collision import prepare, physical_union_samples
from south_fork_rock_union import SourceRockUnion, sha
from source_native_triangle_hash import triangle_hash


def run(geometry_path, native_report_path, visible_probes, output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp directory required')
    output.mkdir()
    original=output/'source-probes.json'
    prepare(geometry_path,original,visible_probes)
    probes=json.loads(original.read_text())
    geometry=json.loads(geometry_path.read_text())
    cap_path=ROOT/geometry['rock_cap_manifest']
    cap=json.loads(cap_path.read_text());origin=cap['origin_utm_and_vertical_datum_m']
    installed=SourceRockUnion(cap_path,ROOT,ROOT/cap['source_mesh_path'],origin[:2],origin[2],
        BASE/'full_reach/source_matched_20260917/bed_revision_manifest.json')
    native=json.loads(native_report_path.read_text())
    proof_path=ROOT/native['proof_path'];proof=json.loads(proof_path.read_text())
    if (sha(proof_path)!=native['proof_sha256'] or native['failures'] or not native['saved_local_mesh']
            or not native['all_directed_triangles_source_exact']
            or proof['revision']!=probes['terrain_revision']
            or proof['expected_native_source_sha256']!=native['native_source']['collision_source_sha256']):
        raise ValueError('Candidate native geometry does not match the physical union')
    world_origin=np.array(probes['world_origin_utm_m']);datum=probes['datum_m']
    positions=np.array([p['world_position_cm'] for p in probes['baseline']])
    xy=positions[:,:2]*[.01,-.01]+world_origin
    parent=positions[:,2]*.01+datum
    # Re-evaluate the exact original triangles after frame round-trip; the
    # revision's bit-exact parent check must not be bypassed with a tolerance.
    rev=installed.terrain_revision
    scope=np.all(xy>=rev.lower,axis=1)&np.all(xy<=rev.upper,axis=1)
    parent[scope]=rev.original.sample(*(xy[scope]-rev.origin).T)+rev.datum
    height,rock=physical_union_samples(installed,xy,parent)
    for p,z,owner in zip(probes['baseline'],height,rock):
        p['world_position_cm'][2]=float((z-datum)*100)
        p['expected_candidate']=bool(owner) # same retained cap in both states
    with np.load(ROOT/cap['cap_path'],allow_pickle=False) as a:
        # export_troublemaker_dem_rock_cap reflects Blender Y AND reverses
        # winding; the importer restores Y but retains that directed order.
        cap_hash=triangle_hash(a['solid_vertices_m']*100,a['solid_triangles'][:,[0,2,1]])
        cap_count=len(a['solid_triangles'])
    cap_asset='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917/SM_CapturedRockInferredFlanks'
    assets={}
    for role,asset,digest,count in (
        ('installed',proof['installed_asset'],proof['installed_native_source_sha256'],proof['triangle_count']),
        ('candidate',proof['asset'],proof['expected_native_source_sha256'],proof['triangle_count']),
        ('cap',cap_asset,cap_hash,cap_count)):
        path=ROOT/'unreal/Content'/(asset[6:]+'.uasset')
        assets[role]=dict(asset=asset,package_sha256=sha(path),native_source_sha256=digest,triangle_count=count)
    if assets['candidate']['package_sha256']!=native['mesh_sha256']:
        raise ValueError('Saved candidate package changed')
    probes.update(schema='raftsim.constriction_installed_union_probes.v1',assets=assets,
        native_proof=proof_path.relative_to(ROOT).as_posix(),native_proof_sha256=sha(proof_path),
        native_report=native_report_path.relative_to(ROOT).as_posix(),native_report_sha256=sha(native_report_path),
        map_sha256=sha(ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'),
        installed_union=installed.identity,source_probes_sha256=sha(original),position_tolerance_cm=.1,
        normal_game_integrated=False,semantic_classification_accepted=False)
    path=output/'probes.json';path.write_text(json.dumps(probes,indent=2)+'\n')
    print(json.dumps(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),
        baseline=len(probes['baseline']),combined=len(probes['combined']),assets=assets),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('geometry',type=Path);p.add_argument('--native-report',type=Path,required=True)
    p.add_argument('--source-visible-probes',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.geometry.resolve(),a.native_report.resolve(),a.source_visible_probes.resolve(),a.output)
