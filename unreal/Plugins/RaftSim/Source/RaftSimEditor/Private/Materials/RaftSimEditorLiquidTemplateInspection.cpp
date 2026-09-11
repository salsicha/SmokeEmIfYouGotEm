#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraSystem.h"
#include "NiagaraScript.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraRendererProperties.h"
#include "NiagaraSimulationStageBase.h"
#include "Materials/MaterialInterface.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"

namespace
{
TSharedRef<FJsonObject> InspectProperties(const UObject* Object)
{
    auto Result=MakeShared<FJsonObject>();
    for (TFieldIterator<FProperty> It(Object->GetClass());It;++It)
    {
        const FString Name=It->GetName();
        if (!Name.Contains(TEXT("Binding")) && !Name.Contains(TEXT("Visibility")) &&
            !Name.Contains(TEXT("Function")) && !Name.Contains(TEXT("Switch")) &&
            !Name.Contains(TEXT("InputParameter")) && !Name.Contains(TEXT("Hlsl"))) continue;
        FString Value;
        It->ExportTextItem_Direct(Value,It->ContainerPtrToValuePtr<void>(Object),nullptr,
                                 const_cast<UObject*>(Object),PPF_None);
        Result->SetStringField(Name,Value);
    }
    return Result;
}
void InspectLiquidTemplates(const TArray<FString>& Args)
{
    // Read-only engine-asset inspection. Plugin mounting is explicit on the
    // process command line; this adds no NiagaraFluids package dependency.
    if (Args.Num()!=1) { UE_LOG(LogTemp,Error,TEXT("Usage: RaftSim.InspectLiquidTemplates <output.json>"));return; }
    TArray<TSharedPtr<FJsonValue>> Systems;
    for (const TCHAR* Name : {TEXT("Grid3D_Flip_Splash"),TEXT("Grid3D_Flip_Hose"),
         TEXT("Grid3D_Flip_Pool"),TEXT("Grid3D_FLIP_Coupled")})
    {
        const FString Path=FString::Printf(TEXT("/NiagaraFluids/Templates/Liquid/3D/Systems/%s.%s"),Name,Name);
        auto Entry=MakeShared<FJsonObject>();Entry->SetStringField(TEXT("path"),Path);
        auto* System=LoadObject<UNiagaraSystem>(nullptr,*Path);
        Entry->SetBoolField(TEXT("loaded"),System!=nullptr);
        if (System)
        {
            System->WaitForCompilationComplete(false,false);
            Entry->SetBoolField(TEXT("ready"),System->IsReadyToRun());
            TArray<TSharedPtr<FJsonValue>> Parameters,Emitters;
            TArray<FNiagaraVariable> Variables;
            const auto& Store=System->GetExposedParameters();Store.GetParameters(Variables);
            for (const auto& V:Variables)
            {
                auto P=MakeShared<FJsonObject>();P->SetStringField(TEXT("name"),V.GetName().ToString());
                P->SetStringField(TEXT("type"),V.GetType().GetName());
                if (V.GetType()==FNiagaraTypeDefinition::GetFloatDef())P->SetNumberField(TEXT("value"),Store.GetParameterValue<float>(V));
                else if (V.GetType()==FNiagaraTypeDefinition::GetIntDef() || V.GetType()==FNiagaraTypeDefinition::GetBoolDef() || V.GetType().IsEnum())
                    P->SetNumberField(TEXT("value"),Store.GetParameterValue<int32>(V));
                else if (V.GetType()==FNiagaraTypeDefinition::GetVec3Def())
                {
                    const FVector3f Value=Store.GetParameterValue<FVector3f>(V);
                    P->SetArrayField(TEXT("value"),{MakeShared<FJsonValueNumber>(Value.X),MakeShared<FJsonValueNumber>(Value.Y),MakeShared<FJsonValueNumber>(Value.Z)});
                }
                Parameters.Add(MakeShared<FJsonValueObject>(P));
            }
            for (const auto& Handle:System->GetEmitterHandles())
            {
                auto E=MakeShared<FJsonObject>();E->SetStringField(TEXT("name"),Handle.GetName().ToString());
                E->SetBoolField(TEXT("enabled"),Handle.GetIsEnabled());
                if (const auto* Data=Handle.GetInstance().GetEmitterData())
                {
                    E->SetBoolField(TEXT("gpu_simulation"),Data->SimTarget==ENiagaraSimTarget::GPUComputeSim);
                    E->SetBoolField(TEXT("local_space"),Data->bLocalSpace);
                    TArray<TSharedPtr<FJsonValue>> Renderers,Stages,RapidParameters;
                    TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts);
                    for (const auto* Script:Scripts)
                    {
                        TArray<FNiagaraVariable> RapidVariables;
                        Script->RapidIterationParameters.GetParameters(RapidVariables);
                        for (const auto& V:RapidVariables)
                        {
                            auto P=MakeShared<FJsonObject>();
                            P->SetStringField(TEXT("script"),Script->GetName());
                            P->SetStringField(TEXT("name"),V.GetName().ToString());
                            P->SetStringField(TEXT("type"),V.GetType().GetName());
                            const auto& Values=Script->RapidIterationParameters;
                            const auto BaseType=V.GetType().RemoveStaticDef();
                            if (BaseType==FNiagaraTypeDefinition::GetFloatDef()) P->SetNumberField(TEXT("value"),Values.GetParameterValue<float>(V));
                            else if (BaseType==FNiagaraTypeDefinition::GetIntDef() || BaseType==FNiagaraTypeDefinition::GetBoolDef() || BaseType.IsEnum())
                                P->SetNumberField(TEXT("value"),Values.GetParameterValue<int32>(V));
                            else if (BaseType==FNiagaraTypeDefinition::GetVec3Def())
                            {
                                const FVector3f Value=Values.GetParameterValue<FVector3f>(V);
                                P->SetArrayField(TEXT("value"),{MakeShared<FJsonValueNumber>(Value.X),MakeShared<FJsonValueNumber>(Value.Y),MakeShared<FJsonValueNumber>(Value.Z)});
                            }
                            RapidParameters.Add(MakeShared<FJsonValueObject>(P));
                        }
                    }
                    E->SetArrayField(TEXT("rapid_iteration"),RapidParameters);
                    for (auto* Renderer:Data->GetRenderers())
                    {
                        auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("class"),Renderer->GetClass()->GetName());
                        R->SetBoolField(TEXT("enabled"),Renderer->GetIsEnabled());
                        R->SetObjectField(TEXT("bindings"),InspectProperties(Renderer));
                        TArray<UMaterialInterface*> Materials;Renderer->GetUsedMaterials(nullptr,Materials);
                        TArray<TSharedPtr<FJsonValue>> Paths;
                        for (auto* Material:Materials)Paths.Add(MakeShared<FJsonValueString>(Material ? Material->GetPathName() : TEXT("null")));
                        R->SetArrayField(TEXT("materials"),Paths);Renderers.Add(MakeShared<FJsonValueObject>(R));
                    }
                    for (auto* Stage:Data->GetSimulationStages())
                    {
                        auto S=MakeShared<FJsonObject>();S->SetStringField(TEXT("name"),Stage->SimulationStageName.ToString());
                        S->SetBoolField(TEXT("enabled"),Stage->bEnabled);Stages.Add(MakeShared<FJsonValueObject>(S));
                    }
                    E->SetArrayField(TEXT("renderers"),Renderers);E->SetArrayField(TEXT("stages"),Stages);
                }
                Emitters.Add(MakeShared<FJsonValueObject>(E));
            }
            Entry->SetArrayField(TEXT("parameters"),Parameters);Entry->SetArrayField(TEXT("emitters"),Emitters);
            // Inspect embedded graph defaults without changing any template or
            // loading private Niagara editor APIs. Linked values are reported
            // explicitly: a pin's default alone is not necessarily active.
            TArray<TSharedPtr<FJsonValue>> GraphNodes;
            const auto InspectNode=[&](UObject* Object)
            {
                auto* Node=Cast<UEdGraphNode>(Object);
                if (!Node) return;
                auto N=MakeShared<FJsonObject>();
                N->SetStringField(TEXT("path"),Node->GetPathName());
                N->SetStringField(TEXT("title"),Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
                N->SetObjectField(TEXT("properties"),InspectProperties(Node));
                TArray<TSharedPtr<FJsonValue>> Pins;
                for (const auto* Pin:Node->Pins)
                {
                    auto P=MakeShared<FJsonObject>();
                    P->SetStringField(TEXT("direction"),Pin->Direction==EGPD_Input ? TEXT("input") : TEXT("output"));
                    P->SetStringField(TEXT("name"),Pin->PinName.ToString());
                    P->SetStringField(TEXT("default"),Pin->DefaultValue);
                    TArray<TSharedPtr<FJsonValue>> Links;
                    for (const auto* Link:Pin->LinkedTo)
                        Links.Add(MakeShared<FJsonValueString>(Link->GetOwningNode()->GetNodeTitle(ENodeTitleType::FullTitle).ToString()+TEXT(".")+Link->PinName.ToString()));
                    P->SetArrayField(TEXT("links"),Links);Pins.Add(MakeShared<FJsonValueObject>(P));
                }
                N->SetArrayField(TEXT("inputs"),Pins);GraphNodes.Add(MakeShared<FJsonValueObject>(N));
            };
            ForEachObjectWithOuter(System,InspectNode,EGetObjectsFlags::IncludeNestedObjects);
            // This shared module computes the runtime renderer-enable values.
            for (const TCHAR* Module:{TEXT("Grid3D_FLIP_FLUID_CONTROLS"),TEXT("Grid3D_ComputeBoundary"),
                 TEXT("Grid3D_SetBoundaryGridValues"),TEXT("Grid3D_FLIP_Tank_Spawn"),TEXT("Grid3D_Flip_GridParticles")})
                if (auto* Shared=LoadObject<UNiagaraScript>(nullptr,*FString::Printf(
                    TEXT("/NiagaraFluids/Modules/Grid3D/%s.%s"),Module,Module)))
                    ForEachObjectWithOuter(Shared,InspectNode,EGetObjectsFlags::IncludeNestedObjects);
            Entry->SetArrayField(TEXT("embedded_function_nodes"),GraphNodes);
            GraphNodes.Empty();
            for (const TCHAR* Module:{TEXT("Grid3D_Secondary_EmissionPoints"),TEXT("Grid3D_Secondary_SpawnParticles"),TEXT("Grid3D_Secondary_UpdateParticles")})
                if (auto* Shared=LoadObject<UNiagaraScript>(nullptr,*FString::Printf(
                    TEXT("/NiagaraFluids/Modules/Grid3D/Secondary/%s.%s"),Module,Module)))
                    ForEachObjectWithOuter(Shared,InspectNode,EGetObjectsFlags::IncludeNestedObjects);
            Entry->SetArrayField(TEXT("secondary_module_nodes"),GraphNodes);
            if (auto* Kill=LoadObject<UNiagaraScript>(nullptr,TEXT("/Niagara/Modules/Update/Lifetime/KillParticlesInVolume.KillParticlesInVolume")))
            {
                GraphNodes.Empty();
                ForEachObjectWithOuter(Kill,InspectNode,EGetObjectsFlags::IncludeNestedObjects);
                Entry->SetArrayField(TEXT("retirement_module_nodes"),GraphNodes);
            }
            GraphNodes.Empty();
            for (const TCHAR* InputPath:{
                TEXT("/Niagara/DynamicInputs/Arrays/SelectVectorFromArray.SelectVectorFromArray"),
                TEXT("/Niagara/DynamicInputs/Arrays/SelectIntFromWeightedDistributionArray.SelectIntFromWeightedDistributionArray"),
                TEXT("/Niagara/DynamicInputs/Math/ModuloInt.ModuloInt")})
                if (auto* Input=LoadObject<UNiagaraScript>(nullptr,InputPath))
                    ForEachObjectWithOuter(Input,InspectNode,EGetObjectsFlags::IncludeNestedObjects);
            Entry->SetArrayField(TEXT("source_array_nodes"),GraphNodes);
        }
        Systems.Add(MakeShared<FJsonValueObject>(Entry));
    }
    auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("systems"),Systems);
    Report->SetBoolField(TEXT("packages_saved"),false);
    FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));
    if (!FFileHelper::SaveStringToFile(Text,*Args[0]))
    { UE_LOG(LogTemp,Error,TEXT("Liquid template report write failed")); }
    else
    { UE_LOG(LogTemp,Display,TEXT("Liquid template inspection saved: %s; no package changes"),*Args[0]); }
}
FAutoConsoleCommand Command(TEXT("RaftSim.InspectLiquidTemplates"),
    TEXT("Read current 3D FLIP template parameters/renderers/stages; requires -EnablePlugins=NiagaraFluids, saves no assets."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&InspectLiquidTemplates));
