#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimMovingDetailMeshTest,
    "RaftSim.WaterDetail.MovingDetailMeshSampling",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimMovingDetailMeshTest::RunTest(const FString&)
{
    TArray<FVector2D> Points;TArray<int32> Triangles;
    for (int32 Y=0;Y<=16;++Y)for(int32 X=0;X<=16;++X)
    {
        Points.Emplace(-544000.+X*100.,-360000.+Y*100.);
        if(X<16 && Y<16)
        {
            const int32 A=Y*17+X;Triangles.Append({A,A+17,A+1,A+1,A+17,A+18});
        }
    }
    // A zero macro profile must still acquire samples for dynamic GPU waves.
    const auto Height=[](const FVector2D&) { return 0.f; };
    TArray<FBox2D> EmptyProfile={FBox2D(FVector2D(0,0),FVector2D(1,1))};
    for (int32 Shift : {0,250,550})
    {
        const FBox2D Window(FVector2D(-543800.+Shift,-359800.),FVector2D(-543400.+Shift,-359300.));
        FRaftSimSurfaceRefinement Serial,Parallel;
        if(!TestTrue(TEXT("flat macro receives dynamic-field samples"),Serial.BuildAdaptive(
            Points,Triangles,Height,3,.5f,EmptyProfile,nullptr,false,false,&Window,50.f)))return false;
        TestTrue(TEXT("parallel build succeeds"),Parallel.BuildAdaptive(
            Points,Triangles,Height,3,.5f,EmptyProfile,nullptr,true,true,&Window,50.f));
        TestTrue(TEXT("serial/parallel exact topology and ownership"),Serial.Triangles==Parallel.Triangles &&
            Serial.MidpointParents==Parallel.MidpointParents && Serial.TriangleOrigins==Parallel.TriangleOrigins);
        TArray<FVector2D> Expanded;Serial.Expand(Points,Expanded);
        for(int32 I=0;I<Points.Num();++I)TestTrue(TEXT("original XY immutable"),Expanded[I]==Points[I]);
        double Area=0,MaxSpan=0;TMap<uint64,int32> Edges;
        for(int32 T=0;T<Serial.Triangles.Num();T+=3)
        {
            const int32 A=Serial.Triangles[T],B=Serial.Triangles[T+1],C=Serial.Triangles[T+2];
            FBox2D Bounds(ForceInit);Bounds+=Expanded[A];Bounds+=Expanded[B];Bounds+=Expanded[C];
            const double Signed=FVector2D::CrossProduct(Expanded[B]-Expanded[A],Expanded[C]-Expanded[A])*.5;
            TestTrue(TEXT("winding preserved"),Signed<0);Area-=Signed;
            if(Window.Intersect(Bounds))MaxSpan=FMath::Max(MaxSpan,FMath::Max(Bounds.GetSize().X,Bounds.GetSize().Y));
            const int32 V[]={A,B,C};
            for(int32 E=0;E<3;++E)
                ++Edges.FindOrAdd((uint64(FMath::Min(V[E],V[(E+1)%3]))<<32)|uint32(FMath::Max(V[E],V[(E+1)%3])));
        }
        TestTrue(TEXT("maximum intersecting triangle axis span is half a metre"),MaxSpan<=50.);
        TestTrue(TEXT("area retained exactly, one surface"),Area==2560000.);
        for(const auto& E:Edges)
        {
            const auto A=Expanded[int32(E.Key>>32)],B=Expanded[int32(uint32(E.Key))];
            const bool Boundary=(A.X==B.X && (A.X==-544000. || A.X==-542400.)) ||
                (A.Y==B.Y && (A.Y==-360000. || A.Y==-358400.));
            TestEqual(TEXT("conforming edges, no holes or T junctions"),E.Value,Boundary ? 1 : 2);
        }
    }
    return true;
}
#endif
