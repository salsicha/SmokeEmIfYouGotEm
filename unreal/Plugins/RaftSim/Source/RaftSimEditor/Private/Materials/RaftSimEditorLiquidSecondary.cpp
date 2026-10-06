#include "HAL/IConsoleManager.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeAssignment.h"
#include "NiagaraNodeCustomHlsl.h"
#include "RaftSimLiquidGraphRead.h"
#include "RaftSimLiquidSecondaryMath.h"
#include "RaftSimLiquidSecondaryOptics.h"
#include "RaftSimLiquidWindowProfile.h"
#include "RaftSimLiquidStageInterface.h"
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#include "NiagaraScriptVariable.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "NiagaraDataInterfaceGrid3DCollectionReader.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NiagaraSpriteRendererProperties.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UObjectHash.h"

namespace
{
bool AddSecondaryInput(UNiagaraNodeCustomHlsl* Node,FName AnchorName,FName PinName,const FNiagaraVariable& Variable)
{
    auto* Anchor=Node->FindPin(AnchorName,EGPD_Input);
    if (!Anchor || Anchor->LinkedTo.Num()!=1 || Node->FindPin(PinName,EGPD_Input)) return false;
    auto* Read=RaftSimLiquidGraph::DuplicateTypedMapRead(Anchor->LinkedTo[0],Variable);
    if (!Read) return false;
    Node->Signature.Inputs.Add(FNiagaraVariable(Variable.GetType(),PinName));
    auto* Pin=Node->CreatePin(EGPD_Input,UEdGraphSchema_Niagara::TypeDefinitionToPinType(Variable.GetType()),PinName);
    // Niagara's history builder indexes signature inputs by pin index and
    // assumes the dynamic Add pin is last. CreatePin alone appends after it.
    auto* Add=Node->FindPin(TEXT("Add"),EGPD_Input);
    if (!Add) return false;
    Node->Pins.RemoveSingle(Pin);Node->Pins.Insert(Pin,Node->Pins.Find(Add));
    Pin->MakeLinkTo(Read);
    int32 Index=0;
    for (const auto* Input:Node->Pins) if (Input->Direction==EGPD_Input && Input!=Add)
    {
        if (!Node->Signature.Inputs.IsValidIndex(Index) || Node->Signature.Inputs[Index].GetName()!=Input->PinName) return false;
        ++Index;
    }
    if (Index!=Node->Signature.Inputs.Num()) return false;
    return true;
}

bool CorrectSecondarySources(UNiagaraSystem* System,FVersionedNiagaraEmitterData* Data,bool SharedSurface,bool ExactContact,bool EndpointPrediction)
{
    TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
    TSet<UNiagaraGraph*> Graphs;
    for (auto* Script:Scripts)
        if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
    int32 Modules=0,Curls=0,Emissions=0,Spawns=0,Updates=0;bool Valid=true;
    for (auto* Graph:Graphs) for (const auto& N:Graph->Nodes)
    {
        auto* Call=Cast<UNiagaraNodeFunctionCall>(N);
        if (!Call || !Call->FunctionScript || !Call->FunctionScript->GetName().StartsWith(TEXT("Grid3D_Secondary_"))) continue;
        const FString Name=Call->FunctionScript->GetName();
        if (Name!=TEXT("Grid3D_Secondary_EmissionPoints") && Name!=TEXT("Grid3D_Secondary_SpawnParticles") && Name!=TEXT("Grid3D_Secondary_UpdateParticles")) continue;
        auto* Owned=DuplicateObject<UNiagaraScript>(Call->FunctionScript,System,FName(*(TEXT("RiverMetric_")+Name)));
        TArray<UObject*> OwnedObjects;GetObjectsWithOuter(Owned,OwnedObjects,EGetObjectsFlags::IncludeNestedObjects);
        // Creating typed read nodes must happen after releasing UObject's hash
        // iteration lock, not inside ForEachObjectWithOuter's callback.
        for (auto* Object:OwnedObjects)
        {
            auto* Node=Cast<UNiagaraNodeCustomHlsl>(Object);
            auto* Property=Node ? FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl")) : nullptr;
            if (!Property) continue;
            FString Code=Property->GetPropertyValue_InContainer(Node);bool Changed=false;
            const FNiagaraVariable Extents(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents"));
            if (Code.Contains(TEXT("Vy_left")))
            {
                Valid &= AddSecondaryInput(Node,TEXT("dx"),TEXT("RiverExtents"),Extents);
                Code=RaftSimLiquidSecondaryMath::Curl();++Curls;Changed=true;
            }
            else if (Code.Contains(TEXT("NumEmitted")) && Code.Contains(TEXT("EmissionCounter")))
            {
                Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverExtents"),Extents);
                for (const auto& Input:TArray<TPair<FName,FName>>{{TEXT("RiverFlow"),TEXT("Module.SimGridReader")},{TEXT("RiverSdf"),TEXT("Module.SDFReader")}})
                {
                    const auto* Variable=Node->GetNiagaraGraph()->GetScriptVariable(Input.Value);
                    if (!Variable) { Valid=false;continue; }
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),Input.Key,Variable->Variable);
                }
                const auto* Reader=Node->GetNiagaraGraph()->GetScriptVariable(TEXT("Module.SimGridReader"));
                if (!Reader) Valid=false;
                else Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverBoundary"),FNiagaraVariable(Reader->Variable.GetType(),TEXT("Emitter.BoundaryReader")));
                if (SharedSurface)
                {
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverSurface"),RaftSimLiquidSecondarySurface::Variable());
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverAge"),FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Emitter.Age")));
                }
                Code=RaftSimLiquidSecondaryMath::Emission(SharedSurface);Valid &= !Code.IsEmpty();++Emissions;Changed=true;
            }
            else if (Code.Contains(TEXT("World = mul(float4(Unit, 1), UnitToWorld).xyz;")))
            {
                Code.ReplaceInline(TEXT("World = mul(float4(Unit, 1), UnitToWorld).xyz;"),
                    *(RaftSimLiquidSecondaryMath::WorldVelocity(TEXT("Velocity"),TEXT("UnitToWorld"))+TEXT("World = mul(float4(Unit, 1), UnitToWorld).xyz;")));
                ++Spawns;Changed=true;
            }
            else if (Code.Contains(TEXT("TmpVelMag")) && Node->FindPin(TEXT("OutPosition"),EGPD_Output))
            {
                Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverUnitToWorld"),FNiagaraVariable(FNiagaraTypeDefinition::GetMatrix4Def(),TEXT("Emitter.UnitToWorld")));
                const auto* Reader=Node->GetNiagaraGraph()->GetScriptVariable(TEXT("Module.BoundaryReader"));
                if (!Reader) Valid=false;
                else Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverBoundary"),Reader->Variable);
                // The inherited active branch returned State only to a debug
                // color node, leaving Particles.State at its spawn default.
                auto* VelocityOut=Node->FindPin(TEXT("OutVelocity"),EGPD_Output);
                auto* StateOut=Node->FindPin(TEXT("OutState"),EGPD_Output);
                if (!VelocityOut || !StateOut || VelocityOut->LinkedTo.Num()!=1) Valid=false;
                else
                {
                    auto* Set=Cast<UNiagaraNode>(VelocityOut->LinkedTo[0]->GetOwningNode());
                    if (!Set || Set->GetClass()->GetName()!=TEXT("NiagaraNodeParameterMapSet")) Valid=false;
                    else
                    {
                        auto* State=Set->FindPin(TEXT("Particles.State"),EGPD_Input);
                        if (!State)
                        {
                            State=Set->CreatePin(EGPD_Input,UEdGraphSchema_Niagara::TypeDefinitionToPinType(FNiagaraTypeDefinition::GetIntDef()),TEXT("Particles.State"));
                            if (auto* Add=Set->FindPin(TEXT("Add"),EGPD_Input))
                            { Set->Pins.RemoveSingle(State);Set->Pins.Insert(State,Set->Pins.Find(Add)); }
                        }
                        State->BreakAllPinLinks();State->MakeLinkTo(StateOut);
                        Set->MarkNodeRequiresSynchronization(TEXT("Persist actual foam/spray/bubble state"),true);
                        if (SharedSurface)
                        {
                            for (const auto& Pair:TArray<TPair<FName,FName>>{{TEXT("OutSurfaceAge"),TEXT("Particles.RiverSurfaceAge")},{TEXT("OutSurfacePhi"),TEXT("Particles.RiverSurfacePhi")}})
                            {
                                const auto Type=FNiagaraTypeDefinition::GetFloatDef();
                                Node->Signature.Outputs.Add(FNiagaraVariable(Type,Pair.Key));
                                auto* Out=Node->CreatePin(EGPD_Output,UEdGraphSchema_Niagara::TypeDefinitionToPinType(Type),Pair.Key);
                                if (auto* Add=Node->FindPin(TEXT("Add"),EGPD_Output))
                                { Node->Pins.RemoveSingle(Out);Node->Pins.Insert(Out,Node->Pins.Find(Add)); }
                                auto* In=Set->CreatePin(EGPD_Input,UEdGraphSchema_Niagara::TypeDefinitionToPinType(Type),Pair.Value);
                                if (auto* Add=Set->FindPin(TEXT("Add"),EGPD_Input))
                                { Set->Pins.RemoveSingle(In);Set->Pins.Insert(In,Set->Pins.Find(Add)); }
                                In->MakeLinkTo(Out);
                            }
                        }
                    }
                }
                if (SharedSurface)
                {
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverSurface"),RaftSimLiquidSecondarySurface::Variable());
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverAge"),FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Emitter.Age")));
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverExtents"),Extents);
                }
                if(ExactContact)
                {
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("Terrain"),FNiagaraVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Contact Triangles")));
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverPhysicalExtents"),FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RiverSecondaryPhysicalExtents")));
                }
                Code=RaftSimLiquidSecondaryMath::Update(Node->FindPin(TEXT("OutColor"),EGPD_Output)!=nullptr,SharedSurface,ExactContact,EndpointPrediction);
                if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryCurrentSurface")))
                {
                    Valid &= AddSecondaryInput(Node,TEXT("SimDt"),TEXT("RiverStage"),URaftSimLiquidStageInterface::Variable());
                    Code+=TEXT("\n// RiverSecondaryCurrentSurfaceStage: retain the actual stage DI binding.\nint stageReady;RiverStage.ReadReady(stageReady);OutAlive=OutAlive && stageReady==1;\n");
                }
                Valid &= !Code.IsEmpty();
                ++Updates;Changed=true;
            }
            else if (Code.Contains(TEXT("IsInside = round(Mask) == 1")))
            {
                // The old scalar Boundary attribute no longer exists on the
                // vector boundary grid. Its read would register an incompatible
                // second attribute beside SolidVelocity_Boundary.
                auto* Mask=Node->FindPin(TEXT("Mask"),EGPD_Input);
                if (!Mask) Valid=false;
                else { Mask->BreakAllPinLinks();Mask->DefaultValue=TEXT("0"); }
                Code=TEXT("IsInside=false; // Vector boundary checked by RiverSecondaryTimeIntegration.");Changed=true;
            }
            if (Changed)
            {
                Property->SetPropertyValue_InContainer(Node,Code);
                Node->MarkNodeRequiresSynchronization(TEXT("Metric time-aware secondary surface model"),true);
            }
        }
        Call->FunctionScript=Owned;Call->MarkNodeRequiresSynchronization(TEXT("Owned river secondary module"),true);++Modules;
    }
    UE_LOG(LogTemp,Display,TEXT("River secondary math modules=%d curl=%d emission=%d spawn=%d update=%d valid=%d"),Modules,Curls,Emissions,Spawns,Updates,Valid);
    return Valid && Modules==3 && Curls==1 && Emissions==1 && Spawns==1 && Updates==2;
}

