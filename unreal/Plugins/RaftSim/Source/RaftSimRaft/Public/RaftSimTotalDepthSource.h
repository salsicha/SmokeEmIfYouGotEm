#pragma once
#include "CoreMinimal.h"
#include "RaftSimDetailSampleGrid.h"

// Immutable sampled mean/source packet, not the evolving simulation state.
// Point-grid bilinear resampling of h/hu/hv preserves their interpolation;
// it is NOT a conservative finite-volume remap or surveyed bathymetry.
struct FRaftSimTotalDepthSource
{
    FIntPoint Size=FIntPoint(128,128);
    FVector2f OriginMeters=FVector2f::ZeroVector;
    FVector2f CoarseSampleOriginMeters=FVector2f::ZeroVector;
    float CellMeters=.5f;
    double SampleSeconds=0;
    uint64 Revision=0;
    TArray<FVector4f> State; // h,hu,hv,0; source supplies no transported foam
    TArray<float> Bed;
    TArray<FVector2f> Reference; // same-sample actual bed, carrier surface
    TArray<FVector4f> ExteriorState; // 512 ghost centres: west/east/south/north, h/hu/hv/0
    TArray<float> ExteriorBed;
    TArray<float> FaceNormalVelocity; // independent actual face observations, positive-axis orientation
    // Optional diagnostic source stencil. Three actual fine-cell rings,
    // including corners; no new evolving state or pressure boundary policy.
    TArray<FVector4f> PressureStencilState;
    TArray<float> PressureStencilBed;
    static constexpr int32 PressureStencilCount=134*134-128*128;
    static FIntPoint PressureStencilCell(int32 I)
    {
        check(I>=0 && I<PressureStencilCount);
        if(I<3*134)return FIntPoint(I%134-3,I/134-3);
        I-=3*134;
        if(I<128*6)return FIntPoint(I%6<3?I%6-3:128+I%6-3,I/6);
        I-=128*6;return FIntPoint(I%134-3,128+I/134);
    }
    // Only a moved packet owns one closing observation on the OLD window at
    // this exact native instant. It is sampled before changing coordinates,
    // never inferred by clamping/remapping the new exterior.
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> ClosingWindowSource;

    static FIntPoint ExteriorCell(int32 I)
    {
        check(I>=0 && I<512);
        if(I<128)return FIntPoint(-1,I);
        if(I<256)return FIntPoint(128,I-128);
        if(I<384)return FIntPoint(I-256,-1);
        return FIntPoint(I-384,128);
    }

    static FVector2f ExteriorFace(int32 I)
    {
        const auto P=ExteriorCell(I);
        if(I<256)return FVector2f(I<128?-.5f:127.5f,P.Y);
        return FVector2f(P.X,I<384?-.5f:127.5f);
    }

    bool Validate(FString& Error) const
    {
        FRaftSimDetailSampleGrid Grid;
        if(Size!=FIntPoint(128,128) || CellMeters!=.5f || OriginMeters.ContainsNaN() ||
            !Grid.Register(OriginMeters) || CoarseSampleOriginMeters!=Grid.CoarseOriginMeters ||
            !FMath::IsFinite(SampleSeconds) || !Revision || State.Num()!=128*128 || Bed.Num()!=State.Num() || Reference.Num()!=State.Num() ||
            ExteriorState.Num()!=512 || ExteriorBed.Num()!=512 || FaceNormalVelocity.Num()!=512)
        {Error=TEXT("Invalid total-depth live source registration or array dimensions");return false;}
        for(int32 I=0;I<State.Num();++I)
        {
            const auto S=State[I];
            if(S.ContainsNaN() || S.X<0 || S.W!=0 || (S.X==0 && (S.Y!=0 || S.Z!=0)) ||
                (S.X>0 && (!FMath::IsFinite(S.Y/S.X) || !FMath::IsFinite(S.Z/S.X))) ||
                !FMath::IsFinite(Bed[I]) || Reference[I].ContainsNaN() || Bed[I]!=Reference[I].X)
            {Error=FString::Printf(TEXT("Invalid unmasked total-depth live source cell%d"),I);return false;}
        }
        for(int32 I=0;I<512;++I)
        {
            const auto S=ExteriorState[I];
            if(S.ContainsNaN() || S.X<0 || S.W!=0 || (S.X==0 && (S.Y!=0 || S.Z!=0)) ||
                (S.X>0 && (!FMath::IsFinite(S.Y/S.X) || !FMath::IsFinite(S.Z/S.X))) || !FMath::IsFinite(ExteriorBed[I]) ||
                !FMath::IsFinite(FaceNormalVelocity[I]))
            {Error=FString::Printf(TEXT("Invalid live exterior source cell%d"),I);return false;}
        }
        if(!PressureStencilState.IsEmpty() || !PressureStencilBed.IsEmpty())
        {
            if(PressureStencilState.Num()!=PressureStencilCount || PressureStencilBed.Num()!=PressureStencilCount)
            {Error=TEXT("Incomplete pressure-stencil source halo");return false;}
            for(int32 I=0;I<PressureStencilCount;++I)
            {
                const auto S=PressureStencilState[I];
                if(S.ContainsNaN() || S.X<0 || S.W!=0 || (S.X==0 && (S.Y!=0 || S.Z!=0)) ||
                    (S.X>0 && (!FMath::IsFinite(S.Y/S.X) || !FMath::IsFinite(S.Z/S.X))) || !FMath::IsFinite(PressureStencilBed[I]))
                {Error=FString::Printf(TEXT("Invalid pressure-stencil source cell%d"),I);return false;}
            }
        }
        Error.Reset();return true;
    }

