#include "Misc/AutomationTest.h"
#include "RaftSimFoamAdvection.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFoamAdvectionTest,"RaftSim.Water.FoamBoundedAdvection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimFoamAdvectionTest::RunTest(const FString&)
{
    using namespace RaftSimFoamAdvection;
    constexpr int32 W=96,H=80,N=W*H,Steps=40;
    TArray<uint8> Wet;Wet.Init(1,N);
    TArray<float> Initial;Initial.SetNum(N);
    const auto Profile=[](double X,double Y){return float(.1+.8*FMath::Exp(-((X-36)*(X-36)/18+(Y-35)*(Y-35)/32)));};
    for(int32 I=0;I<N;++I)Initial[I]=Profile(I%W,I/W);
    // Independent translated Gaussian expectation, both axes and signs.
    for(const FVector2D V : {FVector2D(.37,.23),FVector2D(-.31,.19),FVector2D(.17,-.29)})
    {
        TArray<FVector2D> Vel,Back;Vel.Init(V,N);Back.SetNum(N);
        for(int32 I=0;I<N;++I)Back[I]=FVector2D(I%W,I/W)-V;
        auto Low=Initial,High=Initial;
        for(int32 Step=0;Step<Steps;++Step)
        {
            const auto C=Correct(W,H,High,Wet,Wet,Back,Vel,1,1);
            auto NewLow=Low,NewHigh=High;
            for(int32 I=0;I<N;++I)
            {
                const auto S=Stencil(W,H,Back[I]);
                NewLow[I]=S.Valid ? Sample(S,Low) : .1f;
                NewHigh[I]=C.Corrected[I] ? C.Values[I] : (S.Valid ? Sample(S,High) : .1f);
                if(C.Corrected[I])
                {
                    float Min=1,Max=0;
                    for(int32 K=0;K<4;++K)if(S.Weight[K]>0)
                    {Min=FMath::Min(Min,High[S.Index[K]]);Max=FMath::Max(Max,High[S.Index[K]]);}
                    if(!TestTrue(TEXT("every correction stays inside original contributing donor range"),C.Values[I]>=Min && C.Values[I]<=Max))return false;
                }
            }
            Low=MoveTemp(NewLow);High=MoveTemp(NewHigh);
        }
        double LowError=0,HighError=0;
        for(int32 Y=12;Y<H-12;++Y)for(int32 X=12;X<W-12;++X)
        {
            const double Expected=Profile(X-Steps*V.X,Y-Steps*V.Y);
            LowError+=FMath::Abs(Low[Y*W+X]-Expected);HighError+=FMath::Abs(High[Y*W+X]-Expected);
        }
        AddInfo(FString::Printf(TEXT("40-step profile: first_order_L1=%.9g corrected_L1=%.9g"),LowError,HighError));
        TestTrue(TEXT("translated narrow profile error at least halved, unchanged grid and duration"),HighError<.5*LowError);
    }
    TArray<FVector2D> Vel,Back;Vel.Init(FVector2D::ZeroVector,N);Back.SetNum(N);
    for(int32 I=0;I<N;++I)Back[I]=FVector2D(I%W,I/W);
    auto C=Correct(W,H,Initial,Wet,Wet,Back,Vel,1,1);
    TestEqual(TEXT("zero velocity retains every boundary node"),C.CorrectedCount,N);
    for(int32 I=0;I<N;++I)if(!TestEqual(TEXT("stationary field bit-exact"),C.Values[I],Initial[I]))return false;
    TestEqual(TEXT("held time is not corrected"),Correct(W,H,Initial,Wet,Wet,Back,Vel,1,0).CorrectedCount,0);
    TestEqual(TEXT("invalid duration refused"),Correct(W,H,Initial,Wet,Wet,Back,Vel,1,std::numeric_limits<double>::quiet_NaN()).CorrectedCount,0);
    TArray<float> Ramp;Ramp.SetNum(N);
    for(int32 I=0;I<N;++I)
    {
        const FVector2D P(I%W,I/W);
        Ramp[I]=.2f+.002f*P.X+.003f*P.Y;
        Vel[I]=FVector2D(.2+.002*P.X+.001*P.Y,-.3+.003*P.Y);
        Back[I]=P-Vel[I];
    }
    C=Correct(W,H,Ramp,Wet,Wet,Back,Vel,1,1);
    TestTrue(TEXT("varying flow has qualified inverse-map samples"),C.CorrectedCount>N/2);
    for(int32 I=0;I<N;++I)if(C.Corrected[I])
        if(!TestTrue(TEXT("affine profile has no spurious variable-velocity correction"),
            FMath::Abs(C.Values[I]-(.2+.002*Back[I].X+.003*Back[I].Y))<2.e-7))return false;
    // A long trace with wet endpoints must not skip an intervening rock.
    for(int32 Y=0;Y<H;++Y)Wet[Y*W+40]=0;
    for(int32 I=0;I<N;++I){Vel[I]=FVector2D(5,0);Back[I]=FVector2D(I%W-5,I/W);}
    C=Correct(W,H,Initial,Wet,Wet,Back,Vel,1,1);
    TestFalse(TEXT("no high-order correction through rock"),bool(C.Corrected[35*W+43]));
    TestFalse(TEXT("no correction using exterior history"),bool(C.Corrected[35*W+2]));
    auto PreviouslyDry=Wet;PreviouslyDry[35*W+60]=0;
    C=Correct(W,H,Initial,PreviouslyDry,Wet,Back,Vel,1,1);
    TestFalse(TEXT("newly wet history refused"),bool(C.Corrected[35*W+60]));
    const auto Edge=Stencil(W,H,FVector2D(20,30));auto ReadyMask=Wet;
    ReadyMask[30*W+21]=0;
    TestTrue(TEXT("zero-weight neighbor does not poison a sample"),Ready(Edge,ReadyMask));
    Wet.Init(1,N);
    TArray<uint8> Valid;Valid.Init(1,N);
    for(int32 I=0;I<N;++I)Back[I]=FVector2D(W-1-I%W,I/W);
    TestFalse(TEXT("orientation-reversing map refused even at exact inverse root"),
        InverseStencil(35*W+30,W,H,Back,FVector2D(W-1-30,35),Wet,Wet,Valid).Valid);
    return true;
}
#endif