bool SetSecondarySpawnBudget(FVersionedNiagaraEmitterData* Data,int32 Budget)
{
    TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
    TSet<UNiagaraGraph*> Graphs;
    for (auto* Script:Scripts)
        if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
    UNiagaraNodeAssignment* Assignment=nullptr;
    for (auto* Graph:Graphs) for (const auto& Node:Graph->Nodes)
        if (auto* A=Cast<UNiagaraNodeAssignment>(Node);A && A->FindAssignmentTarget(TEXT("Emitter.MaxSecondaryParticlesPerFrame"))!=INDEX_NONE)
        { if (Assignment && Assignment!=A) return false;Assignment=A; }
    if (!Assignment) return false;
    const FName Name(TEXT("Module.Emitter.MaxSecondaryParticlesPerFrame"));
    const auto* Input=Assignment->GetCalledGraph()->GetScriptVariable(Name);
    if (!Input) return false;
    const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(Name,FName(*Assignment->GetFunctionName()));
    auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Assignment,Alias,
        Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
    Pin.BreakAllPinLinks();Pin.DefaultValue=FString::FromInt(Budget);
    CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Secondary request matches GPU safety budget"),true);
    Assignment->MarkNodeRequiresSynchronization(TEXT("Bound actual secondary spawn request, not only rejection ceiling"),true);
    Data->MaxGPUParticlesSpawnPerFrame=Budget;
    return true;
}

