#include "AssetRegistry/AssetRegistryModule.h"
#include "HAL/IConsoleManager.h"
#include "RaftSimLiquidSecondarySurface.h"
#include "Misc/PackageName.h"
#include "NiagaraSystem.h"
#include "NiagaraScript.h"
#include "NiagaraComponent.h"
#include "NiagaraDataInterfaceRigidMeshCollisionQuery.h"
#include "NiagaraSimCacheFunctionLibrary.h"
#include "Misc/FileHelper.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraScriptVariable.h"
#include "NiagaraScriptSource.h"
#include "NiagaraNodeOutput.h"
#include "NiagaraRendererProperties.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "UObject/UObjectHash.h"
#include "UObject/UObjectIterator.h"
#include "EngineUtils.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"

namespace
{
void CreateLiquidFixture(const TArray<FString>& Args)
{
    // Isolated review asset only. No game map, production material, or engine
    // template is edited; NiagaraFluids must be mounted for this process.
    const bool BoundedReview=Args.Num()==1 && Args[0]==TEXT("bounded");
    const bool ChannelReview=BoundedReview || (Args.Num()==1 && Args[0]==TEXT("channel"));
    const bool CollisionReview=ChannelReview || (Args.Num()==1 && Args[0]==TEXT("collision"));
    const FString Destination=BoundedReview
        ? TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelBoundedReview") : ChannelReview
        ? TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelOwnedReview") : CollisionReview
        ? TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodyCollisionReview")
        : TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodySDFReview");
    if ((!Args.IsEmpty() && !CollisionReview) || FPackageName::DoesPackageExist(Destination))
    {
        UE_LOG(LogTemp,Error,TEXT("Liquid fixture accepts optional collision/channel and refuses an existing destination"));return;
    }
    auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/NiagaraFluids/Templates/Liquid/3D/Systems/Grid3D_Flip_Hose.Grid3D_Flip_Hose"));
    auto* MethodEnum=LoadObject<UEnum>(nullptr,TEXT("/NiagaraFluids/Enums/ENiagaraFLIPRenderingMethod.ENiagaraFLIPRenderingMethod"));
    if (!Source || !MethodEnum) { UE_LOG(LogTemp,Error,TEXT("Missing engine liquid fixture dependencies"));return; }
    FString SdfEnumName;
    for (int32 Index=0;Index<MethodEnum->NumEnums();++Index)
        if (MethodEnum->GetDisplayNameTextByIndex(Index).ToString()==TEXT("Direct SDF"))
            SdfEnumName=MethodEnum->GetNameStringByIndex(Index);
    if (SdfEnumName.IsEmpty()) { UE_LOG(LogTemp,Error,TEXT("Direct SDF enum entry not found"));return; }

    UPackage* Package=CreatePackage(*Destination);
    auto* System=DuplicateObject<UNiagaraSystem>(Source,Package,*FPackageName::GetLongPackageAssetName(Destination));
    System->SetFlags(RF_Public|RF_Standalone|RF_Transactional);
    if (ChannelReview)
        for (auto& Handle:System->GetEmitterHandles())
            if (auto* Data=Handle.GetInstance().GetEmitterData()) Data->RemoveParent();
    int32 RemovedRapidValues=0;
    const auto RemoveCachedInput=[&](const FString& Alias)
    {
        // Match the editor's linked-input workflow: stale rapid-iteration
        // constants must not override the new graph bindings. Include owned
        // emitter/system scripts, not only compilable particle scripts.
        ForEachObjectWithOuter(System,[&](UObject* Object)
        {
            if (auto* Script=Cast<UNiagaraScript>(Object))
            {
                TArray<FNiagaraVariable> Variables;Script->RapidIterationParameters.GetParameters(Variables);
                for (const auto& Variable:Variables)
                    if (Variable.GetName().ToString().EndsWith(TEXT(".")+Alias))
                    { Script->RapidIterationParameters.RemoveParameter(Variable);++RemovedRapidValues; }
            }
        },EGetObjectsFlags::IncludeNestedObjects);
    };
    TArray<UNiagaraNodeFunctionCall*> Controls;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object))
            if (Call->FunctionScript && Call->FunctionScript->GetPathName()==TEXT("/NiagaraFluids/Modules/Grid3D/Grid3D_FLIP_FLUID_CONTROLS.Grid3D_FLIP_FLUID_CONTROLS"))
                Controls.Add(Call);
    },EGetObjectsFlags::IncludeNestedObjects);
    int32 Overrides=0;
    for (auto* Call:Controls)
    {
        auto* Input=Call->GetCalledGraph()->GetScriptVariable(FName(TEXT("Module.Rendering Method")));
        if (!Input || !Input->Variable.GetType().IsEnum()) continue;
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
            FName(TEXT("Module.Rendering Method")),FName(*Call->GetFunctionName()));
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
            *Call,Alias,Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=SdfEnumName;
        Call->MarkNodeRequiresSynchronization(TEXT("Explicit review liquid rendering method"),true);++Overrides;
        if (ChannelReview)
        {
            // Current template binds Right to +X, Left to -X, Up to +Z.
            // Keep the upstream wall behind the source and open the outlet.
            for (const auto& Setting:TArray<TPair<FName,FString>>{
                {TEXT("Module.Open Boundary Right"),TEXT("true")},
                {TEXT("Module.Open Boundary Left"),TEXT("false")},
                {TEXT("Module.Open Boundary Up"),TEXT("true")},
                {TEXT("Module.Open Boundary Down"),TEXT("false")},
                {TEXT("Module.Open Boundary Front"),TEXT("false")},
                {TEXT("Module.Open Boundary Back"),TEXT("false")}})
            {
                auto* BoundaryInput=Call->GetCalledGraph()->GetScriptVariable(Setting.Key);
                if (!BoundaryInput) { UE_LOG(LogTemp,Error,TEXT("Missing open-boundary input"));return; }
                const auto BoundaryAlias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
                    Setting.Key,FName(*Call->GetFunctionName()));
                auto& BoundaryPin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
                    *Call,BoundaryAlias,BoundaryInput->Variable.GetType(),BoundaryInput->Metadata.GetVariableGuid(),FGuid());
                BoundaryPin.BreakAllPinLinks();BoundaryPin.DefaultValue=Setting.Value;
                CastChecked<UNiagaraNode>(BoundaryPin.GetOwningNode())->MarkNodeRequiresSynchronization(
                    TEXT("Channel boundary override pin default changed"),true);
                RemoveCachedInput(BoundaryAlias.GetParameterHandleString().ToString());
            }
            Call->MarkNodeRequiresSynchronization(TEXT("Explicit channel boundaries without stale rapid constants"),true);
        }
    }
    if (Overrides==0) { UE_LOG(LogTemp,Error,TEXT("No render-method override; fixture not saved"));return; }
    int32 CollisionOverrides=0;
    if (CollisionReview)
    {
        // Match explicitly tagged simple geometry, not a captured river bed.
        // Exclude distance fields to isolate the analytic primitive boundary.
        TArray<UNiagaraNodeFunctionCall*> Boundaries;
        ForEachObjectWithOuter(System,[&](UObject* Object)
        {
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object))
                if (Call->FunctionScript && Call->FunctionScript->GetName()==TEXT("Grid3D_ComputeBoundary"))
                    Boundaries.Add(Call);
        },EGetObjectsFlags::IncludeNestedObjects);
        for (auto* Call:Boundaries)
        {
            for (const auto& Setting: {TPair<FName,FString>(TEXT("Module.Use Mesh Collisions"),TEXT("true")),
                                      TPair<FName,FString>(TEXT("Module.Use Mesh Distance Fields"),TEXT("false"))})
            {
                auto* Input=Call->GetCalledGraph()->GetScriptVariable(Setting.Key);
                if (!Input) { UE_LOG(LogTemp,Error,TEXT("Missing collision module input %s"),*Setting.Key.ToString());return; }
                const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
                    Setting.Key,FName(*Call->GetFunctionName()));
                auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
                    *Call,Alias,Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
                Pin.BreakAllPinLinks();Pin.DefaultValue=Setting.Value;
                ++CollisionOverrides;
            }
            Call->MarkNodeRequiresSynchronization(TEXT("Explicit tagged primitive liquid collisions"),true);
        }
        const FNiagaraVariable CollisionVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceRigidMeshCollisionQuery::StaticClass()),TEXT("User.Collide_Meshes"));
        auto* Collision=Cast<UNiagaraDataInterfaceRigidMeshCollisionQuery>(System->GetExposedParameters().GetDataInterface(CollisionVariable));
        if (!Collision || Collision->GetOutermost()!=Package || CollisionOverrides==0)
        { UE_LOG(LogTemp,Error,TEXT("Missing project-owned liquid collision interface or graph override"));return; }
        Collision->ActorTags={FName(TEXT("RaftSimLiquidFixtureObstacle"))};
        Collision->ComponentTags.Empty();Collision->SourceActors.Empty();
        Collision->OnlyUseMoveable=false;Collision->UseComplexCollisions=false;
        Collision->MaxNumPrimitives=16;
    }
    int32 SdfRenderers=0;
    for (auto& Handle:System->GetEmitterHandles())
    {
        if (auto* Data=Handle.GetInstance().GetEmitterData())
        {
            for (auto* Renderer:Data->GetRenderers())
            {
                TArray<UMaterialInterface*> Materials;Renderer->GetUsedMaterials(nullptr,Materials);
                const bool IsSdf=Materials.ContainsByPredicate([](auto* Material)
                    { return Material && Material->GetName().Contains(TEXT("M_WaterSDF_Inst")); });
                Renderer->SetIsEnabled(IsSdf);
                if (IsSdf)
                {
                    // Deep duplication must own the SDF MIC. Its render-target
                    // bindings remain intact; no new broad water plane exists.
                    for (auto* Material:Materials)
                        if (Material && Material->GetOutermost()!=Package)
                        { UE_LOG(LogTemp,Error,TEXT("SDF material is not project-owned; refusing save"));return; }
                    ++SdfRenderers;
                }
            }
        }
    }
    auto& Store=System->GetExposedParameters();
    int32 SourceBindings=0;
    if (ChannelReview)
    {
        // Explicit runtime inputs are the future hydraulic coupling seam.
        // These controlled-test defaults are NOT measured river discharge.
        const auto AddVector=[&](FName Name,FVector3f Value)
        {
            FNiagaraVariable Variable(FNiagaraTypeDefinition::GetVec3Def(),Name);
            Store.AddParameter(Variable);Store.SetParameterValue(Value,Variable);
        };
        AddVector(TEXT("User.Inlet Velocity"),FVector3f(250,0,0));
        AddVector(TEXT("User.Inlet Position"),FVector3f(-135,0,60));
        AddVector(TEXT("User.Inlet Scale"),FVector3f(0.4f,2.8f,0.8f));
        FNiagaraVariable Rate(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate"));
        Store.AddParameter(Rate);Store.SetParameterValue<float>(20000,Rate);
        FNiagaraVariable Outlet(FNiagaraTypeDefinition::GetBoolDef(),TEXT("User.Open Outlet"));
        Store.AddParameter(Outlet);Store.SetParameterValue<FNiagaraBool>(FNiagaraBool(true),Outlet);
        TArray<FNiagaraVariable> UserVariables;Store.GetParameters(UserVariables);
        TSet<FNiagaraVariableBase> Known;
        for (const auto& Variable:UserVariables) Known.Add(Variable);
        bool BindingsValid=true;
        const auto Bind=[&](UNiagaraNodeFunctionCall* Call,FName InputName,FName UserName)
        {
            auto* Input=Call->GetCalledGraph()->GetScriptVariable(InputName);
            if (!Input) { UE_LOG(LogTemp,Error,TEXT("Missing inlet input %s on %s"),*InputName.ToString(),*Call->GetFunctionName());BindingsValid=false;return; }
            const FNiagaraVariableBase User(Input->Variable.GetType(),UserName);
            if (!Known.Contains(User)) { UE_LOG(LogTemp,Error,TEXT("Inlet parameter type mismatch %s"),*UserName.ToString());BindingsValid=false;return; }
            const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(InputName,FName(*Call->GetFunctionName()));
            auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
                *Call,Alias,Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
            Pin.BreakAllPinLinks();
            RemoveCachedInput(Alias.GetParameterHandleString().ToString());
            FNiagaraStackGraphUtilities::SetLinkedParameterValueForFunctionInput(Pin,User,Known);
            Call->MarkNodeRequiresSynchronization(TEXT("Runtime channel inlet parameters"),true);
            ++SourceBindings;
        };
        TArray<UNiagaraNodeFunctionCall*> Calls;
        ForEachObjectWithOuter(System,[&](UObject* Object)
        { if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object)) Calls.Add(Call); },EGetObjectsFlags::IncludeNestedObjects);
        int32 OutletBindings=0;
        for (auto* Call:Calls)
        {
            if (!Call->FunctionScript) continue;
            if (Call->FunctionScript->GetName()==TEXT("SphereLocation"))
            {
                Bind(Call,TEXT("Module.Offset"),TEXT("User.Inlet Position"));
                Bind(Call,TEXT("Module.Non Uniform Scale"),TEXT("User.Inlet Scale"));
            }
            if (Call->GetFunctionName()==TEXT("SpawnRate001"))
                Bind(Call,TEXT("Module.SpawnRate"),TEXT("User.Inlet Particle Rate"));
            if (Call->GetFunctionName()==TEXT("SetVariables_9467D3964304D77DD887728C19B28EE9"))
                Bind(Call,TEXT("Module.Particles.Velocity"),TEXT("User.Inlet Velocity"));
            if (Call->FunctionScript->GetName()==TEXT("Grid3D_ComputeBoundary") ||
                Call->FunctionScript->GetName()==TEXT("Grid3D_ComputeHighPrecisionBoundary"))
            {
                const int32 Before=SourceBindings;
                Bind(Call,TEXT("Module.Open Boundary +X"),TEXT("User.Open Outlet"));
                OutletBindings+=SourceBindings-Before;
            }
        }
        SourceBindings-=OutletBindings;
        if (!BindingsValid || SourceBindings!=4 || OutletBindings!=4)
        { UE_LOG(LogTemp,Error,TEXT("Expected four channel inlet bindings, found%d"),SourceBindings);return; }
        UE_LOG(LogTemp,Display,TEXT("Liquid channel direct outlet bindings=%d"),OutletBindings);
        // Start dry: the inherited source culls particles spawned inside
        // existing fluid. Initial tank filling is not a valid inlet test.
        Store.SetParameterValue<float>(0,FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Water Height")));
    }
    if (BoundedReview)
    {
        // This fixture has a fixed 400x400x500 cm domain with its floor at z=0.
        // Remove only particles that have left that domain. This is lifecycle
        // management, not a calibrated discharge or replacement for solid walls.
        auto* KillScript=LoadObject<UNiagaraScript>(nullptr,
            TEXT("/Niagara/Modules/Update/Lifetime/KillParticlesInVolume.KillParticlesInVolume"));
        auto* Shapes=LoadObject<UEnum>(nullptr,
            TEXT("/Niagara/Enums/ENiagaraKillVolumeOptions.ENiagaraKillVolumeOptions"));
        if (!KillScript || !Shapes) { UE_LOG(LogTemp,Error,TEXT("Missing retirement dependencies"));return; }
        FString BoxEnum;
        for (int32 Index=0;Index<Shapes->NumEnums();++Index)
            if (Shapes->GetDisplayNameTextByIndex(Index).ToString()==TEXT("Box")) BoxEnum=Shapes->GetNameStringByIndex(Index);
        int32 RetirementModules=0;
        for (auto& Handle:System->GetEmitterHandles())
        {
            if (!Handle.GetName().ToString().Contains(TEXT("FluidControl"))) continue;
            auto* Data=Handle.GetInstance().GetEmitterData();
            if (!Data) continue;
            TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
            for (auto* Script:Scripts)
            {
                if (!Script || Script->GetUsage()!=ENiagaraScriptUsage::ParticleUpdateScript) continue;
                auto* SourceGraph=Cast<UNiagaraScriptSource>(Script->GetLatestSource());
                UNiagaraNodeOutput* Output=nullptr;
                if (SourceGraph && SourceGraph->NodeGraph)
                    for (const auto& Node:SourceGraph->NodeGraph->Nodes)
                        if (auto* Candidate=Cast<UNiagaraNodeOutput>(Node))
                            if (Candidate->GetUsage()==ENiagaraScriptUsage::ParticleUpdateScript) Output=Candidate;
                if (!Output) { UE_LOG(LogTemp,Error,TEXT("No retirement update graph"));return; }
                auto* Call=FNiagaraStackGraphUtilities::AddScriptModuleToStack(KillScript,*Output,INDEX_NONE,TEXT("RetireOutsideChannel"));
                if (!Call || BoxEnum.IsEmpty()) { UE_LOG(LogTemp,Error,TEXT("Cannot add channel retirement"));return; }
                auto* ShapePin=Call->FindPin(TEXT("Kill Shape"),EGPD_Input);
                if (!ShapePin) { UE_LOG(LogTemp,Error,TEXT("Missing retirement shape switch"));return; }
                ShapePin->DefaultValue=BoxEnum;
                Call->MarkNodeRequiresSynchronization(TEXT("Channel retirement box switch"),true);
                for (const auto& Setting:TArray<TPair<FName,FString>>{
                    {TEXT("Module.Invert Volume"),TEXT("true")},
                    {TEXT("Module.Kill Volume Enabled"),TEXT("true")},
                    {TEXT("Module.Origin Offset"),TEXT("0.000,0.000,250.000")},
                    {TEXT("Module.Box Size"),TEXT("400.000,400.000,500.000")}})
                {
                    auto* Input=Call->GetCalledGraph()->GetScriptVariable(Setting.Key);
                    if (!Input) { UE_LOG(LogTemp,Error,TEXT("Missing retirement input %s"),*Setting.Key.ToString());return; }
                    const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(Setting.Key,FName(*Call->GetFunctionName()));
                    auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
                        *Call,Alias,Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
                    Pin.BreakAllPinLinks();Pin.DefaultValue=Setting.Value;
                    CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Bounded channel retirement"),true);
                    RemoveCachedInput(Alias.GetParameterHandleString().ToString());
                }
                ++RetirementModules;
            }
        }
        if (RetirementModules!=1) { UE_LOG(LogTemp,Error,TEXT("Expected one retirement module, found%d"),RetirementModules);return; }
    }
    Store.SetParameterValue<int32>(64,FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("User.Num Cells Max Axis")));
    Store.SetParameterValue<int32>(4,FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("User.Particles Per Cell")));
    Store.SetParameterValue<int32>(40,FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("User.Pressure Iterations")));
    Store.SetParameterValue<FNiagaraBool>(FNiagaraBool(false),FNiagaraVariable(FNiagaraTypeDefinition::GetBoolDef(),TEXT("User.Show Bounds")));
    System->RequestCompile(true);System->WaitForCompilationComplete(false,false);
    if (SdfRenderers!=1 || !System->IsReadyToRun())
    { UE_LOG(LogTemp,Error,TEXT("Liquid fixture not ready or SDF renderer count !=1; refusing save"));return; }
    FAssetRegistryModule::AssetCreated(System);Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;SaveArgs.TopLevelFlags=RF_Public|RF_Standalone;SaveArgs.SaveFlags=SAVE_NoError;
    const bool Saved=UPackage::SavePackage(Package,System,
        *FPackageName::LongPackageNameToFilename(Destination,FPackageName::GetAssetPackageExtension()),SaveArgs);
    UE_LOG(LogTemp,Display,TEXT("Liquid fixture saved=%d explicit_method=%s overrides=%d sdf_renderers=%d asset=%s"),
        Saved,*SdfEnumName,Overrides,SdfRenderers,*Destination);
    UE_LOG(LogTemp,Display,TEXT("Liquid fixture collision_review=%d collision_overrides=%d"),CollisionReview,CollisionOverrides);
    UE_LOG(LogTemp,Display,TEXT("Liquid fixture channel_review=%d source_bindings=%d"),ChannelReview,SourceBindings);
    UE_LOG(LogTemp,Display,TEXT("Liquid fixture removed_rapid_values=%d"),RemovedRapidValues);
}
FAutoConsoleCommand FixtureCommand(TEXT("RaftSim.CreateLiquidFixture"),
    TEXT("Create an isolated explicit-SDF liquid fixture, optional collision; refuses overwrite; requires NiagaraFluids."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&CreateLiquidFixture));
