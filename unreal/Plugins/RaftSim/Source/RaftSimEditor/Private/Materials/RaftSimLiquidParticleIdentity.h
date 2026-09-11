#pragma once
#include "NiagaraSystem.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeOutput.h"
#include "NiagaraNodeAssignment.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "ViewModels/Stack/NiagaraParameterHandle.h"

// Identity is (simulation generation, birth owner, unsigned birth sequence).
// The generation belongs to the regional coordinator and changes on reset.
// These two integer particle fields are assigned ONLY at birth. A later owner
// transfer must copy them, never derive them from the destination's local ID.
inline bool RaftSimInstallLiquidParticleIdentity(UNiagaraSystem* System,
    const TSet<UNiagaraGraph*>& Graphs,int32 BirthOwner,FString& Error)
{
    Error=TEXT("Particle identity requires one unused owned spawn stack and a valid birth owner");
    if (!System || System->GetOutermost()!=GetTransientPackage() || BirthOwner<0 || BirthOwner>4095) return false;
    UNiagaraNodeOutput* Spawn=nullptr;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) return false;
        for (const auto& Node:Graph->Nodes)
            if (auto* Output=Cast<UNiagaraNodeOutput>(Node);Output && Output->GetUsage()==ENiagaraScriptUsage::ParticleSpawnScript)
            { if (Spawn) return false;Spawn=Output; }
    }
    if (!Spawn) return false;
    const auto Int=FNiagaraTypeDefinition::GetIntDef();
    const FNiagaraVariable Owner(Int,TEXT("Particles.RiverBirthOwner"));
    const FNiagaraVariable Sequence(Int,TEXT("Particles.RiverBirthSequence"));
    // UniqueID is assigned by native SpawnMain before this stack executes. It
    // is not a recycled persistent-ID slot and must never pass through float.
    auto* Assignment=FNiagaraStackGraphUtilities::AddParameterModuleToStack(
        {Owner,Sequence},*Spawn,INDEX_NONE,{FString::FromInt(BirthOwner),TEXT("0")});
    if (!Assignment) return false;
    const auto Handle=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
        FNiagaraParameterHandle(TEXT("Module.Particles.RiverBirthSequence")),Assignment);
    auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Assignment,Handle,Int,FGuid(),FGuid());
    const FNiagaraVariableBase NativeSequence(Int,TEXT("Particles.UniqueID"));
    FNiagaraStackGraphUtilities::SetLinkedParameterValueForFunctionInput(Pin,NativeSequence,{NativeSequence});
    Assignment->MarkNodeRequiresSynchronization(TEXT("Immutable integer water-particle birth identity"),true);
    Error.Reset();return true;
}
