#include "Misc/AutomationTest.h"
#include "RaftSimCrestNormals.h"
#include "RaftSimCrestMidpointExpansion.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestNormalsTest,"RaftSim.M4.CrestNormals",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestNormalsTest::RunTest(const FString&)
{
    constexpr int32 N=41;
    TArray<FProcMeshVertex> Input;Input.SetNum(N*N);
    TArray<uint32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        const int32 I=Y*N+X;auto& V=Input[I];
        V.Position=FVector(-544000+X*25,-360000+Y*25,0);
        V.Normal=FVector(.1,.2,1).GetSafeNormal();V.Tangent=FProcMeshTangent(FVector(.9,.1,0),I%2!=0);
        V.Color=FColor(I%255,40,90,255);V.UV0=FVector2D(X,Y);V.UV1=FVector2D(-1,4);V.UV2=FVector2D(.1,.7);V.UV3=FVector2D(3,-2);
        if(X<N-1 && Y<N-1){const uint32 A=I;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimCrestNormals Cached,FullCache;int64 Compared=0;
    for(int32 Frame=0;Frame<24;++Frame)
    {
        int32 SourceCount=Frame<15 ? N*N/2 : N*N/3;
        if(Frame==0)SourceCount=N*N; // No vertices consume recomputed normals.
        if(Frame==2)SourceCount=0; // All incident faces must still be evaluated.
        if(Frame==5)SourceCount=N*N-1; // Sparse fine region needs adjacent coarse faces.
        for(int32 I=0;I<Input.Num();++I)Input[I].Position.Z=FMath::Sin(I*.39+Frame*.17)*20.+I%7;
        if(Frame==3)Input[14].Position=Input[15].Position;
        if(Frame==7)for(int32 T=0;T<Triangles.Num();T+=3)Swap(Triangles[T+1],Triangles[T+2]);
        if(Frame==10)Triangles.Append({14,14,15,0,0,0});
        if(Frame==18)Triangles.Reset();
        if(Frame==20)Triangles.Append({0,1,2,3,4,5,N*N-1,1,2});
        if(Frame==22)Cached.Reset();
        auto A=Input,B=Input;const uint64 Before=Cached.Builds;
        FRaftSimCrestNormals::Reference(A,Triangles,SourceCount);
        if(!TestTrue(TEXT("parallel path accepts valid changing mesh"),Cached.Apply(B,Triangles,SourceCount,true)))return false;
        if(Frame==4)TestEqual(TEXT("unchanged topology reuses incidence with new heights"),Cached.Builds,Before);
        auto Full=Input;
        TestTrue(TEXT("full-face control accepts same input"),FullCache.Apply(Full,Triangles,SourceCount,false));
        for(int32 I=0;I<A.Num();++I)
        {
            if(!FRaftSimCrestMidpointExpansion::EqualAttributes(A[I],B[I]) ||
                !FRaftSimCrestMidpointExpansion::EqualAttributes(Full[I],B[I]))
            {AddError(FString::Printf(TEXT("attribute mismatch frame=%d vertex=%d"),Frame,I));return false;}
            ++Compared;
        }
    }
    auto Invalid=Input;TArray<uint32> Bad={0,1,uint32(Input.Num())};
    TestFalse(TEXT("out of range triangle rejected"),Cached.Apply(Invalid,Bad,2));
    TestFalse(TEXT("incomplete triangle rejected"),Cached.Apply(Invalid,{0,1},2));
    TestFalse(TEXT("invalid source prefix rejected"),Cached.Apply(Invalid,{},Input.Num()+1));
    AddInfo(FString::Printf(TEXT("Exact normal/tangent and all-attribute comparisons: %lld vertices,24 changing frames,degenerate/repeated/winding/dry/rewet/reset/source-prefix changes"),Compared));
    return !HasAnyErrors();
}
#endif
