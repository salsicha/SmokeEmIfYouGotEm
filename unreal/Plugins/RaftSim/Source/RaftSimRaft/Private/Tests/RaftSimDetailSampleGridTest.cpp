#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthSource.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDetailSampleGridTest,"RaftSim.WaterDetail.DetailSampleGrid",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDetailSampleGridTest::RunTest(const FString&)
{
    const auto AtNode=[](int32 X,int32 Y)
    {
        // Fixed, non-affine world data; includes positive sub1cm films.
        const int32 K=((X*7+Y*11)%23+23)%23;
        const float H=K==0?1e-30f:K==1?.005f:1.f+K*.03125f;
        return FVector4f(H,(X%5)*.125f,(Y%7)*-.0625f,0.f);
    };
    const auto BedAt=[](int32 X,int32 Y){return float(128.+.125*(X%7)+.25*(Y%3));};
    const auto Packet=[&](FVector2f Origin,uint64 Revision)
    {
        FRaftSimDetailSampleGrid Grid;Grid.Register(Origin);
        TArray<FVector4f> HUV,G;
        for(int32 Y=-1;Y<=65;++Y)for(int32 X=-1;X<=65;++X)
        {
            const int32 WX=int32(Grid.CoarseOriginMeters.X)+X,WY=int32(Grid.CoarseOriginMeters.Y)+Y;
            const auto F=AtNode(WX,WY);const float B=BedAt(WX,WY);
            HUV.Add(F);G.Add(FVector4f(B,B+F.X,F.X,0));
        }
        TArray<float> FaceVelocity;FaceVelocity.Init(0,512);
        FString E;return FRaftSimTotalDepthSource::Build(HUV,G,FaceVelocity,Origin,0,Revision,E);
    };
    int64 Compared=0,ExteriorCompared=0;uint64 Revision=1;
    for(const FVector2f Origin:{FVector2f(-5460,-3632),FVector2f(-.5f,-.5f),FVector2f(.5f,.5f),FVector2f(19,27.5f)})
    {
        const auto Previous=Packet(Origin,Revision++);
        if(!TestTrue(TEXT("world-lattice packet builds"),Previous.IsValid()))return false;
        for(const FIntPoint Shift:{FIntPoint(1,0),FIntPoint(-1,0),FIntPoint(0,1),FIntPoint(0,-1),
            FIntPoint(1,1),FIntPoint(-1,-1),FIntPoint(17,-19),FIntPoint(-21,16),FIntPoint(127,127)})
        {
            const auto Next=Packet(Origin+FVector2f(Shift.X*.5f,Shift.Y*.5f),Revision++);
            if(!TestTrue(TEXT("all half-cell phases and signed shifts build"),Next.IsValid()))return false;
            bool Equal=true;
            for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
            {
                const int32 PX=X+Shift.X,PY=Y+Shift.Y;
                if(PX<0 || PY<0 || PX>=128 || PY>=128)continue;
                const int32 I=Y*128+X,J=PY*128+PX;
                Equal &= FMemory::Memcmp(&Next->State[I],&Previous->State[J],16)==0 &&
                    FMemory::Memcmp(&Next->Bed[I],&Previous->Bed[J],4)==0 &&
                    FMemory::Memcmp(&Next->Reference[I],&Previous->Reference[J],8)==0;
                ++Compared;
            }
            TestTrue(TEXT("retained h/M, bed and reference are bit-exact for a frozen world field"),Equal);
            for(int32 I=0;I<512;++I)
            {
                const auto P=FRaftSimTotalDepthSource::ExteriorCell(I);
                const auto CompareGhost=[&](const auto& Exterior,const auto& Interior,FIntPoint Q)
                {
                    if(Q.X<0 || Q.Y<0 || Q.X>=128 || Q.Y>=128)return;
                    const int32 J=Q.Y*128+Q.X;
                    Equal &= FMemory::Memcmp(&Exterior->ExteriorState[I],&Interior->State[J],16)==0 &&
                        Exterior->ExteriorBed[I]==Interior->Bed[J];
                    ++ExteriorCompared;
                };
                CompareGhost(Previous,Next,P-Shift);CompareGhost(Next,Previous,P+Shift);
            }
            TestTrue(TEXT("ghost/interior exchange retains the exact same world samples across remaps"),Equal);
        }
    }
    // Reproduce the old phase error with a one-metre triangular bed wave.
    // Integer nodes alternate0/1m, while half-integer samples all equal0.5m.
    TArray<float> Original,Shifted;Original.SetNum(65*65);Shifted.Init(.5f,65*65);
    for(int32 Y=0;Y<65;++Y)for(int32 X=0;X<65;++X)Original[Y*65+X]=float(X%2);
    FRaftSimDetailSampleGrid Zero,Half;Zero.Register(FVector2f::ZeroVector);Half.Register(FVector2f(.5f,0));
    const float OldError=FMath::Abs(Zero.Interpolate<float>(Original,2,0)-Zero.Interpolate<float>(Shifted,1,0));
    TestEqual(TEXT("historical moving-lattice interpolation changes the same bed position"),OldError,.5f);
    TestEqual(TEXT("fixed lattice retains the actual same-position sample"),
        Zero.Interpolate<float>(Original,2,0),Half.Interpolate<float>(Original,1,0));
    // Endpoint must copy the correct node, even when lerping with alpha1
    // would lose the small endpoint value through floating-point cancellation.
    Original.Init(1e20f,65*65);Original.Last()=3.25f;
    Half.Register(FVector2f(.5f,.5f));
    TestEqual(TEXT("positive corner addresses node64 in both axes exactly"),Half.Interpolate<float>(Original,127,127),3.25f);
    // Expanded halo must not change any old interior interpolation arithmetic.
    TArray<float> Halo;Halo.Init(-17.f,67*67);
    for(int32 Y=0;Y<65;++Y)for(int32 X=0;X<65;++X)Halo[(Y+1)*67+X+1]=Original[Y*65+X];
    bool SameInterior=true;
    for(int32 PY=0;PY<2;++PY)for(int32 PX=0;PX<2;++PX)
    {
        FRaftSimDetailSampleGrid G;G.Register(FVector2f(PX*.5f,PY*.5f));
        for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
            SameInterior &= G.Interpolate<float>(Original,X,Y)==G.InterpolateHalo<float>(Halo,X,Y);
    }
    TestTrue(TEXT("all65536 interior samples match the old65x65 interpolation bits"),SameInterior);
    FRaftSimDetailSampleGrid Invalid;
    TestFalse(TEXT("quarter-cell origin refused, not snapped"),Invalid.Register(FVector2f(.25f,0)));
    TestFalse(TEXT("nonfinite origin refused"),Invalid.Register(FVector2f(std::numeric_limits<float>::infinity(),0)));
    auto Valid=Packet(FVector2f(-.5f,.5f),Revision++);
    FRaftSimTotalDepthSource Unpaired=*Valid;Unpaired.CoarseSampleOriginMeters.X+=1;
    FString E;TestFalse(TEXT("unpaired coarse registration refused"),Unpaired.Validate(E));
    AddInfo(FString::Printf(TEXT("World-aligned source grid: %lld retained cells bit-exact; historical phase error%.3fm, fixed0; no time-varying flow freeze"),Compared,OldError));
    AddInfo(FString::Printf(TEXT("Exterior world sampling: %lld ghost/interior exchanges bit-exact;65536 interior interpolation comparisons exact"),ExteriorCompared));
    return !HasAnyErrors();
}
#endif