FAutoConsoleCommand ContactCommand(TEXT("RaftSim.InspectLiquidContactModules"),
    TEXT("Read-only focused inspection of engine particle contact modules."),
    FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
    {
        if (Args.Num()!=1 || FPaths::FileExists(Args[0])) return;
        auto Report=MakeShared<FJsonObject>();
        for (const TCHAR* ScriptPath:{
            TEXT("/NiagaraFluids/Modules/Grid3D/Grid3D_FLIP_ParticleUpdate.Grid3D_FLIP_ParticleUpdate"),
            TEXT("/Niagara/Modules/Collision/Collision.Collision"),
            TEXT("/Niagara/Modules/Collision/CollisionQueryAndResponse.CollisionQueryAndResponse"),
            TEXT("/NiagaraFluids/Modules/Grid3D/Grid3D_SetResolution.Grid3D_SetResolution"),
            TEXT("/NiagaraFluids/Modules/Grid3D/Grid3D_FLIP_Tank_Spawn.Grid3D_FLIP_Tank_Spawn"),
            TEXT("/NiagaraFluids/Modules/Grid3D/RasterizationGrid3D_SetResolution.RasterizationGrid3D_SetResolution"),
            TEXT("/Niagara/Modules/NeighborQuery/NeighborQuery_SetResolution.NeighborQuery_SetResolution"),
            TEXT("/NiagaraFluids/Modules/Particles/SolveCollisionConstraints.SolveCollisionConstraints"),
            TEXT("/NiagaraFluids/Modules/Particles/PBD_SolveCollisionConstraints.PBD_SolveCollisionConstraints")})
        {
            auto* Script=LoadObject<UNiagaraScript>(nullptr,ScriptPath);
            if (!Script) continue;
            TArray<TSharedPtr<FJsonValue>> Nodes;
            ForEachObjectWithOuter(Script,[&](UObject* Object)
            {
                if (auto* Node=Cast<UEdGraphNode>(Object))
                {
                    auto Entry=MakeShared<FJsonObject>();
                    Entry->SetStringField(TEXT("title"),Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
                    Entry->SetObjectField(TEXT("properties"),InspectProperties(Node));
                    TArray<TSharedPtr<FJsonValue>> Pins;
                    for (const auto* Pin:Node->Pins)
                    {
                        auto P=MakeShared<FJsonObject>();P->SetStringField(TEXT("name"),Pin->PinName.ToString());
                        P->SetStringField(TEXT("direction"),Pin->Direction==EGPD_Input ? TEXT("input") : TEXT("output"));
                        P->SetStringField(TEXT("default"),Pin->DefaultValue);
                        if (auto* Enum=Cast<UEnum>(Pin->PinType.PinSubCategoryObject.Get()))
                        {
                            auto Options=MakeShared<FJsonObject>();
                            for (int32 I=0;I<Enum->NumEnums();++I)
                                Options->SetStringField(Enum->GetNameStringByIndex(I),Enum->GetDisplayNameTextByIndex(I).ToString());
                            P->SetObjectField(TEXT("enum_options"),Options);
                        }
                        TArray<TSharedPtr<FJsonValue>> Links;
                        for (const auto* Link:Pin->LinkedTo) Links.Add(MakeShared<FJsonValueString>(
                            Link->GetOwningNode()->GetNodeTitle(ENodeTitleType::FullTitle).ToString()+TEXT(".")+Link->PinName.ToString()));
                        P->SetArrayField(TEXT("links"),Links);Pins.Add(MakeShared<FJsonValueObject>(P));
                    }
                    Entry->SetArrayField(TEXT("pins"),Pins);Nodes.Add(MakeShared<FJsonValueObject>(Entry));
                }
            },EGetObjectsFlags::IncludeNestedObjects);
            Report->SetArrayField(Script->GetName(),Nodes);
        }
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        FFileHelper::SaveStringToFile(Json,*Args[0]);
    }));
}
