#include "RaftSimWaterShoreline.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
namespace
{
TMap<uint64,int32> Boundary(const TArray<uint32>& T)
{
    TMap<uint64,int32> Counts;
    for(int32 I=0;I<T.Num();I+=3)for(int32 E=0;E<3;++E)
    {uint32 A=T[I+E],B=T[I+(E+1)%3];++Counts.FindOrAdd((uint64(FMath::Min(A,B))<<32)|FMath::Max(A,B));}
    for(auto It=Counts.CreateIterator();It;++It)if(It.Value()==2)It.RemoveCurrent();
    return Counts;
}
double MaxSlope(const TArray<FProcMeshVertex>& V,const TArray<uint32>& T)
{
    double Result=0;
    for(int32 I=0;I<T.Num();I+=3)
    {
        const FVector N=FVector::CrossProduct(V[T[I+1]].Position-V[T[I]].Position,V[T[I+2]].Position-V[T[I]].Position);
        Result=FMath::Max(Result,FMath::Sqrt(N.X*N.X+N.Y*N.Y)/FMath::Abs(N.Z));
    }
    return Result;
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineBankFanTest,"RaftSim.M4.ShorelineOppositeDryFan",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineBankFanTest::RunTest(const FString&)
{
    // Every wet pattern, rotations/reflections and both index-storage modes.
    // All vertices/attributes and boundary segments must be unchanged, not
    // merely the area. Fully wet, disconnected and non-pentagon cases retain
    // the exact original indices. Interior diagonals are the only candidate.
    for(bool Compact:{false,true})for(double Angle:{0.,.37,UE_DOUBLE_PI*.5})
    for(double Sign:{-1.,1.})for(int32 Mask=0;Mask<16;++Mask)
    {
        TArray<FProcMeshVertex> Source;
        TArray<uint8> Wet,Available;TArray<float> H,Bed;Available.Init(1,4);
        int32 WetCount=0;
        for(int32 I=0;I<4;++I)
        {
            const double X=I%2,Y=I/2;auto& V=Source.AddDefaulted_GetRef();
            V.Position=FVector(FMath::Cos(Angle)*X-FMath::Sin(Angle)*Y,
                Sign*(FMath::Sin(Angle)*X+FMath::Cos(Angle)*Y),1.+.12*X+.7*Y);
            V.Normal=FVector::UpVector;V.UV0=FVector2D(X,Y);V.Color=FColor(17+I,81,123,255);
            Wet.Add(bool(Mask&(1<<I)));H.Add(Wet.Last()?1.f:0.f);Bed.Add(Wet.Last()?0.f:2.f);WetCount+=Wet.Last();
        }
        TArray<FProcMeshVertex> Old,New;TArray<uint32> OT,NT;
        auto A=Source,B=Source;
        if(!TestTrue(TEXT("old builds"),RaftSimWaterShoreline::Build(2,2,MoveTemp(A),Wet,Available,H,Bed,Old,OT,nullptr,nullptr,Compact,false)) ||
           !TestTrue(TEXT("candidate builds"),RaftSimWaterShoreline::Build(2,2,MoveTemp(B),Wet,Available,H,Bed,New,NT,nullptr,nullptr,Compact,true)))return false;
        TestEqual(TEXT("same triangle count"),NT.Num(),OT.Num());TestEqual(TEXT("same vertex count"),New.Num(),Old.Num());
        for(int32 I=0;I<New.Num();++I)
        {
            TestEqual(TEXT("positions unchanged"),New[I].Position,Old[I].Position);
            TestEqual(TEXT("color unchanged"),New[I].Color,Old[I].Color);
            TestEqual(TEXT("UV unchanged"),New[I].UV0,Old[I].UV0);
        }
        const auto OB=Boundary(OT),NB=Boundary(NT);
        TestTrue(TEXT("identical boundary segments"),OB.OrderIndependentCompareEqual(NB));
        if(WetCount!=3)TestTrue(TEXT("all other wet patterns exact"),OT==NT);
        for(int32 I=0;I<NT.Num();I+=3)
        {
            const FVector P=New[NT[I]].Position*.2+New[NT[I+1]].Position*.3+New[NT[I+2]].Position*.5;
            FVector Sample;
            TestTrue(TEXT("new triangles remain sampleable"),RaftSimWaterShoreline::Sample(FVector2D(P.X,P.Y),0,NT.Num(),New,NT,Sample));
            TestTrue(TEXT("barycentric support follows new surface"),FMath::Abs(Sample.Z-P.Z)<1.e-10);
        }
    }
    // Captured cell [-5411,-5410] x [3599,3600] at world13.110338888s.
    // Preserve the actual submitted source heights, cached depths and beds.
    TArray<FProcMeshVertex> Source;Source.SetNum(4);
    const double Z[]={8.1117325756419064,8.2187602954931947,8.6742701051415611,8.9405517578125};
    for(int32 I=0;I<4;++I){Source[I].Position=FVector(I%2,I/2,Z[I]);Source[I].Normal=FVector::UpVector;}
    TArray<uint8> Wet={1,1,0,1},Available={1,1,1,1};
    TArray<float> H={.60379546880722046f,.95815956592559814f,7.78138837631559e-6f,.22636397182941437f};
    TArray<float> Bed={7.5079345703125f,7.2606048583984375f,9.015777587890625f,8.714141845703125f};
    TArray<FProcMeshVertex> Old,New;TArray<uint32> OT,NT;auto A=Source,B=Source;
    RaftSimWaterShoreline::Build(2,2,MoveTemp(A),Wet,Available,H,Bed,Old,OT,nullptr,nullptr,true,false);
    RaftSimWaterShoreline::Build(2,2,MoveTemp(B),Wet,Available,H,Bed,New,NT,nullptr,nullptr,true,true);
    const double OldSlope=MaxSlope(Old,OT),NewSlope=MaxSlope(New,NT);
    TestTrue(TEXT("reproduces captured cliff slope"),FMath::Abs(OldSlope-3.3213180448)<1.e-8);
    TestTrue(TEXT("same cell no longer concentrates slope in sliver"),NewSlope<1.4 && NewSlope<OldSlope);
    AddInfo(FString::Printf(TEXT("Captured bank cell max slope old=%.12g candidate=%.12g; no vertex/shoreline change"),OldSlope,NewSlope));
    RaftSimWaterShoreline::FTopologyCache Cache;TArray<int32> Offsets;bool Rebuilt=false;
    for(int32 Step=0;Step<4;++Step)
    {
        auto Input=Source;const bool Candidate=Step==1 || Step==2;
        TestTrue(TEXT("cache update succeeds"),Cache.Update(2,2,MoveTemp(Input),Wet,Available,H,Bed,New,NT,Offsets,Rebuilt,true,Candidate));
        TestEqual(TEXT("topology mode is part of cache identity"),Rebuilt,Step!=2);
    }
    return !HasAnyErrors();
}
#endif
