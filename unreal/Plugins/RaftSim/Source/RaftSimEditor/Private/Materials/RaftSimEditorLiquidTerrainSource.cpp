#include "AssetRegistry/AssetRegistryModule.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeAssignment.h"
#include "NiagaraNodeOutput.h"
#include "NiagaraScriptVariable.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "NiagaraDataInterfaceRigidMeshCollisionQuery.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "UObject/SavePackage.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"

namespace
{
void CreateTerrainLiquid()
{
    const FString Destination=TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview");
    if (FPackageName::DoesPackageExist(Destination))
    { UE_LOG(LogTemp,Error,TEXT("Refusing to overwrite terrain liquid review"));return; }
    FString Text;
    const FString Profile=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/
        TEXT("SourceArt/RaftSim/SouthForkLiquidWindow20260908/native_source_profile.json"));
    TSharedPtr<FJsonObject> Json;
    if (!FFileHelper::LoadFileToString(Text,*Profile) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json) || !Json.IsValid() ||
        Json->GetStringField(TEXT("schema"))!=TEXT("raftsim.native_face_liquid_source.v1"))
    { UE_LOG(LogTemp,Error,TEXT("Missing native-face source profile"));return; }
    auto* Base=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelBoundedReview.NS_LiquidChannelBoundedReview"));
    auto* SelectVector=LoadObject<UNiagaraScript>(nullptr,
        TEXT("/Niagara/DynamicInputs/Arrays/SelectVectorFromArray.SelectVectorFromArray"));
    auto* SelectWeighted=LoadObject<UNiagaraScript>(nullptr,
        TEXT("/Niagara/DynamicInputs/Arrays/SelectIntFromWeightedDistributionArray.SelectIntFromWeightedDistributionArray"));
    auto* DistributionClass=LoadClass<UNiagaraDataInterface>(nullptr,
        TEXT("/Script/Niagara.NiagaraDataInterfaceArrayDistributionInt"));
    if (!Base || !SelectVector || !SelectWeighted || !DistributionClass)
    { UE_LOG(LogTemp,Error,TEXT("Missing terrain liquid dependencies"));return; }
    UPackage* Package=CreatePackage(*Destination);
    auto* System=DuplicateObject<UNiagaraSystem>(Base,Package,*FPackageName::GetLongPackageAssetName(Destination));
    System->SetFlags(RF_Public|RF_Standalone|RF_Transactional);
    auto& Store=System->GetExposedParameters();
    const auto& Positions=Json->GetArrayField(TEXT("positions_world_offset_cm"));
    const auto& Velocities=Json->GetArrayField(TEXT("velocities_world_cm_per_s"));
    const auto& Weights=Json->GetArrayField(TEXT("weights_m3_per_s"));
    if (Positions.IsEmpty() || Positions.Num()!=Velocities.Num() || Positions.Num()!=Weights.Num())
    { UE_LOG(LogTemp,Error,TEXT("Mismatched terrain source arrays"));return; }
    const auto AddVectorArray=[&](FName Name,const TArray<TSharedPtr<FJsonValue>>& Values)
    {
        FNiagaraVariable Variable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name);
        auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
        for (const auto& Value:Values)
        {
            const auto& V=Value->AsArray();
            const FVector Vector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());
            Array->FloatData.Add(Vector);Array->InternalFloatData.Add(FVector3f(Vector));
        }
        Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    };
    AddVectorArray(TEXT("User.River Source Positions"),Positions);
    AddVectorArray(TEXT("User.River Source Velocities"),Velocities);
    auto* Distribution=NewObject<UNiagaraDataInterface>(System,DistributionClass);
    auto* ArrayProperty=FindFProperty<FArrayProperty>(DistributionClass,TEXT("ArrayData"));
    auto* EntryProperty=ArrayProperty ? CastField<FStructProperty>(ArrayProperty->Inner) : nullptr;
    auto* ValueProperty=EntryProperty ? FindFProperty<FIntProperty>(EntryProperty->Struct,TEXT("Value")) : nullptr;
    auto* WeightProperty=EntryProperty ? FindFProperty<FFloatProperty>(EntryProperty->Struct,TEXT("Weight")) : nullptr;
    if (!ValueProperty || !WeightProperty)
    { UE_LOG(LogTemp,Error,TEXT("Unexpected weighted-distribution reflection schema"));return; }
    FScriptArrayHelper Entries(ArrayProperty,ArrayProperty->ContainerPtrToValuePtr<void>(Distribution));
    Entries.Resize(Weights.Num());
    for (int32 Index=0;Index<Weights.Num();++Index)
    {
        ValueProperty->SetPropertyValue_InContainer(Entries.GetRawPtr(Index),Index);
        WeightProperty->SetPropertyValue_InContainer(Entries.GetRawPtr(Index),static_cast<float>(Weights[Index]->AsNumber()));
    }
    // The public reflected property builds the engine's O(1) alias table.
    // No private Niagara header or custom shader implementation is required.
    FPropertyChangedEvent Changed(ArrayProperty);
    Distribution->PostEditChangeProperty(Changed);
    const FNiagaraVariable DistributionVariable(FNiagaraTypeDefinition(DistributionClass),TEXT("User.River Source Distribution"));
    Store.AddParameter(DistributionVariable);Store.SetDataInterface(Distribution,DistributionVariable);
    Store.SetParameterValue<FVector3f>(FVector3f(2100,2100,800),FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
    Store.SetParameterValue<float>(Json->GetNumberField(TEXT("requested_spawn_particles_per_second")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate")));
    Store.SetParameterValue<FVector3f>(FVector3f::ZeroVector,FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.Inlet Scale")));
    TArray<FNiagaraVariable> Variables;Store.GetParameters(Variables);
    TSet<FNiagaraVariableBase> Known;
    for (const auto& V:Variables) Known.Add(V);
    const FNiagaraVariable SampleIndex(FNiagaraTypeDefinition::GetIntDef(),TEXT("Particles.RiverSourceIndex"));
    Known.Add(SampleIndex);
    bool Valid=true;
    const auto Override=[&](UNiagaraNodeFunctionCall* Call,FName InputName)->UEdGraphPin*
    {
        auto* Input=Call->GetCalledGraph()->GetScriptVariable(InputName);
        if (!Input) { UE_LOG(LogTemp,Error,TEXT("Missing source input %s on %s"),*InputName.ToString(),*Call->GetFunctionName());Valid=false;return nullptr; }
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(InputName,FName(*Call->GetFunctionName()));
        // Remove old rapid constants just as the editor's linked-input path does.
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
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
            *Call,Alias,Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();return &Pin;
    };
    const auto Bind=[&](UNiagaraNodeFunctionCall* Call,FName InputName,FName Name)
    {
        if (auto* Pin=Override(Call,InputName))
        {
            const auto* Input=Call->GetCalledGraph()->GetScriptVariable(InputName);
            FNiagaraStackGraphUtilities::SetLinkedParameterValueForFunctionInput(*Pin,
                FNiagaraVariableBase(Input->Variable.GetType(),Name),Known);
            Call->MarkNodeRequiresSynchronization(TEXT("Spatial native-flux source binding"),true);
        }
    };
    const auto Literal=[&](UNiagaraNodeFunctionCall* Call,FName InputName,const FString& Value)
    {
        if (auto* Pin=Override(Call,InputName))
        {
            Pin->DefaultValue=Value;
            CastChecked<UNiagaraNode>(Pin->GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Terrain fluid boundary setting"),true);
        }
    };
    const auto Switch=[&](UNiagaraNodeFunctionCall* Call,FName Name,const TCHAR* EnumPath,const TCHAR* Display)
    {
        auto* Pin=Call->FindPin(Name,EGPD_Input);
        auto* Enum=LoadObject<UEnum>(nullptr,EnumPath);
        bool Found=false;
        if (Pin && Enum)
            for (int32 Index=0;Index<Enum->NumEnums();++Index)
                if (Enum->GetDisplayNameTextByIndex(Index).ToString()==Display)
                { Pin->DefaultValue=Enum->GetNameStringByIndex(Index);Found=true;break; }
        if (!Found) { UE_LOG(LogTemp,Error,TEXT("Missing spatial source switch %s"),*Name.ToString());Valid=false; }
        Call->MarkNodeRequiresSynchronization(TEXT("Explicit spatial source selection mode"),true);
    };
    UNiagaraNodeOutput* SpawnOutput=nullptr;
    for (auto& Handle:System->GetEmitterHandles())
    {
        auto* Data=Handle.GetInstance().GetEmitterData();
        if (!Data || !Handle.GetName().ToString().Contains(TEXT("FluidControl"))) continue;
        Data->RemoveParent();
        TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
        for (auto* Script:Scripts)
            if (Script && Script->GetUsage()==ENiagaraScriptUsage::ParticleSpawnScript)
                if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource()))
                    for (const auto& Node:Source->NodeGraph->Nodes)
                        if (auto* Output=Cast<UNiagaraNodeOutput>(Node))
                            if (Output->GetUsage()==ENiagaraScriptUsage::ParticleSpawnScript) SpawnOutput=Output;
    }
    if (!SpawnOutput) { UE_LOG(LogTemp,Error,TEXT("Missing terrain particle spawn stack"));return; }
    auto* Assignment=FNiagaraStackGraphUtilities::AddParameterModuleToStack({SampleIndex},*SpawnOutput,0,{TEXT("0")});
    if (auto* Pin=Override(Assignment,TEXT("Module.Particles.RiverSourceIndex")))
    {
        UNiagaraNodeFunctionCall* Weighted=nullptr;
        FNiagaraStackGraphUtilities::SetDynamicInputForFunctionInput(*Pin,SelectWeighted,Weighted);
        Bind(Weighted,TEXT("Module.Weighted Distribution Int Array"),TEXT("User.River Source Distribution"));
    }
    TArray<UNiagaraNodeFunctionCall*> Calls;
    TArray<UNiagaraNodeFunctionCall*> SpawnModules;
    // Follow only the active spawn parameter-map chain. Nested copied scratch
    // graphs can contain identically named modules that are not source culls.
    TSet<UEdGraphNode*> Visited;
    UEdGraphNode* Cursor=SpawnOutput;
    while (Cursor && !Visited.Contains(Cursor))
    {
        Visited.Add(Cursor);
        if (auto* Module=Cast<UNiagaraNodeFunctionCall>(Cursor)) SpawnModules.Add(Module);
        UEdGraphNode* Previous=nullptr;
        for (auto* Pin:Cursor->Pins)
            if (Pin->Direction==EGPD_Input &&
                Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() &&
                Pin->LinkedTo.Num()==1)
            { Previous=Pin->LinkedTo[0]->GetOwningNode();break; }
        Cursor=Previous;
    }
    ForEachObjectWithOuter(System,[&](UObject* Object)
    { if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object)) Calls.Add(Call); },EGetObjectsFlags::IncludeNestedObjects);
    int32 SourceBindings=0,Retirement=0,MeshFields=0,RemovedSourceCull=0;
    for (auto* Call:Calls)
    {
        const FString Name=Call->FunctionScript ? Call->FunctionScript->GetName() : FString();
        FName Target,Array;
        if (Name==TEXT("SphereLocation"))
        { Target=TEXT("Module.Offset");Array=TEXT("User.River Source Positions"); }
        if (Call->GetFunctionName()==TEXT("SetVariables_9467D3964304D77DD887728C19B28EE9"))
        { Target=TEXT("Module.Particles.Velocity");Array=TEXT("User.River Source Velocities"); }
        if (!Target.IsNone())
        {
            if (auto* Pin=Override(Call,Target))
            {
                UNiagaraNodeFunctionCall* Select=nullptr;
                FNiagaraStackGraphUtilities::SetDynamicInputForFunctionInput(*Pin,SelectVector,Select);
                Switch(Select,TEXT("Array Sampling Mode"),TEXT("/Niagara/Enums/ENiagaraArraySamplingMode.ENiagaraArraySamplingMode"),TEXT("Direct Set"));
                Bind(Select,TEXT("Module.Vector Selection Array"),Array);
                Bind(Select,TEXT("Module.Direct Array Index"),SampleIndex.GetName());
                ++SourceBindings;
            }
        }
        if (Name==TEXT("Grid3D_FLIP_FLUID_CONTROLS"))
        {
            // Exposed controls map to X=Left/Right, Y=Back/Front, Z=Down/Up.
            for (const TCHAR* Face:{TEXT("Right"),TEXT("Left"),TEXT("Back"),TEXT("Up"),TEXT("Front")})
                Literal(Call,FName(*FString::Printf(TEXT("Module.Open Boundary %s"),Face)),TEXT("true"));
            Literal(Call,TEXT("Module.Open Boundary Down"),TEXT("false"));
        }
        if (Name==TEXT("Grid3D_ComputeBoundary"))
        { Literal(Call,TEXT("Module.Use Mesh Distance Fields"),TEXT("true"));++MeshFields; }
        if (Name==TEXT("KillParticlesInVolume"))
        {
            Literal(Call,TEXT("Module.Origin Offset"),TEXT("0.000,0.000,400.000"));
            Literal(Call,TEXT("Module.Box Size"),TEXT("2100.000,2100.000,800.000"));++Retirement;
        }
        if (SpawnModules.Contains(Call) && (Call->GetFunctionName()==TEXT("ScratchModule_01") || Call->GetFunctionName()==TEXT("KillParticles001")))
        {
            // Prescribed incoming mass must not disappear because the inlet
            // already contains water. Terrain/out-of-domain tests still apply.
            FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Call,false);++RemovedSourceCull;
        }
    }
    const FNiagaraVariable CollisionVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceRigidMeshCollisionQuery::StaticClass()),TEXT("User.Collide_Meshes"));
    auto* Collision=Cast<UNiagaraDataInterfaceRigidMeshCollisionQuery>(Store.GetDataInterface(CollisionVariable));
    if (Collision) Collision->ActorTags={FName(TEXT("RaftSimLiquidTerrain"))};
    if (!Valid || !Collision || SourceBindings!=2 || Retirement!=1 || MeshFields!=1 || RemovedSourceCull!=2)
    { UE_LOG(LogTemp,Error,TEXT("Terrain wiring invalid source=%d retirement=%d mesh=%d cull=%d"),SourceBindings,Retirement,MeshFields,RemovedSourceCull);return; }
    System->RequestCompile(true);System->WaitForCompilationComplete(false,false);
    if (!System->IsReadyToRun()) { UE_LOG(LogTemp,Error,TEXT("Terrain liquid compile failed"));return; }
    FAssetRegistryModule::AssetCreated(System);Package->MarkPackageDirty();
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    const bool Saved=UPackage::SavePackage(Package,System,
        *FPackageName::LongPackageNameToFilename(Destination,FPackageName::GetAssetPackageExtension()),Args);
    UE_LOG(LogTemp,Display,TEXT("Terrain liquid saved=%d source_points=%d nominal_Q=%.9f source_bindings=%d"),
        Saved,Positions.Num(),Json->GetNumberField(TEXT("total_inflow_m3_per_s")),SourceBindings);
}
FAutoConsoleCommand Command(TEXT("RaftSim.CreateSouthForkLiquidTerrain"),
    TEXT("Create a captured-terrain liquid review with spatial native-flux sources; never overwrite or promote."),
    FConsoleCommandDelegate::CreateStatic(&CreateTerrainLiquid));
}
