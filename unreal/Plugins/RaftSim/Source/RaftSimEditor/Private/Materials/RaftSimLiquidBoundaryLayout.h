#pragma once
#include "CoreMinimal.h"

// Shared decoding of the per-region GPU boundary table. Legacy tables are
// unchanged. Validated v3 uploads negate only header[3].z as an ABI marker;
// all dimensions returned below are positive. No global active-layout state.
inline FString RaftSimLiquidBoundaryLayoutHlsl(const TCHAR* Profile,const TCHAR* Prefix)
{
    FString Code=TEXT(
        "float3 LLMeta,LLDims,LLAxisX,LLAxisY; PP.Get(2,LLMeta); PP.Get(3,LLDims); PP.Get(0,LLAxisX); PP.Get(1,LLAxisY);\n"
        "bool LLRect=LLDims.z<0; float3 LLStep,LLCells,LLComputeExtent,LLOrigin; float2 LLHalf; int LLHeader;\n"
        "if(LLRect) { LLOrigin=LLMeta; LLHalf=LLDims.xy*0.5; PP.Get(4,LLStep); PP.Get(5,LLCells); PP.Get(7,LLComputeExtent); LLHeader=8; }\n"
        "else { LLOrigin=float3(0,0,LLMeta.z); LLHalf=LLMeta.yy; LLStep=float3(LLMeta.x,LLMeta.x,LLDims.x); LLCells=float3(LLDims.y,LLDims.y,LLDims.z); LLComputeExtent=float3(2*LLHalf+4*LLStep.xy,LLStep.z*LLCells.z); LLHeader=4; }\n"
        "int LLVectorOffset=LLHeader+2*(int)(LLCells.x+LLCells.y);\n");
    Code.ReplaceInline(TEXT("PP"),Profile,ESearchCase::CaseSensitive);
    Code.ReplaceInline(TEXT("LL"),Prefix,ESearchCase::CaseSensitive);
    return Code;
}

// Input: centred physical station/lateral XY and absolute datum Z. Corners are
// deliberately not promoted into an arbitrary face. Output names are prefixed.
inline FString RaftSimLiquidBoundaryFaceHlsl(const TCHAR* Position,const TCHAR* Prefix)
{
    FString Code=TEXT(
        "int LLFace=-1; float LLAlong=0; float3 LLPosition=POS;\n"
        "if(abs(LLPosition.y)<LLHalf.y && abs(LLPosition.x)>=LLHalf.x) { LLFace=LLPosition.x<0?0:1; LLAlong=LLPosition.y; }\n"
        "else if(abs(LLPosition.x)<LLHalf.x && abs(LLPosition.y)>=LLHalf.y) { LLFace=LLPosition.y<0?2:3; LLAlong=LLPosition.x; }\n"
        "int LLColumn=0,LLRowOffset=0;\n"
        "if(LLFace>=0) { int LLCount=(int)(LLFace<2?LLCells.y:LLCells.x); float LLWidth=LLFace<2?LLHalf.y:LLHalf.x; float LLSpacing=LLFace<2?LLStep.y:LLStep.x;\n"
        " LLColumn=clamp((int)floor((LLAlong+LLWidth)/LLSpacing),0,LLCount-1);\n"
        " LLRowOffset=LLFace<2?LLFace*(int)LLCells.y:2*(int)LLCells.y+(LLFace-2)*(int)LLCells.x; }\n");
    Code.ReplaceInline(TEXT("POS"),Position,ESearchCase::CaseSensitive);
    Code.ReplaceInline(TEXT("LL"),Prefix,ESearchCase::CaseSensitive);
    return Code;
}

// Pressure-grid index -> centred XY/absolute Z. The query applies geographic
// lateral reflection once, after this proper-rotation Niagara grid coordinate.
inline FString RaftSimLiquidBoundaryGridPositionHlsl(const TCHAR* Index,const TCHAR* Profile)
{
    return RaftSimLiquidBoundaryLayoutHlsl(Profile,TEXT("gridStage"))+
        FString::Printf(TEXT("float3 stageGridPosition=float3((float2((%s).xy)+0.5)*gridStageStep.xy-0.5*gridStageComputeExtent.xy,gridStageOrigin.z+((%s).z+0.5)*gridStageStep.z);\n"),Index,Index);
}
