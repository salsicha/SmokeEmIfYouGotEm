#include "AssetRegistry/AssetRegistryModule.h"
#include "RaftSimLiquidGraphRead.h"
#include "HAL/IConsoleManager.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraSystem.h"
#include "NiagaraComponent.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSimulationStageBase.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeOutput.h"
#include "NiagaraNodeInput.h"
#include "NiagaraNodeAssignment.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraNodeCustomHlsl.h"
#include "NiagaraDataInterfaceRigidMeshCollisionQuery.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "EdGraphSchema_Niagara.h"
#include "NiagaraScriptVariable.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "ViewModels/Stack/NiagaraParameterHandle.h"
#include "UObject/SavePackage.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"
#include "RaftSimRegisteredTerrainQuery.h"
#include "RaftSimCompatibleProjection.h"
#include "RaftSimLiquidFoam.h"
#include "RaftSimLiquidWindowProfile.h"
#include "RaftSimAffineTransfer.h"
#include "RaftSimLiquidContactProfile.h"
#include "RaftSimLiquidBoundaryProfile.h"
#include "RaftSimLiquidGridAllocation.h"
#include "RaftSimLiquidInitialState.h"
#include "RaftSimLiquidRegionalContact.h"
#include "RaftSimLiquidParentExterior.h"
#include "RaftSimLiquidInletAdvection.h"

namespace
{
bool LoadRegisteredContact(UNiagaraSystem* System)
{
    FString Text;TSharedPtr<FJsonObject> Profile;
    if (!FFileHelper::LoadFileToString(Text,*(RaftSimLiquidWindowProfile::Directory()/TEXT("triangle_contact_profile.json"))) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Profile)) return false;
    TArray<FVector3f> Packed;
    if (!RaftSimLiquidContactProfile::Decode(Profile,Packed)) return false;
    auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
    for (const auto& Point:Packed)
    {
        Array->FloatData.Add(FVector(Point));Array->InternalFloatData.Add(Point);
    }
    const FNiagaraVariable Variable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Contact Triangles"));
    auto& Store=System->GetExposedParameters();Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    return true;
}

using RaftSimLiquidGraph::DuplicateTypedMapRead;

bool InstallRegionalParticleNeighbors(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs)
{
    UNiagaraNodeFunctionCall* Existing=nullptr;UNiagaraNodeOutput* Spawn=nullptr;int32 Calls=0,Spawns=0;
    for (auto* G:Graphs) for (const auto& N:G->Nodes)
    {
        if (auto* C=Cast<UNiagaraNodeFunctionCall>(N);C && C->FunctionScript && C->FunctionScript->GetName()==TEXT("AddParticleToNeighborQuery"))
        { Existing=C;++Calls; }
        if (auto* O=Cast<UNiagaraNodeOutput>(N);O && O->GetUsage()==ENiagaraScriptUsage::ParticleSpawnScript)
        { Spawn=O;++Spawns; }
    }
    if (Calls!=1 || Spawns!=1)
    { UE_LOG(LogTemp,Error,TEXT("Spawn NQ expected one writer and spawn output; found %d/%d"),Calls,Spawns);return false; }
    struct FInput { FString Name,Default;FNiagaraTypeDefinition Type;FName Linked; };
    TArray<FInput> Inputs;const FString Prefix=Existing->GetFunctionName()+TEXT(".");
    for (const auto& N:Existing->GetNiagaraGraph()->Nodes) for (const auto* P:N->Pins)
        if (P->Direction==EGPD_Input && P->PinName.ToString().StartsWith(Prefix))
        {
            FInput In;In.Name=P->PinName.ToString().RightChop(Prefix.Len());In.Default=P->DefaultValue;
            In.Type=UEdGraphSchema_Niagara::PinToTypeDefinition(P);
            if (P->LinkedTo.Num()>1) { UE_LOG(LogTemp,Error,TEXT("Spawn NQ override has multiple links: %s"),*In.Name);return false; }
            if (P->LinkedTo.Num()==1)
            {
                const auto* Source=P->LinkedTo[0];
                if (In.Name==TEXT("Add Method") && In.Type.GetEnum())
                {
                    // The verified regional neighborhood gather uses native
                    // insertion method 0 (one floor-index bin, not multi-bin
                    // duplicated deposits). The template selects this through
                    // a dynamic enum node; freeze that same regional method.
                    In.Default=In.Type.GetEnum()->GetNameStringByValue(0);
                }
                else if (Source->GetOwningNode()->GetClass()->GetName()!=TEXT("NiagaraNodeParameterMapGet"))
                { UE_LOG(LogTemp,Error,TEXT("Spawn NQ override %s comes from %s"),*In.Name,*Source->GetOwningNode()->GetClass()->GetName());return false; }
                else In.Linked=Source->PinName;
            }
            Inputs.Add(In);
        }
    // Native NQ addresses slots with ExecIndex(), which is relative to spawn
    // or update. Writing from both stacks collides at slot zero on birth frames.
    // Gather once over the complete post-spawn particle set instead; this also
    // ensures IDs/index tables are committed before neighbor sorting and P2G.
    FVersionedNiagaraEmitter Owner;
    for (const auto& H:System->GetEmitterHandles())
        if (H.GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter")) Owner=H.GetInstance();
    auto* Source=Cast<UNiagaraScriptSource>(Spawn->GetNiagaraGraph()->GetOuter());
    if (!Owner.Emitter || !Source) return false;
    auto* Stage=NewObject<UNiagaraSimulationStageGeneric>(Owner.Emitter);
    Stage->SimulationStageName=TEXT("Regional Neighbor Insertion");
    Stage->IterationSource=ENiagaraIterationSource::Particles;
    Stage->NumIterations.SetDefaultParameter(FNiagaraTypeDefinition::GetIntDef(),1);
    Stage->Script=NewObject<UNiagaraScript>(Stage);
    Stage->Script->SetUsage(ENiagaraScriptUsage::ParticleSimulationStageScript);
    Stage->Script->SetUsageId(Stage->GetMergeId());Stage->Script->SetLatestSource(Source);
    Owner.Emitter->AddSimulationStage(Stage,Owner.Version);
    Owner.Emitter->MoveSimulationStageToIndex(Stage,0,Owner.Version);
    FGraphNodeCreator<UNiagaraNodeOutput> OutputCreator(*Source->NodeGraph);
    auto* Output=OutputCreator.CreateNode();Output->SetUsage(ENiagaraScriptUsage::ParticleSimulationStageScript);
    Output->SetUsageId(Stage->Script->GetUsageId());
    Output->Outputs.Add(FNiagaraVariable(FNiagaraTypeDefinition::GetParameterMapDef(),TEXT("Out")));OutputCreator.Finalize();
    FGraphNodeCreator<UNiagaraNodeInput> InputCreator(*Source->NodeGraph);
    auto* Input=InputCreator.CreateNode();Input->Input=FNiagaraVariable(FNiagaraTypeDefinition::GetParameterMapDef(),TEXT("InputMap"));
    Input->Usage=ENiagaraInputNodeUsage::Parameter;InputCreator.Finalize();
    UEdGraphPin* InMap=nullptr;UEdGraphPin* OutMap=nullptr;
    for (auto* Pin:Output->Pins) if (Pin->Direction==EGPD_Input && UEdGraphSchema_Niagara::PinToTypeDefinition(Pin)==FNiagaraTypeDefinition::GetParameterMapDef()) InMap=Pin;
    for (auto* Pin:Input->Pins) if (Pin->Direction==EGPD_Output && UEdGraphSchema_Niagara::PinToTypeDefinition(Pin)==FNiagaraTypeDefinition::GetParameterMapDef()) OutMap=Pin;
    if (!InMap || !OutMap) return false;InMap->MakeLinkTo(OutMap);
    // Preserve the actual beginning of this native step before FLIP/PIC
    // advection/contact. Outflow must prove a segment crossing of a physical
    // open parent face; current position or velocity extrapolation is not enough.
    const auto PositionType=FNiagaraTypeDefinition::GetPositionDef();
    auto* Remember=FNiagaraStackGraphUtilities::AddParameterModuleToStack(
        {FNiagaraVariable(PositionType,TEXT("Particles.RiverStepStartPosition"))},*Output,INDEX_NONE,{TEXT("0,0,0")});
    if (!Remember) return false;
    const auto RememberHandle=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
        FNiagaraParameterHandle(TEXT("Module.Particles.RiverStepStartPosition")),Remember);
    auto& RememberPin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
        *Remember,RememberHandle,PositionType,FGuid(),FGuid());
    const FNiagaraVariableBase CurrentPosition(PositionType,TEXT("Particles.Position"));
    FNiagaraStackGraphUtilities::SetLinkedParameterValueForFunctionInput(RememberPin,CurrentPosition,{CurrentPosition});
    Remember->MarkNodeRequiresSynchronization(TEXT("Native pre-advection particle segment origin"),true);
    auto* Added=FNiagaraStackGraphUtilities::AddScriptModuleToStack(Existing->FunctionScript, *Output,INDEX_NONE,TEXT("RegionalParticleNeighborInsertion"));
    if (!Added) return false;
    for (const auto& In:Inputs)
    {
        const auto Handle=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(FNiagaraParameterHandle(FName(*(TEXT("Module.")+In.Name))),Added);
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Added,Handle,In.Type,FGuid(),FGuid());
        if (!In.Linked.IsNone())
        {
            const FNiagaraVariableBase V(In.Type,In.Linked);
            FNiagaraStackGraphUtilities::SetLinkedParameterValueForFunctionInput(Pin,V,{V});
        }
        else Pin.DefaultValue=In.Default;
    }
    FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Existing,false);
    Added->MarkNodeRequiresSynchronization(TEXT("Disjoint complete post-spawn neighbor insertion before native P2G"),true);
    UE_LOG(LogTemp,Display,TEXT("Regional post-spawn neighbor stage copied %d native overrides"),Inputs.Num());
    return true;
}

