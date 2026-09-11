#pragma once
#include "RaftSimLiquidGraphRead.h"
#include "NiagaraSystem.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraNodeCustomHlsl.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "RaftSimLiquidStageInterface.h"

// Regional startup must not allocate NX*NY*(water-height+oversampling)*PPC
// candidates only to kill most of them. Replace the TRUE count input of the
// native one-time timing gate, not SpawnInfo.Count itself: subsequent frames
// must still emit zero initial particles and HasSpawnedThisFrame must agree.
inline bool RaftSimInstallLiquidInitialBurstCount(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,int32 Count)
{
    if (!System || System->GetOutermost()!=GetTransientPackage() || Count<0 || Count>163840) return false;
    UNiagaraNodeFunctionCall* Spawn=nullptr;int32 Matches=0;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) return false;
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_FLIP_Tank_Spawn")) { Spawn=Call;++Matches; }
    }
    if (Matches!=1) return false;
    auto* Owned=DuplicateObject<UNiagaraScript>(Spawn->FunctionScript,System,TEXT("RegionalExactInitialBurst"));
    auto* Source=Cast<UNiagaraScriptSource>(Owned->GetLatestSource());if (!Source) return false;
    UEdGraphPin* Burst=nullptr;
    for (const auto& Node:Source->NodeGraph->Nodes)
        if (auto* Pin=Node->FindPin(TEXT("Emitter.Module.SpawnBurst"),EGPD_Input))
        { if (Burst) return false;Burst=Pin; }
    if (!Burst || Burst->LinkedTo.Num()!=1) return false;
    auto* Make=Burst->LinkedTo[0]->GetOwningNode();auto* CountPin=Make->FindPin(TEXT("Count"),EGPD_Input);
    if (!CountPin || CountPin->LinkedTo.Num()!=1) return false;
    auto* Select=Cast<UNiagaraNode>(CountPin->LinkedTo[0]->GetOwningNode());if (!Select) return false;
    auto* Yes=Select->FindPin(TEXT("int32 if True"),EGPD_Input);
    auto* No=Select->FindPin(TEXT("int32 if False"),EGPD_Input);
    auto* Condition=Select->FindPin(TEXT("Condition"),EGPD_Input);
    if (!Yes || Yes->LinkedTo.Num()!=1 || !No || !No->LinkedTo.IsEmpty() ||
        (!No->DefaultValue.IsEmpty() && No->DefaultValue!=TEXT("0")) || !Condition || Condition->LinkedTo.Num()!=1) return false;
    Yes->BreakAllPinLinks();Yes->DefaultValue=FString::FromInt(Count);
    Select->MarkNodeRequiresSynchronization(TEXT("Exact regional initial seed count; native timing retained"),true);
    Spawn->FunctionScript=Owned;Spawn->MarkNodeRequiresSynchronization(TEXT("No grid-sized excess initial allocation"),true);
    return true;
}

