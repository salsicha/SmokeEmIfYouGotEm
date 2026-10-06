#include "Misc/AutomationTest.h"
#include "RaftSimCrestHistory.h"
#include "RaftSimIncrementalCrestHistory.h"
#include "RaftSimCrestMidpointExpansion.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimIncrementalCrestHistoryTest,
    "RaftSim.M4.IncrementalCrestHistory",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimIncrementalCrestHistoryTest::RunTest(const FString&)
{
    FRaftSimCrestHistory Reference;
    FRaftSimIncrementalCrestHistory Candidate;
    FRandomStream Random(94021);
    TArray<int32> Keys;for(int32 I=0;I<256;++I)Keys.Add(I/4);
    int32 Sparse=0;
    for(int32 Frame=0;Frame<160;++Frame)
    {
        // Entire duplicate groups move to brand-new keys and merge again.
        if(Frame%9==0)for(int32 I=40;I<44;++I)Keys[I]=-100-Frame;
        if(Frame%9==1)for(int32 I=40;I<44;++I)Keys[I]=3;
        for(int32 J=0;J<5;++J)Keys[Random.RandRange(0,255)]=Random.RandRange(-20,80);
        if(Frame==80){Reference.Reset();Candidate.Reset();}
        TArray<FProcMeshVertex> A;A.SetNum(260);
        TArray<uint8> Boundary;Boundary.SetNum(256);
        TArray<float> Target;Target.Init(0,260);
        for(int32 I=0;I<260;++I)
        {
            A[I].Position=FVector(I<4 ? -1000-I : Keys[I-4],3,Frame*.17+I*.013);
            A[I].Normal=FVector(0,0,1);A[I].Tangent=FProcMeshTangent(1,0,0);
            if(I>=4){Boundary[I-4]=(Frame+I)%17==0;Target[I]=float((Frame-I)*.39);}
        }
        auto B=A;TArray<float> RA,RB;
        const float Alpha=Frame%11==0 ? 0.f : (Frame%13==0 ? 1.f : .27f);
        const bool DA=Reference.Apply(A,4,Boundary,Target,Alpha,RA);
        const bool DB=Candidate.Apply(B,4,Boundary,Target,Alpha,RB);
        if(!TestTrue(TEXT("sparse duplicate-group corrections and dense classification exact"),DA==DB && RA==RB))return false;
        for(int32 I=0;I<A.Num();++I)if(!FRaftSimCrestMidpointExpansion::EqualAttributes(A[I],B[I]))
        {AddError(FString::Printf(TEXT("Sparse history differs at frame%d node%d"),Frame,I));return false;}
        Sparse+=Candidate.bIncrementalUpdate;
    }
    TestTrue(TEXT("incremental remove/insert path repeatedly exercised"),Sparse>=150);
    return !HasAnyErrors();
}
#endif
