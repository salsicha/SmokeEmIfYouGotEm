#include "RaftSimWaterInterpolationPacking.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterInterpolationPackingTest,"RaftSim.M4.WaterInterpolationPacking",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterInterpolationPackingTest::RunTest(const FString&)
{
    using namespace RaftSimWaterInterpolationPacking;
    for(int32 N:{0,1,17,1025,50625})
    {
        TArray<FVector> P,Q;TArray<FLinearColor> C;TArray<FVector2D> F,W,UV,T;
        TArray<FProcMeshTangent> Tangents;
        for(int32 I=0;I<N;++I)
        {
            P.Emplace(I*.13,-I*.29,I*.17);Q.Add(I%7 ? FVector(.2,.3,.8) : FVector::ZeroVector);
            C.Emplace((I%511)/255.f,-.2f,.45f,1.4f);F.Emplace(I*.017,-I*.009);W.Emplace(.3,-.7);
            UV.Emplace(I*.03,-I*.02);T.Emplace(-.7,I*.001);Tangents.Emplace(FVector(.7,.2,.1),I%2!=0);
        }
        auto RP=P,RQ=Q;auto RC=C;auto RF=F,RW=W;
        auto CP=P,CQ=Q;auto CC=C;auto CF=F,CW=W;
        TArray<FProcMeshVertex> Reference,Candidate;
        for(float Alpha:{0.f,1.f,.37f,1.e-7f,.81f})for(bool Transport:{false,true})
        {
            // Independent original actor arithmetic, not the helper under test.
            for(int32 I=0;I<N;++I)
            {
                P[I].Z+=.01;Q[I].X-=.007;C[I].R-=.013f;F[I].Y+=.021;W[I].X-=.002;
                RP[I]=FMath::Lerp(RP[I],P[I],Alpha);
                RQ[I]=FMath::Lerp(RQ[I],Q[I],Alpha).GetSafeNormal();
                RC[I]=FMath::Lerp(RC[I],C[I],Alpha);
                RF[I]=FMath::Lerp(RF[I],F[I],Alpha);
                RW[I]=FMath::Lerp(RW[I],W[I],Alpha);
            }
            TestTrue(TEXT("reference packing"),RaftSimWaterSourcePacking::Pack(RP,RQ,RC,UV,RF,RW,Tangents,Reference,false,
                Transport ? TConstArrayView<FVector2D>(T) : TConstArrayView<FVector2D>(RF)));
            TestTrue(TEXT("fused blend and packing"),BlendAndPack({P,Q,C,F,W},{CP,CQ,CC,CF,CW},Alpha,UV,Tangents,
                Transport ? TConstArrayView<FVector2D>(T) : TConstArrayView<FVector2D>(),Candidate));
            const auto Same=[](const auto& A,const auto& B)
            {return A.Num()==B.Num() && (!A.Num() || FMemory::Memcmp(A.GetData(),B.GetData(),SIZE_T(A.Num())*sizeof(A[0]))==0);};
            TestTrue(TEXT("every rendered field bit and carried history"),Same(RP,CP)&&Same(RQ,CQ)&&Same(RC,CC)&&Same(RF,CF)&&Same(RW,CW));
            bool Exact=Reference.Num()==Candidate.Num();
            for(int32 I=0;Exact && I<N;++I)Exact=FRaftSimCrestMidpointExpansion::EqualAttributes(Reference[I],Candidate[I]);
            TestTrue(TEXT("all mesh attributes including fallback or supplied transport"),Exact);
        }
        if(N)
        {
            const auto Before=Candidate;const auto BeforeP=CP;UV.Pop();
            TestFalse(TEXT("invalid packing shape rejects before interpolation"),BlendAndPack({P,Q,C,F,W},{CP,CQ,CC,CF,CW},.5f,UV,Tangents,T,Candidate));
            TestTrue(TEXT("rejected input preserves rendered positions and packed output"),CP==BeforeP &&
                Candidate.Num()==Before.Num() && FMemory::Memcmp(Candidate.GetData(),Before.GetData(),Candidate.Num()*sizeof(FProcMeshVertex))==0);
        }
    }
    return !HasAnyErrors();
}
#endif