bool LoadGridBoundary(UNiagaraSystem* System,bool VectorBoundary=false)
{
    FString Text;TSharedPtr<FJsonObject> Profile;
    const FString Path=RaftSimLiquidWindowProfile::Directory()/
        (VectorBoundary ? TEXT("grid_vector_boundary_profile.json") : TEXT("grid_boundary_profile.json"));
    if (!FFileHelper::LoadFileToString(Text,*Path) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Profile)) return false;
    RaftSimLiquidBoundaryProfile::FDecoded Decoded;
    if (!RaftSimLiquidBoundaryProfile::Decode(Profile,VectorBoundary,Decoded)) return false;
    // This command still creates the fixed native fixture. Refuse a different
    // domain until source/seed installation and explicit native XYZ allocation
    // are coupled to it; accepting new metadata alone would silently simulate
    // a different region. The decoder/query is shared with that next installer.
    if (Decoded.Rectangular)
    { UE_LOG(LogTemp,Error,TEXT("Rectangular boundary requires coupled regional source/seed/grid installation; fixed fixture rejected"));return false; }
    auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
    for (const auto& P:Decoded.Packed)
    {
        Array->FloatData.Add(FVector(P));Array->InternalFloatData.Add(P);
    }
    const FNiagaraVariable Variable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Grid Boundary"));
    auto& Store=System->GetExposedParameters();Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    return true;
}

bool InstallRegisteredPressureBoundary(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,bool DrivenBoundary=false,bool OutletStage=false,bool VectorBoundary=false,bool CanonicalWorld=false,bool ParentExterior=false)
{
    // Regional exterior/shared faces need their own tables; never interpret a
    // legacy window profile as regional forcing merely by changing the frame.
    if (CanonicalWorld && (DrivenBoundary || OutletStage || VectorBoundary) && !ParentExterior) return false;
    if (ParentExterior && !(CanonicalWorld && DrivenBoundary && OutletStage && VectorBoundary)) return false;
    UNiagaraNodeFunctionCall* Boundary=nullptr;int32 Calls=0;
    for (auto* Graph:Graphs)
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_ComputeBoundary")) { Boundary=Call;++Calls; }
    if (Calls!=1) return false;
    auto* Owned=DuplicateObject<UNiagaraScript>(Boundary->FunctionScript,System,TEXT("RegisteredTrianglePressureBoundary"));
    UNiagaraGraph* Graph=CastChecked<UNiagaraScriptSource>(Owned->GetLatestSource())->NodeGraph;
    if (CanonicalWorld)
    {
        // The native module ALSO samples Landscape after its mesh query and
        // can override the registered terrain even when that DI reports invalid.
        // Regional solids have one authority: the preserved triangle page.
        TArray<UNiagaraNodeFunctionCall*> Landscape;
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->Signature.Name==TEXT("GetHeight")) Landscape.Add(Call);
        if (Landscape.Num()!=1) return false;
        auto* Empty=NewObject<UNiagaraNodeCustomHlsl>(Graph);Empty->CreateNewGuid();Graph->AddNode(Empty,false,false);
        Empty->ScriptUsage=ENiagaraScriptUsage::Function;Empty->Signature.Name=TEXT("RegisteredContactOnlyNoLandscapeFallback");
        Empty->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Value")),
            FNiagaraVariable(FNiagaraTypeDefinition::GetBoolDef(),TEXT("IsValid"))};
        FindFProperty<FStrProperty>(Empty->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Empty,TEXT("Value=-1e30; IsValid=false;\n"));
        Empty->AllocateDefaultPins();
        for (const FName Name:{FName(TEXT("Value")),FName(TEXT("IsValid"))})
        {
            auto* Out=Landscape[0]->FindPin(Name,EGPD_Output);if (!Out) return false;
            const auto Links=Out->LinkedTo;Out->BreakAllPinLinks();
            for (auto* Link:Links) Empty->FindPin(Name,EGPD_Output)->MakeLinkTo(Link);
        }
        Empty->MarkNodeRequiresSynchronization(TEXT("Captured triangles are the only regional terrain authority"),true);
    }
    UNiagaraNodeFunctionCall* Old=nullptr;int32 Queries=0;
    for (const auto& Node:Graph->Nodes)
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->Signature.Name==TEXT("GetClosestPointMeshDistanceFieldNoNormal")) { Old=Call;++Queries; }
    if (Queries!=1) { UE_LOG(LogTemp,Error,TEXT("Exact boundary: expected one mesh query, found%d"),Queries);return false; }
    auto* Position=Old->FindPin(TEXT("World Position"),EGPD_Input);
    auto* Collision=Old->FindPin(TEXT("Collision DI"),EGPD_Input);
    if (!Position || !Collision || Position->LinkedTo.Num()!=1 || Collision->LinkedTo.Num()!=1) return false;
    const FNiagaraTypeDefinition Type(UNiagaraDataInterfaceArrayFloat3::StaticClass());
    auto* Read=DuplicateTypedMapRead(Collision->LinkedTo[0],FNiagaraVariable(Type,TEXT("User.River Contact Triangles")));
    if (!Read) return false;
    UEdGraphPin* BoundaryRead=nullptr;
    if (DrivenBoundary)
    {
        BoundaryRead=DuplicateTypedMapRead(Collision->LinkedTo[0],FNiagaraVariable(Type,
            ParentExterior?TEXT("User.River Parent Exterior"):TEXT("User.River Grid Boundary")));
        if (!BoundaryRead) return false;
    }
    auto* Query=NewObject<UNiagaraNodeCustomHlsl>(Graph);Query->CreateNewGuid();Graph->AddNode(Query,false,false);
    Query->ScriptUsage=ENiagaraScriptUsage::Function;Query->Signature.Name=TEXT("RegisteredTriangleBoundary");
    Query->Signature.Inputs={FNiagaraVariable(Type,TEXT("Terrain")),FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Position"))};
    if (DrivenBoundary) Query->Signature.Inputs.Add(FNiagaraVariable(Type,TEXT("Boundary")));
    Query->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Distance")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Closest")),FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("Velocity"))};
    FString Hlsl=FString(TEXT("float distance,encoded; float3 closest,normal,wallVelocity; bool valid;\n"))+
        RaftSimRegisteredTerrainQueryHlsl(TEXT("Position"),CanonicalWorld)+TEXT("Distance=distance; Closest=closest; Velocity=wallVelocity;\n");
    if (DrivenBoundary)
    {
        Hlsl+=RaftSimLiquidBoundaryLayoutHlsl(TEXT("Boundary"),TEXT("inflow"));
        Hlsl+=TEXT("float3 inflowSourcePosition=")+(ParentExterior?FString(TEXT("float3(Position.x,-Position.y,Position.z)")):
            RaftSimLiquidWindowProfile::SourcePositionHlsl(TEXT("Position")))+TEXT(";\n"
            "float3 inflowLocal=float3(dot(inflowSourcePosition-inflowOrigin,inflowAxisX),dot(inflowSourcePosition-inflowOrigin,inflowAxisY),Position.z);\n");
        Hlsl+=RaftSimLiquidBoundaryFaceHlsl(TEXT("inflowLocal"),TEXT("inflow"));
        Hlsl+=TEXT(
        "// PrescribedNativeFaceFlux: virtual normal-velocity boundary outside the physical domain only.\n"
        "int face=inflowFace;\n"
        "if(face>=0) { float3 row; Boundary.Get(inflowHeader+inflowRowOffset+inflowColumn,row);\n"
        "  if(Position.z>row.x && Position.z<row.y) {\n"
        "    Distance=-0.01; Closest=Position; Velocity=0;\n"
        "    if(face<2) Velocity.x=face==0?row.z:-row.z; else Velocity.y=face==2?row.z:-row.z;\n"
        "  }\n"
        "}\n");
    }
    if(OutletStage) Hlsl.ReplaceInline(TEXT("if(Position.z>row.x && Position.z<row.y)"),TEXT("if(row.z>=0 && Position.z>row.x && Position.z<row.y)"));
    if(VectorBoundary)
    {
        if (!OutletStage || Hlsl.ReplaceInline(
            TEXT("if(face<2) Velocity.x=face==0?row.z:-row.z; else Velocity.y=face==2?row.z:-row.z;"),
            TEXT("// NativeVectorInflow: local grid components, same discrete normal discharge.\n"
                 "Boundary.Get(inflowVectorOffset+inflowRowOffset+inflowColumn,Velocity);"),ESearchCase::CaseSensitive)!=1) return false;
    }
    if (DrivenBoundary && (ParentExterior || RaftSimLiquidWindowProfile::Geographic()))
    {
        // Select the original physical face/column in the canonical source
        // frame, then express its velocity in Niagara's reflected local Y.
        Hlsl+=TEXT("Velocity.y=-Velocity.y;\n");
    }
    if (ParentExterior)
        Hlsl+=TEXT("// ParentExteriorHalfVelocity: explicit IEEE nearest-even half lattice, including subnormals.\n"
            "// Do not delegate the rounding direction to a driver conversion intrinsic.\n"
            "for(int halfAxis=0;halfAxis<3;++halfAxis) { float halfV=abs(Velocity[halfAxis]);\n"
            " int halfExponent=(int)((asuint(halfV)>>23)&255u);\n"
            " float halfQuantum=asfloat((uint)max(halfExponent-10,103)<<23);\n"
            " float halfScaled=halfV/halfQuantum,halfBase=floor(halfScaled),halfFraction=halfScaled-halfBase;\n"
            " if(halfFraction>0.5 || (halfFraction==0.5 && (((uint)halfBase&1u)!=0))) halfBase+=1;\n"
            " Velocity[halfAxis]=sign(Velocity[halfAxis])*halfBase*halfQuantum; }\n");
    FindFProperty<FStrProperty>(Query->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Query,Hlsl);
    Query->AllocateDefaultPins();
    Query->FindPin(TEXT("Terrain"),EGPD_Input)->MakeLinkTo(Read);
    Query->FindPin(TEXT("Position"),EGPD_Input)->MakeLinkTo(Position->LinkedTo[0]);
    if (DrivenBoundary) Query->FindPin(TEXT("Boundary"),EGPD_Input)->MakeLinkTo(BoundaryRead);
    if(OutletStage)
    {
        int32 Classified=0;
        for(const auto& Item:Graph->Nodes)
            if(auto* Custom=Cast<UNiagaraNodeCustomHlsl>(Item);Custom && Custom->FindPin(TEXT("RetBoundary"),EGPD_Output))
            {
                auto* Property=FindFProperty<FStrProperty>(Custom->GetClass(),TEXT("CustomHlsl"));
                if(!Property) return false;
                if(!RaftSimAddCustomInput(Custom,FNiagaraVariable(Type,TEXT("StageProfile")),BoundaryRead) ||
                   !RaftSimAddCustomInput(Custom,FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("StageWorldPosition")),Position->LinkedTo[0])) return false;
                FString Code=Property->GetPropertyValue_InContainer(Custom)+TEXT("\n// NativeOutletStageClassification: open pressure boundary, not a moving solid.\n"
                    "float3 canonicalAxisX,canonicalAxisY; StageProfile.Get(0,canonicalAxisX);StageProfile.Get(1,canonicalAxisY);\n")+
                    RaftSimOutletStageQuery(*FString::Printf(TEXT("float3(dot(%s,canonicalAxisX),dot(%s,canonicalAxisY),StageWorldPosition.z)"),
                        ParentExterior?TEXT("float3(StageWorldPosition.x,-StageWorldPosition.y,StageWorldPosition.z)"):
                            *RaftSimLiquidWindowProfile::SourcePositionHlsl(TEXT("StageWorldPosition")),
                        ParentExterior?TEXT("float3(StageWorldPosition.x,-StageWorldPosition.y,StageWorldPosition.z)"):
                            *RaftSimLiquidWindowProfile::SourcePositionHlsl(TEXT("StageWorldPosition"))),TEXT("StageProfile"),false,ParentExterior)+
                    TEXT("if(prescribedStage) RetBoundary=3;\n");
                Property->SetPropertyValue_InContainer(Custom,Code);Custom->MarkNodeRequiresSynchronization(TEXT("Native outgoing stage classification"),true);++Classified;
            }
        if(Classified!=1) { UE_LOG(LogTemp,Error,TEXT("Expected one final boundary classifier, found %d"),Classified);return false; }
    }
    for (const auto& Names:TArray<TPair<FName,FName>>{{TEXT("Closest Distance"),TEXT("Distance")},
        {TEXT("Closest Position"),TEXT("Closest")},{TEXT("Closest Velocity"),TEXT("Velocity")}})
    {
        auto* Output=Old->FindPin(Names.Key,EGPD_Output);if (!Output) return false;
        const auto Links=Output->LinkedTo;Output->BreakAllPinLinks();
        for (auto* Pin:Links) Query->FindPin(Names.Value,EGPD_Output)->MakeLinkTo(Pin);
    }
    Query->MarkNodeRequiresSynchronization(TEXT("Pressure uses preserved terrain triangles"),true);
    Boundary->FunctionScript=Owned;Boundary->MarkNodeRequiresSynchronization(TEXT("Shared terrain for pressure and particles"),true);
    return true;
}

