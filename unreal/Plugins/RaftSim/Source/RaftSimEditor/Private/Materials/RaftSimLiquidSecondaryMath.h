#pragma once
#include "RaftSimSecondaryTerrainSweep.h"
#include "RaftSimLiquidSecondarySurface.h"

namespace RaftSimLiquidSecondaryMath
{
inline FString Curl()
{
    return TEXT(R"HLSL(
// RiverMetricSecondaryCurl: actual anisotropic cell dimensions, inverse seconds.
int nx,ny,nz; Grid.GetNumCells(nx,ny,nz);
int3 n=int3(nx,ny,nz), p=int3(IndexX,IndexY,IndexZ);
int3 lo=max(p-1,0), hi=min(p+1,n-1);
float3 cell=RiverExtents/float3(n);
float3 xp,xm,yp,ym,zp,zm;
Grid.GetPreviousVectorValue<Attribute="Velocity">(hi.x,p.y,p.z,xp);
Grid.GetPreviousVectorValue<Attribute="Velocity">(lo.x,p.y,p.z,xm);
Grid.GetPreviousVectorValue<Attribute="Velocity">(p.x,hi.y,p.z,yp);
Grid.GetPreviousVectorValue<Attribute="Velocity">(p.x,lo.y,p.z,ym);
Grid.GetPreviousVectorValue<Attribute="Velocity">(p.x,p.y,hi.z,zp);
Grid.GetPreviousVectorValue<Attribute="Velocity">(p.x,p.y,lo.z,zm);
float3 ddx=(xp-xm)/(max(hi.x-lo.x,1)*cell.x);
float3 ddy=(yp-ym)/(max(hi.y-lo.y,1)*cell.y);
float3 ddz=(zp-zm)/(max(hi.z-lo.z,1)*cell.z);
curl=float3(ddy.z-ddz.y,ddz.x-ddx.z,ddx.y-ddy.x);
)HLSL");
}

inline FString Emission(bool SharedSurface=false)
{
    FString Code=TEXT(R"HLSL(
// RiverSurfaceEmissionRate: particles / m2 / second, not particles / frame.
// Empirical aeration response, not a resolved two-phase entrainment model.
int nx,ny,nz; RiverFlow.GetNumCells(nx,ny,nz);
float3 cell=RiverExtents/float3(nx,ny,nz);
float band=max(cell.x,max(cell.y,cell.z));
float3 velocity; RiverFlow.SamplePreviousGridVector3Value<Attribute="Velocity">(CurrUnit,velocity);
float activity=smoothstep(1.2,4.0,VorticityMagnitude)*saturate((length(velocity)-50.0)/150.0);
float support=saturate(1.0+SDFValue/band);
// One-sided triangular delta kernel integrates to one across the wet band.
float areaM2=2.0*cell.x*cell.y*cell.z/band*0.0001*support;
float expected=120.0*areaM2*activity*SimDt;
bool valid=SimDt>0 && SimDt<=0.25 && isfinite(expected) && SDFValue<=0 && SDFValue>-band;
float4 boundary;
RiverBoundary.GetPreviousVector4Value<Attribute="SolidVelocity_Boundary">(IndexX,IndexY,IndexZ,boundary);
valid=valid && round(boundary.w)!=1 && round(boundary.w)!=3;
int emitted=valid ? int(floor(expected))+(frac(expected)>Random0To1 ? 1 : 0) : 0;
if (emitted>0)
{
    int sx,sy,sz; RiverSdf.GetNumCells(sx,sy,sz);
    float3 du=1.0/float3(sx,sy,sz);
    float xp,xm,yp,ym,zp,zm;
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit+float3(du.x,0,0),xp);
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit-float3(du.x,0,0),xm);
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit+float3(0,du.y,0),yp);
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit-float3(0,du.y,0),ym);
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit+float3(0,0,du.z),zp);
    RiverSdf.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit-float3(0,0,du.z),zm);
    float3 grad=float3(xp-xm,yp-ym,zp-zm)/(2.0*du*RiverExtents);
    float g2=dot(grad,grad);
    // Avoid seeding the artificial vertical walls of the finite review window.
    float3 unit=CurrUnit-SDFValue*grad/max(g2,0.01)/RiverExtents;
    if (g2>0.04 && grad.z>0.2*sqrt(g2) && all(unit>du) && all(unit<1.0-du))
    {
        int2 size; EmissionPositions.GetNumCells(size.x,size.y);
        float previous=0; EmissionCounter.SetParticleNeighborCount(0,emitted,previous);
        int first=max(0,int(previous));
        for(int i=first;i<first+emitted && i<MaxSecondaryParticlesPerFrame;++i)
        {
            int unused=0; int x=i%size.x,y=i/size.x;
            EmissionPositions.SetGridValue(x,y,0,unit.x,unused);
            EmissionPositions.SetGridValue(x,y,1,unit.y,unused);
            EmissionPositions.SetGridValue(x,y,2,unit.z,unused);
        }
    }
}
)HLSL");
    if (SharedSurface)
    {
        Code=RaftSimLiquidSecondarySurface::Sample()+Code;
        Code.ReplaceInline(TEXT("SDFValue"),TEXT("phi"));
        Code.ReplaceInline(TEXT("bool valid=SimDt>0"),TEXT("bool valid=surfaceReady && SimDt>0"));
        const int32 Start=Code.Find(TEXT("    int sx,sy,sz; RiverSdf.GetNumCells"));
        const int32 End=Code.Find(TEXT("    float g2=dot(grad,grad);"));
        if (Start==INDEX_NONE || End<=Start) return FString();
        Code=Code.Left(Start)+RaftSimLiquidSecondarySurface::Gradient()+Code.Mid(End);
    }
    return Code;
}

