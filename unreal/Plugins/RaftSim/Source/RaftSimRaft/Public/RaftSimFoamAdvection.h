#pragma once
#include "CoreMinimal.h"

// BFECC corrects reversible transport only. Generation, decay and shore/tongue
// attenuation must be applied ONCE by the caller, after this operator.
// This transports a presentation concentration, not conservative air volume.
namespace RaftSimFoamAdvection
{
struct FStencil
{
    int32 Index[4] = {};
    double Weight[4] = {};
    bool Valid = false;
};

inline FStencil Stencil(int32 W,int32 H,FVector2D P)
{
    FStencil S;
    if(W<2 || H<2 || !FMath::IsFinite(P.X) || !FMath::IsFinite(P.Y) ||
        P.X<0 || P.Y<0 || P.X>W-1 || P.Y>H-1)return S;
    const int32 X=FMath::Min(FMath::FloorToInt(P.X),W-2),Y=FMath::Min(FMath::FloorToInt(P.Y),H-2);
    const double Fx=P.X-X,Fy=P.Y-Y;
    S.Index[0]=Y*W+X;S.Index[1]=Y*W+X+1;S.Index[2]=(Y+1)*W+X;S.Index[3]=(Y+1)*W+X+1;
    S.Weight[0]=(1-Fx)*(1-Fy);S.Weight[1]=Fx*(1-Fy);S.Weight[2]=(1-Fx)*Fy;S.Weight[3]=Fx*Fy;
    S.Valid=true;return S;
}

inline float Sample(const FStencil& S,TConstArrayView<float> Values)
{
    double Result=0;
    for(int32 K=0;K<4;++K)if(S.Weight[K]>0)Result+=S.Weight[K]*Values[S.Index[K]];
    return Result;
}

inline bool Ready(const FStencil& S,TConstArrayView<uint8> Valid)
{
    if(!S.Valid)return false;
    for(int32 K=0;K<4;++K)if(S.Weight[K]>0 && !Valid[S.Index[K]])return false;
    return true;
}

// Conservative eligibility, not a boundary condition: require the entire node
// rectangle containing a characteristic to be wet at both endpoints in time.
// This may reject some usable diagonal paths, but never corrects across a rock
// just because the two endpoints happen to be wet. The caller keeps its original
// first-order result wherever correction is unavailable.
inline bool WetPath(int32 I,int32 W,const FStencil& S,TConstArrayView<uint8> OldWet,TConstArrayView<uint8> NewWet)
{
    if(!S.Valid)return false;
    int32 MinX=I%W,MaxX=MinX,MinY=I/W,MaxY=MinY;
    for(int32 K=0;K<4;++K)if(S.Weight[K]>0)
    {
        MinX=FMath::Min(MinX,S.Index[K]%W);MaxX=FMath::Max(MaxX,S.Index[K]%W);
        MinY=FMath::Min(MinY,S.Index[K]/W);MaxY=FMath::Max(MaxY,S.Index[K]/W);
    }
    for(int32 Y=MinY;Y<=MaxY;++Y)for(int32 X=MinX;X<=MaxX;++X)
        if(!OldWet[Y*W+X] || !NewWet[Y*W+X])return false;
    return true;
}

struct FResult
{
    TArray<float> Values;
    TArray<uint8> Corrected;
    int32 CorrectedCount=0,LimitedCount=0;
};

// Invert the SAME discrete departure map. Merely negating a spatially varying
// velocity is not its inverse: that introduces a false correction even for an
// affine dye ramp. Newton inversion is local, checked against the original map,
// and refused at folds, incomplete stencils or nonconvergence. This corrects
// spatial interpolation, not the temporal accuracy of the Euler characteristic.
inline FStencil InverseStencil(int32 I,int32 W,int32 H,TConstArrayView<FVector2D> Back,
    FVector2D Guess,TConstArrayView<uint8> OldWet,TConstArrayView<uint8> NewWet,
    TConstArrayView<uint8> ForwardValid)
{
    const FVector2D Target(I%W,I/W);
    for(int32 Iteration=0;Iteration<8;++Iteration)
    {
        const auto S=Stencil(W,H,Guess);
        if(!WetPath(I,W,S,OldWet,NewWet) || !Ready(S,ForwardValid))return {};
        FVector2D Mapped=FVector2D::ZeroVector;
        for(int32 K=0;K<4;++K)if(S.Weight[K]>0)Mapped+=Back[S.Index[K]]*S.Weight[K];
        const FVector2D Error=Target-Mapped;
        const double Fx=Guess.X-S.Index[0]%W,Fy=Guess.Y-S.Index[0]/W;
        const FVector2D DX=(Back[S.Index[1]]-Back[S.Index[0]])*(1-Fy)+(Back[S.Index[3]]-Back[S.Index[2]])*Fy;
        const FVector2D DY=(Back[S.Index[2]]-Back[S.Index[0]])*(1-Fx)+(Back[S.Index[3]]-Back[S.Index[1]])*Fx;
        const double Det=DX.X*DY.Y-DY.X*DX.Y;
        if(!FMath::IsFinite(Det) || Det<=0)return {};
        if(FMath::Max(FMath::Abs(Error.X),FMath::Abs(Error.Y))<1.e-9)return S;
        for(int32 K=0;K<4;++K)if(!ForwardValid[S.Index[K]])return {};
        Guess+=FVector2D((Error.X*DY.Y-DY.X*Error.Y)/Det,(DX.X*Error.Y-Error.X*DX.Y)/Det);
    }
    return {};
}

inline FResult Correct(int32 W,int32 H,TConstArrayView<float> Old,
    TConstArrayView<uint8> OldWet,TConstArrayView<uint8> NewWet,
    TConstArrayView<FVector2D> BackwardNodes,TConstArrayView<FVector2D> Velocity,
    double Spacing,double Dt)
{
    FResult Out;
    const int64 Count=int64(W)*H;
    if(W<2 || H<2 || Count!=Old.Num() || Count!=OldWet.Num() || Count!=NewWet.Num() ||
        Count!=BackwardNodes.Num() || Count!=Velocity.Num() || !FMath::IsFinite(Spacing) ||
        !FMath::IsFinite(Dt) || Spacing<=0 || Dt<=0)return Out;
    const int32 N=Old.Num();
    Out.Values.Init(0,N);Out.Corrected.Init(0,N);
    TArray<FStencil> ForwardStencils;ForwardStencils.SetNum(N);
    TArray<float> Forward,Source;Forward.Init(0,N);Source.Init(0,N);
    TArray<uint8> ForwardValid,SourceValid;ForwardValid.Init(0,N);SourceValid.Init(0,N);
    for(int32 I=0;I<N;++I)
    {
        if(!OldWet[I] || !NewWet[I])continue;
        const auto S=Stencil(W,H,BackwardNodes[I]);ForwardStencils[I]=S;
        if(!WetPath(I,W,S,OldWet,NewWet))continue;
        const float V=Sample(S,Old);
        if(!FMath::IsFinite(V))continue;
        Forward[I]=V;ForwardValid[I]=1;
    }
    for(int32 I=0;I<N;++I)
    {
        if(!ForwardValid[I] || !FMath::IsFinite(Old[I]))continue;
        const FVector2D Reverse=FVector2D(I%W,I/W)+Velocity[I]*(Dt/Spacing);
        const auto S=InverseStencil(I,W,H,BackwardNodes,Reverse,OldWet,NewWet,ForwardValid);
        if(!S.Valid)continue;
        Source[I]=Old[I]+.5f*(Old[I]-Sample(S,Forward));
        SourceValid[I]=FMath::IsFinite(Source[I]);
    }
    for(int32 I=0;I<N;++I)
    {
        const auto& S=ForwardStencils[I];
        if(!ForwardValid[I] || !Ready(S,SourceValid))continue;
        float Low=TNumericLimits<float>::Max(),High=TNumericLimits<float>::Lowest();
        for(int32 K=0;K<4;++K)if(S.Weight[K]>0)
        {Low=FMath::Min(Low,Old[S.Index[K]]);High=FMath::Max(High,Old[S.Index[K]]);}
        const float Candidate=Sample(S,Source);
        if(!FMath::IsFinite(Candidate))continue;
        Out.Values[I]=FMath::Clamp(Candidate,Low,High);Out.Corrected[I]=1;++Out.CorrectedCount;
        Out.LimitedCount+=Candidate<Low || Candidate>High;
    }
    return Out;
}
}