bool InstallHydraulicInitialState(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs)
{
    FString Text;TSharedPtr<FJsonObject> Profile;
    const FString Path=RaftSimLiquidWindowProfile::Directory()/TEXT("hydraulic_initial_state.json");
    if (!FFileHelper::LoadFileToString(Text,*Path) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Profile) ||
        !Profile.IsValid() || Profile->GetStringField(TEXT("schema"))!=TEXT("raftsim.registered_liquid_initial_state.v1")) return false;
    const auto& Positions=Profile->GetArrayField(TEXT("positions_world_cm"));
    const auto& Velocities=Profile->GetArrayField(TEXT("velocities_world_cm_per_s"));
    // Preserve the 163840 seed-table limit. The inherited tank burst depends
    // on grid dimensions and can allocate more candidates; extras are not
    // water. Regional startup separately replaces it with the exact seed count.
    if (Positions.IsEmpty() || Positions.Num()>163840 || Positions.Num()!=Velocities.Num()) return false;
    const FNiagaraTypeDefinition ArrayType(UNiagaraDataInterfaceArrayFloat3::StaticClass());
    const FNiagaraVariable PositionVariable(ArrayType,TEXT("User.River Initial Positions"));
    const FNiagaraVariable VelocityVariable(ArrayType,TEXT("User.River Initial Velocities"));
    const auto AddArray=[&](const FNiagaraVariable& Variable,const TArray<TSharedPtr<FJsonValue>>& Values)
    {
        auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
        for (const auto& Value:Values)
        {
            const auto& V=Value->AsArray();
            if (V.Num()!=3) return false;
            const FVector Raw(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());
            const FVector Point=Variable==PositionVariable ? RaftSimLiquidWindowProfile::PresentPosition(Raw) : RaftSimLiquidWindowProfile::PresentVector(Raw);
            if (Point.ContainsNaN()) return false;
            Array->FloatData.Add(Point);Array->InternalFloatData.Add(FVector3f(Point));
        }
        auto& Store=System->GetExposedParameters();Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);return true;
    };
    if (!AddArray(PositionVariable,Positions) || !AddArray(VelocityVariable,Velocities)) return false;
    return RaftSimInstallLiquidInitialStateReader(System,Graphs);
}

bool CorrectRiverBoundaryAxes(UNiagaraSystem* System,TOptional<float> PicFlipRatio={})
{
    TArray<UNiagaraNodeFunctionCall*> Controls;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object);Call && Call->FunctionScript &&
            Call->FunctionScript->GetName()==TEXT("Grid3D_FLIP_FLUID_CONTROLS") &&
            Call->GetNiagaraGraph()->IsIn(System)) Controls.Add(Call);
    },EGetObjectsFlags::IncludeNestedObjects);
    if (Controls.Num()!=1) { UE_LOG(LogTemp,Error,TEXT("River boundary: expected one owned control, found%d"),Controls.Num());return false; }
    auto* Call=Controls[0];
    // Trace the exposed controls through ComputeBoundary's module bindings,
    // not its custom-HLSL argument labels: X=Left/Right, Y=Back/Front,
    // Z=Down/Up. All four horizontal numerical faces exchange river flow.
    // Keep the lower vertical domain face closed and the upper face open.
    for (const TCHAR* Face:{TEXT("Right"),TEXT("Left"),TEXT("Down"),TEXT("Up"),TEXT("Back"),TEXT("Front")})
    {
        const FName Name(*FString::Printf(TEXT("Module.Open Boundary %s"),Face));
        const auto* Input=Call->GetCalledGraph()->GetScriptVariable(Name);
        if (!Input) return false;
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(Name,FName(*Call->GetFunctionName()));
        ForEachObjectWithOuter(System,[&](UObject* Object)
        {
            if (auto* Script=Cast<UNiagaraScript>(Object))
            {
                TArray<FNiagaraVariable> Rapid;Script->RapidIterationParameters.GetParameters(Rapid);
                for (const auto& V:Rapid)
                    if (V.GetName().ToString().EndsWith(TEXT(".")+Alias.GetParameterHandleString().ToString()))
                        Script->RapidIterationParameters.RemoveParameter(V);
            }
        },EGetObjectsFlags::IncludeNestedObjects);
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Call,Alias,
            Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=FString(Face)==TEXT("Down") ? TEXT("false") : TEXT("true");
        CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("River face axes, not tank labels"),true);
    }
    Call->MarkNodeRequiresSynchronization(TEXT("Four horizontal open boundaries and closed floor"),true);
    if (PicFlipRatio.IsSet())
    {
        // Diagnostic only: distinguish transfer dissipation from pressure/contact
        // forces. Never modify the saved template or silently change the default.
        const FName Name(TEXT("Module.PIC FLIP Ratio"));
        const auto* Input=Call->GetCalledGraph()->GetScriptVariable(Name);
        if (!Input || Input->Variable.GetType()!=FNiagaraTypeDefinition::GetFloatDef()) return false;
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(Name,FName(*Call->GetFunctionName()));
        ForEachObjectWithOuter(System,[&](UObject* Object)
        {
            if (auto* Script=Cast<UNiagaraScript>(Object))
            {
                TArray<FNiagaraVariable> Rapid;Script->RapidIterationParameters.GetParameters(Rapid);
                for (const auto& V:Rapid)
                    if (V.GetName().ToString().EndsWith(TEXT(".")+Alias.GetParameterHandleString().ToString()))
                        Script->RapidIterationParameters.RemoveParameter(V);
            }
        },EGetObjectsFlags::IncludeNestedObjects);
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Call,Alias,
            Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=FString::SanitizeFloat(PicFlipRatio.GetValue());
        CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Explicit transient PIC/FLIP transfer diagnostic"),true);
        UE_LOG(LogTemp,Display,TEXT("Transient transfer diagnostic PIC/FLIP=%g; saved default unchanged"),PicFlipRatio.GetValue());
    }
    return true;
}

