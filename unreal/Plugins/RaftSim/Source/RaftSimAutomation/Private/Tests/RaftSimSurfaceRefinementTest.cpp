#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"
#include "RaftSimWaterCarrierMeshComponent.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSurfaceRefinementTest,
    "RaftSim.WaterDetail.ConformingSurfaceRefinement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimSurfaceRefinementTest::RunTest(const FString&)
{
    TArray<FVector2D> Points;TArray<int32> Triangles;TArray<FVector> Plane;TArray<FLinearColor> Colors;
    for (int32 Y=0;Y<9;++Y)for (int32 X=0;X<9;++X)
    {
        const float U=1.5f*X,V=1.5f*Y;Points.Add(FVector2D(U,V));
        Plane.Add(FVector(U,V,2+0.1*U-0.2*V));Colors.Add(FLinearColor(0.02f*U,0.01f*V,0.5f,0.75f));
        if (X<8 && Y<8)
        {
            const int32 A=Y*9+X,B=A+1,C=A+9,D=C+1;
            Triangles.Append({A,C,B,B,C,D});
        }
    }
    for (int32 Levels : {2,3})
    {
    const FBox2D Window(FVector2D(3,3),FVector2D(6,6));FRaftSimSurfaceRefinement Refined;
    if (!TestTrue(TEXT("bounded refinement builds"),Refined.Build(Points,Triangles,Window,Levels)))return false;
    TArray<FVector2D> Expanded;TArray<FVector> ExpandedPlane;TArray<FLinearColor> ExpandedColors;
    Refined.Expand(Points,Expanded);Refined.Expand(Plane,ExpandedPlane);Refined.Expand(Colors,ExpandedColors);
    TMap<uint64,int32> EdgeCounts;double Area=0,MaxPlaneError=0,MaxColorError=0,MaxFineEdge=0;
    bool bValid=true;int32 OutsideOriginalTriangles=0;
    const auto Key=[](int32 A,int32 B) { return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); };
    for (int32 I=0;I<Refined.Triangles.Num();I+=3)
    {
        const int32 V[]={Refined.Triangles[I],Refined.Triangles[I+1],Refined.Triangles[I+2]};
        for (int32 Index:V)bValid &= Expanded.IsValidIndex(Index);
        if (!bValid)break;
        const FVector2D A=Expanded[V[0]],B=Expanded[V[1]],C=Expanded[V[2]];
        const double SignedArea=FVector2D::CrossProduct(B-A,C-A)*0.5;
        bValid &= SignedArea<0;Area-=SignedArea;
        if (V[0]<81 && V[1]<81 && V[2]<81)++OutsideOriginalTriangles;
        const FVector2D Centroid=(A+B+C)/3;
        for (int32 E=0;E<3;++E)
        {
            ++EdgeCounts.FindOrAdd(Key(V[E],V[(E+1)%3]));
            if (Window.IsInside(Centroid))MaxFineEdge=FMath::Max(MaxFineEdge,(Expanded[V[E]]-Expanded[V[(E+1)%3]]).Size());
        }
    }
    for (const auto& Edge:EdgeCounts)
    {
        const FVector2D A=Expanded[int32(Edge.Key>>32)],B=Expanded[int32(uint32(Edge.Key))];
        const bool bBoundary=(A.X==0 && B.X==0)||(A.Y==0 && B.Y==0)||(A.X==12 && B.X==12)||(A.Y==12 && B.Y==12);
        bValid &= Edge.Value==(bBoundary ? 1 : 2);
    }
    for (int32 I=0;I<Expanded.Num();++I)
    {
        const FVector2D P=Expanded[I];
        MaxPlaneError=FMath::Max(MaxPlaneError,FMath::Abs(ExpandedPlane[I].Z-(2+0.1*P.X-0.2*P.Y)));
        const FLinearColor C=ExpandedColors[I];
        MaxColorError=FMath::Max(MaxColorError,double(FMath::Max(FMath::Abs(C.R-0.02f*P.X),FMath::Abs(C.G-0.01f*P.Y))));
        bValid &= C.B==0.5f && C.A==0.75f;
    }
    TestTrue(TEXT("no winding flips, holes, internal boundary edges or nonmanifold seams"),bValid);
    TestTrue(TEXT("triangle area preserved, no overlapping second surface"),FMath::Abs(Area-144)<1.e-6);
    TestTrue(TEXT("source plane and interpolated attributes preserved"),MaxPlaneError<1.e-6 && MaxColorError<1.e-6);
    const double EdgeScale=Levels==2 ? 1.0 : 0.5;
    TestTrue(TEXT("crux triangles actually finer than hydraulic lattice"),MaxFineEdge<=0.531*EdgeScale && MaxFineEdge>0.5*EdgeScale);
    TestTrue(TEXT("distant source triangles are not needlessly refined"),OutsideOriginalTriangles>0);
    auto Invalid=Triangles;Invalid[0]=100000;
    TestFalse(TEXT("invalid source rejected"),Refined.Build(Points,Invalid,Window,2));
    AddInfo(FString::Printf(TEXT("Conforming refinement: area %.9g, plane error %.9g, color error %.9g, maximum crux edge %.9g m, untouched triangles %d"),
        Area,MaxPlaneError,MaxColorError,MaxFineEdge,OutsideOriginalTriangles));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterCarrierBoundsTest,
    "RaftSim.WaterDetail.GPUCarrierLiveBounds",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimWaterCarrierBoundsTest::RunTest(const FString&)
{
    auto* Carrier=NewObject<URaftSimWaterCarrierMeshComponent>();
    const auto DefaultBounds=Carrier->CalcBounds(FTransform::Identity);
    Carrier->SetHydraulicBounds(FBox(FVector(-100,-200,700),FVector(100,200,900)));
    auto Bounds=Carrier->CalcBounds(FTransform(FVector(1000,2000,0)));
    TestTrue(TEXT("world bounds follow GPU-displaced hydraulic stage"),Bounds.Origin.Equals(FVector(1000,2000,800),1.e-6));
    TestTrue(TEXT("coarse hydraulic extent retained"),Bounds.BoxExtent.Equals(FVector(100,200,100),1.e-6));
    Carrier->SetHydraulicBounds(FBox(FVector(-100,-200,800),FVector(100,200,1000)));
    Bounds=Carrier->CalcBounds(FTransform::Identity);
    TestTrue(TEXT("stage change updates culling without a fine vertex upload"),Bounds.Origin.Equals(FVector(0,0,900),1.e-6));
    Carrier->SetHydraulicBounds(FBox(ForceInit));
    Bounds=Carrier->CalcBounds(FTransform::Identity);
    TestTrue(TEXT("leaving GPU mode restores ordinary mesh bounds"),Bounds.Origin.Equals(DefaultBounds.Origin,1.e-6) && Bounds.BoxExtent.Equals(DefaultBounds.BoxExtent,1.e-6));
    return true;
}
#endif
