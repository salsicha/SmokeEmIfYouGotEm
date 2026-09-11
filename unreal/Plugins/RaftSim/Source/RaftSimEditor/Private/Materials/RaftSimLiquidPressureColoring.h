#pragma once
#include "CoreMinimal.h"

// The native pressure dispatch has NX/2 threads. Wide (+/-2) dependencies
// require floor(index/2) coloring, not ordinary nearest-neighbor red/black.
// For NX=4k+2, the last thread owns BOTH remaining parity lanes in one color
// and no cells in the other. Never round the physical grid or drop its tail.
namespace RaftSimLiquidPressureColoring
{
inline int32 X(int32 Thread,int32 Y,int32 Z,int32 Iteration,int32 GlobalPhase=0)
{
    return (Thread/2)*4+Thread%2+2*((Y/2+Z/2+Iteration%2+GlobalPhase)%2);
}
inline int32 Lanes(int32 Base,int32 NX)
{
    if (Base<0 || Base>=NX) return 0;
    return NX%4==2 && Base==NX-2 ? 2 : 1;
}
inline FString Wrap(const FString& Body,const FString& PressureGrid)
{
    return FString::Printf(TEXT(
        "// CompatiblePartialColorTail: bound every read/write; keep both final parity lanes.\n"
        "Pressure=0; int pressureNX,pressureNY,pressureNZ; %s.GetNumCells(pressureNX,pressureNY,pressureNZ);\n"
        "int pressureLanes=(IndexX>=0 && IndexX<pressureNX && IndexY>=0 && IndexY<pressureNY && IndexZ>=0 && IndexZ<pressureNZ) ? "
        "((pressureNX%%4==2 && IndexX==pressureNX-2) ? 2 : 1) : 0;\n"
        "for(int pressureLane=0;pressureLane<pressureLanes;++pressureLane) {\n"),*PressureGrid)+
        Body.Replace(TEXT("int3 p=int3(IndexX,IndexY,IndexZ);"),TEXT("int3 p=int3(IndexX+pressureLane,IndexY,IndexZ);"))+
        TEXT("}\n");
}
}