bool CorrectRotatedParticleTransfer(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,bool CompleteGather,bool CenteredTransfer=false,
    const RaftSimLiquidRegionalState::FState* Region=nullptr)
{
    // Preserve unnormalized, volume-weighted momentum for the regional
    // coordinator. A half-precision normalized velocity cannot be reduced
    // conservatively after contributions from different owners are mixed.
    const FNiagaraVariable RawVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceGrid3DCollection::StaticClass()),TEXT("Emitter.RiverRawTransfer"));
    if (Region)
    {
        if (!CompleteGather || !CenteredTransfer || !FMath::IsFinite(Region->ParticleVolume) || Region->ParticleVolume<=0) return false;
        UNiagaraNodeOutput* Spawn=nullptr;int32 Spawns=0;
        for (auto* Graph:Graphs) for (const auto& N:Graph->Nodes)
            if (auto* Output=Cast<UNiagaraNodeOutput>(N);Output && Output->GetUsage()==ENiagaraScriptUsage::EmitterSpawnScript)
            { Spawn=Output;++Spawns; }
        if (Spawns!=1) return false;
        // Grid3DCollection discovers named attributes through its owning
        // NiagaraSystem. User DIs are cloned beneath the component and lose
        // that owner. An emitter-spawn default DI retains native discovery.
        auto* Assignment=FNiagaraStackGraphUtilities::AddParameterModuleToStack({RawVariable},*Spawn,0,{TEXT("")});
        if (!Assignment) return false;
        const auto Handle=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(FNiagaraParameterHandle(TEXT("Module.Emitter.RiverRawTransfer")),Assignment);
        auto& Override=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Assignment,Handle,RawVariable.GetType(),FGuid(),FGuid());
        UNiagaraDataInterface* DataObject=nullptr;
        FNiagaraStackGraphUtilities::SetDataInterfaceValueForFunctionInput(Override,UNiagaraDataInterfaceGrid3DCollection::StaticClass(),
            Handle.GetParameterHandleString().ToString(),DataObject);
        auto* Raw=Cast<UNiagaraDataInterfaceGrid3DCollection>(DataObject);if (!Raw) return false;
        Raw->NumCells=Region->ComputationalCells;Raw->WorldBBoxSize=Region->Extent;
        Raw->SetResolutionMethod=ESetResolutionMethod::Independent;
        Raw->NumAttributes=0;Raw->bOverrideFormat=true;Raw->OverrideBufferFormat=ENiagaraGpuBufferFormat::Float;
        Raw->ClearBeforeNonIterationStage=false; // Every raster invocation writes every cell, including empty cells.
    }
    UNiagaraNodeFunctionCall* Raster=nullptr;
    int32 Calls=0;
    for (auto* Graph:Graphs)
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_FLIP_RasterizeNQParticles"))
            { Raster=Call;++Calls; }
    if (Calls!=1) return false;
    auto* Owned=DuplicateObject<UNiagaraScript>(Raster->FunctionScript,System,TEXT("TerrainGridFrameParticleTransfer"));
    int32 Corrections=0,CenteredCorrections=0;
    TArray<UObject*> TransferNodes;GetObjectsWithOuter(Owned,TransferNodes,EGetObjectsFlags::IncludeNestedObjects);
    // Wiring the new DI creates map-get nodes; never do that while the global
    // UObject hash is locked by ForEachObjectWithOuter.
    auto CorrectNode=[&](UObject* Object)
    {
        auto* Node=Cast<UNiagaraNodeCustomHlsl>(Object);
        auto* Property=Node ? FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl")) : nullptr;
        if (!Property) return;
        FString Code=Property->GetPropertyValue_InContainer(Node);
        if (!Code.Contains(TEXT("TotalWeight")) || !Code.Contains(TEXT("CurrParticleVelocity"))) return;
        if (!Node->FindPin(TEXT("UnitToWorld"),EGPD_Input) || !Node->FindPin(TEXT("Velocity"),EGPD_Output)) return;
        if (Region)
        {
            UEdGraphPin* GridPin=nullptr;
            for (auto* Pin:Node->Pins)
                if (Pin->Direction==EGPD_Input && Pin->LinkedTo.Num()==1 &&
                    Pin->PinType.PinSubCategoryObject==UNiagaraDataInterfaceGrid3DCollection::StaticClass())
                { GridPin=Pin;break; }
            if (!GridPin || GridPin->LinkedTo.Num()!=1)
            { UE_LOG(LogTemp,Error,TEXT("Raw P2G requires a linked grid interface input"));
                for (const auto* Pin:Node->Pins) UE_LOG(LogTemp,Display,TEXT("P2G pin %s (%d links)"),*Pin->PinName.ToString(),Pin->LinkedTo.Num());return; }
            auto* RawRead=DuplicateTypedMapRead(GridPin->LinkedTo[0],RawVariable);
            if (!RaftSimAddCustomInput(Node,FNiagaraVariable(RawVariable.GetType(),TEXT("RawTransfer")),RawRead))
            { UE_LOG(LogTemp,Error,TEXT("Raw P2G map read failed from %s"),*GridPin->LinkedTo[0]->GetOwningNode()->GetClass()->GetName());return; }
            const FString NormalizeIf=Code.Contains(TEXT("CurrNQIndexX = IndexX + x"))?TEXT("if (TotalWeight > 1e-8)"):TEXT("if (TotalWeight > 0.0)");
            const FString RawCode=FString::Printf(TEXT(
                "// RegionalRawP2G: volume-weighted local momentum BEFORE normalization.\n"
                "float3 rawLocalMomentum=float3(dot(Velocity,normalize(UnitToWorld[0].xyz)),\n"
                " dot(Velocity,normalize(UnitToWorld[1].xyz)),dot(Velocity,normalize(UnitToWorld[2].xyz)));\n"
                "RawTransfer.SetVector4Value<Attribute=\"Momentum_Volume\">(IndexX,IndexY,IndexZ,\n"
                " float4(rawLocalMomentum,TotalWeight)*%.9g);\n"),float(Region->ParticleVolume))+NormalizeIf;
            if (Code.ReplaceInline(*NormalizeIf,*RawCode,ESearchCase::CaseSensitive)!=1)
            { UE_LOG(LogTemp,Error,TEXT("Raw P2G normalization anchor missing: %s"),*Code.Right(950));return; }
        }
        // NQ reads world/simulation-space particle velocities, whereas the MAC
        // pressure grid and its G2P consumer use grid-local vectors. UnitToWorld
        // rows contain scaled grid axes: normalize before projecting a vector.
        // This is a basis conversion, not a velocity clamp or added force.
        const FString Anchor=TEXT("Velocity /= TotalWeight;");
        if (Code.ReplaceInline(*Anchor,TEXT(
            "Velocity /= TotalWeight;\n"
            "float3 worldVelocity = Velocity;\n"
            "Velocity = float3(dot(worldVelocity, normalize(UnitToWorld[0].xyz)),\n"
            "                  dot(worldVelocity, normalize(UnitToWorld[1].xyz)),\n"
            "                  dot(worldVelocity, normalize(UnitToWorld[2].xyz)));"),ESearchCase::CaseSensitive)!=1) return;
        if (CompleteGather)
        {
            // The DI stores all neighbors, but the stock consumer truncates the
            // list at the initial particles-per-cell target. A continuous source
            // can exceed that target: dropping arbitrary neighbors loses their
            // momentum. The actual count is the safe allocated-list bound.
            if (Code.ReplaceInline(TEXT("CurrNQCount = min(MaxParticlesPerCell, CurrNQCount);"),
                TEXT("// Gather every valid neighbor; bounded by the actual allocated count."),ESearchCase::CaseSensitive)!=1) return;
        }
        if (CenteredTransfer && Code.Contains(TEXT("CurrNQIndexX = IndexX + x")))
        {
            // NQ insertion is floor(Unit*NumCells), while the velocity texture
            // lives at (Index+.5). The old [-1,0]^3 equal-weight gather was
            // offset by half a cell. The full tent support intersects 27 bins.
            int32 Loops=0;
            for (const TCHAR* Axis:{TEXT("x"),TEXT("y"),TEXT("z")})
                Loops+=Code.ReplaceInline(*FString::Printf(TEXT("%s <= 0"),Axis),
                    *FString::Printf(TEXT("%s <= 1"),Axis),ESearchCase::CaseSensitive);
            if (Loops!=3 || Code.ReplaceInline(TEXT("if (UseComplexWeight)"),TEXT("if (true)"),ESearchCase::CaseSensitive)!=3) return;
            // World-space axis-aligned weights are also wrong for a rotated,
            // non-cubic grid. Project displacement onto each actual cell axis.
            if (Code.ReplaceInline(TEXT("float3 IndexDifference = (CurrParticlePosition - World) / dx;"),TEXT(
                "// CenteredMetricParticleTransfer: same centered tent basis as G2P.\n"
                "float3 displacement = CurrParticlePosition - World;\n"
                "float3 IndexDifference = float3(\n"
                " dot(displacement,normalize(UnitToWorld[0].xyz))*NumCellsX/length(UnitToWorld[0].xyz),\n"
                " dot(displacement,normalize(UnitToWorld[1].xyz))*NumCellsY/length(UnitToWorld[1].xyz),\n"
                " dot(displacement,normalize(UnitToWorld[2].xyz))*NumCellsZ/length(UnitToWorld[2].xyz));"),ESearchCase::CaseSensitive)!=1) return;
            ++CenteredCorrections;
        }
        Property->SetPropertyValue_InContainer(Node,Code);
        Node->MarkNodeRequiresSynchronization(TEXT("World particle velocity to rotated grid basis"),true);
        ++Corrections;
    };
    for (auto* Object:TransferNodes) CorrectNode(Object);
    // The stock graph contains separate single-cell and neighborhood gathers.
    // Correct both branches; the static switch compiles only the selected one.
    if (Corrections!=2) { UE_LOG(LogTemp,Error,TEXT("Grid-frame review: unexpected NQ shader structure (%d)"),Corrections);return false; }
    if (CenteredTransfer && CenteredCorrections!=1)
    { UE_LOG(LogTemp,Error,TEXT("Centered transfer: expected exactly one verified neighborhood branch"));return false; }
    Raster->FunctionScript=Owned;
    Raster->MarkNodeRequiresSynchronization(TEXT("Owned grid-frame-correct particle transfer"),true);
    return true;
}

