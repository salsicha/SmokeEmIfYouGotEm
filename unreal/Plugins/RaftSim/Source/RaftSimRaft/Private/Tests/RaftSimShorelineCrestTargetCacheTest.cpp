#include "Misc/AutomationTest.h"
#include "RaftSimShorelineCrests.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineCrestTargetCacheTest,
    "RaftSim.M4.ShorelineCrestTargetCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineCrestTargetCacheTest::RunTest(const FString&)
{
    constexpr int32 N=17;
    TArray<FProcMeshVertex> Source;Source.SetNum(N*N);
    TArray<uint32> SourceIndices;TArray<int32> SourceOffsets;
    TArray<float> Coarse,Shore;Coarse.SetNum(N*N);Shore.SetNum(N*N);
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        auto& V=Source[Y*N+X];V.Position=FVector(-544000+X*100,-360000+Y*100,100);
        V.Normal=FVector::UpVector;V.Tangent=FProcMeshTangent(FVector::ForwardVector,true);
        V.UV0=FVector2D(X,Y);V.UV1=FVector2D(-2,3);V.UV2=FVector2D(.2,.4);V.UV3=FVector2D(1,-3);
        V.Color=FColor(13,51,89,255);
        if(X<N-1 && Y<N-1)
        {
            SourceOffsets.Add(SourceIndices.Num());const uint32 A=Y*N+X;
            SourceIndices.Append({A,A+N,A+1,A+1,A+N,A+N+1});
        }
    }
    SourceOffsets.Add(SourceIndices.Num());
    float Amplitude=37.f;TAtomic<int32> Queries{0};
    FRaftSimShorelineCrestInput Input;
    Input.DetailWindowCm=FBox2D(FVector2D(-543800,-359800),FVector2D(-543000,-359000));
    Input.DetailSpanCm=50;Input.BlendAlpha=.37f;
    Input.HeightAtWorldXYCm=[&](const FVector2D& P)
    {
        ++Queries;const double X=(P.X+544000)*.01-8,Y=(P.Y+360000)*.01-8;
        return float(Amplitude*FMath::Exp(-X*X*.3-Y*Y*.15));
    };
    FRaftSimShorelineCrests Cached,Fresh;
    int64 ComparedVertices=0;uint64 ExpectedBuilds=0;
    for(int32 Frame=0;Frame<16;++Frame)
    {
        const bool ChangedProfile=Frame==7,ChangedXY=Frame==10,ChangedDetail=Frame==13;
        if(ChangedProfile)Amplitude+=2;
        if(ChangedXY)Source[8*N+8].Position.X+=.137;
        if(ChangedDetail)Input.DetailWindowCm=FBox2D(Input.DetailWindowCm.Min+FVector2D(25,0),Input.DetailWindowCm.Max+FVector2D(25,0));
        Input.ProfileKey={Amplitude};
        for(int32 I=0;I<Source.Num();++I)
        {
            Shore[I]=.4f+.5f*float((I+Frame)%11)/10.f;
            Coarse[I]=Input.HeightAtWorldXYCm(FVector2D(Source[I].Position.X,Source[I].Position.Y))*Shore[I]+Frame*.03125f;
            Source[I].Position.Z=100.+Coarse[I]+Frame*.125;
            Source[I].Color.R=uint8((I+Frame)%255);
            Source[I].UV3.X=Frame*.25;
        }
        Queries.Store(0);
        TArray<FProcMeshVertex> A,B;TArray<uint32> AT,BT;TArray<int32> AO,BO;
        if(!TestTrue(TEXT("cached updates succeed"),Cached.Update(Source,SourceIndices,SourceOffsets,Coarse,Shore,Input,A,AT,AO)))return false;
        const bool MustBuild=Frame==0 || ChangedProfile || ChangedXY || ChangedDetail;
        if(MustBuild)++ExpectedBuilds;
        TestEqual(TEXT("only geometry/profile/detail changes rebuild selection"),Cached.GetBuildCount(),ExpectedBuilds);
        if(!MustBuild)TestEqual(TEXT("changing shore/coarse/base/optical inputs requires no profile query"),Queries.Load(),0);
        else TestTrue(TEXT("changed selection inputs recompute profile"),Queries.Load()>0);
        // Force the comparison path to rebuild its selection every frame,
        // retaining the SAME temporal history. Resetting the object would
        // test different blending histories rather than cache correctness.
        auto FreshInput=Input;FreshInput.ProfileKey.Add(Frame);
        if(!Fresh.Update(Source,SourceIndices,SourceOffsets,Coarse,Shore,FreshInput,B,BT,BO))return false;
        TestTrue(TEXT("fresh and cached topology and cell ownership identical"),AT==BT && AO==BO && A.Num()==B.Num());
        TestTrue(TEXT("fresh and cached target corrections identical"),Cached.GetTargetCorrectionsCm()==Fresh.GetTargetCorrectionsCm());
        bool Equal=A.Num()==B.Num();
        for(int32 I=0;Equal && I<A.Num();++I)
        {
            const auto& V=A[I];const auto& W=B[I];
            Equal=V.Position==W.Position && V.Normal==W.Normal && V.Color==W.Color &&
                V.UV0==W.UV0 && V.UV1==W.UV1 && V.UV2==W.UV2 && V.UV3==W.UV3 &&
                V.Tangent.TangentX==W.Tangent.TangentX && V.Tangent.bFlipTangentY==W.Tangent.bFlipTangentY;
            if(I<Source.Num())Equal=Equal && V.Position==Source[I].Position;
            ++ComparedVertices;
        }
        TestTrue(TEXT("every rendered attribute matches full rebuild exactly; source positions retained"),Equal);
    }
    AddInfo(FString::Printf(TEXT("Independent target-cache comparisons: %lld vertices over16 changing frames;4 selection builds rather than16"),ComparedVertices));
    return !HasAnyErrors();
}
#endif
