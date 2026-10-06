#include "RaftSimWaterShoreline.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimParallelBankTest,"RaftSim.M4.ParallelBankCurves",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimParallelBankTest::RunTest(const FString&)
{
    using namespace RaftSimWaterShoreline;
    constexpr int32 N=25;
    int32 ParallelEligibleFrames=0,ReusedFrames=0,PreparedReuses=0;
    for(bool Compact:{false,true})for(double Sign:{-1.,1.})
    {
        FTopologyCache Serial,Parallel;
        TArray<FProcMeshVertex> V[2];TArray<uint32> T[2];TArray<int32> O[2];
        for(int32 Frame=0;Frame<24;++Frame)
        {
            TArray<FProcMeshVertex> Source;TArray<float> H,B;TArray<uint8> Wet,Available;
            for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
            {
                // Isolated dry corners plus adjoining pairs exercise both
                // fixed and changing-size banks, including shared edges.
                const bool Dry=(X%4==1 && Y%4==1) || (X%4==2 && Y%8==1);
                // Scale wet donors together so the adjacent fan direction
                // remains eligible while adaptive segment counts change.
                const float Depth=Dry ? 0.f : (.2f+.01f*((X+Y)%7))*(1.f+.4f*(Frame/2));
                H.Add(Depth);B.Add(Dry ? 2.f+.1f*(X%3) : .01f*(Y%3));
                Wet.Add(!Dry);Available.Add(1);
                FProcMeshVertex P;P.Position=FVector(-543000.+X*100.,Sign*(361100.+Y*100.),100.*(B.Last()+Depth));
                P.Normal=FVector(.01*X,.01*Y,1.).GetSafeNormal();
                P.UV0=FVector2D(X,Y);P.UV1=FVector2D(Depth,Frame);P.UV2=FVector2D(Y*.2,X*.3);P.UV3=FVector2D(Frame*.1,Depth);
                P.Color=FColor(X*7,Y*7,Frame*9,255);P.Tangent=FProcMeshTangent(FVector(1.,.01*Y,0.).GetSafeNormal(),bool(X%2));
                Source.Add(P);
            }
            if(Frame==9)H[N+1]=1.e-12f; // Exact-dry eligibility must invalidate.
            if(Frame==12)Available[2*N+2]=0;
            if(Frame==16){H[N+2]=.8f;Wet[N+2]=1;B[N+2]=0.f;}
            if(Frame==20)for(auto& P:Source)P.Position.X+=.25;
            bool Rebuilt[2]={};
            for(int32 Kind=0;Kind<2;++Kind)
            {
                auto Input=Source;auto& Cache=Kind ? Parallel : Serial;
                if(!TestTrue(TEXT("serial/parallel current mesh valid"),Cache.Update(N,N,MoveTemp(Input),Wet,Available,H,B,
                    V[Kind],T[Kind],O[Kind],Rebuilt[Kind],Compact,true,true,Kind==1)))return false;
            }
            if(Serial.GetCurvedBanks().Num()>=128 && Frame>0)++ParallelEligibleFrames;
            PreparedReuses+=Parallel.GetPreparedCurveReuseCount();
            if(!Rebuilt[0])++ReusedFrames;
            TestTrue(TEXT("same topology, ownership and rebuild decision"),T[0]==T[1] && O[0]==O[1] && Rebuilt[0]==Rebuilt[1] && V[0].Num()==V[1].Num());
            TestTrue(TEXT("same cache counters"),Serial.GetReuseCount()==Parallel.GetReuseCount() && Serial.GetRebuildCount()==Parallel.GetRebuildCount());
            // Only submitted vertices affect rendering. Reserved unused slots
            // may retain different historical values after a forced rebuild.
            for(uint32 I:T[0])if(!TestTrue(TEXT("all submitted attribute bits preserved"),
                FRaftSimCrestMidpointExpansion::EqualAttributes(V[0][I],V[1][I])))return false;
            const auto& A=Serial.GetCurvedBanks();const auto& C=Parallel.GetCurvedBanks();
            if(!TestEqual(TEXT("same bank count"),A.Num(),C.Num()))return false;
            for(int32 I=0;I<A.Num();++I)
            {
                if(!TestEqual(TEXT("same adaptive node count"),A[I].IntermediateCount(),C[I].IntermediateCount()))return false;
                for(int32 J=0;J<A[I].IntermediateCount();++J)
                    TestTrue(TEXT("same current curve and interpolation fraction"),A[I].Point(J)==C[I].Point(J) && A[I].Fraction(J)==C[I].Fraction(J));
            }
        }
    }
    TestTrue(TEXT("large bank sets exercised repeatedly"),ParallelEligibleFrames>40);
    TestTrue(TEXT("reuse as well as rebuild exercised"),ReusedFrames>10);
    TestTrue(TEXT("current prepared curves reused during real topology changes"),PreparedReuses>100);
    return !HasAnyErrors();
}
#endif