bool AddPrivateTerrainProjection(UNiagaraNode* Outer,UEdGraphPin* VelocityRead,bool ExactTriangles,bool CanonicalWorld=false,bool ParentExterior=false)
{
    auto* Graph=Outer->GetNiagaraGraph();
    auto* Position=Outer->FindPin(TEXT("Position"),EGPD_Output);
    auto* Velocity=Outer->FindPin(TEXT("Velocity"),EGPD_Output);
    auto* OriginalGet=Cast<UNiagaraNode>(VelocityRead->GetOwningNode());
    if (!Position || !Velocity || !OriginalGet || Position->LinkedTo.Num()!=1 || Velocity->LinkedTo.Num()!=1) return false;
    UEdGraphPin* MapSource=nullptr;
    for (auto* Pin:OriginalGet->Pins)
        if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() && Pin->LinkedTo.Num()==1)
            MapSource=Pin->LinkedTo[0];
    if (!MapSource) return false;
    // Duplicate an existing map-get so Niagara's output/default GUID mapping is
    // retained. No private Niagara editor header or unexported pin API is used.
    auto* Get=DuplicateObject<UNiagaraNode>(OriginalGet,Graph);
    Get->CreateNewGuid();Graph->AddNode(Get,false,false);
    // Duplicated pin arrays reference the source graph, but the source pins do
    // not reciprocally reference this new node. Clear only the new arrays.
    for (auto* Pin:Get->Pins) Pin->LinkedTo.Reset();
    auto* Terrain=Get->FindPin(TEXT("Particles.Velocity"),EGPD_Output);
    if (!Terrain) return false;
    const FNiagaraVariable Variable(ExactTriangles ? FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()) :
        FNiagaraTypeDefinition(UNiagaraDataInterfaceRigidMeshCollisionQuery::StaticClass()),ExactTriangles ? TEXT("User.River Contact Triangles") : TEXT("User.Collide_Meshes"));
    const auto Type=UEdGraphSchema_Niagara::TypeDefinitionToPinType(Variable.GetType());
    Terrain->PinName=Variable.GetName();Terrain->PinType=Type;
    auto* Defaults=FindFProperty<FMapProperty>(Get->GetClass(),TEXT("PinOutputToPinDefaultPersistentId"));
    if (!Defaults) return false;
    FScriptMapHelper Mapping(Defaults,Defaults->ContainerPtrToValuePtr<void>(Get));
    bool DefaultUpdated=false;
    for (int32 Index=0;Index<Mapping.GetMaxIndex();++Index)
        if (Mapping.IsValidIndex(Index) && *reinterpret_cast<FGuid*>(Mapping.GetKeyPtr(Index))==Terrain->PersistentGuid)
            for (auto* Pin:Get->Pins)
                if (Pin->PersistentGuid==*reinterpret_cast<FGuid*>(Mapping.GetValuePtr(Index)))
                { Pin->PinType=Type;Pin->DefaultValue.Empty();Pin->DefaultObject=nullptr;DefaultUpdated=true; }
    if (!DefaultUpdated) return false;
    for (auto* Pin:Get->Pins)
        if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct()) Pin->MakeLinkTo(MapSource);
    Get->MarkNodeRequiresSynchronization(TEXT("Explicit tagged terrain DI read"),true);

    auto* Project=NewObject<UNiagaraNodeCustomHlsl>(Graph);
    Project->CreateNewGuid();Graph->AddNode(Project,false,false);
    Project->ScriptUsage=ENiagaraScriptUsage::Function;
    Project->Signature.Name=TEXT("ProjectTaggedTerrainContact");
    Project->Signature.Inputs={
        FNiagaraVariable(Variable.GetType(),TEXT("Terrain")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Position")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("PreviousPosition")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("Velocity")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("DeltaTime"))};
    Project->Signature.Outputs={
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("ProjectedPosition")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("ProjectedVelocity")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("QueryDistance")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("QueryValid")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("QueryNormalZ")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("QueryWallSpeed")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("StepLength"))};
    auto* Hlsl=FindFProperty<FStrProperty>(Project->GetClass(),TEXT("CustomHlsl"));
    if (!Hlsl) return false;
    Hlsl->SetPropertyValue_InContainer(Project,TEXT(
        "ProjectedPosition=PreviousPosition; ProjectedVelocity=Velocity; QueryDistance=100000; QueryValid=0; QueryNormalZ=0; QueryWallSpeed=0; StepLength=length(Position-PreviousPosition);\n"
        "float3 travel=Position-PreviousPosition; int steps=clamp((int)ceil(length(travel)/8.0),1,32);\n"
        "float3 increment=travel/steps;\n"
        "for(int step=0;step<steps;++step) {\n"
        " float3 safePosition=ProjectedPosition; ProjectedPosition+=increment;\n"
        " for(int iteration=0;iteration<4;++iteration) {\n"
        " float distance, encoded; float3 closest, normal, wallVelocity; bool valid;\n"
        " Terrain.GetClosestPointMeshDistanceFieldAccurate(ProjectedPosition,DeltaTime,1.0,400.0,distance,closest,normal,wallVelocity,valid,encoded);\n"
        " if(step==0 && iteration==0) { QueryDistance=distance; QueryValid=valid ? 1.0 : 0.0; QueryNormalZ=valid ? normal.z : 0.0; QueryWallSpeed=valid ? length(wallVelocity) : 0.0; }\n"
        " if(!isfinite(distance)) { ProjectedPosition=safePosition; increment=0; break; }\n"
        " if(distance>=2.0) break;\n"
        " if(!valid || dot(normal,normal)<0.5) { ProjectedPosition=safePosition; increment=0; break; }\n"
        " normal=normalize(normal);\n"
        " ProjectedPosition+=normal*min(2.0-distance,100.0);\n"
        " float inward=dot(ProjectedVelocity-wallVelocity,normal);\n"
        " ProjectedVelocity-=normal*min(inward,0.0);\n"
        " increment-=normal*min(dot(increment,normal),0.0);\n"
        " }\n"
        "}\n"));
    if (ExactTriangles)
    {
        FString Code=Hlsl->GetPropertyValue_InContainer(Project);
        if (Code.ReplaceInline(TEXT(" Terrain.GetClosestPointMeshDistanceFieldAccurate(ProjectedPosition,DeltaTime,1.0,400.0,distance,closest,normal,wallVelocity,valid,encoded);\n"),
            *RaftSimRegisteredTerrainQueryHlsl(TEXT("ProjectedPosition"),CanonicalWorld),ESearchCase::CaseSensitive)!=1) return false;
        // This query returns vertical clearance. Move above the exact top,
        // then remove only inward normal momentum. No particle deletion.
        if (Code.ReplaceInline(TEXT("ProjectedPosition+=normal*min(2.0-distance,100.0);"),
            TEXT("ProjectedPosition.z+=max(2.0-distance,0.0);"),ESearchCase::CaseSensitive)!=1) return false;
        Hlsl->SetPropertyValue_InContainer(Project,Code);
    }
    if(ParentExterior)
    {
        if(!ExactTriangles || !CanonicalWorld) return false;
        Project->Signature.Inputs.Add(FNiagaraVariable(Variable.GetType(),TEXT("InletProfile")));
        Project->Signature.Outputs.Add(FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("InletRawPosition")));
        Project->Signature.Outputs.Add(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("InletRawVelocity")));
        Project->Signature.Outputs.Add(FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("InletFace")));
        FString Code=Hlsl->GetPropertyValue_InContainer(Project);
        if(Code.ReplaceInline(TEXT("ProjectedVelocity=Velocity;"),TEXT("ProjectedVelocity=inletVelocity;"),ESearchCase::CaseSensitive)!=1 ||
            Code.ReplaceInline(TEXT("float3 travel=Position-PreviousPosition;"),TEXT("float3 travel=inletPosition-PreviousPosition;"),ESearchCase::CaseSensitive)!=1) return false;
        Hlsl->SetPropertyValue_InContainer(Project,RaftSimLiquidInletAdvectionHlsl()+Code);
    }
    Project->AllocateDefaultPins();
    if(ParentExterior)
    {
        auto* Read=DuplicateTypedMapRead(Terrain,FNiagaraVariable(Variable.GetType(),TEXT("User.River Parent Exterior")));
        if(!Read) return false;
        Project->FindPin(TEXT("InletProfile"),EGPD_Input)->MakeLinkTo(Read);
    }
    auto* TargetPosition=Position->LinkedTo[0];auto* TargetVelocity=Velocity->LinkedTo[0];
    TargetPosition->BreakAllPinLinks();TargetVelocity->BreakAllPinLinks();
    const auto Link=[&](const TCHAR* Name,EEdGraphPinDirection Direction,UEdGraphPin* Other)
    { auto* Pin=Project->FindPin(Name,Direction);if (!Pin) return false;Pin->MakeLinkTo(Other);return true; };
    if (!Link(TEXT("Terrain"),EGPD_Input,Terrain) || !Link(TEXT("Position"),EGPD_Input,Position) ||
        !Link(TEXT("Velocity"),EGPD_Input,Velocity) || !Link(TEXT("ProjectedPosition"),EGPD_Output,TargetPosition) ||
        !Link(TEXT("ProjectedVelocity"),EGPD_Output,TargetVelocity)) return false;
    UEdGraphPin* DeltaTime=nullptr;
    UEdGraphPin* PreviousPosition=nullptr;
    for (const auto& Node:Graph->Nodes)
        if (Node!=Project)
            for (auto* Pin:Node->Pins)
                if (Pin->Direction==EGPD_Output)
                {
                    if (Pin->PinName==TEXT("Engine.DeltaTime")) DeltaTime=Pin;
                    if (Pin->PinName==TEXT("Particles.Position")) PreviousPosition=Pin;
                }
    if (!DeltaTime || !Link(TEXT("DeltaTime"),EGPD_Input,DeltaTime)) return false;
    if (!PreviousPosition || !Link(TEXT("PreviousPosition"),EGPD_Input,PreviousPosition)) return false;
    for (const auto& Output:TArray<TPair<FName,FName>>{
        {TEXT("QueryDistance"),TEXT("Particles.TerrainContactDistance")},
        {TEXT("QueryValid"),TEXT("Particles.TerrainContactValid")},
        {TEXT("QueryNormalZ"),TEXT("Particles.TerrainContactNormalZ")},
        {TEXT("QueryWallSpeed"),TEXT("Particles.TerrainContactWallSpeed")},
        {TEXT("StepLength"),TEXT("Particles.TerrainContactStepLength")}})
    {
        auto PinType=UEdGraphSchema_Niagara::TypeDefinitionToPinType(FNiagaraTypeDefinition::GetFloatDef());
        PinType.PinSubCategory=TargetPosition->PinType.PinSubCategory;
        auto* Pin=TargetPosition->GetOwningNode()->CreatePin(EGPD_Input,PinType,Output.Value);
        if (!Link(*Output.Key.ToString(),EGPD_Output,Pin)) return false;
    }
    if(ParentExterior)
    {
        for(const auto& Pair:TArray<TPair<FName,FName>>{
            {TEXT("InletRawPosition"),TEXT("Particles.RiverInletRawPosition")},
            {TEXT("InletRawVelocity"),TEXT("Particles.RiverInletRawVelocity")},
            {TEXT("InletFace"),TEXT("Particles.RiverInletFace")}})
        {
            auto* Output=Project->FindPin(Pair.Key,EGPD_Output);
            if(!Output) return false;
            auto PinType=Output->PinType;PinType.PinSubCategory=TargetPosition->PinType.PinSubCategory;
            auto* Pin=TargetPosition->GetOwningNode()->CreatePin(EGPD_Input,PinType,Pair.Value);
            Pin->MakeLinkTo(Output);
        }
    }
    Project->MarkNodeRequiresSynchronization(TEXT("Tagged mesh contact with tangential velocity preserved"),true);
    return true;
}