FAutoConsoleCommandWithWorldAndArgs SecondaryReview(TEXT("RaftSim.LiquidSecondaryReview"),
    TEXT("Unsaved native spray/foam emitter on the owned liquid review; not physical or visual acceptance."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        const bool SharedSurface=Args.Num()==1 && Args[0]==TEXT("shared-surface");
        const bool ExactContact=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryExactContact"));
        const bool EndpointPrediction=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryEndpointPrediction"));
        if(EndpointPrediction && !SharedSurface) return;
        const bool CurrentSurface=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryCurrentSurface"));
        if(CurrentSurface && (!SharedSurface || !EndpointPrediction)) return;
        if (!Args.IsEmpty() && !SharedSurface) return;
        UNiagaraComponent* Component=nullptr;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetOutermost()==GetTransientPackage() &&
                It->GetAsset()->GetName().Contains(TEXT("_Foam_")))
            { if (Component) return;Component=*It; }
        if (!Component)
        { UE_LOG(LogTemp,Error,TEXT("No unique owned secondary liquid candidate"));return; }
        auto* System=Component->GetAsset();
        FNiagaraEmitterHandle* Secondary=nullptr;FString FluidName;
        for (auto& Handle:System->GetEmitterHandles())
        {
            if (Handle.GetName()==TEXT("Grid3D_FLIP_Secondary_Emitter")) Secondary=&Handle;
            if (Handle.GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter")) FluidName=Handle.GetName().ToString();
        }
        // Hose already owns this disabled emitter. Keep its existing graphs.
        if (!Secondary || FluidName.IsEmpty() || System->GetNumEmitters()!=2)
        { UE_LOG(LogTemp,Error,TEXT("Unexpected native liquid emitter inventory"));return; }
        auto* Data=Secondary->GetInstance().GetEmitterData();
        if (!Data || !Secondary->GetInstance().Emitter->IsIn(System) || Data->GetRenderers().Num()!=2)
        { UE_LOG(LogTemp,Error,TEXT("Unexpected owned secondary renderer/version data"));return; }
        for (auto* Renderer:Data->GetRenderers())
            if (!Renderer->IsA<UNiagaraSpriteRendererProperties>())
            { UE_LOG(LogTemp,Error,TEXT("Secondary renderer is not a particle sprite"));return; }
        Component->DeactivateImmediate();
        // The surface-foam variant is built without a redundant native foam
        // attribute; its SDF reader and producer retain the same RGBA layout.
        Secondary->SetIsEnabled(true,*System,false);
        Data->GetRenderers()[0]->SetIsEnabled(false);
        Data->GetRenderers()[1]->SetIsEnabled(true);
        // Niagara rejects an oversized batch; it does not truncate it to the
        // safety ceiling. Bound the actual emission buffer/request as well.
        if (!SetSecondarySpawnBudget(Data,2048))
        { UE_LOG(LogTemp,Error,TEXT("Could not set actual secondary spawn budget"));return; }
        if (SharedSurface && !RaftSimLiquidSecondarySurface::Install(System))
        { UE_LOG(LogTemp,Error,TEXT("Could not install owned secondary surface cache"));return; }
        if (SharedSurface)
        {
            Data->AttributesToPreserve.AddUnique(TEXT("Particles.RiverSurfaceAge"));
            Data->AttributesToPreserve.AddUnique(TEXT("Particles.RiverSurfacePhi"));
        }
        if(ExactContact)
        {
            const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Contact Triangles"));
            const auto* Terrain=Cast<UNiagaraDataInterfaceArrayFloat3>(System->GetExposedParameters().GetDataInterface(V));
            if(!Terrain || Terrain->InternalFloatData.Num()<8)
            { UE_LOG(LogTemp,Error,TEXT("Secondary exact contact requires the registered primary terrain array"));return; }
            const auto& Meta=Terrain->InternalFloatData[0];const auto& Dims=Terrain->InternalFloatData[1];
            if(Meta.ContainsNaN() || Dims.ContainsNaN() || Meta.Z<=0 || Dims.X<=0 || Dims.Y<=0 || Dims.Z<=0 ||
                int64(Dims.Y)*int64(Dims.Z)*6+2!=Terrain->InternalFloatData.Num())
            { UE_LOG(LogTemp,Error,TEXT("Invalid registered terrain layout for secondary sweep"));return; }
            TSharedPtr<FJsonObject> Profile;
            if(!RaftSimLiquidWindowProfile::Read(TEXT("grid_boundary_profile.json"),Profile)) return;
            const auto& Physical=Profile->GetArrayField(TEXT("physical_extents_cm"));
            const auto& Computational=Profile->GetArrayField(TEXT("computational_extents_cm"));
            const auto Grid=System->GetExposedParameters().GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
            if(Physical.Num()!=3 || Computational.Num()!=3) return;
            FVector3f Extent;
            for(int32 Axis=0;Axis<3;++Axis)
            {
                Extent[Axis]=float(Physical[Axis]->AsNumber());
                if(!FMath::IsFinite(Extent[Axis]) || Extent[Axis]<=0 || Extent[Axis]>Grid[Axis] || !FMath::IsNearlyEqual(Grid[Axis],float(Computational[Axis]->AsNumber()),.001f)) return;
            }
            const FNiagaraVariable Bounds(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RiverSecondaryPhysicalExtents"));
            System->GetExposedParameters().AddParameter(Bounds);System->GetExposedParameters().SetParameterValue<FVector3f>(Extent,Bounds);
        }
        if (CurrentSurface)
        {
            const auto V=URaftSimLiquidStageInterface::Variable();
            System->GetExposedParameters().AddParameter(V);
            System->GetExposedParameters().SetDataInterface(NewObject<URaftSimLiquidStageInterface>(System),V);
        }
        if (!CorrectSecondarySources(System,Data,SharedSurface,ExactContact,EndpointPrediction))
        { UE_LOG(LogTemp,Error,TEXT("Could not install metric secondary source/update model"));return; }
        int32 Readers=0;
        ForEachObjectWithOuter(Secondary->GetInstance().Emitter,[&](UObject* Object)
        {
            if (auto* Reader=Cast<UNiagaraDataInterfaceGrid3DCollectionReader>(Object))
            { Reader->EmitterName=FluidName;++Readers; }
        },EGetObjectsFlags::IncludeNestedObjects);
        System->RequestCompile(true);System->WaitForCompilationComplete(false,false);
        if (!System->IsReadyToRun())
        { UE_LOG(LogTemp,Error,TEXT("Secondary fluid candidate failed compilation"));return; }
        auto* Sprite=CastChecked<UNiagaraSpriteRendererProperties>(Data->GetRenderers()[1]);
        auto* Optics=RaftSimCreateSecondaryOptics(Sprite->Material?Sprite->Material->GetMaterial():nullptr);
        if (!Optics)
        { UE_LOG(LogTemp,Error,TEXT("Unexpected secondary optical source"));return; }
        Sprite->Material=Optics;
        Optics->PostEditChange();
        FAssetCompilingManager::Get().FinishAllCompilation();
        if (GShaderCompilingManager) GShaderCompilingManager->FinishAllCompilation();
        Component->ReinitializeSystem();
        UE_LOG(LogTemp,Display,TEXT("Secondary completed-render-surface history requested=%d"),SharedSurface);
        UE_LOG(LogTemp,Display,TEXT("Secondary exact registered terrain sweep requested=%d; visual particles expire on impact, primary water unchanged"),ExactContact);
        UE_LOG(LogTemp,Display,TEXT("Secondary end-of-step phase prediction requested=%d; old surface advected by current grid, not same-step surface acceptance"),EndpointPrediction);
        UE_LOG(LogTemp,Display,TEXT("Native secondary liquid candidate installed: readers=%d fluid=%s one_sprite_renderer=1 spawn_cap_per_frame=2048; metric-surface-v1 empirical source, not calibrated"),Readers,*FluidName);
    }));
}