// Shared by legacy and explicit regional profiles. Consumes already-framed
// arrays; never applies a second source/actor translation to seed positions.
// Must be installed before activation, once. It replaces only the initial
// branch, preserving the existing subsequent external-source spawn branch.
inline bool RaftSimInstallLiquidInitialStateReader(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,bool RegionalStageEvents=false)
{
    if (!System || System->GetOutermost()!=GetTransientPackage()) return false;
    const FNiagaraTypeDefinition ArrayType(UNiagaraDataInterfaceArrayFloat3::StaticClass());
    const FNiagaraVariable PositionVariable(ArrayType,TEXT("User.River Initial Positions"));
    const FNiagaraVariable VelocityVariable(ArrayType,TEXT("User.River Initial Velocities"));
    const auto& Store=System->GetExposedParameters();
    const auto* Positions=Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(PositionVariable));
    const auto* Velocities=Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(VelocityVariable));
    if (!Positions || !Velocities || Positions->InternalFloatData.Num()>163840 ||
        Positions->InternalFloatData.Num()!=Velocities->InternalFloatData.Num()) return false;
    UNiagaraNodeFunctionCall* Initialize=nullptr;int32 Calls=0;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) return false;
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_Flip_GridParticles")) { Initialize=Call;++Calls; }
    }
    if (Calls!=1) { UE_LOG(LogTemp,Error,TEXT("Wet state: expected one grid initializer, found%d"),Calls);return false; }
    auto* Owned=DuplicateObject<UNiagaraScript>(Initialize->FunctionScript,System,TEXT("RegisteredWetVolumeInitialization"));
    auto* Source=Cast<UNiagaraScriptSource>(Owned->GetLatestSource());
    if (!Source) return false;
    UNiagaraGraph* Graph=Source->NodeGraph;
    UNiagaraNode* Set=nullptr;
    for (const auto& Node:Graph->Nodes)
        if (Node->FindPin(TEXT("Particles.Position"),EGPD_Input) && Node->FindPin(TEXT("Particles.Velocity"),EGPD_Input) && Node->FindPin(TEXT("Transient.Kill"),EGPD_Input))
        { if (Set) return false;Set=Cast<UNiagaraNode>(Node); }
    if (!Set) { UE_LOG(LogTemp,Error,TEXT("Wet state: no final initialization map-set"));return false; }
    UEdGraphPin* Targets[3]={};UNiagaraNode* Select=nullptr;
    const FName Attributes[]={TEXT("Particles.Position"),TEXT("Particles.Velocity"),TEXT("Transient.Kill")};
    for (int32 Index=0;Index<3;++Index)
    {
        auto* Pin=Set->FindPin(Attributes[Index],EGPD_Input);
        if (Pin->LinkedTo.Num()!=1) return false;
        auto* Output=Pin->LinkedTo[0];auto* Node=Cast<UNiagaraNode>(Output->GetOwningNode());
        if (!Node || (Select && Select!=Node)) return false;
        Select=Node;
        Targets[Index]=Select->FindPin(FName(*(Output->PinName.ToString()+TEXT(" if True"))),EGPD_Input);
        if (!Targets[Index]) { UE_LOG(LogTemp,Error,TEXT("Wet state: no initial branch for %s"),*Output->PinName.ToString());return false; }
    }
    UEdGraphPin* VelocityRead=nullptr;
    for (const auto& Node:Graph->Nodes)
        if (auto* Pin=Node->FindPin(TEXT("Particles.Velocity"),EGPD_Output)) VelocityRead=Pin;
    if (!VelocityRead) return false;
    auto* PositionRead=RaftSimLiquidGraph::DuplicateTypedMapRead(VelocityRead,PositionVariable);
    auto* InitialVelocityRead=RaftSimLiquidGraph::DuplicateTypedMapRead(VelocityRead,VelocityVariable);
    if (!PositionRead || !InitialVelocityRead) return false;
    UEdGraphPin* StageRead=nullptr;
    if (RegionalStageEvents)
    {
        const auto Variable=URaftSimLiquidStageInterface::Variable();
        auto& Parameters=System->GetExposedParameters();
        if (Parameters.IndexOf(Variable)==INDEX_NONE) Parameters.AddParameter(Variable);
        if (!Parameters.GetDataInterface(Variable)) Parameters.SetDataInterface(NewObject<URaftSimLiquidStageInterface>(System),Variable);
        StageRead=RaftSimLiquidGraph::DuplicateTypedMapRead(VelocityRead,Variable);
        if (!StageRead) return false;
    }
    auto* Seed=NewObject<UNiagaraNodeCustomHlsl>(Graph);Seed->CreateNewGuid();Graph->AddNode(Seed,false,false);
    Seed->ScriptUsage=ENiagaraScriptUsage::Function;Seed->Signature.Name=TEXT("ReadRegisteredWetVolume");
    Seed->Signature.Inputs={FNiagaraVariable(ArrayType,TEXT("InitialPositions")),FNiagaraVariable(ArrayType,TEXT("InitialVelocities"))};
    if (RegionalStageEvents) Seed->Signature.Inputs.Add(FNiagaraVariable(FNiagaraTypeDefinition(URaftSimLiquidStageInterface::StaticClass()),TEXT("RegionalStage")));
    Seed->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("SeedPosition")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("SeedVelocity")),FNiagaraVariable(FNiagaraTypeDefinition::GetBoolDef(),TEXT("SeedKill"))};
    auto* Code=FindFProperty<FStrProperty>(Seed->GetClass(),TEXT("CustomHlsl"));if (!Code) return false;
    FString Hlsl=TEXT(
        "int count; InitialPositions.Length(count); int index=ExecIndex();\n"
        "SeedKill=index>=count; SeedPosition=0; SeedVelocity=0;\n"
        "if(!SeedKill) { InitialPositions.Get(index,SeedPosition); InitialVelocities.Get(index,SeedVelocity); }\n");
    if (RegionalStageEvents) Hlsl+=TEXT("int RegionalStageReady;RegionalStage.ReadReady(RegionalStageReady);SeedKill=SeedKill || RegionalStageReady!=1;\n");
    Code->SetPropertyValue_InContainer(Seed,Hlsl);
    Seed->AllocateDefaultPins();
    Seed->FindPin(TEXT("InitialPositions"),EGPD_Input)->MakeLinkTo(PositionRead);
    Seed->FindPin(TEXT("InitialVelocities"),EGPD_Input)->MakeLinkTo(InitialVelocityRead);
    if (StageRead) Seed->FindPin(TEXT("RegionalStage"),EGPD_Input)->MakeLinkTo(StageRead);
    const FName Outputs[]={TEXT("SeedPosition"),TEXT("SeedVelocity"),TEXT("SeedKill")};
    for (int32 Index=0;Index<3;++Index)
    { Targets[Index]->BreakAllPinLinks();Targets[Index]->MakeLinkTo(Seed->FindPin(Outputs[Index],EGPD_Output)); }
    Seed->MarkNodeRequiresSynchronization(TEXT("Registered wet volume and depth-averaged momentum"),true);
    Initialize->FunctionScript=Owned;Initialize->MarkNodeRequiresSynchronization(TEXT("No empty-tank startup surge"),true);
    UE_LOG(LogTemp,Display,TEXT("Installed registered wet state: %d initial particles, nominal volume only"),Positions->InternalFloatData.Num());
    return true;
}