bool InstallParticleTerrainProjection(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,
    bool Private,bool ExactTriangles,bool CanonicalWorld,UNiagaraNodeFunctionCall*& Update,int32& Rewired,bool ParentExterior=false)
{
    int32 Updates=0;Update=nullptr;Rewired=0;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) return false;
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_FLIP_ParticleUpdate")) { Update=Call;++Updates; }
    }
    if (Updates!=1) return false;
    auto* Owned=DuplicateObject<UNiagaraScript>(Update->FunctionScript,System,TEXT("TerrainContactParticleUpdate"));
    bool Valid=true;TArray<UObject*> OwnedNodes;
    ForEachObjectWithOuter(Owned,[&](UObject* Object){OwnedNodes.Add(Object);},EGetObjectsFlags::IncludeNestedObjects);
    for (UObject* Object:OwnedNodes)
    {
        auto* Node=Cast<UNiagaraNode>(Object);if (!Node) continue;
        auto* Velocity=Node->FindPin(TEXT("Velocity if True"),EGPD_Input);
        auto* Position=Node->FindPin(TEXT("Position if True"),EGPD_Input);
        auto* Output=Node->FindPin(TEXT("Position"),EGPD_Output);
        if (!Velocity || !Velocity->LinkedTo.IsEmpty() || !Position || !Output) continue;
        if (Position->LinkedTo.Num()!=1 || Position->LinkedTo[0]->PinName!=TEXT("Particles.Position") ||
            Output->LinkedTo.Num()!=1 || Output->LinkedTo[0]->PinName!=TEXT("Position if False")) return false;
        auto* Outer=Output->LinkedTo[0]->GetOwningNode();
        auto* FreePosition=Outer->FindPin(TEXT("Position if True"),EGPD_Input);
        auto* FreeVelocity=Outer->FindPin(TEXT("Velocity if True"),EGPD_Input);
        if (!FreePosition || !FreeVelocity || FreePosition->LinkedTo.Num()!=1 ||
            FreeVelocity->LinkedTo.Num()!=1 || FreeVelocity->LinkedTo[0]->PinName!=TEXT("Particles.Velocity")) return false;
        Position->BreakAllPinLinks();Position->MakeLinkTo(FreePosition->LinkedTo[0]);
        Velocity->MakeLinkTo(FreeVelocity->LinkedTo[0]);
        Node->MarkNodeRequiresSynchronization(TEXT("Project terrain contacts without coarse-cell no-slip freeze"),true);
        if (Private && !AddPrivateTerrainProjection(CastChecked<UNiagaraNode>(Outer),FreeVelocity->LinkedTo[0],ExactTriangles,CanonicalWorld,ParentExterior)) Valid=false;
        ++Rewired;
    }
    if (!Valid || Rewired==0) return false;
    Update->FunctionScript=Owned;
    if (Private)
        for (auto* Graph:Graphs) for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetPathName()==TEXT("/Niagara/Modules/Collision/Collision.Collision"))
                FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Call,false);
    Update->MarkNodeRequiresSynchronization(TEXT("Owned terrain-contact particle update"),true);
    return true;
}

void CreateTerrainContact(const TArray<FString>& Options)
{
    const FString Destination=TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainContactReview");
    const bool ReviewedReplacement=Options.Num()==1 && Options[0]==TEXT("replace-reviewed") &&
        FPaths::FileExists(FPaths::ProjectDir()/TEXT("../tmp/liquid-terrain-contact-before-radius-20260908.uasset"));
    if ((!Options.IsEmpty() && !ReviewedReplacement) || (FPackageName::DoesPackageExist(Destination) && !ReviewedReplacement))
    { UE_LOG(LogTemp,Error,TEXT("Refusing to overwrite terrain contact review"));return; }
    auto* Source=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    auto* ContactScript=LoadObject<UNiagaraScript>(nullptr,TEXT("/Niagara/Modules/Collision/Collision.Collision"));
    if (!Source || !ContactScript) return;
    auto* Package=ReviewedReplacement ? LoadPackage(nullptr,*Destination,LOAD_None) : CreatePackage(*Destination);
    if (!Package) return;
    if (ReviewedReplacement) Package->FullyLoad();
    auto* System=ReviewedReplacement ? LoadObject<UNiagaraSystem>(nullptr,*Destination) :
        DuplicateObject<UNiagaraSystem>(Source,Package,*FPackageName::GetLongPackageAssetName(Destination));
    if (!System) return;
    System->SetFlags(RF_Public|RF_Standalone|RF_Transactional);
    TSet<UNiagaraGraph*> Graphs;
    for (auto& Handle:System->GetEmitterHandles())
        if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
            if (auto* Data=Handle.GetInstance().GetEmitterData())
            {
                Data->RemoveParent();
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (auto* Script:Scripts)
                    if (auto* ScriptSource=Cast<UNiagaraScriptSource>(Script->GetLatestSource()))
                        Graphs.Add(ScriptSource->NodeGraph);
            }
    UNiagaraNodeFunctionCall* Reject=nullptr;
    UNiagaraNodeFunctionCall* ExistingContact=nullptr;
    int32 RejectCount=0;
    for (auto* Graph:Graphs)
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node))
            {
                if (Call->FunctionScript==ContactScript) ExistingContact=Call;
                if (Call->GetFunctionName()==TEXT("KillParticles") && Call->FunctionScript &&
                    Call->FunctionScript->GetName()==TEXT("KillParticles"))
                { Reject=Call;++RejectCount; }
            }
    if (RejectCount!=1) { UE_LOG(LogTemp,Error,TEXT("Ambiguous active solid rejection"));return; }
    UNiagaraNodeOutput* Output=nullptr;
    UEdGraphNode* Cursor=Reject;TSet<UEdGraphNode*> Visited;
    while (Cursor && !Visited.Contains(Cursor))
    {
        Visited.Add(Cursor);
        if ((Output=Cast<UNiagaraNodeOutput>(Cursor))) break;
        UEdGraphNode* Next=nullptr;
        for (auto* Pin:Cursor->Pins)
            if (Pin->Direction==EGPD_Output &&
                Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() &&
                Pin->LinkedTo.Num()==1)
            { Next=Pin->LinkedTo[0]->GetOwningNode();break; }
        Cursor=Next;
    }
    if (!Output || Output->GetUsage()!=ENiagaraScriptUsage::ParticleSimulationStageScript)
    { UE_LOG(LogTemp,Error,TEXT("Missing final fluid-particle simulation stage"));return; }
    FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Reject,false);
    auto* Contact=ReviewedReplacement ? ExistingContact : FNiagaraStackGraphUtilities::AddScriptModuleToStack(ContactScript,*Output);
    if (!Contact) return;
    bool Valid=true;
    const auto Literal=[&](FName Name,const FString& Value)
    {
        const auto* Input=Contact->GetCalledGraph()->GetScriptVariable(Name);
        if (!Input) { UE_LOG(LogTemp,Error,TEXT("Missing contact input %s"),*Name.ToString());Valid=false;return; }
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(Name,FName(*Contact->GetFunctionName()));
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Contact,Alias,
            Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=Value;
        CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Mass-preserving contact configuration"),true);
    };
    auto* Query=Contact->FindPin(TEXT("GPU Collision Type"),EGPD_Input);
    auto* QueryEnum=LoadObject<UEnum>(nullptr,TEXT("/Niagara/Enums/ENiagara_GPUCollisionType.ENiagara_GPUCollisionType"));
    bool DistanceFields=false;
    if (Query && QueryEnum)
        for (int32 Index=0;Index<QueryEnum->NumEnums();++Index)
            if (QueryEnum->GetDisplayNameTextByIndex(Index).ToString().Contains(TEXT("Distance")))
            { Query->DefaultValue=QueryEnum->GetNameStringByIndex(Index);DistanceFields=true;break; }
    if (!DistanceFields) { UE_LOG(LogTemp,Error,TEXT("Missing GPU distance-field contact method"));return; }
    auto* RadiusPin=Contact->FindPin(TEXT("Radius Calculation Type"),EGPD_Input);
    auto* RadiusEnum=LoadObject<UEnum>(nullptr,TEXT("/Niagara/Enums/ENiagaraCollisionRadiusOptions.ENiagaraCollisionRadiusOptions"));
    bool CustomRadius=false;
    if (RadiusPin && RadiusEnum)
        for (int32 Index=0;Index<RadiusEnum->NumEnums();++Index)
            if (RadiusEnum->GetDisplayNameTextByIndex(Index).ToString()==TEXT("Custom"))
            { RadiusPin->DefaultValue=RadiusEnum->GetNameStringByIndex(Index);CustomRadius=true;break; }
    if (!CustomRadius) { UE_LOG(LogTemp,Error,TEXT("Missing explicit custom contact radius"));return; }
    for (const auto& Setting:TArray<TPair<FName,FString>>{
        {TEXT("Module.Collision Enabled"),TEXT("true")},
        {TEXT("Module.Correct Interpenetration"),TEXT("true")},
        {TEXT("Module.Kill On Collision"),TEXT("false")},
        {TEXT("Module.Kill Particles Lodged Within Meshes"),TEXT("false")},
        {TEXT("Module.Enable Rest State"),TEXT("false")},
        {TEXT("Module.EnableMaxCollisionCount"),TEXT("false")},
        {TEXT("Module.Randomize Collision Normal"),TEXT("false")},
        {TEXT("Module.Maximum Penetration Correction Distance"),TEXT("300.0")},
        {TEXT("Module.Particle Radius"),TEXT("2.0")},
        {TEXT("Module.Particle Radius Scale"),TEXT("1.0")},
        {TEXT("Module.Restitution"),TEXT("0.0")},
        {TEXT("Module.Friction"),TEXT("0.0")},
        {TEXT("Module.Static Friction"),TEXT("0.0")}})
        Literal(Setting.Key,Setting.Value);
    Contact->MarkNodeRequiresSynchronization(TEXT("Terrain contact instead of particle deletion"),true);
    if (!Valid) return;
    System->RequestCompile(true);System->WaitForCompilationComplete(false,false);
    if (!System->IsReadyToRun()) { UE_LOG(LogTemp,Error,TEXT("Terrain contact compile failed"));return; }
    FAssetRegistryModule::AssetCreated(System);Package->MarkPackageDirty();
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;
    const bool Saved=UPackage::SavePackage(Package,System,
        *FPackageName::LongPackageNameToFilename(Destination,FPackageName::GetAssetPackageExtension()),Args);
    UE_LOG(LogTemp,Display,TEXT("Terrain contact saved=%d; global mesh-distance-field response, no kill, no bounce; exact-bed GPU verification still required"),Saved);
}
FAutoConsoleCommand Command(TEXT("RaftSim.CreateSouthForkLiquidTerrainContact"),
    TEXT("Create isolated non-deleting terrain contact review; never overwrite or promote."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&CreateTerrainContact));