FAutoConsoleCommandWithWorldAndArgs DumpChannelCommand(TEXT("RaftSim.DumpLiquidChannelShaders"),
    TEXT("Dump the owned channel's compiled script translations for boundary/source inspection."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if ((Args.Num()!=1 && Args.Num()!=2) || (Args.Num()==2 && Args[1]!=TEXT("terrain") && Args[1]!=TEXT("active")) || IFileManager::Get().DirectoryExists(*Args[0])) return;
        UNiagaraSystem* System=nullptr;
        if (Args.Num()==2 && Args[1]==TEXT("active"))
        {
            int32 Count=0;
            for (TObjectIterator<UNiagaraComponent> It;It;++It)
                if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetName().Contains(TEXT("LiquidTerrainMomentumReview")))
                { System=It->GetAsset();++Count; }
            if (Count!=1) return;
        }
        else System=LoadObject<UNiagaraSystem>(nullptr,Args.Num()==2 ?
            TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview") :
            TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelOutletReview.NS_LiquidChannelOutletReview"));
        if (!System) return;
        System->RequestCompile(true);
        System->WaitForCompilationComplete(false,false);
        IFileManager::Get().MakeDirectory(*Args[0],true);
        TArray<UNiagaraScript*> Scripts={System->GetSystemSpawnScript(),System->GetSystemUpdateScript()};
        for (const auto& Handle:System->GetEmitterHandles())
            if (const auto* Data=Handle.GetInstance().GetEmitterData()) Data->GetScripts(Scripts,false);
        int32 Index=0,Nonempty=0;
        for (auto* Script:Scripts)
        {
            if (!Script) continue;
            const FString Stem=FString::Printf(TEXT("%02d_%s"),Index++,*Script->GetName());
            const auto& Data=Script->GetVMExecutableData();
            Nonempty+=!Data.LastHlslTranslation.IsEmpty() || !Data.LastHlslTranslationGPU.IsEmpty();
            FFileHelper::SaveStringToFile(Data.LastHlslTranslation,*FPaths::Combine(Args[0],Stem+TEXT(".hlsl")));
            FFileHelper::SaveStringToFile(Data.LastHlslTranslationGPU,*FPaths::Combine(Args[0],Stem+TEXT("_gpu.hlsl")));
        }
        UE_LOG(LogTemp,Display,TEXT("Dumped liquid channel translations for%d scripts, nonempty=%d"),Index,Nonempty);
    }));
