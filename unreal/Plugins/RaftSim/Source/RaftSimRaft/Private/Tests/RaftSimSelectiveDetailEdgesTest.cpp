#include "RaftSimSurfaceRefinement.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimShorelineCrests.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSelectiveDetailEdgesTest,"RaftSim.M4.SelectiveDetailEdges",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSelectiveDetailEdgesTest::RunTest(const FString&)
{
    // Anisotropic curved-bank-like strips, including oblique directions and
    // changing inputs. The requested detail-span gate is not relaxed for them.
    FRaftSimSurfaceRefinement Candidate,Reference;
    Candidate.bSelectiveDetailEdges=true;
    Candidate.bIndexedEdges=Reference.bIndexedEdges=true;
    bool Saved=false;
    for(int32 Frame=0;Frame<18;++Frame)
    {
        const double Angle=Frame*.17;
        TArray<FVector2D> XY;
        for(int32 Y=0;Y<2;++Y)for(int32 X=0;X<2;++X)
        {
            const double U=X*100.,V=Y*(1.+Frame*.1);
            XY.Emplace(U*FMath::Cos(Angle)-V*FMath::Sin(Angle),U*FMath::Sin(Angle)+V*FMath::Cos(Angle));
        }
        const TArray<int32> Root={0,1,2,1,3,2};
        const FBox2D Window(FVector2D(-200,-200),FVector2D(200,200));
        const auto Height=[](const FVector2D& P){return float(.001*P.X+.002*P.Y);};
        for(auto* W:{&Reference,&Candidate})
            if(!TestTrue(TEXT("current strip builds"),W->BuildAdaptive(XY,Root,Height,3,.5f,{},nullptr,
                true,true,&Window,12.5f,true)))return false;
        TArray<FVector2D> P;Candidate.Expand(XY,P);
        FRaftSimSurfaceRefinement Fresh;Fresh.bSelectiveDetailEdges=true;Fresh.bIndexedEdges=true;
        if(!Fresh.BuildAdaptive(XY,Root,Height,3,.5f,{},nullptr,false,false,&Window,12.5f))return false;
        TestTrue(TEXT("changing cached parallel output equals fresh serial output"),
            Candidate.Triangles==Fresh.Triangles && Candidate.MidpointParents==Fresh.MidpointParents &&
            Candidate.TriangleOrigins==Fresh.TriangleOrigins);
        TMap<uint64,int32> Incidence;double Area=0.,MaxSpan=0.;
        for(int32 T=0;T<Candidate.Triangles.Num();T+=3)
        {
            const int32 V[3]={Candidate.Triangles[T],Candidate.Triangles[T+1],Candidate.Triangles[T+2]};
            const double Twice=FVector2D::CrossProduct(P[V[1]]-P[V[0]],P[V[2]]-P[V[0]]);
            TestTrue(TEXT("positive winding"),Twice>0.);Area+=Twice*.5;
            for(int32 E=0;E<3;++E)
            {
                const int32 A=V[E],B=V[(E+1)%3];
                ++Incidence.FindOrAdd((uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)));
                const FVector2D D=P[A]-P[B];MaxSpan=FMath::Max(MaxSpan,FMath::Max(FMath::Abs(D.X),FMath::Abs(D.Y)));
            }
        }
        TestTrue(TEXT("unchanged 12.5cm detail-span gate"),MaxSpan<=12.5+1.e-8);
        TestTrue(TEXT("area preserved"),FMath::Abs(Area-100.*(1.+Frame*.1))<1.e-8);
        for(const auto& E:Incidence)
        {
            const FVector2D A=P[int32(E.Key>>32)],B=P[int32(uint32(E.Key))];
            bool Boundary=false;
            const int32 Outline[4]={0,1,3,2};
            for(int32 K=0;K<4;++K)
            {
                const FVector2D S=XY[Outline[K]],D=XY[Outline[(K+1)%4]]-S;
                Boundary|=FMath::Abs(FVector2D::CrossProduct(A-S,D))<1.e-8 &&
                    FMath::Abs(FVector2D::CrossProduct(B-S,D))<1.e-8;
            }
            TestEqual(TEXT("shared edges conform without internal cracks"),E.Value,Boundary?1:2);
        }
        for(int32 I=0;I<XY.Num();++I)TestTrue(TEXT("source vertices retained exactly"),P[I]==XY[I]);
        Saved|=Candidate.Triangles.Num()<Reference.Triangles.Num();
        AddInfo(FString::Printf(TEXT("frame=%d max_span_cm=%.12g reference_triangles=%d candidate_triangles=%d"),
            Frame,MaxSpan,Reference.Triangles.Num()/3,Candidate.Triangles.Num()/3));
    }
    TestTrue(TEXT("at least one thin strip avoids redundant subdivision"),Saved);
    // Independent interior error against the actual physical crest evaluator,
    // not agreement with our selection predicate or a source-text guard.
    URaftSimWaterRuntimeAdapter::FSupportBreakingSite Site;
    Site.RiverCoordinatesMeters=FVector2D(0,0);Site.FlowDirection=FVector2D(1,0);
    Site.PhysicalCrestHeightMeters=.511849642f;Site.PhysicalCrestLengthMeters=2.f;
    Site.Intensity=1.f;Site.SpillingFraction=1.f;Site.bLocalEnvelopeCap=true;
    const TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites={Site};
    const auto Profile=[&](const FVector2D& P)
    {return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P*.01,Sites,1.f,1.f)*100.f;};
    TArray<FVector2D> Grid;TArray<int32> Root;
    constexpr int32 NX=17,NY=5;
    for(int32 Y=0;Y<NY;++Y)for(int32 X=0;X<NX;++X)Grid.Emplace((X-8)*100.,(Y-2)*5.);
    for(int32 Y=0;Y<NY-1;++Y)for(int32 X=0;X<NX-1;++X)
    {const int32 A=Y*NX+X;Root.Append({A,A+1,A+NX,A+1,A+NX+1,A+NX});}
    const FBox2D Window(FVector2D(-1000,-1000),FVector2D(1000,1000));
    if(!Candidate.BuildAdaptive(Grid,Root,Profile,3,.5f,{},nullptr,true,true,&Window,12.5f,true))return false;
    TArray<FVector2D> Points;Candidate.Expand(Grid,Points);
    double MaxError=0.;
    for(int32 T=0;T<Candidate.Triangles.Num();T+=3)
    {
        const FVector2D A=Points[Candidate.Triangles[T]],B=Points[Candidate.Triangles[T+1]],C=Points[Candidate.Triangles[T+2]];
        const double HA=Profile(A),HB=Profile(B),HC=Profile(C);
        for(int32 U=0;U<=11;++U)for(int32 V=0;V<=11-U;++V)
        {
            const double WB=U/11.,WC=V/11.,WA=1.-WB-WC;
            MaxError=FMath::Max(MaxError,FMath::Abs(double(Profile(A*WA+B*WB+C*WC))-(HA*WA+HB*WB+HC*WC)));
        }
    }
    TestTrue(TEXT("independent physical crest interior error stays within 2cm"),MaxError<=2.);
    AddInfo(FString::Printf(TEXT("physical crest maximum interior error_cm=%.12g triangles=%d"),MaxError,Candidate.Triangles.Num()/3));
    if(!Candidate.BuildAdaptive(Grid,Root,Profile,3,.5f) || !Reference.BuildAdaptive(Grid,Root,Profile,3,.5f))return false;
    TestTrue(TEXT("macro-only refinement remains exactly the reference topology"),Candidate.Triangles==Reference.Triangles &&
        Candidate.MidpointParents==Reference.MidpointParents && Candidate.TriangleOrigins==Reference.TriangleOrigins);
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSelectiveCrestModeTest,"RaftSim.M4.SelectiveCrestMode",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSelectiveCrestModeTest::RunTest(const FString&)
{
    FRaftSimShorelineCrests State;
    FRaftSimShorelineCrestInput Input;
    Input.ProfileKey={1.};Input.HeightAtWorldXYCm=[](const FVector2D&){return 0.f;};
    Input.DetailWindowCm=FBox2D(FVector2D(-1,-1),FVector2D(101,2));Input.DetailSpanCm=12.5f;
    TArray<FProcMeshVertex> Source;Source.SetNum(4);
    for(int32 I=0;I<4;++I){Source[I].Position=FVector((I%2)*100.,I/2,100.);Source[I].Normal=FVector::UpVector;}
    const TArray<uint32> Root={0,1,2,1,3,2};const TArray<int32> Cells={0,6};
    const TArray<float> Coarse={0,0,0,0},Shore={1,1,1,1};
    Input.SourceCrestCm=Coarse;Input.SourceShoreWeight=Shore;
    TArray<FProcMeshVertex> V;TArray<uint32> T;TArray<int32> Offsets;
    int32 ReferenceCount=0;
    for(int32 Frame=0;Frame<3;++Frame)
    {
        const bool Enabled=Frame==1;
        if(!TestTrue(TEXT("actual crest state accepts mode switch"),State.Update(Source,Root,Cells,Coarse,Shore,Input,V,T,Offsets,Enabled)))return false;
        if(Frame==0)ReferenceCount=T.Num();
        if(Enabled)TestTrue(TEXT("actual published topology avoids redundant short-edge subdivisions"),T.Num()<ReferenceCount);
        if(Frame==2)TestEqual(TEXT("switching mode invalidates same-input geometry cache"),T.Num(),ReferenceCount);
        TestTrue(TEXT("published cell ownership retained"),Offsets.Num()==2 && Offsets[0]==0 && Offsets[1]==T.Num());
        for(const auto& P:V)TestTrue(TEXT("published plane unchanged"),P.Position.Z==100.);
    }
    return !HasAnyErrors();
}
#endif
