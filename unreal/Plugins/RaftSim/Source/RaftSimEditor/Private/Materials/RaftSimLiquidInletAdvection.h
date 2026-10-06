#pragma once
#include "RaftSimLiquidBoundaryLayout.h"
#include "RaftSimRegisteredTerrainQuery.h"

// Prescribed inflow is a velocity boundary, not an absorbing particle sink.
// Relax the normal component in a short physical upstream reservoir band.
// Tangential/vertical motion and outgoing boundary rows remain unchanged.
// The prior submerged plane condition remains a final prescribed-inlet limit.
// This is evaluated before the existing swept terrain contact, not after exit
// classification, so the unchanged exit gate still sees actual native motion.
inline FString RaftSimLiquidInletAdvectionHlsl()
{
    return RaftSimLiquidBoundaryLayoutHlsl(TEXT("InletProfile"),TEXT("ib"))+TEXT(
        "float3 inletPosition=Position,inletVelocity=Velocity;\n"
        "InletRawPosition=Position; InletRawVelocity=Velocity; InletFace=0;\n"
        "float3 ibLower,ibWX,ibWY; InletFrame.Get(0,ibLower); InletFrame.Get(1,ibWX); InletFrame.Get(2,ibWY);\n"
        "float3 ia=RaftSimLiquidPhysicalPoint(PreviousPosition,ibLower,ibWX,ibWY);\n"
        "float3 iz=RaftSimLiquidPhysicalPoint(Position,ibLower,ibWX,ibWY);\n"
        "float3 ibExtent=float3(2*ibHalf,ibStep.z*ibCells.z);\n"
        "if(ibRect && DeltaTime>0 && isfinite(DeltaTime) && all(isfinite(ia)) && all(isfinite(iz)) && all(isfinite(Velocity)) && all(ia>=0) && all(ia<=ibExtent)) {\n"
        " // NativeInletRelaxation: physical boundary only, never regional cuts.\n"
        " float irDistance=1.e30; int irFace=-1; bool irTie=false;\n"
        " for(int irF=0;irF<4;++irF) {\n"
        "  float irD=(irF%2)==0?ia[irF/2]:ibExtent[irF/2]-ia[irF/2];\n"
        "  if(irD<irDistance-0.000001) { irDistance=irD; irFace=irF; irTie=false; }\n"
        "  else if(abs(irD-irDistance)<=0.000001) irTie=true;\n"
        " }\n"
        " float irWidth=min(4*ibStep[irFace/2],0.25*ibExtent[irFace/2]);\n"
        " if(!irTie && irDistance<irWidth && iz.z>=0 && iz.z<=ibExtent.z) {\n"
        "  int irTangent=irFace<2?1:0;\n"
        "  int irColumn=clamp((int)floor(ia[irTangent]/ibStep[irTangent]),0,(int)ibCells[irTangent]-1);\n"
        "  int irOffset=irFace==0?0:irFace==1?(int)ibCells.y:irFace==2?2*(int)ibCells.y:2*(int)ibCells.y+(int)ibCells.x;\n"
        "  float3 irRow; InletProfile.Get(ibHeader+irOffset+irColumn,irRow);\n"
        "  if(all(isfinite(irRow)) && irRow.z>0) {\n"
        "   float3 irNormal=(irFace<2?ibWX:ibWY)*((irFace%2)==0?1:-1);\n"
        "   float3 irWorldFace=PreviousPosition-irNormal*irDistance;\n"
        "   float distance,encoded; float3 closest,normal,wallVelocity; bool valid;\n")+
        RaftSimRegisteredTerrainQueryHlsl(TEXT("irWorldFace"),true)+TEXT(
        "   float irDepth=irRow.y-closest.z;\n"
        "   if(valid && isfinite(distance) && distance>0 && isfinite(irDepth) && irDepth>0) {\n"
        "    float irAverage,irEnd; RaftSimLiquidInletRelaxation(irDistance,irWidth,irDepth,DeltaTime,irAverage,irEnd);\n"
        "    float3 irTravel=Position-PreviousPosition;\n"
        "    inletPosition=Position+irNormal*((irRow.z*DeltaTime-dot(irTravel,irNormal))*(1-irAverage));\n"
        "    inletVelocity=Velocity+irNormal*((irRow.z-dot(Velocity,irNormal))*(1-irEnd));\n"
        "    InletFace=irFace+1;\n"
        "    iz=RaftSimLiquidPhysicalPoint(inletPosition,ibLower,ibWX,ibWY);\n"
        "   }\n"
        "  }\n"
        " }\n"
        " float ibFirst=2; int ibFace=-1; bool ibTie=false;\n"
        " for(int ibAxis=0;ibAxis<3;++ibAxis) {\n"
        "  if(iz[ibAxis]>=0 && iz[ibAxis]<=ibExtent[ibAxis]) continue;\n"
        "  bool ibHigh=iz[ibAxis]>ibExtent[ibAxis];\n"
        "  float ibT=((ibHigh?ibExtent[ibAxis]:0)-ia[ibAxis])/(iz[ibAxis]-ia[ibAxis]);\n"
        "  if(ibT<ibFirst-8*1.192092896e-7) { ibFirst=ibT; ibFace=2*ibAxis+(ibHigh?1:0); ibTie=false; }\n"
        "  else if(abs(ibT-ibFirst)<=8*1.192092896e-7) ibTie=true;\n"
        " }\n"
        " if(!ibTie && ibFace>=0 && ibFace<4 && ibFirst>=0 && ibFirst<=1) {\n"
        "  float3 ibHit=lerp(ia,iz,ibFirst); int ibTangent=ibFace<2?1:0;\n"
        "  int ibColumn=clamp((int)floor(ibHit[ibTangent]/ibStep[ibTangent]),0,(int)ibCells[ibTangent]-1);\n"
        "  int ibOffset=ibFace==0?0:ibFace==1?(int)ibCells.y:ibFace==2?2*(int)ibCells.y:2*(int)ibCells.y+(int)ibCells.x;\n"
        "  float3 ibRow; InletProfile.Get(ibHeader+ibOffset+ibColumn,ibRow);\n"
        "  if(ibRow.z>=0 && all(isfinite(ibRow)) && ibHit.z+ibOrigin.z<ibRow.y) {\n"
        "   float3 ibWorldHit=lerp(PreviousPosition,inletPosition,ibFirst);\n"
        "   float distance,encoded; float3 closest,normal,wallVelocity; bool valid;\n")+
        RaftSimRegisteredTerrainQueryHlsl(TEXT("ibWorldHit"),true)+TEXT(
        "   if(valid && isfinite(distance) && distance>0) {\n"
        "    float3 ibNormal=(ibFace<2?ibWX:ibWY)*((ibFace%2)==0?1:-1);\n"
        "    float3 ibTravel=inletPosition-PreviousPosition;\n"
        "    inletPosition=PreviousPosition+(ibTravel-ibNormal*dot(ibTravel,ibNormal))+ibNormal*(ibRow.z*DeltaTime);\n"
        "    inletPosition=RaftSimLiquidPrescribedNormalPosition(PreviousPosition,inletPosition,ibNormal,ibRow.z*DeltaTime);\n"
        "    inletVelocity=inletVelocity+ibNormal*(ibRow.z-dot(inletVelocity,ibNormal)); InletFace=ibFace+1;\n"
        "   }\n"
        "  }\n"
        " }\n"
        "}\n");
}