    static TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Build(
        TConstArrayView<FVector4f> CoarseHUV,TConstArrayView<FVector4f> CoarseGeometry,TConstArrayView<float> FaceVelocity,
        FVector2f Origin,double SampleTime,uint64 Revision,FString& Error)
    {
        FRaftSimDetailSampleGrid Grid;
        const bool Wide=CoarseHUV.Num()==69*69;
        if(!Grid.Register(Origin) || (CoarseHUV.Num()!=67*67 && !Wide) || CoarseGeometry.Num()!=CoarseHUV.Num() || FaceVelocity.Num()!=512)
        {Error=TEXT("Live source requires paired67x67 samples including actual exterior halo");return nullptr;}
        TArray<FVector4f> Conserved;Conserved.Reserve(CoarseHUV.Num());
        for(int32 I=0;I<CoarseHUV.Num();++I)
        {
            const auto F=CoarseHUV[I],G=CoarseGeometry[I];
            if(F.ContainsNaN() || F.X<0 || G.ContainsNaN() || G.Z!=F.X)
            {Error=FString::Printf(TEXT("Invalid paired live source sample%d"),I);return nullptr;}
            // bWet and legacy1cm cutoff deliberately do not participate.
            // h is independent of rounded absolute (surface-bed).
            Conserved.Add(FVector4f(F.X,F.X*F.Y,F.X*F.Z,0));
            if(Conserved.Last().ContainsNaN())
            {Error=TEXT("Live source momentum is not representable");return nullptr;}
        }
        const auto Sample=[&](TConstArrayView<FVector4f> Values,int32 X,int32 Y)
        {return Wide?Grid.InterpolatePressureHalo<FVector4f>(Values,X,Y):Grid.InterpolateHalo<FVector4f>(Values,X,Y);};
        auto R=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>();
        R->OriginMeters=Origin;R->SampleSeconds=SampleTime;R->Revision=Revision;
        R->FaceNormalVelocity.Append(FaceVelocity.GetData(),FaceVelocity.Num());
        R->CoarseSampleOriginMeters=Grid.CoarseOriginMeters;
        R->State.SetNumUninitialized(128*128);R->Bed.SetNumUninitialized(128*128);R->Reference.SetNumUninitialized(128*128);
        for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
        {
            const int32 I=Y*128+X;
            R->State[I]=Sample(Conserved,X,Y);
            const auto G=Sample(CoarseGeometry,X,Y);
            R->Bed[I]=G.X;R->Reference[I]=FVector2f(G.X,G.Y);
        }
        R->ExteriorState.SetNumUninitialized(512);R->ExteriorBed.SetNumUninitialized(512);
        for(int32 I=0;I<512;++I)
        {
            const auto P=ExteriorCell(I);
            R->ExteriorState[I]=Sample(Conserved,P.X,P.Y);
            R->ExteriorBed[I]=Sample(CoarseGeometry,P.X,P.Y).X;
        }
        if(Wide)
        {
            R->PressureStencilState.SetNumUninitialized(PressureStencilCount);
            R->PressureStencilBed.SetNumUninitialized(PressureStencilCount);
            for(int32 I=0;I<PressureStencilCount;++I)
            {
                const auto P=PressureStencilCell(I);
                R->PressureStencilState[I]=Sample(Conserved,P.X,P.Y);
                R->PressureStencilBed[I]=Sample(CoarseGeometry,P.X,P.Y).X;
            }
        }
        if(!R->Validate(Error))return nullptr;return R;
    }
};