FAutoConsoleCommandWithWorld TelemetryCommand(TEXT("RaftSim.LiquidFixtureTelemetry"),
    TEXT("Log actual isolated liquid age and data-interface initialization, not visual acceptance."),
    FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
    {
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            if (It->GetWorld()!=World || !It->GetAsset() ||
                !It->GetAsset()->GetPathName().Contains(TEXT("LiquidBodyReview"))) continue;
            if (const auto Controller=It->GetSystemInstanceController())
            {
                Controller->WaitForConcurrentTickAndFinalize();
                UE_LOG(LogTemp,Display,TEXT("LiquidFixture actual_age=%.6f interfaces_initialized=%d active=%d state=%d"),
                    Controller->GetAge(),Controller->GetAreDataInterfacesInitialized(),It->IsActive(),
                    static_cast<int32>(Controller->GetActualExecutionState()));
            }
        }
    }));
FAutoConsoleCommandWithWorld SolidLossControlCommand(TEXT("RaftSim.LiquidTerrainSolidLossControl"),
    TEXT("UNSAVED diagnostic only: retain solid-classified particles to isolate mass loss; never a collision fix."),
    FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
    {
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            if (It->GetWorld()!=World || !It->GetAsset() ||
                It->GetAsset()->GetName()!=TEXT("NS_SouthForkLiquidTerrainReview")) continue;
            auto* Control=DuplicateObject<UNiagaraSystem>(It->GetAsset(),GetTransientPackage(),
                TEXT("LiquidBodyReviewSouthForkLiquidTerrainSolidLossControl"));
            TSet<UNiagaraGraph*> ActiveFluidGraphs;
            for (const auto& Handle:Control->GetEmitterHandles())
                if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
                    if (const auto* Data=Handle.GetInstance().GetEmitterData())
                    {
                        TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                        for (auto* Script:Scripts)
                            if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource()))
                                ActiveFluidGraphs.Add(Source->NodeGraph);
                    }
            int32 Rejections=0;
            ForEachObjectWithOuter(Control,[&](UObject* Object)
            {
                if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object))
                    if (ActiveFluidGraphs.Contains(Call->GetNiagaraGraph()) && Call->GetFunctionName()==TEXT("KillParticles") && Call->FunctionScript &&
                        Call->FunctionScript->GetName()==TEXT("KillParticles"))
                    {
                        FNiagaraStackGraphUtilities::SetModuleIsEnabled(*Call,false);
                        ++Rejections;
                    }
            },EGetObjectsFlags::IncludeNestedObjects);
            if (Rejections!=1)
            { UE_LOG(LogTemp,Error,TEXT("Ambiguous solid-loss control modules=%d; unchanged"),Rejections);return; }
            Control->RequestCompile(true);Control->WaitForCompilationComplete(false,false);
            if (!Control->IsReadyToRun())
            { UE_LOG(LogTemp,Error,TEXT("Solid-loss diagnostic compilation failed"));return; }
            It->SetAsset(Control);
            UE_LOG(LogTemp,Display,TEXT("UNSAVED solid-loss diagnostic active; solid-classified particles retained, terrain pressure and escape retirement unchanged. NOT collision acceptance."));
            return;
        }
    }));
