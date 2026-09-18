#include "Misc/AutomationTest.h"
#include "RaftSimCrestHistory.h"
#include "RaftSimIncrementalCrestHistory.h"
#include "RaftSimCrestMidpointExpansion.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestHistoryTest,
    "RaftSim.M4.CrestHistory",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestHistoryTest::RunTest(const FString&)
{
    FRaftSimCrestHistory Dense,Mapped;
    FRaftSimFastCrestHistory FastDense,FastMapped;
    FRaftSimIncrementalCrestHistory Incremental,IncrementalMapped;
    TMap<FVector2D,float> Reference;
    int64 Compared=0; int32 DenseCalls=0,IncrementalCalls=0;
    for(int32 Frame=0;Frame<36;++Frame)
    {
        if(Frame==29) { Dense.Reset(); Mapped.Reset(); FastDense.Reset(); FastMapped.Reset(); Incremental.Reset(); IncrementalMapped.Reset(); Reference.Reset(); }
        const int32 SourceCount=Frame<24 ? 11 : 7;
        const int32 Count=Frame==27 ? 0 : (Frame>=20 && Frame<26 ? 19031 : 20000);
        TArray<FProcMeshVertex> Original; Original.SetNum(SourceCount+Count);
        TArray<uint8> Boundary; Boundary.SetNum(Count);
        TArray<float> Target; Target.Init(0,Original.Num());
        for(int32 I=0;I<Original.Num();++I)
        {
            // Duplicates have DISTINCT target/boundary values. Reordering,
            // translated windows, growth/shrink and changing source prefixes
            // must preserve old-map lookup ownership, not merely index equality.
            int32 Key=I<SourceCount ? -1-I : (I-SourceCount)/2;
            if(Frame>=12 && Frame<20) Key=10000-Key;
            // Sparse moves remove an owner, insert below an existing owner,
            // swap groups, and restore duplicate groups on subsequent frames.
            if(Frame>=2 && Frame<6 && I>=SourceCount && (I-SourceCount)%997==0)
                Key=(Key+Frame*11)%10000;
            const double Drift=Frame>=8 && Frame<12 ? .137*(Frame-7) : 0.;
            auto& V=Original[I];
            V.Position=FVector(-543700.+Key*3.7+Drift,-359000.+(Key%127)*.23,20.+Frame*.79+I*.003);
            V.Normal=FVector(.2,.3,.9); V.UV0=FVector2D(I,Frame);
            V.Color=FColor(19,83,127,255); V.Tangent=FProcMeshTangent(1,0,0);
            if(I>=SourceCount)
            {
                Boundary[I-SourceCount]=(I+Frame)%13==0;
                Target[I]=float(FMath::Sin(I*.031+Frame*.19)*53.);
            }
        }
        const float Alpha=Frame%5==0 ? 0.f : (Frame%7==0 ? 1.f : .31f);
        auto Expected=Original,A=Original,B=Original,C=Original,D=Original,E=Original,F=Original;
        TArray<float> ExpectedRendered; ExpectedRendered.Init(0,Original.Num());
        TMap<FVector2D,float> Next;
        for(int32 I=0;I<Count;++I)
        {
            const int32 Node=SourceCount+I; auto& V=Expected[Node];
            const FVector2D XY(V.Position.X,V.Position.Y);
            const float* Old=Reference.Find(XY);
            const float Correction=Boundary[I] ? 0.f : FMath::Lerp(Old ? *Old : 0.f,Target[Node],Alpha);
            V.Position.Z+=Correction; ExpectedRendered[Node]=Correction; Next.Add(XY,Correction);
        }
        Reference=MoveTemp(Next);
        TArray<float> RenderedA,RenderedB,RenderedC,RenderedD;
        DenseCalls+=Dense.Apply(A,SourceCount,Boundary,Target,Alpha,RenderedA);
        Mapped.Apply(B,SourceCount,Boundary,Target,Alpha,RenderedB,false);
        FastDense.Apply(C,SourceCount,Boundary,Target,Alpha,RenderedC);
        FastMapped.Apply(D,SourceCount,Boundary,Target,Alpha,RenderedD,false);
        TArray<float> RenderedE,RenderedF;
        Incremental.Apply(E,SourceCount,Boundary,Target,Alpha,RenderedE);
        IncrementalMapped.Apply(F,SourceCount,Boundary,Target,Alpha,RenderedF,false);
        IncrementalCalls+=Incremental.bIncrementalUpdate;
        if(!TestTrue(TEXT("all temporal corrections exactly match original serial map"),
            RenderedA==ExpectedRendered && RenderedB==ExpectedRendered &&
            RenderedC==ExpectedRendered && RenderedD==ExpectedRendered &&
            RenderedE==ExpectedRendered && RenderedF==ExpectedRendered)) return false;
        if(!TestTrue(TEXT("candidate vertex bytes equal original hash for dense and mapped histories"),
            FMemory::Memcmp(A.GetData(),C.GetData(),SIZE_T(A.Num())*sizeof(FProcMeshVertex))==0 &&
            FMemory::Memcmp(B.GetData(),D.GetData(),SIZE_T(B.Num())*sizeof(FProcMeshVertex))==0))return false;
        for(int32 I=0;I<Original.Num();++I)
        {
            if(!FRaftSimCrestMidpointExpansion::EqualAttributes(Expected[I],E[I]) ||
               !FRaftSimCrestMidpointExpansion::EqualAttributes(Expected[I],F[I]))
            {AddError(FString::Printf(TEXT("incremental frame%d vertex%d differs"),Frame,I));return false;}
            if(A[I].Position!=Expected[I].Position || B[I].Position!=Expected[I].Position ||
                A[I].Normal!=Original[I].Normal || A[I].UV0!=Original[I].UV0 ||
                A[I].Color!=Original[I].Color || A[I].Tangent.TangentX!=Original[I].Tangent.TangentX)
            { AddError(FString::Printf(TEXT("frame%d vertex%d differs"),Frame,I)); return false; }
        }
        Compared+=Original.Num();
    }
    TestTrue(TEXT("stable-coordinate dense path was exercised repeatedly"),DenseCalls>=15);
    TestTrue(TEXT("sparse exact-coordinate membership updates exercised"),IncrementalCalls>=5);
    AddInfo(FString::Printf(TEXT("Exact serial-history comparison: %lld vertices,36 changing frames,%d dense calls; duplicate last-writer ownership, crop/reset/boundary/alpha verified"),Compared,DenseCalls));
    return !HasAnyErrors();
}
#endif
