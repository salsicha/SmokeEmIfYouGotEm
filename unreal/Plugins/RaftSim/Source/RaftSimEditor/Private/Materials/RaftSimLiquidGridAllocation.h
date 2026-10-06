#pragma once
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraScriptVariable.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"

// Configure the one authoritative 3D grid; dependent grids keep their existing
// Other Grid bindings and resolution multipliers. Never edit engine scripts.
inline bool RaftSimInstallLiquidGridAllocation(UNiagaraSystem* System,FIntVector Cells,FVector3f Extent,FString& Error)
{
    if (!System || System->GetOutermost()!=GetTransientPackage() || Cells.GetMin()<4 || Cells.GetMax()>4096 ||
        int64(Cells.X)*Cells.Y*Cells.Z*8>2000000 || Cells.X%2 || Extent.ContainsNaN() || Extent.GetMin()<=0)
    { Error=TEXT("Invalid transient bounded liquid allocation");return false; }
    auto* Enum=LoadObject<UEnum>(nullptr,TEXT("/NiagaraFluids/Enums/ENiagaraGrid2DResolution.ENiagaraGrid2DResolution"));
    FString Independent,MaxAxis;
    if (Enum) for (int32 I=0;I<Enum->NumEnums();++I)
    {
        const FString Display=Enum->GetDisplayNameTextByIndex(I).ToString();
        if (Display==TEXT("Independent")) Independent=Enum->GetNameStringByIndex(I);
        if (Display==TEXT("Max Axis")) MaxAxis=Enum->GetNameStringByIndex(I);
    }
    if (Independent.IsEmpty() || MaxAxis.IsEmpty()) { Error=TEXT("Native resolution modes unavailable");return false; }
    TSet<UNiagaraGraph*> Graphs;TSet<UNiagaraScript*> Scripts;
    for (const auto& Handle:System->GetEmitterHandles())
        if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
            if (auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Owned;Data->GetScripts(Owned,false);
                for (auto* Script:Owned)
                {
                    Scripts.Add(Script);
                    if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
                }
            }
    UNiagaraNodeFunctionCall* Primary=nullptr;int32 Matches=0;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) { Error=TEXT("Grid graph is not owned by the transient system");return false; }
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
                Call->FunctionScript->GetName()==TEXT("Grid3D_SetResolution") && Call->GetFunctionName()==TEXT("Grid3D_SetResolution"))
            { Primary=Call;++Matches; }
    }
    auto* Mode=Primary?Primary->FindPin(TEXT("Resolution Method"),EGPD_Input):nullptr;
    if (Matches!=1 || !Mode || !Mode->LinkedTo.IsEmpty() || (Mode->DefaultValue!=MaxAxis && Mode->DefaultValue!=Independent))
    { Error=TEXT("Expected exactly one owned primary max-axis/independent allocator");return false; }
    // Validate every input before changing the owned graph.
    for (const TCHAR* Input:{TEXT("Module.NumCellsX"),TEXT("Module.NumCellsY"),TEXT("Module.NumCellsZ"),TEXT("Module.Resolution Mult")})
        if (!Primary->GetCalledGraph()->GetScriptVariable(FName(Input))) { Error=FString(TEXT("Missing allocator input: "))+Input;return false; }
    Mode->DefaultValue=Independent;
    const auto Set=[&](const TCHAR* Name,const FString& Value)
    {
        const auto* Input=Primary->GetCalledGraph()->GetScriptVariable(FName(Name));
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(FName(Name),FName(*Primary->GetFunctionName()));
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Primary,Alias,
            Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=Value;
        CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Independent regional XYZ allocation"),true);
        for (auto* Script:Scripts)
        {
            TArray<FNiagaraVariable> Variables;Script->RapidIterationParameters.GetParameters(Variables);
            for (const auto& Variable:Variables)
                if (Variable.GetName().ToString().EndsWith(Alias.GetParameterHandleString().ToString()))
                    Script->RapidIterationParameters.RemoveParameter(Variable);
        }
    };
    Set(TEXT("Module.NumCellsX"),FString::FromInt(Cells.X));
    Set(TEXT("Module.NumCellsY"),FString::FromInt(Cells.Y));
    Set(TEXT("Module.NumCellsZ"),FString::FromInt(Cells.Z));
    Set(TEXT("Module.Resolution Mult"),TEXT("1.0"));
    System->GetExposedParameters().SetParameterValue<FVector3f>(Extent,
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
    const FNiagaraVariable Request(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells"));
    System->GetExposedParameters().AddParameter(Request);
    System->GetExposedParameters().SetParameterValue<FVector3f>(FVector3f(Cells),Request);
    Primary->MarkNodeRequiresSynchronization(TEXT("Explicit XYZ allocation; dependent grids inherit"),true);
    return true;
}
