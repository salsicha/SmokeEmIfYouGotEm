#include "Misc/AutomationTest.h"
#include "RaftSimPlayableCrestMesh.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPlayableCrestMeshTest,
    "RaftSim.Water.PlayableCrestReconstruction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimPlayableCrestMeshTest::RunTest(const FString&)
{
    using FAdapter=URaftSimWaterRuntimeAdapter;
    TArray<FVector2D> Points;
    TArray<int32> Triangles;
    TArray<float> Shore,CrestCm;
    TArray<FAdapter::FSupportBreakingSite> Sites;
    Sites.Add({FVector2D(.23,.41),.8f,.56f,2.0f,1.0f,true});
    const auto Height=[&](FVector2D P) { return FAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.22f,1.5f); };
    for (int32 Y=0;Y<17;++Y) for(int32 X=0;X<17;++X)
    {
        const FVector2D P(-12+1.5*X,-12+1.5*Y);
        Points.Add(P);Shore.Add(FMath::SmoothStep(-12.0f,-6.0f,float(P.Y)));
        CrestCm.Add(Height(P)*Shore.Last()*100);
        if(X<16 && Y<16) { int32 A=Y*17+X,B=A+1,C=A+17,D=C+1;Triangles.Append({A,C,B,B,C,D}); }
    }
    FRaftSimSurfaceRefinement Ref;
    const FBox2D Finest(FVector2D(-3,-4),FVector2D(4,4));
    TestTrue(TEXT("conforming refinement built"),Ref.Build(Points,Triangles,FBox2D(FVector2D(-9,-9),FVector2D(9,9)),3,&Finest));
    TArray<FVector2D> FinePoints;Ref.Expand(Points,FinePoints);
    TArray<float> FineShore;Ref.Expand(Shore,FineShore);
    for(float Sign:{1.0f,-1.0f})
    {
        TArray<FVector> Base,Positions,Normals;
        for(int32 I=0;I<Points.Num();++I)
            Base.Add(FVector(Points[I].X*100,Points[I].Y*100*Sign,800+2*Points[I].X+CrestCm[I]));
        Ref.Expand(Base,Positions);Normals.Init(FVector::UpVector,Positions.Num());
        RaftSimPlayableCrestMesh::Reconstruct(Ref,FinePoints,CrestCm,Shore,Sites,.22f,1.5f,1,Sign,Positions,Normals);
        TArray<FVector> CachedPositions,CachedNormals;
        TArray<float> Cache;
        Ref.Expand(Base,CachedPositions);CachedNormals.Init(FVector::UpVector,CachedPositions.Num());
        RaftSimPlayableCrestMesh::Reconstruct(Ref,FinePoints,CrestCm,Shore,Sites,.22f,1.5f,1,Sign,CachedPositions,CachedNormals,&Cache,true);
        TestTrue(TEXT("cache build has exact uncached positions"),CachedPositions==Positions);
        Ref.Expand(Base,CachedPositions);
        RaftSimPlayableCrestMesh::Reconstruct(Ref,FinePoints,CrestCm,Shore,Sites,.22f,1.5f,1,Sign,CachedPositions,CachedNormals,&Cache,false);
        TestTrue(TEXT("exact-input reuse has exact uncached positions"),CachedPositions==Positions);
        TestTrue(TEXT("cached path retains exact geometric normals"),CachedNormals==Normals);
        double MaximumVertexError=0,CoarseError=0,FineError=0;
        for(int32 I=0;I<Points.Num();++I)
            TestEqual(TEXT("original support/shore vertices are unchanged"),Positions[I],Base[I]);
        for(int32 I=0;I<FinePoints.Num();++I)
        {
            const double Expected=800+2*FinePoints[I].X+Height(FinePoints[I])*FineShore[I]*100;
            MaximumVertexError=FMath::Max(MaximumVertexError,FMath::Abs(Positions[I].Z-Expected));
            TestTrue(TEXT("finite upward geometric normals in both handednesses"),!Normals[I].ContainsNaN() && Normals[I].Z>0);
        }
        const auto Error=[&](const TArray<int32>& Indices,const TArray<FVector2D>& XY,const TArray<FVector>& V)
        {
            double Max=0;
            for(int32 T=0;T<Indices.Num();T+=3)
            {
                const int32 A=Indices[T],B=Indices[T+1],C=Indices[T+2];
                const FVector2D P=(XY[A]+XY[B]+XY[C])/3;
                if(FMath::Abs(P.X)>6 || FMath::Abs(P.Y)>6)continue;
                Max=FMath::Max(Max,FMath::Abs((V[A].Z+V[B].Z+V[C].Z)/300-(8+.02*P.X+Height(P))));
            }
            return Max;
        };
        CoarseError=Error(Triangles,Points,Base);FineError=Error(Ref.Triangles,FinePoints,Positions);
        TestTrue(TEXT("reconstructed vertex follows actual support profile within .001 cm"),MaximumVertexError<.001);
        TestTrue(TEXT("fine triangles reduce crest error by at least fourfold"),FineError<CoarseError*.25);
        TestTrue(TEXT("fine crest error below 2 cm"),FineError<.02);
        AddInfo(FString::Printf(TEXT("sign=%.0f coarse_error_m=%.6f fine_error_m=%.6f vertex_error_cm=%.9f"),Sign,CoarseError,FineError,MaximumVertexError));
    }
    return true;
}
#endif
