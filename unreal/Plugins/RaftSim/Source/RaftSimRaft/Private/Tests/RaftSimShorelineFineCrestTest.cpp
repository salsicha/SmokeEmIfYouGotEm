#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "RaftSimPreparedBreakingHeightRange.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RenderingThread.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineFineCrestTest,"RaftSim.M4.ShorelineFineCrest",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineFineCrestTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Actor=World->SpawnActor<AActor>();
    auto* Mesh=NewObject<URaftSimShorelineMeshComponent>(Actor);
    Actor->SetRootComponent(Mesh); Mesh->RegisterComponent();
    constexpr int32 N=33;
    TArray<uint8> Wet,Available; Wet.Init(1,N*N); Available.Init(1,N*N);
    TArray<float> H,Bed,Coarse,Shore; H.Init(1,N*N); Bed.Init(0,N*N); Shore.Init(1,N*N);
    for (int32 Y=24; Y<=26; ++Y) for (int32 X=24; X<=26; ++X)
    { Wet[Y*N+X]=0; H[Y*N+X]=0; Bed[Y*N+X]=2; }
    URaftSimWaterRuntimeAdapter::FSupportBreakingSite Site;
    Site.RiverCoordinatesMeters=FVector2D(-5439.,3606.);
    Site.PhysicalCrestHeightMeters=.511849642f; Site.PhysicalCrestLengthMeters=2.f;
    Site.FlowDirection=FVector2D(-.695725685170176,.718307574089602);
    Site.Intensity=1.f; Site.SpillingFraction=1.f; Site.bLocalEnvelopeCap=true;
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites={Site};
    const FRaftSimPreparedBreakingHeightRange Prepared(Sites);
    const auto Area=[](const TArray<FProcMeshVertex>& V,const TArray<uint32>& T)
    {
        double Sum=0.;
        for (int32 I=0; I<T.Num(); I+=3) Sum+=FMath::Abs(FVector::CrossProduct(
            V[T[I+1]].Position-V[T[I]].Position,V[T[I+2]].Position-V[T[I]].Position).Z)*.5;
        return Sum;
    };
    for (double Sign:{-1.,1.})
    {
        FRaftSimShorelineCrestInput Input;
        Input.ProfileKey={Sign,Site.PhysicalCrestHeightMeters};
        Input.PreparedHeightRangeWidthAtWorldXYCm=[&](const FBox2D& Box)
        {
            FBox2D Field(ForceInit);
            Field+=FVector2D(Box.Min.X*.01,Box.Min.Y*.01*Sign);
            Field+=FVector2D(Box.Max.X*.01,Box.Max.Y*.01*Sign);
            return Prepared.WidthMeters(Field)*100.f;
        };
        Input.TightHeightRangeWidthAtWorldXYCm=[&](const FBox2D& Box)
        {
            FBox2D Field(ForceInit);
            Field+=FVector2D(Box.Min.X*.01,Box.Min.Y*.01*Sign);
            Field+=FVector2D(Box.Max.X*.01,Box.Max.Y*.01*Sign);
            return Prepared.WidthMeters<true>(Field)*100.f;
        };
        Input.HeightAtWorldXYCm=[&](const FVector2D& P)
        { return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(P.X*.01,P.Y*.01*Sign),Sites,1.f,1.f)*100.f; };
        TArray<FProcMeshVertex> Source; Source.SetNum(N*N); Coarse.SetNum(N*N);
        for (int32 Y=0; Y<N; ++Y) for (int32 X=0; X<N; ++X)
        {
            const int32 I=Y*N+X;
            Source[I].Position=FVector((-5455.+X)*100.,Sign*(3590.+Y)*100.,100.);
            Source[I].Normal=FVector::UpVector; Source[I].Color=FColor(17,81,123,255);
            Source[I].UV0=FVector2D(X,Y); Source[I].UV1=FVector2D(-2,3); Source[I].UV2=FVector2D(.2,.4);
            Coarse[I]=Input.HeightAtWorldXYCm(FVector2D(Source[I].Position.X,Source[I].Position.Y));
            Source[I].Position.Z+=Coarse[I];
        }
        Input.SourceCrestCm=Coarse; Input.SourceShoreWeight=Shore;
        auto Copy=Source;
        if (!TestTrue(TEXT("actual clipped component accepts shared fine crests"),
            Mesh->SetClippedWaterMesh(N,N,MoveTemp(Copy),Wet,Available,H,Bed,&Input))) return false;
        const auto& V=Mesh->GetWaterVertices(); const auto& T=Mesh->GetWaterIndices();
        for (int32 I=0; I<N*N; ++I)
        {
            TestTrue(TEXT("every original source position is unchanged"),V[I].Position==Source[I].Position);
            TestTrue(TEXT("source foam/flow/wake encoding unchanged"),V[I].Color==Source[I].Color && V[I].UV1==Source[I].UV1 && V[I].UV2==Source[I].UV2);
        }
        TArray<FProcMeshVertex> Original; TArray<uint32> OriginalTriangles;
        Copy=Source;
        if (!RaftSimWaterShoreline::Build(N,N,MoveTemp(Copy),Wet,Available,H,Bed,Original,OriginalTriangles,nullptr,nullptr,true)) return false;
        // Independently retain the old full edge reserve through refinement.
        // Compact CPU numbering must change no actual fine triangle attribute.
        TArray<FProcMeshVertex> Reserved,ReservedFine;
        TArray<uint32> ReservedTriangles,ReservedFineTriangles;
        TArray<int32> ReservedOffsets,ReservedFineOffsets;
        TArray<RaftSimWaterShoreline::FEdge> ReservedEdges;
        Copy=Source;
        if (!RaftSimWaterShoreline::Build(N,N,MoveTemp(Copy),Wet,Available,H,Bed,
            Reserved,ReservedTriangles,&ReservedOffsets,&ReservedEdges)) return false;
        TArray<float> ReservedCoarse,ReservedShore;
        ReservedCoarse.Init(0,Reserved.Num()); ReservedShore.Init(0,Reserved.Num());
        for (int32 I=0; I<N*N; ++I) { ReservedCoarse[I]=Coarse[I]; ReservedShore[I]=Shore[I]; }
        for (const auto& E:ReservedEdges)
        { ReservedCoarse[E.Node]=Coarse[E.WetVertex]; ReservedShore[E.Node]=Shore[E.WetVertex]; }
        FRaftSimShorelineCrests ReservedRefinement;
        if (!ReservedRefinement.Update(Reserved,ReservedTriangles,ReservedOffsets,ReservedCoarse,
            ReservedShore,Input,ReservedFine,ReservedFineTriangles,ReservedFineOffsets)) return false;
        bool SameFine=T.Num()==ReservedFineTriangles.Num() && Mesh->GetCellOffsets()==ReservedFineOffsets;
        for (int32 I=0; SameFine && I<T.Num(); ++I)
        {
            const auto& A=V[T[I]]; const auto& B=ReservedFine[ReservedFineTriangles[I]];
            SameFine=A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==B.UV3 &&
                A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
        }
        TestTrue(TEXT("compact CPU edges preserve every fine triangle corner, normal and optical attribute exactly"),SameFine);
        FBox2D Bounds(ForceInit);
        for (double D:{-6.,14.}) for (double A:{-12.,12.})
        {
            const FVector2D P=Site.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),Site.FlowDirection);
            Bounds+=FVector2D(P.X*100.,P.Y*100.*Sign);
        }
        TArray<FBox2D> Regions={Bounds.ExpandBy(.01)};
        TArray<FVector2D> OriginalXY; for (const auto& P:Original) OriginalXY.Emplace(P.Position.X,P.Position.Y);
        TArray<int32> OriginalT; for (uint32 I:OriginalTriangles) OriginalT.Add(int32(I));
        FRaftSimSurfaceRefinement Full,Bounded;
        if (!Full.BuildAdaptive(OriginalXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f) ||
            !Bounded.BuildAdaptive(OriginalXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f,Regions)) return false;
        TestTrue(TEXT("exact zero-support rejection preserves every refinement parent and triangle"),
            Full.MidpointParents==Bounded.MidpointParents && Full.Triangles==Bounded.Triangles && Full.TriangleOrigins==Bounded.TriangleOrigins);
        FRaftSimSurfaceRefinement Parallel;
        if (!Parallel.BuildAdaptive(OriginalXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f,Regions,nullptr,true)) return false;
        TestTrue(TEXT("parallel selection preserves exact serial parent, triangle and owner order"),
            Full.MidpointParents==Parallel.MidpointParents && Full.Triangles==Parallel.Triangles && Full.TriangleOrigins==Parallel.TriangleOrigins);
        TAtomic<int32> ParallelQueries(0);
        const auto CountParallel=[&](const FVector2D& P)
        { ++ParallelQueries; return Input.HeightAtWorldXYCm(P); };
        FRaftSimSurfaceRefinement BatchMemo;
        if (!BatchMemo.BuildAdaptive(OriginalXY,OriginalT,CountParallel,3,.5f,Regions,nullptr,true,false)) return false;
        const int32 UncachedQueries=ParallelQueries.Load(); ParallelQueries.Store(0);
        if (!BatchMemo.BuildAdaptive(OriginalXY,OriginalT,CountParallel,3,.5f,Regions,nullptr,true,true)) return false;
        TestTrue(TEXT("batch-local parallel memoization preserves exact fresh serial topology"),
            Full.MidpointParents==BatchMemo.MidpointParents && Full.Triangles==BatchMemo.Triangles && Full.TriangleOrigins==BatchMemo.TriangleOrigins);
        TestTrue(TEXT("independent batch tables reduce repeated exact profile evaluations"),
            ParallelQueries.Load()>0 && ParallelQueries.Load()<UncachedQueries);
        TMap<FVector2D,float> Values;
        int32 Queries=0;
        const auto Counted=[&](const FVector2D& P) { ++Queries; return Input.HeightAtWorldXYCm(P); };
        FRaftSimSurfaceRefinement Memoized;
        if (!Memoized.BuildAdaptive(OriginalXY,OriginalT,Counted,3,.5f,Regions,&Values)) return false;
        const int32 FirstQueries=Queries; Queries=0;
        if (!Memoized.BuildAdaptive(OriginalXY,OriginalT,Counted,3,.5f,Regions,&Values)) return false;
        TestEqual(TEXT("unchanged analytic coordinates require no repeat profile evaluations"),Queries,0);
        // A moving wet-boundary point changes geometry, but not the analytic
        // values at every other exact world coordinate. Compare a fresh build.
        auto ShiftedXY=OriginalXY;
        ShiftedXY[(N/2)*N+N/2]+=FVector2D(.137,-.291);
        Queries=0;
        if (!Memoized.BuildAdaptive(ShiftedXY,OriginalT,Counted,3,.5f,Regions,&Values) ||
            !Bounded.BuildAdaptive(ShiftedXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f,Regions)) return false;
        TestTrue(TEXT("changed geometry reuses only exact unchanged profile coordinates"),Queries>0 && Queries<FirstQueries);
        TestTrue(TEXT("memoized moving geometry is identical to fresh selection"),
            Memoized.MidpointParents==Bounded.MidpointParents && Memoized.Triangles==Bounded.Triangles && Memoized.TriangleOrigins==Bounded.TriangleOrigins);
        if (!Parallel.BuildAdaptive(ShiftedXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f,Regions,nullptr,true)) return false;
        TestTrue(TEXT("parallel moved-coordinate selection equals a fresh serial build"),
            Bounded.MidpointParents==Parallel.MidpointParents && Bounded.Triangles==Parallel.Triangles && Bounded.TriangleOrigins==Parallel.TriangleOrigins);
        if (!BatchMemo.BuildAdaptive(ShiftedXY,OriginalT,Input.HeightAtWorldXYCm,3,.5f,Regions,nullptr,true,true)) return false;
        TestTrue(TEXT("batch-local memoization never reuses a stale moved-coordinate sample"),
            Bounded.MidpointParents==BatchMemo.MidpointParents && Bounded.Triangles==BatchMemo.Triangles && Bounded.TriangleOrigins==BatchMemo.TriangleOrigins);
        TestTrue(TEXT("refinement adds vertices to this real oblique crest"),Mesh->GetActiveVertexCount()>Original.Num());
        TestTrue(TEXT("fine water preserves original wet area including the island"),FMath::Abs(Area(V,T)-Area(Original,OriginalTriangles))<1.e-5);
        const auto& Offsets=Mesh->GetCellOffsets();
        double MaxError=0,MaxAnchor=0; int32 Samples=0;
        for (int32 Y=0; Y<N-1; ++Y) for (int32 X=0; X<N-1; ++X)
        {
            const int32 Cell=Y*(N-1)+X, A=Y*N+X;
            for (int32 I=Offsets[Cell]; I<Offsets[Cell+1]; I+=3)
            {
                const auto& P=V[T[I]].Position; const auto& Q=V[T[I+1]].Position; const auto& R=V[T[I+2]].Position;
                const FVector Center=(P+Q+R)/3.; FVector Anchor;
                if (!RaftSimWaterShoreline::Sample(FVector2D(Center.X,Center.Y),Offsets[Cell],Offsets[Cell+1],V,T,Anchor)) return false;
                MaxAnchor=FMath::Max(MaxAnchor,FVector::Distance(Anchor,Center));
                TestTrue(TEXT("refined face points upward in either geographic orientation"),FVector::CrossProduct(R-P,Q-P).Z>0);
                if (!Wet[A] || !Wet[A+1] || !Wet[A+N] || !Wet[A+N+1]) continue;
                // Independent sevenths, not the quarters used by selection.
                for (int32 U=0; U<=7; ++U) for (int32 W=0; W<=7-U; ++W)
                {
                    const FVector Point=P*(1.-(U+W)/7.)+Q*(U/7.)+R*(W/7.);
                    const double Expected=100.+Input.HeightAtWorldXYCm(FVector2D(Point.X,Point.Y));
                    MaxError=FMath::Max(MaxError,FMath::Abs(Point.Z-Expected)); ++Samples;
                }
            }
        }
        TestTrue(TEXT("shared fine crest meets unchanged two-centimeter target"),MaxError<=2.);
        TestTrue(TEXT("anchors sample actual fine triangles"),MaxAnchor<1.e-5);
        World->SendAllEndOfFrameUpdates(); FlushRenderingCommands(); auto* Proxy=Mesh->GetSceneProxy();
        const uint64 Builds=Mesh->GetCrestRefinement().GetBuildCount();
        Copy=Source; Input.BlendAlpha=.25f;
        if (!Mesh->SetClippedWaterMesh(N,N,MoveTemp(Copy),Wet,Available,H,Bed,&Input)) return false;
        World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
        TestTrue(TEXT("stable fine mesh preserves actual rendering proxy"),Proxy && Proxy==Mesh->GetSceneProxy());
        TestEqual(TEXT("exact unchanged profile reuses refinement"),Mesh->GetCrestRefinement().GetBuildCount(),Builds);
        AddInfo(FString::Printf(TEXT("Clipped fine crest sign=%g: samples=%d max_error_cm=%.9g source_vertices=%d active_vertices=%d triangles=%d anchor_error_cm=%.9g"),
            Sign,Samples,MaxError,N*N,Mesh->GetActiveVertexCount(),T.Num()/3,MaxAnchor));
        // A changed profile key must invalidate all analytic samples, even
        // though the world coordinates and shoreline are exactly unchanged.
        TAtomic<int32> ChangedQueries(0);
        Input.ProfileKey.Add(123.);
        Input.HeightAtWorldXYCm=[&](const FVector2D&) { ++ChangedQueries; return 0.f; };
        Input.BlendAlpha=1.f;
        Coarse.Init(0.f,N*N); Input.SourceCrestCm=Coarse;
        for (auto& P:Source) P.Position.Z=100.;
        Copy=Source;
        if (!Mesh->SetClippedWaterMesh(N,N,MoveTemp(Copy),Wet,Available,H,Bed,&Input)) return false;
        TestTrue(TEXT("changed profile recomputes analytic values"),ChangedQueries.Load()>0);
        TestEqual(TEXT("zero replacement profile retains no stale fine crest vertices"),Mesh->GetActiveVertexCount(),Original.Num());
        TestTrue(TEXT("zero replacement profile restores exact clipped triangles"),Mesh->GetWaterIndices()==OriginalTriangles);
    }
    return !HasAnyErrors();
}
#endif