FAutoConsoleCommandWithWorldAndArgs ParticleReadbackCommand(TEXT("RaftSim.LiquidFixtureParticles"),
    TEXT("Read current GPU liquid particles to a diagnostic JSON; blocking, not for performance runs."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=1) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            if (It->GetWorld()!=World || !It->GetAsset() ||
                !It->GetAsset()->GetPathName().Contains(TEXT("LiquidBodyReview"))) continue;
            FNiagaraSimCacheCreateParameters Parameters;
            Parameters.bAllowDataInterfaceCaching=false;
            UNiagaraSimCache* Captured=nullptr;
            TStrongObjectPtr<UNiagaraSimCache> Cache(NewObject<UNiagaraSimCache>());
            if (!UNiagaraSimCacheFunctionLibrary::CaptureNiagaraSimCacheImmediate(Cache.Get(),Parameters,*It,Captured,false))
            { UE_LOG(LogTemp,Error,TEXT("Liquid GPU particle readback failed"));return; }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("asset"),It->GetAsset()->GetPathName());
            Report->SetBoolField(TEXT("blocking_gpu_readback"),true);
            const bool Terrain=It->GetAsset()->GetName().Contains(TEXT("SouthForkLiquidTerrain"));
            const FTransform Transform=It->GetComponentTransform();
            bool ExtentsValid=false;
            const FVector GridExtents=Terrain ? It->GetVariableVec3(TEXT("User.World Grid Extents"),ExtentsValid) : FVector(400,400,500);
            const bool GridHalo=It->GetAsset()->GetName().Contains(TEXT("_GridHalo_"));
            // Halo is numerical support, not a change to the physical exchange
            // or retirement region. Keep comparisons on the same native faces.
            const FVector Extents=GridHalo ? FVector(2100,2100,800) : GridExtents;
            if (Terrain && (!ExtentsValid || Extents.GetMin()<=0))
            { UE_LOG(LogTemp,Error,TEXT("Missing terrain liquid domain extents"));return; }
            UStaticMeshComponent* TerrainProbe=nullptr;
            int32 ProbeCount=0;
            if (Terrain)
                for (TActorIterator<AStaticMeshActor> Actor(World);Actor;++Actor)
                    if (Actor->ActorHasTag(TEXT("RaftSimLiquidTerrainProbe")))
                    { TerrainProbe=Actor->GetStaticMeshComponent();++ProbeCount; }
            if (Terrain && ProbeCount!=1)
            { UE_LOG(LogTemp,Error,TEXT("Terrain readback requires exactly one exact-bed probe actor"));return; }
            Report->SetBoolField(TEXT("captured_terrain_probe"),Terrain);
            Report->SetStringField(TEXT("domain_local_extents_cm"),Extents.ToString());
            Report->SetStringField(TEXT("computational_grid_extents_cm"),GridExtents.ToString());
            Report->SetStringField(TEXT("domain_transform"),Transform.ToString());
            Report->SetStringField(TEXT("component_bounds_origin_cm"),It->Bounds.Origin.ToString());
            Report->SetStringField(TEXT("component_bounds_extent_cm"),It->Bounds.BoxExtent.ToString());
            if (Terrain)
            {
                TArray<UMaterialInterface*> UsedMaterials;It->GetUsedMaterials(UsedMaterials);
                TArray<TSharedPtr<FJsonValue>> MaterialStates;
                for (auto* Material:UsedMaterials)
                {
                    if (!Material) continue;
                    auto M=MakeShared<FJsonObject>();M->SetStringField(TEXT("path"),Material->GetPathName());
                    auto Vectors=MakeShared<FJsonObject>();auto Scalars=MakeShared<FJsonObject>();
                    TArray<FMaterialParameterInfo> Infos;TArray<FGuid> Guids;
                    Material->GetAllVectorParameterInfo(Infos,Guids);
                    for (const auto& Info:Infos)
                    {
                        FLinearColor Value;
                        if (Material->GetVectorParameterValue(Info,Value)) Vectors->SetStringField(Info.Name.ToString(),Value.ToString());
                    }
                    Infos.Reset();Guids.Reset();Material->GetAllScalarParameterInfo(Infos,Guids);
                    for (const auto& Info:Infos)
                    {
                        float Value=0;
                        if (Material->GetScalarParameterValue(Info,Value)) Scalars->SetNumberField(Info.Name.ToString(),Value);
                    }
                    M->SetObjectField(TEXT("vectors"),Vectors);M->SetObjectField(TEXT("scalars"),Scalars);
                    auto Textures=MakeShared<FJsonObject>();
                    Infos.Reset();Guids.Reset();Material->GetAllTextureParameterInfo(Infos,Guids);
                    for (const auto& Info:Infos)
                    {
                        UTexture* Value=nullptr;
                        if (Material->GetTextureParameterValue(Info,Value) && Value)
                            Textures->SetStringField(Info.Name.ToString(),Value->GetPathName());
                    }
                    M->SetObjectField(TEXT("textures"),Textures);
                    MaterialStates.Add(MakeShared<FJsonValueObject>(M));
                }
                Report->SetArrayField(TEXT("runtime_materials"),MaterialStates);
                auto State=MakeShared<FJsonObject>();
                Cache->ForEachEmitterAttribute(INDEX_NONE,[&](const FNiagaraSimCacheVariable& Attribute)
                {
                    const FString Key=Attribute.Variable.GetName().ToString();
                    if (!Key.Contains(TEXT("WorldToUnit")) && !Key.Contains(TEXT("UnitToWorld")) &&
                        !Key.Contains(TEXT("GridCenter")) && !Key.EndsWith(TEXT("DeltaTime")) &&
                        !Key.Contains(TEXT("LocalToWorld")) && !Key.Contains(TEXT("WorldToLocal")) &&
                        !Key.Contains(TEXT("PIC")) && !Key.Contains(TEXT("Pressure")) &&
                        !Key.Contains(TEXT("Neighbor")) && !Key.Contains(TEXT("ParticlesPerCell")) &&
                        !Key.Contains(TEXT("SpawnOutputInfo")) && !Key.Contains(TEXT("TotalSpawnedParticles"))) return true;
                    TArray<float> Floats;TArray<FFloat16> Halfs;TArray<int32> Ints;
                    Cache->ReadAttribute(Floats,Halfs,Ints,Attribute.Variable.GetName(),NAME_None,0);
                    TArray<TSharedPtr<FJsonValue>> Values;
                    for (float Value:Floats) Values.Add(MakeShared<FJsonValueNumber>(Value));
                    for (int32 Value:Ints) Values.Add(MakeShared<FJsonValueNumber>(Value));
                    State->SetArrayField(Key,Values);
                    return true;
                });
                Report->SetObjectField(TEXT("captured_system_state"),State);
            }
            if (!Terrain) Report->SetStringField(TEXT("obstacle_centre_cm"),TEXT("X=0 Y=0 Z=100"));
            const auto InDomain=[&](const FVector& P)
            { return FMath::Abs(P.X)<=Extents.X*.5 && FMath::Abs(P.Y)<=Extents.Y*.5 && P.Z>=0 && P.Z<=Extents.Z; };
            TArray<TSharedPtr<FJsonValue>> Emitters;
            for (const FName Name:Cache->GetEmitterNames())
            {
                const bool Primary=Name==TEXT("Grid3D_FLIP_FluidControl_Emitter");
                TArray<FVector> Positions,Velocities;
                Cache->ReadPositionAttribute(Positions,TEXT("Position"),Name,true,0);
                Cache->ReadVectorAttribute(Velocities,TEXT("Velocity"),Name,0);
                TArray<int32> SourceIndices,UniqueIDs;
                if (Terrain && !Positions.IsEmpty())
                {
                    if (Primary) Cache->ReadIntAttribute(SourceIndices,TEXT("RiverSourceIndex"),Name,0);
                    else SourceIndices.Init(-1,Positions.Num()); // Secondary has no native-face source identity.
                    Cache->ReadIntAttribute(UniqueIDs,TEXT("UniqueID"),Name,0);
                }
                FBox Bounds(ForceInit);int32 Inside80=0,Inside60=0,Nonfinite=0;
                double MinimumRadius=DBL_MAX,SpeedSum=0;int32 FiniteSpeeds=0;
                for (const auto& Position:Positions)
                {
                    if (Position.ContainsNaN()) { ++Nonfinite;continue; }
                    Bounds+=Position;
                    const double Radius=(Position-FVector(0,0,100)).Length();
                    MinimumRadius=FMath::Min(MinimumRadius,Radius);
                    Inside80+=Radius<80;Inside60+=Radius<60;
                }
                for (const auto& Velocity:Velocities)
                    if (!Velocity.ContainsNaN()) { SpeedSum+=Velocity.Length();++FiniteSpeeds; }
                auto E=MakeShared<FJsonObject>();
                E->SetStringField(TEXT("emitter"),Name.ToString());
                E->SetNumberField(TEXT("position_count"),Positions.Num());
                E->SetNumberField(TEXT("velocity_count"),Velocities.Num());
                if(Terrain && Primary && FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidAffineTransfer")))
                {
                    TArray<FVector> Ax,Ay,Az,SamplePositions,SampleUnits;
                    Cache->ReadVectorAttribute(Ax,TEXT("RiverAffineX"),Name,0);
                    Cache->ReadVectorAttribute(Ay,TEXT("RiverAffineY"),Name,0);
                    Cache->ReadVectorAttribute(Az,TEXT("RiverAffineZ"),Name,0);
                    Cache->ReadPositionAttribute(SamplePositions,TEXT("RiverAffineSamplePosition"),Name,true,0);
                    Cache->ReadVectorAttribute(SampleUnits,TEXT("RiverAffineSampleUnit"),Name,0);
                    if(Ax.Num()!=Positions.Num() || Ay.Num()!=Positions.Num() || Az.Num()!=Positions.Num() || SamplePositions.Num()!=Positions.Num() || SampleUnits.Num()!=Positions.Num() || UniqueIDs.Num()!=Positions.Num())
                    { UE_LOG(LogTemp,Error,TEXT("Actual GPU affine state missing: positions=%d columns=%d/%d/%d samples=%d"),Positions.Num(),Ax.Num(),Ay.Num(),Az.Num(),SamplePositions.Num());return; }
                    TArray<TSharedPtr<FJsonValue>> Rows;
                    for(int32 I=0;I<Positions.Num();++I)
                    {
                        if(Ax[I].ContainsNaN() || Ay[I].ContainsNaN() || Az[I].ContainsNaN() || SamplePositions[I].ContainsNaN() || SampleUnits[I].ContainsNaN())
                        { UE_LOG(LogTemp,Error,TEXT("Nonfinite actual GPU affine state"));return; }
                        const auto X=Transform.InverseTransformVectorNoScale(Ax[I]);
                        const auto Y=Transform.InverseTransformVectorNoScale(Ay[I]);
                        const auto Z=Transform.InverseTransformVectorNoScale(Az[I]);
                        const auto P=Transform.InverseTransformPosition(SamplePositions[I]);
                        TArray<TSharedPtr<FJsonValue>> Row;
                        for(double V:{double(UniqueIDs[I]),P.X,P.Y,P.Z,X.X,X.Y,X.Z,Y.X,Y.Y,Y.Z,Z.X,Z.Y,Z.Z,SampleUnits[I].X,SampleUnits[I].Y,SampleUnits[I].Z}) Row.Add(MakeShared<FJsonValueNumber>(V));
                        Rows.Add(MakeShared<FJsonValueArray>(Row));
                    }
                    E->SetStringField(TEXT("affine_columns"),TEXT("unique_id,sample_local_x_cm,sample_local_y_cm,sample_local_z_cm,dvx_dx,dvy_dx,dvz_dx,dvx_dy,dvy_dy,dvz_dy,dvx_dz,dvy_dz,dvz_dz,sample_unit_x,sample_unit_y,sample_unit_z"));
                    E->SetArrayField(TEXT("affine_rows"),Rows);
                    if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidCompatibleAdvection")))
                    {
                        TArray<FVector> Advected,Transport;TArray<float> Status;
                        Cache->ReadPositionAttribute(Advected,TEXT("RiverAdvectedPosition"),Name,true,0);
                        Cache->ReadVectorAttribute(Transport,TEXT("RiverAdvectedVelocity"),Name,0);
                        Cache->ReadFloatAttribute(Status,TEXT("RiverAdvectionStatus"),Name,0);
                        if(Advected.Num()!=Positions.Num() || Transport.Num()!=Positions.Num() || Status.Num()!=Positions.Num())
                        { UE_LOG(LogTemp,Error,TEXT("Compatible advection GPU state missing"));return; }
                        TArray<TSharedPtr<FJsonValue>> AdvectionRows;
                        for(int32 I=0;I<Positions.Num();++I)
                        {
                            const FVector P=Transform.InverseTransformPosition(Advected[I]);
                            const FVector V=Transform.InverseTransformVectorNoScale(Transport[I]);
                            TArray<TSharedPtr<FJsonValue>> Row;
                            for(double Value:{double(UniqueIDs[I]),P.X,P.Y,P.Z,V.X,V.Y,V.Z,double(Status[I])})
                                Row.Add(MakeShared<FJsonValueNumber>(Value));
                            AdvectionRows.Add(MakeShared<FJsonValueArray>(Row));
                        }
                        E->SetStringField(TEXT("advection_columns"),TEXT("unique_id,precontact_local_x_cm,precontact_local_y_cm,precontact_local_z_cm,transport_local_x_cm_s,transport_local_y_cm_s,transport_local_z_cm_s,compatible_midpoint_applied"));
                        E->SetArrayField(TEXT("advection_rows"),AdvectionRows);
                    }
                }
                if (Terrain && !Primary && !Positions.IsEmpty())
                {
                    TArray<int32> States;TArray<FVector2D> Sizes;TArray<FVector4> MaterialParameters;
                    Cache->ReadIntAttribute(States,TEXT("State"),Name,0);
                    Cache->ReadVector2Attribute(Sizes,TEXT("SpriteSize"),Name,0);
                    Cache->ReadVector4Attribute(MaterialParameters,TEXT("DynamicMaterialParameter"),Name,0);
                    if (UniqueIDs.Num()!=Positions.Num() || States.Num()!=Positions.Num() || Sizes.Num()!=Positions.Num() || MaterialParameters.Num()!=Positions.Num())
                    { UE_LOG(LogTemp,Error,TEXT("Secondary render state attributes missing"));return; }
                    TArray<TSharedPtr<FJsonValue>> RenderRows;
                    for (int32 Index=0;Index<Positions.Num();++Index)
                    {
                        TArray<TSharedPtr<FJsonValue>> Row;
                        for (double Value:{double(UniqueIDs[Index]),double(States[Index]),Sizes[Index].X,Sizes[Index].Y,
                            MaterialParameters[Index].X,MaterialParameters[Index].Y,MaterialParameters[Index].Z,MaterialParameters[Index].W})
                            Row.Add(MakeShared<FJsonValueNumber>(Value));
                        RenderRows.Add(MakeShared<FJsonValueArray>(Row));
                    }
                    E->SetStringField(TEXT("secondary_render_columns"),TEXT("unique_id,state,sprite_width_cm,sprite_height_cm,material_x,material_y,material_z,material_w"));
                    E->SetArrayField(TEXT("secondary_render_rows"),RenderRows);
                    if (It->GetAsset()->GetExposedParameters().IndexOf(RaftSimLiquidSecondarySurface::Variable())!=INDEX_NONE)
                    {
                        TArray<float> Ages,Distances;
                        Cache->ReadFloatAttribute(Ages,TEXT("RiverSurfaceAge"),Name,0);
                        Cache->ReadFloatAttribute(Distances,TEXT("RiverSurfacePhi"),Name,0);
                        if (Ages.Num()!=Positions.Num() || Distances.Num()!=Positions.Num())
                        { UE_LOG(LogTemp,Error,TEXT("Secondary shared-surface GPU attributes missing: positions=%d ages=%d distances=%d"),Positions.Num(),Ages.Num(),Distances.Num());return; }
                        TArray<TSharedPtr<FJsonValue>> Rows;
                        for (int32 I=0;I<Positions.Num();++I)
                        {
                            TArray<TSharedPtr<FJsonValue>> Row{MakeShared<FJsonValueNumber>(UniqueIDs[I]),MakeShared<FJsonValueNumber>(Ages[I]),MakeShared<FJsonValueNumber>(Distances[I])};
                            Rows.Add(MakeShared<FJsonValueArray>(Row));
                        }
                        E->SetStringField(TEXT("secondary_surface_columns"),TEXT("unique_id,sampled_surface_age_seconds,sampled_surface_distance_cm"));
                        E->SetStringField(TEXT("secondary_surface_distance_semantics"),
                            FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryCurrentSurface"))
                            ? TEXT("Integrated endpoint; current reconstruction published before secondary stages; clock rounding still audited")
                            : FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryEndpointPrediction"))
                            ? TEXT("End-of-step position, RK2 transport prediction from previous completed surface; not current reconstructed distance")
                            : TEXT("Pre-integration position sampled against previous completed rendered surface"));
                        E->SetArrayField(TEXT("secondary_surface_rows"),Rows);
                    }
                }
                if (Primary && It->GetAsset()->GetName().Contains(TEXT("_Private_")) && !Positions.IsEmpty())
                {
                    TArray<float> Distances,Valid,NormalZ,WallSpeed,StepLength;
                    Cache->ReadFloatAttribute(Distances,TEXT("TerrainContactDistance"),Name,0);
                    Cache->ReadFloatAttribute(Valid,TEXT("TerrainContactValid"),Name,0);
                    Cache->ReadFloatAttribute(NormalZ,TEXT("TerrainContactNormalZ"),Name,0);
                    Cache->ReadFloatAttribute(WallSpeed,TEXT("TerrainContactWallSpeed"),Name,0);
                    Cache->ReadFloatAttribute(StepLength,TEXT("TerrainContactStepLength"),Name,0);
                    if (Distances.Num()!=Positions.Num() || Valid.Num()!=Positions.Num() || NormalZ.Num()!=Positions.Num() ||
                        WallSpeed.Num()!=Positions.Num() || StepLength.Num()!=Positions.Num())
                    { UE_LOG(LogTemp,Error,TEXT("Private terrain contact attributes missing"));return; }
                    TArray<TSharedPtr<FJsonValue>> Queries;
                    for (int32 Index=0;Index<Distances.Num();++Index)
                    {
                        TArray<TSharedPtr<FJsonValue>> Row;
                        for (double Value:{double(Distances[Index]),double(Valid[Index]),double(NormalZ[Index]),double(WallSpeed[Index]),double(StepLength[Index])})
                            Row.Add(MakeShared<FJsonValueNumber>(Value));
                        Queries.Add(MakeShared<FJsonValueArray>(Row));
                    }
                    E->SetStringField(TEXT("private_contact_query_columns"),TEXT("distance_cm,normal_valid,normal_z,wall_speed_cm_s,proposed_step_cm"));
                    E->SetArrayField(TEXT("private_contact_query_rows"),Queries);
                }
                if (Terrain && SourceIndices.Num()==Positions.Num() && UniqueIDs.Num()==Positions.Num() && Velocities.Num()==Positions.Num())
                {
                    // Keep actual GPU identity and state for residence/loss
                    // accounting. A stable live count is not a mass balance.
                    TArray<TSharedPtr<FJsonValue>> Samples;
                    for (int32 Index=0;Index<Positions.Num();++Index)
                    {
                        const FVector P=Transform.InverseTransformPosition(Positions[Index]);
                        const FVector V=Transform.InverseTransformVectorNoScale(Velocities[Index]);
                        TArray<TSharedPtr<FJsonValue>> Row;
                        for (double Value:{double(UniqueIDs[Index]),double(SourceIndices[Index]),P.X,P.Y,P.Z,V.X,V.Y,V.Z})
                            Row.Add(MakeShared<FJsonValueNumber>(Value));
                        Samples.Add(MakeShared<FJsonValueArray>(Row));
                    }
                    E->SetStringField(TEXT("particle_rows_columns"),TEXT("unique_id,source_index,local_x_cm,local_y_cm,local_z_cm,local_vx_cm_s,local_vy_cm_s,local_vz_cm_s"));
                    E->SetArrayField(TEXT("particle_rows"),Samples);
                }
                int32 NonfiniteVelocities=0;
                for (const auto& Velocity:Velocities) NonfiniteVelocities+=Velocity.ContainsNaN();
                E->SetNumberField(TEXT("nonfinite_velocities"),NonfiniteVelocities);
                E->SetNumberField(TEXT("nonfinite_positions"),Nonfinite);
                int32 Outside=0,BelowFloor=0,BeyondOutlet=0;
                int32 TerrainHits=0,MissingTerrain=0,BelowBed=0,BelowBedOneCell=0;
                double MaximumPenetration=0;
                for (const auto& P:Positions)
                {
                    if (P.ContainsNaN()) continue;
                    const FVector Local=Terrain ? Transform.InverseTransformPosition(P) : P;
                    Outside+=!InDomain(Local);
                    BelowFloor+=Local.Z<0;BeyondOutlet+=Local.X>Extents.X*.5;
                    if (TerrainProbe && InDomain(Local))
                    {
                        FHitResult Hit;
                        FCollisionQueryParams Query(SCENE_QUERY_STAT(LiquidExactBedReadback),true);
                        if (TerrainProbe->LineTraceComponent(Hit,P+FVector(0,0,100000),P-FVector(0,0,100000),Query))
                        {
                            ++TerrainHits;
                            const double Penetration=Hit.ImpactPoint.Z-P.Z;
                            BelowBed+=Penetration>0.1;
                            BelowBedOneCell+=Penetration>Extents.GetMax()/64.;
                            MaximumPenetration=FMath::Max(MaximumPenetration,Penetration);
                        }
                        else ++MissingTerrain;
                    }
                }
                E->SetNumberField(TEXT("outside_fixture_domain_count"),Outside);
                E->SetNumberField(TEXT("below_fixture_floor_count"),BelowFloor);
                E->SetNumberField(TEXT("beyond_fixture_outlet_count"),BeyondOutlet);
                if (Terrain)
                {
                    E->SetNumberField(TEXT("exact_bed_probe_count"),TerrainHits);
                    E->SetNumberField(TEXT("missing_exact_bed_probe_count"),MissingTerrain);
                    E->SetNumberField(TEXT("below_exact_bed_over_1mm_count"),BelowBed);
                    E->SetNumberField(TEXT("below_exact_bed_over_one_cell_count"),BelowBedOneCell);
                    E->SetNumberField(TEXT("maximum_exact_bed_penetration_cm"),MaximumPenetration);
                    E->SetNumberField(TEXT("fluid_cell_width_cm"),Extents.GetMax()/64.);
                }
                else
                {
                    E->SetNumberField(TEXT("inside_obstacle_radius80cm"),Inside80);
                    E->SetNumberField(TEXT("inside_obstacle_core60cm"),Inside60);
                    if (MinimumRadius!=DBL_MAX) E->SetNumberField(TEXT("minimum_obstacle_centre_distance_cm"),MinimumRadius);
                }
                if (FiniteSpeeds) E->SetNumberField(TEXT("mean_speed_cm_per_s"),SpeedSum/FiniteSpeeds);
                if (Bounds.IsValid)
                {
                    E->SetStringField(TEXT("bounds_min_cm"),Bounds.Min.ToString());
                    E->SetStringField(TEXT("bounds_max_cm"),Bounds.Max.ToString());
                }
                if (Positions.Num()==Velocities.Num())
                {
                    TArray<TSharedPtr<FJsonValue>> Regions;
                    for (int32 Region=0;Region<3;++Region)
                    {
                        int32 Count=0,Forward=0;FVector SumVelocity=FVector::ZeroVector;
                        for (int32 Index=0;Index<Positions.Num();++Index)
                        {
                            const FVector P=Terrain ? Transform.InverseTransformPosition(Positions[Index]) : Positions[Index];
                            const FVector V=Terrain ? Transform.InverseTransformVectorNoScale(Velocities[Index]) : Velocities[Index];
                            if (P.ContainsNaN() || V.ContainsNaN()) continue;
                            // Never count freely falling escaped particles as
                            // evidence of the current inside the liquid grid.
                            if (!InDomain(P)) continue;
                            const bool Inside=Region==0 ? P.X<-Extents.X*.25 : Region==1 ? FMath::Abs(P.X)<=Extents.X*.125 : P.X>Extents.X*.25;
                            if (!Inside) continue;
                            ++Count;Forward+=V.X>0;SumVelocity+=V;
                        }
                        auto RegionReport=MakeShared<FJsonObject>();
                        RegionReport->SetStringField(TEXT("name"),Terrain ? (Region==0 ? TEXT("upstream_local_quarter") : Region==1 ? TEXT("centre_local_quarter") : TEXT("downstream_local_quarter")) :
                            (Region==0 ? TEXT("upstream_x_below_minus100cm") : Region==1 ? TEXT("obstacle_abs_x_below50cm") : TEXT("downstream_x_above100cm")));
                        RegionReport->SetNumberField(TEXT("count"),Count);
                        RegionReport->SetNumberField(TEXT("forward_velocity_count"),Forward);
                        if (Count) RegionReport->SetNumberField(TEXT("mean_velocity_x_cm_per_s"),SumVelocity.X/Count);
                        Regions.Add(MakeShared<FJsonValueObject>(RegionReport));
                    }
                    E->SetArrayField(TEXT("flow_regions"),Regions);
                    E->SetBoolField(TEXT("flow_regions_exclude_outside_fixture_domain"),true);
                }
                Emitters.Add(MakeShared<FJsonValueObject>(E));
            }
            Report->SetArrayField(TEXT("emitters"),Emitters);
            FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            if (!FFileHelper::SaveStringToFile(Json,*Args[0]))
            { UE_LOG(LogTemp,Error,TEXT("Liquid particle report save failed")); }
            return;
        }
    }));
FAutoConsoleCommandWithWorldAndArgs OpacityReviewCommand(TEXT("RaftSim.LiquidTerrainOpacityReview"),
    TEXT("Unsaved visual control: change only the active terrain SDF material opacity, range0..1."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=1) return;
        float Opacity=0;
        if (!LexTryParseString(Opacity,*Args[0]) || !FMath::IsFinite(Opacity) || Opacity<0 || Opacity>1) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetName().Contains(TEXT("SouthForkLiquidTerrain")))
            {
                TArray<UMaterialInterface*> Materials;It->GetUsedMaterials(Materials);
                for (auto* Material:Materials)
                    if (auto* Dynamic=Cast<UMaterialInstanceDynamic>(Material))
                        Dynamic->SetScalarParameterValue(TEXT("Opacity"),Opacity);
            }
    }));
}