// Bounded runtime candidate: the pressure boundary remains unchanged. Replace
// only the coarse solid-cell freeze with inertial motion, then let the existing
// distance-field contact project the particle and remove inward velocity.
FAutoConsoleCommandWithWorldAndArgs MomentumCommand(TEXT("RaftSim.LiquidTerrainMomentumReview"),
    TEXT("Unsaved contact candidate preserving motion in coarse solid cells; requires terrain contact asset."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        const bool SurfaceFoam=Args.Num()>=1 && Args[0]==TEXT("surface-foam");
        const bool Foam=SurfaceFoam || (Args.Num()>=1 && Args[0]==TEXT("foam"));
        const bool VectorBoundary=Foam || (Args.Num()>=1 && Args[0]==TEXT("vector-boundary"));
        const bool CenteredTransfer=VectorBoundary || (Args.Num()>=1 && Args[0]==TEXT("centered-transfer"));
        TOptional<float> PicFlipRatio;
        if (Args.Num()>1)
        {
            float Value=0;
            if (Args.Num()!=2 || (!CenteredTransfer && Args[0]!=TEXT("outlet-stage")) || !Args[1].StartsWith(TEXT("pic-flip=")) ||
                !LexTryParseString(Value,*Args[1].Mid(9)) || !FMath::IsFinite(Value) || Value<0 || Value>1)
            { UE_LOG(LogTemp,Error,TEXT("Expected outlet-stage pic-flip=[0,1] for a transfer diagnostic"));return; }
            PicFlipRatio=Value;
        }
        const bool OutletStage=CenteredTransfer || (Args.Num()>=1 && Args[0]==TEXT("outlet-stage"));
        const bool Compatible=OutletStage || (Args.Num()==1 && Args[0]==TEXT("compatible-projection"));
        const bool DrivenBoundary=Compatible || (Args.Num()==1 && Args[0]==TEXT("driven-boundary"));
        const bool GridHalo=DrivenBoundary || (Args.Num()==1 && Args[0]==TEXT("grid-halo"));
        const bool ExactTriangles=GridHalo || (Args.Num()==1 && Args[0]==TEXT("exact-triangles"));
        const bool WetStart=ExactTriangles || (Args.Num()==1 && Args[0]==TEXT("wet-start"));
        const bool OpenSides=WetStart || (Args.Num()==1 && Args[0]==TEXT("open-sides"));
        const bool CompleteGather=OpenSides || (Args.Num()==1 && Args[0]==TEXT("complete-gather"));
        const bool GridFrame=CompleteGather || (Args.Num()==1 && Args[0]==TEXT("grid-frame"));
        const bool Private=GridFrame || (Args.Num()==1 && Args[0]==TEXT("private"));
        if (!Args.IsEmpty() && !Private) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            if (It->GetWorld()!=World || !It->GetAsset() ||
                It->GetAsset()->GetName()!=TEXT("NS_SouthForkLiquidTerrainContactReview")) continue;
            auto* System=DuplicateObject<UNiagaraSystem>(It->GetAsset(),GetTransientPackage(),
                MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),WetStart ? TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_LiquidBodyReview") : OpenSides ? TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_LiquidBodyReview") : CompleteGather ? TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_LiquidBodyReview") : GridFrame ? TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_LiquidBodyReview") : Private ? TEXT("SouthForkLiquidTerrainMomentumReview_Private_LiquidBodyReview") : TEXT("SouthForkLiquidTerrainMomentumReview_LiquidBodyReview")));
            if (!RaftSimLiquidWindowProfile::InstallRecenteredSources(System))
            { UE_LOG(LogTemp,Error,TEXT("Control-centred source profile installation failed"));return; }
            UNiagaraNodeFunctionCall* Update=nullptr;
            if (ExactTriangles)
            {
                System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_LiquidBodyReview")).ToString());
                if (!LoadRegisteredContact(System)) return;
            }
            if (GridHalo)
            {
                // Keep the 21m physical exchange/retirement faces fixed. Put
                // the inherited two-cell EMPTY border outside those faces,
                // preserving dx=2100/64 cm and the prescribed source volume.
                System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                    TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_LiquidBodyReview")).ToString());
                FString AllocationError;
                if (!RaftSimInstallLiquidGridAllocation(System,FIntVector(68,68,24),FVector3f(2231.25f,2231.25f,800.f),AllocationError))
                { UE_LOG(LogTemp,Error,TEXT("Coupled halo allocation failed: %s"),*AllocationError);return; }
            }
            if (DrivenBoundary)
            {
                if (!LoadGridBoundary(System,VectorBoundary)) return;
                System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                    TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_LiquidBodyReview")).ToString());
            }
            TSet<UNiagaraGraph*> Graphs;
            for (auto& Handle:System->GetEmitterHandles())
                if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
                    if (auto* Data=Handle.GetInstance().GetEmitterData())
                    {
                        TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                        for (auto* Script:Scripts)
                            if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
                    }
            int32 Rewired=0;
            if (!InstallParticleTerrainProjection(System,Graphs,Private,ExactTriangles,false,Update,Rewired))
            { UE_LOG(LogTemp,Error,TEXT("Momentum review: no verified solid selector/projection"));return; }
            if (GridFrame && !CorrectRotatedParticleTransfer(System,Graphs,CompleteGather,CenteredTransfer)) return;
            if (OpenSides && !CorrectRiverBoundaryAxes(System,PicFlipRatio)) return;
            if (WetStart && !InstallHydraulicInitialState(System,Graphs)) return;
            if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidAffineTransfer")))
            {
                if (!CenteredTransfer || !RaftSimAffineTransfer::Install(System,Graphs,Update,DuplicateTypedMapRead))
                { UE_LOG(LogTemp,Error,TEXT("Affine transfer installation failed"));return; }
                Update->MarkNodeRequiresSynchronization(TEXT("Affine grid-to-particle value/gradient"),true);
            }
            if (ExactTriangles && !InstallRegisteredPressureBoundary(System,Graphs,DrivenBoundary,OutletStage,VectorBoundary))
            { UE_LOG(LogTemp,Error,TEXT("Registered boundary installation failed; outlet stage=%d"),OutletStage);return; }
            if (Compatible)
            {
                if (!RaftSimCompatibleProjection::Install(System,Graphs,DuplicateTypedMapRead,OutletStage))
                { UE_LOG(LogTemp,Error,TEXT("Compatible projection installation failed; outlet stage=%d"),OutletStage);return; }
                System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                    TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_CompatibleProjection_LiquidBodyReview")).ToString());
            }
            if(OutletStage) System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_CompatibleProjection_OutletStage_LiquidBodyReview")).ToString());
            if(CenteredTransfer) System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_CompatibleProjection_OutletStage_CenteredTransfer_LiquidBodyReview")).ToString());
            if(VectorBoundary) System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_CompatibleProjection_OutletStage_CenteredTransfer_VectorBoundary_LiquidBodyReview")).ToString());
            if(Foam)
            {
                if (!RaftSimLiquidFoam::Install(System,Graphs,DuplicateTypedMapRead,!SurfaceFoam)) return;
                System->Rename(*MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                    TEXT("SouthForkLiquidTerrainMomentumReview_Private_GridFrame_CompleteGather_OpenSides_WetStart_ExactTriangles_GridHalo_DrivenBoundary_CompatibleProjection_OutletStage_CenteredTransfer_VectorBoundary_Foam_LiquidBodyReview")).ToString());
            }
            System->RequestCompile(true);
            // Resolve graph compilation before collecting GPU resources to wait
            // on: the graph compile can replace the inherited shader resource.
            System->WaitForCompilationComplete(false,false);
            UE_LOG(LogTemp,Display,TEXT("Momentum graph compilation finished; waiting for current GPU shaders"));
            System->WaitForCompilationComplete(true,false);
            if (!System->IsReadyToRun()) { UE_LOG(LogTemp,Error,TEXT("Momentum review compile failed"));return; }
            // VM translation readiness alone does not prove GPU shader success.
            for (const auto& Handle:System->GetEmitterHandles())
                if (Handle.GetIsEnabled())
                if (const auto* Data=Handle.GetInstance().GetEmitterData())
                {
                    TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                    for (const auto* Script:Scripts)
                        if (Script->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript && !Script->DidScriptCompilationSucceed(true))
                        { UE_LOG(LogTemp,Error,TEXT("Momentum review GPU compilation failed: %s"),*Script->GetPathName());return; }
                }
            It->SetAsset(System);
            UE_LOG(LogTemp,Display,TEXT("Momentum review installed; solid selectors=%d; grid-frame-correct=%d; no assets saved, physical acceptance pending"),Rewired,GridFrame);
            return;
        }
    }));
}

