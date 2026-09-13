"""Install registered persistent detail on the normal South Fork parent only."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0,str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as old
from raftsim_material_graph_signature import canonical_graph

ROOT=old.ROOT
BASELINE='094123c76f078c905e2eff67101a48aeb27788599e902cb345b4f7c46cff95f5'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/south-fork-moving-detail-install-v2-20260912.json'
BACKUP=REPORT.with_suffix('.backup.zip')
INCLUDE='/Plugin/RaftSimWaterDetail/Private/RaftSimRegisteredDetailSample.ush'


def main():
    if 'RaftSimAuditMovingDetail' in unreal.SystemLibrary.get_command_line():
        result=json.loads(REPORT.read_text())
        assert old.sha(old.FILE)==result['material_sha256']
        material=unreal.load_asset(old.PATH)
        lib=unreal.MaterialEditingLibrary
        graphs={name:old.graph(material,lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,name)))
            for name in ('MP_WORLD_POSITION_OFFSET','MP_NORMAL','MP_BASE_COLOR','MP_ROUGHNESS','MP_OPACITY','MP_OPACITY_MASK')}
        # Unreal's Python wrappers embed process-local addresses in texture
        # and default-value strings. Strip only those addresses, retaining
        # asset paths, node identities, inputs, code and numeric values.
        assert canonical_graph(graphs)==canonical_graph(result['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE)==result['material_sha256']
        fresh=REPORT.with_name('south-fork-moving-detail-fresh-v3-20260912.json')
        assert not fresh.exists()
        fresh.write_text(json.dumps(dict(material_sha256=result['material_sha256'],fresh_process=True,
            read_only=True,all_six_graphs_exact=True,visual_accepted=False),indent=2)+'\n')
        unreal.log('Fresh playable moving-detail material audit passes')
        return
    assert 'RaftSimIntegrateMovingDetail' in unreal.SystemLibrary.get_command_line()
    assert old.sha(old.FILE)==BASELINE and not REPORT.exists() and not BACKUP.exists()
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(old.PATH)
    nodes=list(lib.get_material_expressions(material))
    coverage,=[n for n in nodes if n.get_editor_property('desc')=='SouthForkTransportedFoamOpticsV1']
    old_vertex=old.links(material,coverage)['VertexFoam']
    assert old_vertex.get_class().get_name()=='MaterialExpressionVertexColor'
    normal=lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)
    wpo=lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    originals={n.get_name():old.graph(material,n)[n.get_name()] for n in nodes}
    consumers=[n.get_name() for n in nodes if coverage in old.links(material,n).values()]
    assert len(consumers)==4
    mask=old.graph(material,lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_OPACITY_MASK))
    protected=[ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected+=list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes={p:old.sha(p) for p in protected}
    with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE,old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest()==BASELINE

    def node(kind):
        return lib.create_material_expression(material,getattr(unreal,kind))
    def connect(source,target,pin,output=''):
        assert lib.connect_material_expressions(source,output,target,pin),(pin,source,target)
    def scalar(name,value):
        n=node('MaterialExpressionScalarParameter');n.set_editor_property('parameter_name',name)
        n.set_editor_property('default_value',value);return n
    def custom(label,code,inputs,output):
        n=node('MaterialExpressionCustom');n.set_editor_property('desc',label)
        n.set_editor_property('description',label);n.set_editor_property('code',code)
        n.set_editor_property('output_type',getattr(unreal.CustomMaterialOutputType,output))
        n.set_editor_property('include_file_paths',[INCLUDE])
        entries=[]
        for name in inputs:
            item=unreal.CustomInput();item.set_editor_property('input_name',name);entries.append(item)
        n.set_editor_property('inputs',entries)
        for name,source in inputs.items():connect(source,n,name)
        return n
    enable=scalar('StatefulDetailEnable',0)
    sign=scalar('StatefulDetailWorldYSign',-1)
    position=node('MaterialExpressionWorldPosition')
    position.set_editor_property('world_position_shader_offset',unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    samples=[]
    textures=[]
    for prefix in ('','Previous'):
        texture=node('MaterialExpressionTextureObjectParameter')
        texture.set_editor_property('parameter_name',prefix+'StatefulDetailTexture')
        texture.set_editor_property('texture',unreal.load_asset('/Engine/EngineResources/Black'))
        textures.append(texture)
        samples.append(custom('SouthFork'+prefix+'RegisteredDetailV1',
            'return RaftSimRegisteredDetailSample(Detail,World.xy*float2(0.01,0.01*Sign))*Enable;',
            dict(Detail=texture,World=position,Sign=sign,Enable=enable),'CMOT_FLOAT4'))
    history=node('MaterialExpressionPreviousFrameSwitch')
    connect(samples[0],history,'Current Frame');connect(samples[1],history,'Previous Frame')
    displacement=custom('SouthForkMovingDetailDisplacementV1','return Base+float3(0,0,100*Detail.x);',
        dict(Base=wpo,Detail=history),'CMOT_FLOAT3')
    assert lib.connect_material_property(displacement,'',unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    slopes=custom('SouthForkMovingDetailNormalV1','return normalize(float3(Base.xy-Detail.yz*Base.z,Base.z));',
        dict(Base=normal,Detail=samples[0]),'CMOT_FLOAT3')
    assert lib.connect_material_property(slopes,'',unreal.MaterialProperty.MP_NORMAL)
    # Resolve's alpha is already density-to-coverage with edge/depth taper.
    # Convert to the inherited optical density units; replace CPU foam in the
    # interior, blend it only through the domain edge, never stack coverages.
    density=old.links(material,coverage)['OpticalDensity']
    authority=custom('SouthForkMovingFoamAuthorityV1',
        'float weight=RaftSimRegisteredDetailWindowWeight(Texture,World.xy*float2(0.01,0.01*Sign))*Enable;\n'
        'float amount=(1-weight)*Vertex.r-log(max(1-Detail.a,1e-6))/max(Density,1e-6);\n'
        'return float3(amount,Vertex.gb);',
        dict(Texture=textures[0],World=position,Sign=sign,Enable=enable,Detail=samples[0],Vertex=old_vertex,Density=density),'CMOT_FLOAT3')
    connect(authority,coverage,'VertexFoam')
    for n in nodes:
        actual=old.graph(material,n)[n.get_name()]
        expected=originals[n.get_name()]
        if n==coverage:
            expected['inputs']['VertexFoam']=authority.get_name()
        assert actual==expected,n.get_name()
    assert old.graph(material,lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_OPACITY_MASK))==mask
    assert [n.get_name() for n in nodes if coverage in old.links(material,n).values()]==consumers
    material.set_editor_property('output_translucent_velocity',True)
    material.set_editor_property('is_translucency_velocity_from_depth',False)
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for p,digest in hashes.items():assert old.sha(p)==digest,str(p)
    graphs={name:old.graph(material,lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,name)))
        for name in ('MP_WORLD_POSITION_OFFSET','MP_NORMAL','MP_BASE_COLOR','MP_ROUGHNESS','MP_OPACITY','MP_OPACITY_MASK')}
    REPORT.write_text(json.dumps(dict(material=old.PATH,material_sha256=old.sha(old.FILE),saved_graphs=graphs,
        previous_sha256=BASELINE,backup_sha256=old.sha(BACKUP),protected_file_count=len(hashes),
        original_nodes_preserved_except_foam_input=True,optical_consumers=consumers,
        registered_history=True,visual_accepted=False,contact_accepted=False,performance_accepted=False),indent=2)+'\n')
    unreal.log('Playable South Fork moving-detail material installed: '+str(REPORT))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
