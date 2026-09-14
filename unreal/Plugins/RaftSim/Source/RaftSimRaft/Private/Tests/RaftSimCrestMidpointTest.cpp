#include "Misc/AutomationTest.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "RaftSimWaterVertexCopy.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestMidpointTest,"RaftSim.M4.CrestMidpointExpansion",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestMidpointTest::RunTest(const FString&)
{
    FRaftSimCrestMidpointExpansion Work;int64 Compared=0;
    const auto Original=[](const FProcMeshVertex& A,const FProcMeshVertex& B)
    {
        FProcMeshVertex V;V.Position=(A.Position+B.Position)*.5;V.Normal=(A.Normal+B.Normal).GetSafeNormal();
        V.Color=((A.Color.ReinterpretAsLinear()+B.Color.ReinterpretAsLinear())*.5f).ToFColor(false);
        V.UV0=(A.UV0+B.UV0)*.5;V.UV1=(A.UV1+B.UV1)*.5;V.UV2=(A.UV2+B.UV2)*.5;V.UV3=(A.UV3+B.UV3)*.5;
        V.Tangent=FProcMeshTangent((A.Tangent.TangentX+B.Tangent.TangentX).GetSafeNormal(),A.Tangent.bFlipTangentY);return V;
    };
    for(int32 Frame=0;Frame<20;++Frame)
    {
        const int32 Sources=Frame<10 ? 317 : 211;TArray<FIntPoint> Parents;
        if(Frame!=7)for(int32 Level=0;Level<3;++Level)
        {
            const int32 Available=Sources+Parents.Num();
            for(int32 I=0;I<2049-Level*173;++I)Parents.Emplace((I*17+Level*31)%Available,(I*71+Frame/4)%Available);
        }
        TArray<FProcMeshVertex> A;A.SetNum(Sources+Parents.Num());
        for(int32 I=0;I<Sources;++I)
        {
            auto& V=A[I];V.Position=FVector(-545000.+I*.137+Frame*.031,356000.-I*.293,I*.17);
            V.Normal=FVector(.2+I*.001,.3,.9).GetSafeNormal();V.Color=FColor(I%251,83,147,(Frame+I)%256);
            V.UV0=FVector2D(I*.007,-.19);V.UV1=FVector2D(-2.7+Frame*.013,3.1);
            V.UV2=FVector2D(.17,.91);V.UV3=FVector2D(.35,-.6-I*.03);
            V.Tangent=FProcMeshTangent(FVector(.9,-.2,I*.001).GetSafeNormal(),I%2!=0);
        }
        auto B=A;for(int32 I=0;I<Parents.Num();++I){const auto P=Parents[I];A[Sources+I]=Original(A[P.X],A[P.Y]);}
        if(!TestTrue(TEXT("dependency expansion succeeds"),Work.Expand(B,Sources,Parents)))return false;
        for(int32 I=0;I<A.Num();++I)if(!FRaftSimCrestMidpointExpansion::EqualAttributes(A[I],B[I]))
        {AddError(FString::Printf(TEXT("attribute bits differ at frame%d vertex%d"),Frame,I));return false;}
        Compared+=A.Num();
        if(Frame==13)Work.Reset();
    }
    TArray<FProcMeshVertex> Bad;Bad.SetNum(2);
    TestFalse(TEXT("forward parent rejected"),Work.Expand(Bad,1,{FIntPoint(0,1)}));
    TestFalse(TEXT("negative parent rejected"),Work.Expand(Bad,1,{FIntPoint(-1,0)}));
    TestFalse(TEXT("missing output rejected"),Work.Expand(Bad,1,{}));
    AddInfo(FString::Printf(TEXT("Compared %lld complete vertex attribute sets over20 changing/dependent/cropped/reset/empty frames"),Compared));
    return !HasAnyErrors();
}
#endif
