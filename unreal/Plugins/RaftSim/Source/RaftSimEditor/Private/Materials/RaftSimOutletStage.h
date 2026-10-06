#pragma once
#include "RaftSimLiquidWindowProfile.h"
#include "RaftSimLiquidBoundaryLayout.h"

// Shared stage query for registered bounded regions. The pressure
// unknown is kinematic pressure in cm^2/s^2; profile stage/bed are engine cm.
inline FString RaftSimOutletStageQuery(const TCHAR* LocalPosition,const TCHAR* Profile,bool GridCoordinates=false,bool CanonicalWorld=false)
{
    FString Code=RaftSimLiquidBoundaryLayoutHlsl(Profile,TEXT("stage"))+
        FString::Printf(TEXT("float3 stagePosition=%s;\n"),LocalPosition);
    if (GridCoordinates && (CanonicalWorld || RaftSimLiquidWindowProfile::Geographic()))
        Code+=TEXT("stagePosition.y=-stagePosition.y;\n");
    if (!GridCoordinates)
        Code+=TEXT("if(stageRect) stagePosition.xy-=float2(dot(stageOrigin,stageAxisX),dot(stageOrigin,stageAxisY));\n");
    Code+=RaftSimLiquidBoundaryFaceHlsl(TEXT("stagePosition"),TEXT("outlet"));
    // Face helper uses the same metadata with its own query-local names.
    for (const TCHAR* Name:{TEXT("Half"),TEXT("Step"),TEXT("Cells")})
        Code.ReplaceInline(*(FString(TEXT("outlet"))+Name),*(FString(TEXT("stage"))+Name));
    Code+=TEXT(
        "bool prescribedStage=false;float externalPressure=0;\n"
        "if(outletFace>=0) { float3 stageRow; PROFILE.Get(stageHeader+outletRowOffset+outletColumn,stageRow);\n"
        " prescribedStage=stageRow.z<0 && stagePosition.z>stageRow.x;\n"
        " if(prescribedStage) externalPressure=980.0*max(stageRow.y-stagePosition.z,0.0); }\n");
    Code.ReplaceInline(TEXT("PROFILE"),Profile,ESearchCase::CaseSensitive);
    return Code;
}

inline UEdGraphPin* RaftSimAddCustomInput(UNiagaraNodeCustomHlsl* Node,const FNiagaraVariable& Variable,UEdGraphPin* Source)
{
    if (!Source) { UE_LOG(LogTemp,Error,TEXT("Stage input missing source: %s"),*Variable.GetName().ToString());return nullptr; }
    int32 AddIndex=INDEX_NONE;
    for (int32 I=0;I<Node->Pins.Num();++I)
        if(Node->Pins[I]->Direction==EGPD_Input && Node->Pins[I]->PinName==TEXT("Add")) { AddIndex=I;break; }
    if(AddIndex==INDEX_NONE) { UE_LOG(LogTemp,Error,TEXT("Stage input missing Add sentinel: %s"),*Variable.GetName().ToString());return nullptr; }
    Node->Signature.Inputs.Add(Variable);
    auto* Pin=Node->CreatePin(EGPD_Input,UEdGraphSchema_Niagara::TypeDefinitionToPinType(Variable.GetType()),Variable.GetName());
    Node->Pins.Remove(Pin);Node->Pins.Insert(Pin,AddIndex);Pin->MakeLinkTo(Source);
    return Pin;
}