bool RaftSimInstallRegionalLiquidContact(UNiagaraSystem* System,const RaftSimLiquidRegionalState::FState& Region,
    const TSharedPtr<FJsonObject>& Contact,FString& Error,const RaftSimLiquidParentExterior::FProfile* Exterior)
{
    Error=TEXT("Regional contact requires an unused transient regional allocation and canonical v3 page");
    FString Schema;TArray<FVector3f> Packed;double RegionId=-1;
    if (!System || System->GetOutermost()!=GetTransientPackage() || !Contact.IsValid() ||
        !Contact->TryGetStringField(TEXT("schema"),Schema) || Schema!=TEXT("raftsim.registered_liquid_contact.v3") ||
        !Contact->TryGetNumberField(TEXT("region_id"),RegionId) || RegionId!=Region.Id ||
        !RaftSimLiquidContactProfile::Decode(Contact,Packed)) return false;
    if (Exterior && !Exterior->Matches(Region)) { Error=TEXT("Parent exterior table does not match this validated regional owner");return false; }
    for (TObjectIterator<UNiagaraComponent> It;It;++It) if (It->GetAsset()==System) return false;
    auto& Store=System->GetExposedParameters();
    if (Store.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.River Region World Origin")))==INDEX_NONE ||
        Store.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells")))==INDEX_NONE) return false;
    if (Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.River Region World Origin")))!=
            FVector3f(RaftSimLiquidRegionalState::FCanonicalFrame::WorldPosition(Region.Frame.Origin)) ||
        Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells")))!=
            FVector3f(Region.ComputationalCells)) return false;
    TSet<UNiagaraGraph*> Graphs;
    for (const auto& Handle:System->GetEmitterHandles())
        if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
            if (auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (auto* Script:Scripts) if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
            }
    auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
    for (const auto P:Packed) { Array->FloatData.Add(FVector(P));Array->InternalFloatData.Add(P); }
    const FNiagaraVariable Variable(FNiagaraTypeDefinition(Array->GetClass()),TEXT("User.River Contact Triangles"));
    Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    if (Exterior)
    {
        auto* Faces=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
        for (const auto P:Exterior->Packed()) { Faces->FloatData.Add(FVector(P));Faces->InternalFloatData.Add(P); }
        const FNiagaraVariable FaceVariable(FNiagaraTypeDefinition(Faces->GetClass()),TEXT("User.River Parent Exterior"));
        Store.AddParameter(FaceVariable);Store.SetDataInterface(Faces,FaceVariable);
        if (!CorrectRiverBoundaryAxes(System)) { Error=TEXT("Regional exterior numerical boundary controls failed");return false; }
    }
    UNiagaraNodeFunctionCall* Update=nullptr;int32 Rewired=0;
    if (!InstallRegionalParticleNeighbors(System,Graphs) || !InstallParticleTerrainProjection(System,Graphs,true,true,true,Update,Rewired,Exterior!=nullptr) ||
        !CorrectRotatedParticleTransfer(System,Graphs,true,true,&Region) ||
        !InstallRegisteredPressureBoundary(System,Graphs,Exterior!=nullptr,Exterior!=nullptr,Exterior!=nullptr,true,Exterior!=nullptr))
    { Error=TEXT("Regional canonical contact/transfer graph installation failed");return false; }
    // The source template's stand-in solid-cell kill is not terrain contact.
    // The exact projection owns contact; never delete primary mass on impact.
    int32 Kills=0,VolumeKills=0;
    for (auto* Graph:Graphs) for (const auto& Node:Graph->Nodes)
    {
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript && Call->FunctionScript->GetName()==TEXT("KillParticlesInVolume"))
        { FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Call,false);++VolumeKills; }
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->GetFunctionName()==TEXT("KillParticles") &&
            Call->FunctionScript && Call->FunctionScript->GetName()==TEXT("KillParticles"))
        { FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Call,false);++Kills; }
    }
    // The inherited 21m fixture box would delete valid regional particles.
    // Regional ownership/outflow handling must account for them explicitly.
    if (Kills!=1 || VolumeKills!=1) { Error=TEXT("Expected one inherited solid and one fixture-volume rejection");return false; }
    Error.Reset();return true;
}

bool RaftSimInstallRegionalLiquidProjection(UNiagaraSystem* System,
    const RaftSimLiquidRegionalState::FParent& Parent,const RaftSimLiquidRegionalState::FState& Region,FString& Error)
{
    RaftSimLiquidRegionalProjection::FLayout Layout;
    if (!RaftSimLiquidRegionalProjection::Build(Parent,Region,Layout,Error)) return false;
    Error=TEXT("Regional projection requires an unused matching allocated/contact-bound clone");
    if (!System || System->GetOutermost()!=GetTransientPackage()) return false;
    for (TObjectIterator<UNiagaraComponent> It;It;++It) if (It->GetAsset()==System) return false;
    const auto& Store=System->GetExposedParameters();
    const FNiagaraVariable Allocation(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells"));
    const FNiagaraVariable Origin(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.River Region World Origin"));
    const FNiagaraVariable Extent(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents"));
    if (Store.IndexOf(Allocation)==INDEX_NONE || Store.IndexOf(Origin)==INDEX_NONE || Store.IndexOf(Extent)==INDEX_NONE ||
        Store.GetParameterValue<FVector3f>(Allocation)!=FVector3f(Region.ComputationalCells) ||
        Store.GetParameterValue<FVector3f>(Extent)!=FVector3f(Region.Extent) ||
        Store.GetParameterValue<FVector3f>(Origin)!=FVector3f(RaftSimLiquidRegionalState::FCanonicalFrame::WorldPosition(Region.Frame.Origin))) return false;
    TSet<UNiagaraGraph*> Graphs;int32 Contacts=0;
    for (const auto& Handle:System->GetEmitterHandles())
        if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
            if (auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (auto* Script:Scripts) if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
            }
    for (auto* Graph:Graphs) for (const auto& Node:Graph->Nodes)
        if (const auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
            Call->FunctionScript->GetName()==TEXT("RegisteredTrianglePressureBoundary")) ++Contacts;
    if (Contacts!=1) return false;
    const FNiagaraVariable ExteriorVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Parent Exterior"));
    const bool HasExterior=Store.IndexOf(ExteriorVariable)!=INDEX_NONE;
    if (HasExterior)
    {
        const auto* Faces=Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(ExteriorVariable));
        if (!Faces || Faces->InternalFloatData.Num()!=8+4*(Parent.Cells.X+Parent.Cells.Y) ||
            Faces->InternalFloatData[0]!=FVector3f(Parent.Frame.AxisX) || Faces->InternalFloatData[1]!=FVector3f(Parent.Frame.AxisY) ||
            Faces->InternalFloatData[2]!=FVector3f(Parent.Frame.Origin) || Faces->InternalFloatData[4]!=FVector3f(Parent.Spacing) ||
            Faces->InternalFloatData[5]!=FVector3f(Parent.Cells))
        { Error=TEXT("Projection parent does not match installed exterior table");return false; }
    }
    if (!RaftSimCompatibleProjection::Install(System,Graphs,DuplicateTypedMapRead,HasExterior,&Layout))
    { Error=TEXT("Regional compatible pressure graph installation failed");return false; }
    Error.Reset();return true;
}
