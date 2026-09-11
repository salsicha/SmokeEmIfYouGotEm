#pragma once

#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "NiagaraSystem.h"

namespace RaftSimLiquidSecondarySurface
{
inline FNiagaraVariable Variable()
{
    return FNiagaraVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceRenderTargetVolume::StaticClass()),TEXT("User.RiverSecondarySurface"));
}

inline bool Install(UNiagaraSystem* System)
{
    if (!System || System->GetOutermost()!=GetTransientPackage()) return false;
    auto& Parameters=System->GetExposedParameters();
    if (Parameters.IndexOf(Variable())!=INDEX_NONE) return false;
    auto* Volume=NewObject<UNiagaraDataInterfaceRenderTargetVolume>(System,TEXT("RiverSecondarySurface"));
    Volume->Size=FIntVector(136,136,48);
    Volume->bInheritUserParameterSettings=false;
    Volume->bOverrideFormat=true;Volume->OverrideRenderTargetFormat=RTF_RGBA16f;
    Volume->OverrideRenderTargetFilter=TF_Bilinear;
    Parameters.AddParameter(Variable());Parameters.SetDataInterface(Volume,Variable());
    return true;
}

// The renderer publishes the completed field after simulation. The next step
// samples the previous simulation state, not the native pre-reconstruction SDF.
// Split half-float age matches the primary surface's existing GPU clock.
inline FString Sample()
{
    return TEXT(R"HLSL(
// RiverSharedSecondarySurface: completed rendered SDF; read-only in Niagara.
float4 surfaceValue; RiverSurface.SampleRenderTargetValue(CurrUnit,0,surfaceValue);
float surfaceAge=surfaceValue.b+surfaceValue.a;
float ageGap=RiverAge-surfaceAge;
bool surfaceReady=surfaceAge>0 && all(isfinite(surfaceValue)) && isfinite(ageGap) &&
                  ageGap>=-0.0005 && ageGap<=min(0.25,max(0.05,2.0*SimDt));
float phi=surfaceValue.r;
)HLSL");
}

inline FString Gradient()
{
    return TEXT(R"HLSL(
int sx,sy,sz; RiverSurface.GetRenderTargetSize(sx,sy,sz);
float3 du=1.0/float3(sx,sy,sz);
float4 xp,xm,yp,ym,zp,zm;
RiverSurface.SampleRenderTargetValue(CurrUnit+float3(du.x,0,0),0,xp);
RiverSurface.SampleRenderTargetValue(CurrUnit-float3(du.x,0,0),0,xm);
RiverSurface.SampleRenderTargetValue(CurrUnit+float3(0,du.y,0),0,yp);
RiverSurface.SampleRenderTargetValue(CurrUnit-float3(0,du.y,0),0,ym);
RiverSurface.SampleRenderTargetValue(CurrUnit+float3(0,0,du.z),0,zp);
RiverSurface.SampleRenderTargetValue(CurrUnit-float3(0,0,du.z),0,zm);
float3 grad=float3(xp.r-xm.r,yp.r-ym.r,zp.r-zm.r)/(2.0*du*RiverExtents);
)HLSL");
}

// Classify the integrated endpoint against a characteristic prediction of the
// completed surface. This corrects pre-step state labels; it is not a claim
// that the predicted level set equals the new particle-reconstructed surface.
inline FString EndpointPrediction()
{
    return TEXT(R"HLSL(
// RiverSecondaryEndpointPrediction: integrate first, then classify phase.
if(OutAlive && surfaceReady && SimDt>0)
{
    float3 delta=OutPosition-Position;
    float3 endUnit=CurrUnit+float3(dot(delta,normalize(RiverUnitToWorld[0].xyz)),
        dot(delta,normalize(RiverUnitToWorld[1].xyz)),dot(delta,normalize(RiverUnitToWorld[2].xyz)))/RiverExtents;
    float duration=max(ageGap,0.0);
    float3 endFlow,midFlow;
    SimGridReader.SamplePreviousGridVector3Value<Attribute="Velocity">(endUnit,endFlow);
    float3 midUnit=endUnit-0.5*duration*endFlow/RiverExtents;
    SimGridReader.SamplePreviousGridVector3Value<Attribute="Velocity">(midUnit,midFlow);
    float3 previousUnit=endUnit-duration*midFlow/RiverExtents;
    float4 endpointSurface;RiverSurface.SampleRenderTargetValue(previousUnit,0,endpointSurface);
    if(any(previousUnit<0) || any(previousUnit>1) || !all(isfinite(endpointSurface)) || !all(isfinite(midFlow))) OutAlive=false;
    else
    {
        float endPhi=endpointSurface.r;
        OutState=abs(endPhi)<FoamThickness?0:endPhi>0?1:2;
        AgingRate=OutState==0?FoamAgingRate:OutState==1?SprayAgingRate:BubbleAgingRate;
        OutSurfacePhi=endPhi;
    }
}
)HLSL");
}
}
