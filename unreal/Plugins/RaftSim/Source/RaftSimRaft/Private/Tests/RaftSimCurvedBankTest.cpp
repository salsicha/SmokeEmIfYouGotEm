#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterBankContour.h"
#include "RaftSimShorelineCrestWeights.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCurvedBankTest,"RaftSim.M4.CurvedHighBank",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCurvedBankTest::RunTest(const FString&)
{
    using namespace RaftSimWaterShoreline;
    for(bool Compact:{false,true})for(double Sign:{-1.,1.})for(double Angle:{0.,.37,UE_DOUBLE_PI*.5})
    for(int32 Mask=0;Mask<16;++Mask)
    {
        TArray<FProcMeshVertex> Source;Source.SetNum(4);
        TArray<float> H,Bed;TArray<uint8> Wet,Available={1,1,1,1};
        for(int32 I=0;I<4;++I)
        {
            const double X=I%2,Y=I/2;
            Source[I].Position=FVector(-543000.+100.*(FMath::Cos(Angle)*X-FMath::Sin(Angle)*Y),
                Sign*(361100.+100.*(FMath::Sin(Angle)*X+FMath::Cos(Angle)*Y)),100.);
            Source[I].Normal=FVector::UpVector;Source[I].UV0=FVector2D(X,Y);Source[I].UV3=FVector2D(2.,3.);
            Wet.Add(bool(Mask&(1<<I)));H.Add(Wet.Last()?1.f:0.f);Bed.Add(Wet.Last()?0.f:2.f);
        }
        TArray<FProcMeshVertex> V,Old;TArray<uint32> T,OT;TArray<int32> Offsets;
        TArray<FCurvedBank> Banks;TArray<RaftSimWaterShoreline::FEdge> Edges;
        auto Input=Source,Legacy=Source;
        if(!TestTrue(TEXT("all wet patterns build"),Build(2,2,MoveTemp(Input),Wet,Available,H,Bed,V,T,&Offsets,&Edges,Compact,true,true,&Banks)))return false;
        Build(2,2,MoveTemp(Legacy),Wet,Available,H,Bed,Old,OT,nullptr,nullptr,Compact,true);
        const int32 Count=Wet[0]+Wet[1]+Wet[2]+Wet[3];
        if(Count!=3)
        {
            TestTrue(TEXT("other patterns retain exact indices"),T==OT);
            TestEqual(TEXT("other patterns retain vertex count"),V.Num(),Old.Num());
        }
        else
        {
            TestEqual(TEXT("one curved bank"),Banks.Num(),1);
            const auto& Bank=Banks[0];
            for(int32 I=0;I<Bank.Segments-1;++I)
            {
                TestTrue(TEXT("new nodes follow zero-depth contour"),
                    FMath::Abs(RaftSimWaterBankContour::SignedDepth(Bank.Bed,Bank.Depth,Bank.Points[I]))<1.e-8);
                TestTrue(TEXT("new nodes preserve transported flow"),V[Bank.FirstNode+I].UV3==FVector2D(2.,3.));
            }
            FRaftSimShorelineCrestWeights Weights;
            const TArray<float> Coarse={2,2,2,2},Shore={.5,.5,.5,.5};
            Weights.Update(V.Num(),Coarse,Shore,Edges,Banks);
            for(int32 I=0;I<Bank.Segments-1;++I)
                TestTrue(TEXT("curve nodes retain matching crest weights"),Weights.Coarse[Bank.FirstNode+I]==2 && Weights.Shore[Bank.FirstNode+I]==.5);
        }
        for(int32 I=0;I<T.Num();I+=3)
        {
            const FVector P=V[T[I]].Position*.2+V[T[I+1]].Position*.3+V[T[I+2]].Position*.5;
            FVector Sampled;
            TestTrue(TEXT("actual output remains sampleable"),Sample(FVector2D(P.X,P.Y),0,T.Num(),V,T,Sampled));
        }
    }
    // Same captured inputs as the v18 provenance report, retained in metres.
    TArray<float> H={.5688362717628479f,.49260467290878296f,0.f,.2190435528755188f};
    TArray<float> Bed={7.243682861328125f,7.27630615234375f,9.9083251953125f,7.7048187255859375f};
    const TArray<uint8> Wet={1,1,0,1},Available={1,1,1,1};
    TArray<FProcMeshVertex> Source;Source.SetNum(4);
    for(int32 I=0;I<4;++I){Source[I].Position=FVector(I%2,I/2,Bed[I]+H[I]);Source[I].Normal=FVector::UpVector;}
    TArray<FProcMeshVertex> V;TArray<uint32> T;TArray<int32> Offsets;FVector P;
    auto Input=Source;
    Build(2,2,MoveTemp(Input),Wet,Available,H,Bed,V,T,nullptr,nullptr,true,true);
    const FVector2D Probe(.6853855723475135,.7033689141421746);
    TestTrue(TEXT("legacy polygon reproduces dry probe coverage"),Sample(Probe,0,T.Num(),V,T,P));
    Input=Source;
    if(!TestTrue(TEXT("captured curved cell builds"),Build(2,2,MoveTemp(Input),Wet,Available,H,Bed,V,T,nullptr,nullptr,true,true,true)))return false;
    TestFalse(TEXT("curved shoreline excludes captured raw-dry probe"),Sample(Probe,0,T.Num(),V,T,P));
    FTopologyCache Cache;bool Rebuilt=false;
    for(int32 Frame=0;Frame<20;++Frame)
    {
        auto Depth=H;
        if(Frame>=4)Depth[0]+=.01f*(Frame/2);
        if(Frame==18)Depth[2]=1.e-12f; // Positive film is not an exactly dry bank.
        Input=Source;
        if(!TestTrue(TEXT("changing bank cache updates"),Cache.Update(2,2,MoveTemp(Input),Wet,Available,Depth,Bed,V,T,Offsets,Rebuilt,true,true,true)))return false;
        auto FreshSource=Source;TArray<FProcMeshVertex> Fresh;TArray<uint32> FT;TArray<int32> FO;
        if(!TestTrue(TEXT("fresh changing bank builds"),Build(2,2,MoveTemp(FreshSource),Wet,Available,Depth,Bed,Fresh,FT,&FO,nullptr,true,true,true)))return false;
        TestTrue(TEXT("reused topology agrees with fresh geometry"),T==FT && Offsets==FO && V.Num()==Fresh.Num());
        for(int32 I=0;I<V.Num() && I<Fresh.Num();++I)
            TestTrue(TEXT("cached attributes equal fresh attributes"),FRaftSimCrestMidpointExpansion::EqualAttributes(V[I],Fresh[I]));
        if(Frame==1)TestFalse(TEXT("unchanged curves reuse topology"),Rebuilt);
        if(Frame==18)TestTrue(TEXT("positive film invalidates curved mode"),Rebuilt && Cache.GetCurvedBanks().IsEmpty());
    }
    return !HasAnyErrors();
}
#endif
