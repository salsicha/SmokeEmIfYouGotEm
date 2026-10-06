#pragma once
#include "CoreMinimal.h"

namespace RaftSimFoamEvolution
{
// Presentation closure for fresh-water froth, not persistent sea foam. The
// existing release survives at active breaking sites; without a local source,
// rising bubbles disappear (less than 0.04% remains after one second).
inline float PoolReleaseRetention(float LocalSource,float DeltaSeconds)
{
    if(DeltaSeconds<=0.f)return 1.f;
    const float Activity=FMath::SmoothStep(.01f,.1f,LocalSource);
    return FMath::Exp(-8.f*(1.f-Activity)*DeltaSeconds);
}

inline float Resolve(float Advected,float Source,float AttackBlend,float Tongue,float Shore,bool bHold)
{
    // A held clock must not repeatedly apply generation or attenuation.
    // Wet/domain membership and spatial remapping are handled by the caller.
    if(bHold)return Advected;
    float Result=FMath::Clamp(Source>Advected
        ? FMath::Lerp(Advected,Source,FMath::Clamp(AttackBlend,0.f,1.f)) : Advected,0.f,1.f);
    if(Tongue>0.f)Result*=1.f-.9f*FMath::Min(Tongue,1.f);
    return Result*Shore;
}

inline float RemapHeld(TConstArrayView<float> Field,int32 Width,int32 Height,float X,float Y)
{
    if(Width<2 || Height<2 || int64(Width)*Height!=Field.Num() ||
        !FMath::IsFinite(X) || !FMath::IsFinite(Y) || X<0 || Y<0 || X>Width-1 || Y>Height-1)return 0.f;
    // The last row/column is an observed node, not an unknown exterior cell.
    // No value outside the old field is extrapolated or clamped to its edge.
    const int32 IX=FMath::Min(FMath::FloorToInt(X),Width-2),IY=FMath::Min(FMath::FloorToInt(Y),Height-2);
    const float FX=X-IX,FY=Y-IY;
    const auto Blend=[](float A,float B,float Alpha)
    {return Alpha==0.f ? A : (Alpha==1.f ? B : FMath::Lerp(A,B,Alpha));};
    return Blend(Blend(Field[IY*Width+IX],Field[IY*Width+IX+1],FX),
        Blend(Field[(IY+1)*Width+IX],Field[(IY+1)*Width+IX+1],FX),FY);
}
}
