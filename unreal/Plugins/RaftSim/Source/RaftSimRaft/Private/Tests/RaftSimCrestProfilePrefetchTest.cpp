#include "Misc/AutomationTest.h"
#include "RaftSimCrestProfilePrefetch.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestProfilePrefetchTest,"RaftSim.M4.CrestProfilePrefetch",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestProfilePrefetchTest::RunTest(const FString&)
{
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<9;++Y)for(int32 X=0;X<9;++X)XY.Emplace(X*100.,Y*100.);
    for(int32 Y=0;Y<8;++Y)for(int32 X=0;X<8;++X)
    {const int32 A=Y*9+X;Triangles.Append({A,A+9,A+1,A+1,A+9,A+10});}
    FRaftSimSurfaceRefinement Reference,Candidate;
    FRaftSimCrestProfilePrefetch Prefetch;
    const auto Wait=[&]()
    {
        const double Deadline=FPlatformTime::Seconds()+10.;
        while(!Prefetch.IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
        return TestTrue(TEXT("owned prefetch completes"),Prefetch.IsReady());
    };
    int32 Adopted=0;int64 AvoidedEvaluations=0;
    for(int32 Frame=0;Frame<18;++Frame)
    {
        const TArray<double> Key={double(Frame),double(Frame%3)};
        const TFunction<float(const FVector2D&)> Height=[Frame](const FVector2D& P)
        {return float(26.*FMath::Exp(-FMath::Square((P.X-280.-Frame*7.)/110.))*(1.+.2*FMath::Sin(P.Y*.019)));};
        if(Frame>0)
        {
            if(!TestTrue(TEXT("warm coordinates submit"),Prefetch.Start(Candidate,Key,Height)) || !Wait())return false;
            if(Frame==5)
                TestFalse(TEXT("changed profile identity rejects every prepared value"),Prefetch.AdoptIfReady({-1.},Candidate));
            else if(Frame==9)
            {Prefetch.Reset();TestFalse(TEXT("reset discards ready result"),Prefetch.AdoptIfReady(Key,Candidate));}
            else {TestTrue(TEXT("matching profile adopts"),Prefetch.AdoptIfReady(Key,Candidate,&Height));++Adopted;}
        }
        auto Points=XY;
        // Different samples/batch membership must fall back to the CURRENT
        // callback, not interpolate or resurrect values from an earlier epoch.
        if(Frame%6>=3)for(int32 I=0;I<Points.Num();++I)Points[I]+=FVector2D((Frame/6+1)*.013,I%4*.017);
        auto CurrentTriangles=Triangles;
        if(Frame==12)CurrentTriangles.SetNum(60);
        TAtomic<int32> Calls[2];Calls[0].Store(0);Calls[1].Store(0);
        for(int32 Kind=0;Kind<2;++Kind)
        {
            const auto Sample=[&](const FVector2D& P){++Calls[Kind];return Height(P);};
            auto& Work=Kind ? Candidate : Reference;
            if(!TestTrue(TEXT("current geometry builds"),Work.BuildAdaptive(Points,CurrentTriangles,Sample,3,.5f,
                {},nullptr,true,true,nullptr,0.f,true)))return false;
        }
        AvoidedEvaluations+=Calls[0].Load()-Calls[1].Load();
        TestTrue(TEXT("all indices, parents and owners are identical"),Reference.Triangles==Candidate.Triangles &&
            Reference.MidpointParents==Candidate.MidpointParents && Reference.TriangleOrigins==Candidate.TriangleOrigins);
        if(Frame==14){Reference.InvalidateTopologyCache();Candidate.InvalidateTopologyCache();}
    }
    TestEqual(TEXT("successful prefetch path exercised"),Adopted,15);
    TestTrue(TEXT("prepared values actually avoid current synchronous evaluations"),AvoidedEvaluations>100);
    const TFunction<float(const FVector2D&)> Constant=[](const FVector2D&){return 4.f;};
    TestTrue(TEXT("audit negative control submits"),Prefetch.Start(Candidate,{99.},Constant));
    if(!Wait())return false;
    const TFunction<float(const FVector2D&)> Wrong=[](const FVector2D&){return 5.f;};
    AddExpectedError(TEXT("CrestPrefetchAudit mismatch"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("audit mismatch rejects entire result"),Prefetch.AdoptIfReady({99.},Candidate,&Wrong));
    FRaftSimSurfaceRefinement Empty;
    TestFalse(TEXT("empty sample plan does not launch"),Prefetch.Start(Empty,{1.},[](const FVector2D&){return 1.f;}));
    TestFalse(TEXT("missing callback does not launch"),Prefetch.Start(Candidate,{1.},{}));
    TestFalse(TEXT("missing profile identity does not launch"),Prefetch.Start(Candidate,{},[](const FVector2D&){return 1.f;}));
    // A blocked pure callback witnesses real in-flight ownership. Reset does
    // not cancel or access freed inputs, and no second job may queue behind it.
    auto Started=MakeShared<TAtomic<bool>,ESPMode::ThreadSafe>(false);
    auto Released=MakeShared<TAtomic<bool>,ESPMode::ThreadSafe>(false);
    const TFunction<float(const FVector2D&)> Blocking=[Started,Released](const FVector2D&)
    {Started->Store(true);while(!Released->Load())FPlatformProcess::Sleep(.001f);return 3.f;};
    const bool Launched=Prefetch.Start(Candidate,{77.},Blocking);
    TestTrue(TEXT("owned blocking job launches"),Launched);
    const double Deadline=FPlatformTime::Seconds()+10.;
    while(Launched && !Started->Load() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
    TestTrue(TEXT("job is observed running"),Started->Load());
    TestFalse(TEXT("unfinished result never blocks adoption"),Prefetch.AdoptIfReady({77.},Candidate));
    TestFalse(TEXT("one in-flight job only"),Prefetch.Start(Candidate,{78.},Blocking));
    Prefetch.Reset();Released->Store(true);
    TestFalse(TEXT("discarded job cannot publish later"),Prefetch.AdoptIfReady({77.},Candidate));
    return !HasAnyErrors();
}
#endif
