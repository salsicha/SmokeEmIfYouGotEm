"""Repair foam-gated compact liquid visibility; save only its actual material.

Native vertex A remains wet/shore/hull coverage, G is depth / 4 m, and the
existing shared transported froth controls foam. The extinction coefficient is
an authored optical approximation, not a measured field or a physics edit.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import zipfile
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from configure_playable_troublemaker_foam import graph_signature
from integrate_south_fork_local_froth import links
from raftsim_material_graph_signature import canonical_graph

PATH='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'
FILE=ROOT/'unreal/Content'/(PATH.removeprefix('/Game/')+'.uasset')
MARKER='Captured wet liquid and shared transported froth coverage V1'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    report=(ROOT/os.environ['RAFTSIM_LIQUID_COVERAGE_REPORT']).resolve()
    backup=report.with_suffix('.backup.zip')
    before_report=report.with_suffix('.before.json')
    if not report.is_relative_to(ROOT/'tmp') or any(p.exists() for p in (report,backup,before_report)):
        raise RuntimeError('Fresh repository-local report and backup required')
    migration=json.loads((ROOT/'tmp/southfork-compact-shared-froth-v1.json').read_text())
    if sha(FILE)!=migration['after_sha256']:
        raise RuntimeError('Unexpected material revision; preserve user changes')
    archived=json.loads((ROOT/'tmp/southfork-compact-shared-froth-v1.before.json').read_text())
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(PATH)
    nodes=list(lib.get_material_expressions(material))
    def custom(marker):
        matches=[n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom)
                 and str(n.get_editor_property('description'))==marker]
        if len(matches)!=1: raise RuntimeError('Expected exactly one '+marker)
        return matches[0]
    if any(str(n.get_editor_property('desc'))==MARKER for n in nodes):
        raise RuntimeError('Already repaired; inspect a fresh read-only audit')
    froth=custom('Captured shared transported froth V2')
    hull=custom('RaftSimLiveSurfaceRaftHullExclusion')
    opacity=canonical_graph(graph_signature(material,unreal.MaterialProperty.MP_OPACITY))
    if opacity!=archived['protected']['OPACITY']:
        raise RuntimeError('Actual opacity differs from the preserved foam-gated graph')
    gate=opacity['nodes']['MaterialExpressionComponentMask_14']
    if gate['r']!='True' or gate['a']!='False':
        raise RuntimeError('Expected verified legacy red/foam gate')
    protected={k:canonical_graph(graph_signature(material,getattr(unreal.MaterialProperty,'MP_'+k)))
               for k in ('BASE_COLOR','ROUGHNESS','SPECULAR','NORMAL','EMISSIVE_COLOR',
                         'WORLD_POSITION_OFFSET','OPACITY_MASK')}
    maps={ROOT/'unreal/Content/RaftSim/Maps'/(name+'.umap'):
          sha(ROOT/'unreal/Content/RaftSim/Maps'/(name+'.umap'))
          for name in ('L_SouthFork_Troublemaker','L_SouthForkAmerican_FullReach')}
    before=sha(FILE)
    blend=str(material.get_editor_property('blend_mode'))
    shading=str(material.get_editor_property('shading_model'))
    if ('BLEND_TRANSLUCENT' not in blend and 'BLEND_ALPHA_COMPOSITE' not in blend
            and 'MSM_SINGLE_LAYER_WATER' not in shading):
        raise RuntimeError('Opacity is not a supported liquid response: '+blend+' / '+shading)
    before_report.write_text(json.dumps(dict(material=PATH,sha256=before,blend=blend,
        shading=shading,opacity=opacity,protected=protected),indent=2)+'\n')
    with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(FILE,FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(backup) as archive:
        if hashlib.sha256(archive.read(FILE.relative_to(ROOT).as_posix())).hexdigest()!=before:
            raise RuntimeError('Material backup verification failed')
    vertex=lib.create_material_expression(material,unreal.MaterialExpressionVertexColor)
    vertex.set_editor_property('desc','Compact native wet A and depth G')
    extinction=lib.create_material_expression(material,unreal.MaterialExpressionScalarParameter)
    extinction.set_editor_property('parameter_name','CapturedLiquidOpticalExtinctionPerM')
    extinction.set_editor_property('default_value',.45)
    coverage=lib.create_material_expression(material,unreal.MaterialExpressionCustom)
    coverage.set_editor_property('description',MARKER)
    coverage.set_editor_property('desc',MARKER)
    coverage.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    coverage.set_editor_property('code',
        'float liquid=1-exp(-max(DepthNorm,0)*4*max(ExtinctionPerM,0));\n'
        'float mixture=liquid+(1-liquid)*saturate(FrothCoverage);\n'
        'return saturate(WetCoverage)*saturate(HullMask)*saturate(mixture);\n')
    pins=[]
    for name in ('DepthNorm','WetCoverage','HullMask','FrothCoverage','ExtinctionPerM'):
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    coverage.set_editor_property('inputs',pins)
    for node,output,pin in ((vertex,'G','DepthNorm'),(vertex,'A','WetCoverage'),
                            (hull,'','HullMask'),(froth,'','FrothCoverage'),
                            (extinction,'','ExtinctionPerM')):
        assert lib.connect_material_expressions(node,output,coverage,pin)
    assert lib.connect_material_property(coverage,'',unreal.MaterialProperty.MP_OPACITY)
    assert links(material,coverage)['FrothCoverage']==froth
    assert links(material,coverage)['HullMask']==hull
    assert all(canonical_graph(graph_signature(material,getattr(unreal.MaterialProperty,'MP_'+k)))==v
               for k,v in protected.items())
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    assert all(sha(path)==value for path,value in maps.items())
    report.write_text(json.dumps(dict(schema='raftsim.compact_wet_liquid_coverage.v1',
        material=PATH,before_sha256=before,after_sha256=sha(FILE),backup_sha256=sha(backup),
        blend=blend,shading=shading,opacity_root=coverage.get_name(),
        native_wet_coverage_channel='A',native_depth_channel='G',depth_decode_m=4.,
        authored_optical_extinction_per_m=.45,
        coefficient_scope='Authored bounded visual extinction approximation, not measured optical data or a change to depth/foam/physics.',
        no_froth_liquid_coverage_at_2m=1-math.exp(-2*.45),
        color_normal_roughness_specular_wpo_opacitymask_emissive_unchanged=True,
        existing_hull_exclusion_retained=True,maps_and_native_physics_unchanged=True,
        visual_accepted=False,boat_accepted=False,packaged_accepted=False,fps_accepted=False),indent=2)+'\n')
    unreal.log('Compact wet liquid coverage repaired: '+str(report))

if __name__=='__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
