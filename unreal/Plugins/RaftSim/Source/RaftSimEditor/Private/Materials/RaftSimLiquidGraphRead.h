#pragma once
#include "NiagaraNode.h"
#include "NiagaraGraph.h"
#include "EdGraphSchema_Niagara.h"
#include "UObject/UnrealType.h"

namespace RaftSimLiquidGraph
{
inline UEdGraphPin* DuplicateTypedMapRead(UEdGraphPin* Original,const FNiagaraVariable& Variable)
{
    TSet<UEdGraphNode*> Visited;
    while(Original && Original->GetOwningNode()->GetClass()->GetName()==TEXT("NiagaraNodeReroute"))
    {
        auto* Node=Original->GetOwningNode();
        if(Visited.Contains(Node)) return nullptr;
        Visited.Add(Node);UEdGraphPin* Upstream=nullptr;
        for(auto* Pin:Node->Pins)
            if(Pin->Direction==EGPD_Input && Pin->LinkedTo.Num()==1)
            { if(Upstream) return nullptr;Upstream=Pin->LinkedTo[0]; }
        Original=Upstream;
    }
    if(!Original) return nullptr;
    auto* Source=Cast<UNiagaraNode>(Original->GetOwningNode());
    if (!Source) return nullptr;
    auto* Graph=Source->GetNiagaraGraph();
    UEdGraphPin* MapSource=nullptr;
    for (auto* Pin:Source->Pins)
        if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() && Pin->LinkedTo.Num()==1)
            MapSource=Pin->LinkedTo[0];
    if (!MapSource) return nullptr;
    auto* Copy=DuplicateObject<UNiagaraNode>(Source,Graph);
    Copy->CreateNewGuid();Graph->AddNode(Copy,false,false);
    for (auto* Pin:Copy->Pins) Pin->LinkedTo.Reset();
    auto* Output=Copy->FindPin(Original->PinName,EGPD_Output);
    auto* Defaults=FindFProperty<FMapProperty>(Copy->GetClass(),TEXT("PinOutputToPinDefaultPersistentId"));
    if (!Output || !Defaults) return nullptr;
    const auto Type=UEdGraphSchema_Niagara::TypeDefinitionToPinType(Variable.GetType());
    Output->PinName=Variable.GetName();Output->PinType=Type;
    bool Updated=false;
    FScriptMapHelper Mapping(Defaults,Defaults->ContainerPtrToValuePtr<void>(Copy));
    for (int32 Index=0;Index<Mapping.GetMaxIndex();++Index)
        if (Mapping.IsValidIndex(Index) && *reinterpret_cast<FGuid*>(Mapping.GetKeyPtr(Index))==Output->PersistentGuid)
            for (auto* Pin:Copy->Pins)
                if (Pin->PersistentGuid==*reinterpret_cast<FGuid*>(Mapping.GetValuePtr(Index)))
                { Pin->PinType=Type;Pin->DefaultValue.Empty();Pin->DefaultObject=nullptr;Updated=true; }
    if (!Updated) return nullptr;
    for (auto* Pin:Copy->Pins)
        if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct()) Pin->MakeLinkTo(MapSource);
    Copy->MarkNodeRequiresSynchronization(TEXT("Typed registered wet-state array read"),true);
    return Output;
}
}
