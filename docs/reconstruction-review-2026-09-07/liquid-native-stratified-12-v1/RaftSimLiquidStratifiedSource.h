#pragma once
#include "RaftSimLiquidGraphRead.h"
#include "NiagaraNodeAssignment.h"
#include "NiagaraNodeCustomHlsl.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "ViewModels/Stack/NiagaraParameterHandle.h"

// Transient regional experiment. Same weighted source sites, velocities and
// birth count; only replace independent with-replacement site draws by one
// shifted stratified CDF sequence per native SpawnInfo group. Initial wet-volume
// initialization remains a separate, unmodified branch.
inline bool RaftSimInstallLiquidStratifiedSource(UNiagaraSystem* System,
    const TSet<UNiagaraGraph*>& Graphs,const TArray<double>& Weights,uint32 Seed,FString& Error)
{
    if(Weights.IsEmpty()) return true; // No external source on this owner.
    Error=TEXT("Stratified source requires an unused transient graph and valid weighted source");
    if(!System || System->GetOutermost()!=GetTransientPackage() || Weights.Num()>65536) return false;
    double Total=0;for(double W:Weights) { if(!FMath::IsFinite(W) || W<0) return false;Total+=W; }
    if(!FMath::IsFinite(Total) || Total<=0) return false;
    auto* Cdf=NewObject<UNiagaraDataInterfaceArrayFloat>(System);double Sum=0;float Previous=0;
    for(int32 I=0;I<Weights.Num();++I)
    {
        Sum+=Weights[I];const float Value=I+1==Weights.Num()?1.f:float(Sum/Total);
        if(Value<Previous || (Weights[I]>0 && Value<=Previous))
        { Error=TEXT("Positive source weight collapsed in float CDF; refusing to lose source support");return false; }
        Cdf->FloatData.Add(Value);Previous=Value;
    }
    const FNiagaraVariable CdfVariable(FNiagaraTypeDefinition(Cdf->GetClass()),TEXT("User.River Source CDF"));
    auto& Store=System->GetExposedParameters();Store.AddParameter(CdfVariable);Store.SetDataInterface(Cdf,CdfVariable);
    UNiagaraNodeAssignment* Assignment=nullptr;UEdGraphPin* OriginalRead=nullptr;
    const FNiagaraVariable SourceIndex(FNiagaraTypeDefinition::GetIntDef(),TEXT("Particles.RiverSourceIndex"));
    for(auto* Graph:Graphs)
    {
        if(!Graph || !Graph->IsIn(System)) return false;
        for(const auto& Node:Graph->Nodes)
        {
            if(auto* A=Cast<UNiagaraNodeAssignment>(Node);A && A->GetAssignmentTargets().Contains(SourceIndex))
            { if(Assignment) return false;Assignment=A; }
            if(auto* Pin=Node->FindPin(TEXT("User.River Source Distribution"),EGPD_Output)) OriginalRead=Pin;
        }
    }
    if(!Assignment || !OriginalRead || Assignment->GetGraph()!=OriginalRead->GetOwningNode()->GetGraph()) return false;
    auto* CdfRead=RaftSimLiquidGraph::DuplicateTypedMapRead(OriginalRead,CdfVariable);
    auto* SequenceRead=RaftSimLiquidGraph::DuplicateTypedMapRead(OriginalRead,
        FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Particles.UniqueID")));
    auto* CountRead=RaftSimLiquidGraph::DuplicateTypedMapRead(OriginalRead,
        FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Engine.ExecutionCount")));
    if(!CdfRead || !SequenceRead || !CountRead) return false;
    auto* Graph=Assignment->GetNiagaraGraph();auto* Node=NewObject<UNiagaraNodeCustomHlsl>(Graph);
    Node->CreateNewGuid();Graph->AddNode(Node,false,false);Node->ScriptUsage=ENiagaraScriptUsage::Function;
    Node->Signature.Name=TEXT("StratifiedRiverSourceSite");
    Node->Signature.Inputs={FNiagaraVariable(CdfVariable.GetType(),TEXT("CDF")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Sequence")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("BatchCount"))};
    Node->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Site"))};
    auto* Property=FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl"));if(!Property) return false;
    // UniqueID is assigned before SpawnMain. ExecIndex and ExecutionCount are
    // relative to this SpawnInfo, not the entire live particle allocation.
    // A shared integer hash randomizes the offset without giving each particle
    // a separate stratum offset. Midpoint conversion is exactly inside (0,1).
    const FString Code=FString::Printf(TEXT(
        "int n; CDF.Length(n); int i=ExecIndex(); Site=0;\n"
        "if(n>0 && BatchCount>0 && i>=0 && i<BatchCount) {\n"
        " uint key=(uint(Sequence)-uint(i)) ^ %uu;\n"
        " key^=key>>16; key*=0x7feb352du; key^=key>>15; key*=0x846ca68bu; key^=key>>16;\n"
        " float offset=(float(key>>9)+0.5)*0.00000011920928955078125;\n"
        " precise float quantile=min((float(i)+offset)/float(BatchCount),asfloat(0x3f7fffffu));\n"
        " int lo=0,hi=n; [loop] while(lo<hi) { int mid=(lo+hi)/2; float c; CDF.Get(mid,c);\n"
        "  if(quantile<c) hi=mid; else lo=mid+1; } Site=lo;\n"
        "}\n"),Seed);
    Property->SetPropertyValue_InContainer(Node,Code);Node->AllocateDefaultPins();
    Node->FindPin(TEXT("CDF"),EGPD_Input)->MakeLinkTo(CdfRead);
    Node->FindPin(TEXT("Sequence"),EGPD_Input)->MakeLinkTo(SequenceRead);
    Node->FindPin(TEXT("BatchCount"),EGPD_Input)->MakeLinkTo(CountRead);
    const auto Handle=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(
        FNiagaraParameterHandle(TEXT("Module.Particles.RiverSourceIndex")),Assignment);
    auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(
        *Assignment,Handle,FNiagaraTypeDefinition::GetIntDef(),FGuid(),FGuid());
    Pin.BreakAllPinLinks();Pin.MakeLinkTo(Node->FindPin(TEXT("Site"),EGPD_Output));
    Node->MarkNodeRequiresSynchronization(TEXT("One weighted stratum per actual source birth"),true);
    Assignment->MarkNodeRequiresSynchronization(TEXT("Prescribed source volume without duplicate random site draws"),true);
    Error.Reset();return true;
}