inline FString WorldVelocity(const TCHAR* Variable,const TCHAR* Matrix)
{
    return FString::Printf(TEXT("\n// RiverSecondaryWorldVelocity: grid vector -> world, without grid scaling.\n"
        "{ float3 local=%s; %s=local.x*normalize(%s[0].xyz)+local.y*normalize(%s[1].xyz)+local.z*normalize(%s[2].xyz); }\n"),
        Variable,Variable,Matrix,Matrix,Matrix);
}

inline FString Update(bool HasColor,bool SharedSurface=false,bool ExactContact=false,bool EndpointPrediction=false)
{
    FString Code=TEXT(R"HLSL(
// RiverSecondaryTimeIntegration: all particle position/velocity are world-space.
OutPosition=Position; OutVelocity=Velocity; OutAlive=Alive; OutState=State; AgingRate=0;
float3 flow; SimGridReader.SamplePreviousGridVector3Value<Attribute="Velocity">(CurrUnit,flow);
)HLSL");
    Code+=WorldVelocity(TEXT("flow"),TEXT("RiverUnitToWorld"));
    if (HasColor) Code+=TEXT("OutColor=float4(1,1,1,1);\n");
    Code+=TEXT(R"HLSL(
float phi; SDFReader.SamplePreviousGridFloatValue<Attribute="SDF">(CurrUnit,phi);
if (SimDt<0 || SimDt>0.25 || !isfinite(SimDt) || !all(isfinite(flow)) || !isfinite(phi)) OutAlive=false;
else if (SimDt>0)
{
    if (abs(phi)<FoamThickness)
    {
        OutState=0; AgingRate=FoamAgingRate;
        OutVelocity=flow; OutPosition=Position+flow*SimDt;
    }
    else if (phi>0)
    {
        OutState=1; AgingRate=SprayAgingRate;
        OutVelocity=Velocity+Gravity*SimDt;
        OutPosition=Position+Velocity*SimDt+0.5*Gravity*SimDt*SimDt;
    }
    else
    {
        OutState=2; AgingRate=BubbleAgingRate;
        // Empirical 4/s relaxation; integrate constant flow/buoyancy exactly.
        float3 terminal=flow+BubbleBounancy/4.0;
        float decay=exp(-4.0*SimDt);
        OutVelocity=terminal+(Velocity-terminal)*decay;
        OutPosition=Position+terminal*SimDt+(Velocity-terminal)*(1.0-decay)/4.0;
    }
}
if (any(CurrUnit<0) || any(CurrUnit>1) || !all(isfinite(OutPosition)) || !all(isfinite(OutVelocity))) OutAlive=false;
// RiverSecondaryVectorBoundary: check the swept path in the actual vector grid.
int bx,by,bz; RiverBoundary.GetNumCells(bx,by,bz);
float3 delta=OutPosition-Position;
float3 unitDelta=float3(dot(delta,normalize(RiverUnitToWorld[0].xyz))/length(RiverUnitToWorld[0].xyz),
                       dot(delta,normalize(RiverUnitToWorld[1].xyz))/length(RiverUnitToWorld[1].xyz),
                       dot(delta,normalize(RiverUnitToWorld[2].xyz))/length(RiverUnitToWorld[2].xyz));
for(int step=0;step<=4;++step)
{
    float3 unit=CurrUnit+unitDelta*(step*0.25);
    int3 index=clamp(int3(unit*float3(bx,by,bz)),0,int3(bx,by,bz)-1);
    float4 boundary; RiverBoundary.GetPreviousVector4Value<Attribute="SolidVelocity_Boundary">(index.x,index.y,index.z,boundary);
    if(any(unit<0) || any(unit>1) || round(boundary.w)==1 || round(boundary.w)==3) OutAlive=false;
}
)HLSL");
    if (SharedSurface)
    {
        Code.ReplaceInline(TEXT("float phi; SDFReader.SamplePreviousGridFloatValue<Attribute=\"SDF\">(CurrUnit,phi);"),
            *(RaftSimLiquidSecondarySurface::Sample()+RaftSimLiquidSecondarySurface::Gradient()+
              TEXT("OutSurfaceAge=surfaceAge; OutSurfacePhi=phi;\n")));
        Code.ReplaceInline(TEXT("if (SimDt<0"),TEXT("if (!surfaceReady || SimDt<0"));
        Code.ReplaceInline(TEXT("OutVelocity=flow; OutPosition=Position+flow*SimDt;"),TEXT(R"HLSL(
        // Foam is constrained to the shared interface, then advected. Never
        // apply a constant world-up offset to camouflage two different SDFs.
        float g2=dot(grad,grad);
        float3 correction=-phi*grad/max(g2,0.04);
        float3 worldCorrection=correction.x*normalize(RiverUnitToWorld[0].xyz)+
            correction.y*normalize(RiverUnitToWorld[1].xyz)+correction.z*normalize(RiverUnitToWorld[2].xyz);
        OutVelocity=flow; OutPosition=Position+worldCorrection+flow*SimDt;
        if(g2<0.04 || !all(isfinite(grad))) OutAlive=false;
)HLSL"));
    }
    if(EndpointPrediction)
    {
        if(!SharedSurface) return FString();
        Code.ReplaceInline(TEXT("// RiverSecondaryVectorBoundary:"),*(RaftSimLiquidSecondarySurface::EndpointPrediction()+TEXT("// RiverSecondaryVectorBoundary:")));
    }
    if(ExactContact) Code+=RaftSimSecondaryTerrainSweepHlsl();
    return Code;
}
}
