#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTriangleSweep.h"
#include "RaftSimHullArcPair.h"
#include "RaftSimFaceOrdering.h"
#include "LandscapeHeightfieldCollisionComponent.h"
#include "Chaos/HeightField.h"
#include <limits>
#include "CollisionQueryParams.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

CSV_DEFINE_CATEGORY(RaftSimGround,true);

bool FRaftSimGroundSourceRegistry::SweepCapturedSphere(const FVector& StartCm,
    const FVector& EndCm,double RadiusCm,FHitResult& OutHit)
{
    CSV_SCOPED_TIMING_STAT(RaftSimGround,Sweep);
    RefreshIfDirty();
    FBox SweptBounds(ForceInit);SweptBounds+=StartCm;SweptBounds+=EndCm;
    SweptBounds=SweptBounds.ExpandBy(RadiusCm);
    bool Found=false;
    for(const auto& WeakMesh:Meshes)
    {
        auto* Mesh=WeakMesh.Get();
        if(!Mesh || !Mesh->IsQueryCollisionEnabled() || !SweptBounds.Intersect(Mesh->Bounds.GetBox()))continue;
        auto& Cache=TriangleCaches.FindOrAdd(WeakMesh);
        if(!Cache || !Cache->Matches(Mesh))
        {
            Cache=MakeShared<FRaftSimTriangleSweepMesh>();
            const double Started=FPlatformTime::Seconds();
            const bool Built=Cache->Build(Mesh);
            UE_LOG(LogTemp,Display,TEXT("Captured triangle sweep source: component=%s triangles=%d ready=%d build_ms=%.3f"),
                *Mesh->GetPathName(),Cache->TriangleCount(),int32(Built),(FPlatformTime::Seconds()-Started)*1000.);
        }
        if(!Cache->IsValid())
        {
            // Missing collision-source data is not permission to pass through
            // terrain or silently fall back to the unreliable sweep.
            OutHit=FHitResult();OutHit.Time=std::numeric_limits<float>::quiet_NaN();
            OutHit.Normal=FVector::UpVector;return true;
        }
        FHitResult Hit;
        if(!Cache->Sweep(StartCm,EndCm,RadiusCm,Hit))continue;
        Hit.Component=Mesh;
        if(!Found || (Hit.bStartPenetrating && !OutHit.bStartPenetrating) ||
            (Hit.bStartPenetrating==OutHit.bStartPenetrating &&
             (Hit.bStartPenetrating?Hit.PenetrationDepth>OutHit.PenetrationDepth:Hit.Time<OutHit.Time)))
        {OutHit=Hit;Found=true;}
    }
    return Found;
}

RaftSimSurfaceSweep::FResult FRaftSimGroundSourceRegistry::SweepCapturedSurface(
    TConstArrayView<FVector> StartCm,TConstArrayView<FVector> EndCm,
    TConstArrayView<FIntVector> Faces,double SkinCm,double ProvenClearanceCm,bool bGroupedBroadPhase,const FRaftSimHullArcPath* Arc)
{
    CSV_SCOPED_TIMING_STAT(RaftSimGround,SurfaceSweep);
    CSV_CUSTOM_STAT(RaftSimGround,LandscapeGroundTriangles,0,ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimGround,LandscapeFaceRefitCalls,0,ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimGround,LandscapeRadixOrderQueries,0,ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimGround,LandscapeReferenceOrderQueries,0,ECsvCustomStatOp::Accumulate);
    using namespace RaftSimSurfaceSweep;
    FResult Best;
    if(StartCm.IsEmpty() || StartCm.Num()!=EndCm.Num() || Faces.IsEmpty() ||
        !FMath::IsFinite(SkinCm) || SkinCm<=1.e-8 || !FMath::IsFinite(ProvenClearanceCm) || ProvenClearanceCm>=SkinCm)return Best;
    FBox Bounds(ForceInit);
    for(int32 I=0;I<StartCm.Num();++I)
    {
        if(StartCm[I].ContainsNaN() || EndCm[I].ContainsNaN())return Best;
        Bounds+=StartCm[I];Bounds+=EndCm[I];
    }
    for(const auto& F:Faces)
        if(!StartCm.IsValidIndex(F.X) || !StartCm.IsValidIndex(F.Y) || !StartCm.IsValidIndex(F.Z))return Best;
    Bounds=Bounds.ExpandBy(SkinCm+1.e-8);
    RefreshIfDirty();Best.Status=EStatus::Clear;Best.Time=1.;uint64 Pairs=0;
    for(const auto& WeakMesh:Meshes)
    {
        auto* Mesh=WeakMesh.Get();
        if(!Mesh || !Mesh->IsQueryCollisionEnabled() || !Bounds.Intersect(Mesh->Bounds.GetBox()))continue;
        auto& Cache=TriangleCaches.FindOrAdd(WeakMesh);
        if(!Cache || !Cache->Matches(Mesh))
        {
            Cache=MakeShared<FRaftSimTriangleSweepMesh>();
            const double Started=FPlatformTime::Seconds();const bool Built=Cache->Build(Mesh);
            UE_LOG(LogTemp,Display,TEXT("Captured surface sweep source: component=%s triangles=%d closed_components=%d ready=%d build_ms=%.3f"),
                *Mesh->GetPathName(),Cache->TriangleCount(),Cache->ClosedSourceCount(),int32(Built),(FPlatformTime::Seconds()-Started)*1000.);
        }
        auto Hit=Cache->SweepSurface(StartCm,EndCm,Faces,SkinCm,ProvenClearanceCm,bGroupedBroadPhase,Arc);Hit.GroundComponent=Mesh;
        Pairs+=Hit.TrianglePairs;
        if(Hit.Status==EStatus::Invalid || Hit.Status==EStatus::Unresolved || Hit.Status==EStatus::InitialIntersection)
        {Hit.TrianglePairs=Pairs;return Hit;}
        if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
    }
    // Visit the actual Complex Chaos heightfield triangles (including its
    // holes and native diagonal), not a fitted bed or sampled support spheres.
    // The retained tree caches only connectivity; a query containing actual
    // terrain triangles refits every original face's endpoint bounds. Empty
    // Chaos heightfield queries must not pay for a 38344-face refit. The
    // reference switch/audit is for
    // same-input qualification, never a different collision model.
    static const bool ExhaustiveLandscape=FParse::Param(FCommandLine::Get(),TEXT("RaftSimExhaustiveLandscapeFaces"));
    static const bool AuditLandscapeTree=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLandscapeFaceTreeAudit"));
    // Exact signed ordering passed same-input original-asset controls and
    // repeated native full routes in both execution orders. No face, bound,
    // narrow-phase or contact tie changes. Original Sort is diagnostic-only.
    static const bool RadixLandscapeOrder=RaftSimFaceOrdering::UsesRadixLandscapeOrder(FCommandLine::Get());
    const bool UseLandscapeTree=bGroupedBroadPhase && !ExhaustiveLandscape;
    bool LandscapeTreeReady=false;
    RaftSimHullArcPair::FQueryDerivatives LandscapeArcDerivatives(Arc);
    TArray<int32> LandscapeCandidates;
    TArray<int32> LandscapeOrderingScratch;
    for(const auto& WeakLandscape:Landscapes)
    {
        auto* Landscape=WeakLandscape.Get();if(!Landscape)continue;
        TInlineComponentArray<ULandscapeHeightfieldCollisionComponent*> Components(Landscape);
        for(auto* Component:Components)
        {
            if(!Component || !Component->IsQueryCollisionEnabled() || !Bounds.Intersect(Component->Bounds.GetBox()))continue;
            if(!Component->HeightfieldRef || !Component->HeightfieldRef->HeightfieldGeometry){Best.Status=EStatus::Invalid;return Best;}
            const FTransform Rigid(Component->GetComponentQuat(),Component->GetComponentLocation());
            FBox LocalBounds(ForceInit);
            for(int32 I=0;I<8;++I)LocalBounds+=Rigid.InverseTransformPosition(FVector(
                I&1?Bounds.Max.X:Bounds.Min.X,I&2?Bounds.Max.Y:Bounds.Min.Y,I&4?Bounds.Max.Z:Bounds.Min.Z));
            const Chaos::FAABB3 Query(LocalBounds.Min,LocalBounds.Max);
            Component->HeightfieldRef->HeightfieldGeometry->VisitTriangles(Query,Chaos::FRigidTransform3::Identity,
                [&](const Chaos::FTriangle& T,int32 GroundFace,int32,int32,int32)
                {
                    if(Best.Status!=EStatus::Clear && Best.Status!=EStatus::Contact)return;
                    CSV_CUSTOM_STAT(RaftSimGround,LandscapeGroundTriangles,1,ECsvCustomStatOp::Accumulate);
                    if(UseLandscapeTree && !LandscapeTreeReady)
                    {
                        CSV_SCOPED_TIMING_STAT(RaftSimGround,LandscapeFaceRefit);
                        CSV_CUSTOM_STAT(RaftSimGround,LandscapeFaceRefitCalls,1,ECsvCustomStatOp::Accumulate);
                        // The old per-candidate loop converted each vertex
                        // again for every incident face and ground triangle.
                        // Refresh the SAME multiplication once per original
                        // vertex on this query, only after actual ground exists.
                        LandscapeStartMeters.SetNumUninitialized(StartCm.Num());
                        LandscapeEndMeters.SetNumUninitialized(EndCm.Num());
                        for(int32 I=0;I<StartCm.Num();++I)
                        {
                            LandscapeStartMeters[I]=StartCm[I]*.01;
                            LandscapeEndMeters[I]=EndCm[I]*.01;
                        }
                        if(!LandscapeMovingFaces.Refit(LandscapeStartMeters,LandscapeEndMeters,Faces,SkinCm*.01,true))
                        {Best.Status=EStatus::Invalid;return;}
                        LandscapeTreeReady=true;
                    }
                    FTriangle Ground;FBox GroundBounds(ForceInit);
                    for(int32 J=0;J<3;++J){Ground.V[J]=Rigid.TransformPosition(FVector(T[J]))*.01;GroundBounds+=Ground.V[J];}
                    if(UseLandscapeTree)
                    {
                        CSV_SCOPED_TIMING_STAT(RaftSimGround,LandscapeFaceQuery);
                        {
                            CSV_SCOPED_TIMING_STAT(RaftSimGround,LandscapeFaceTraversal);
                            LandscapeMovingFaces.GatherCandidates(GroundBounds,LandscapeCandidates);
                        }
                        {
                            CSV_SCOPED_TIMING_STAT(RaftSimGround,LandscapeFaceOrdering);
                            if(RadixLandscapeOrder)RaftSimFaceOrdering::Radix(LandscapeCandidates,LandscapeOrderingScratch);
                            else LandscapeCandidates.Sort();
                        }
                        CSV_CUSTOM_STAT(RaftSimGround,LandscapeRadixOrderQueries,int32(RadixLandscapeOrder),ECsvCustomStatOp::Accumulate);
                        CSV_CUSTOM_STAT(RaftSimGround,LandscapeReferenceOrderQueries,int32(!RadixLandscapeOrder),ECsvCustomStatOp::Accumulate);
                        if(AuditLandscapeTree)
                        {
                            TArray<int32> Reference;
                            for(int32 I=0;I<Faces.Num();++I)
                            {
                                FBox FaceBox(ForceInit);
                                for(int32 J=0;J<3;++J){FaceBox+=StartCm[Faces[I][J]]*.01;FaceBox+=EndCm[Faces[I][J]]*.01;}
                                if(FaceBox.ExpandBy(SkinCm*.01).Intersect(GroundBounds))Reference.Add(I);
                            }
                            if(Reference!=LandscapeCandidates)
                            {
                                UE_LOG(LogTemp,Error,TEXT("Landscape original-face tree differs from exhaustive endpoint bounds"));
                                Best.Status=EStatus::Invalid;return;
                            }
                        }
                    }
                    const int32 CandidateCount=UseLandscapeTree?LandscapeCandidates.Num():Faces.Num();
                    CSV_CUSTOM_STAT(RaftSimGround,LandscapeOriginalFaces,Faces.Num(),ECsvCustomStatOp::Accumulate);
                    CSV_CUSTOM_STAT(RaftSimGround,LandscapeCandidateFaces,CandidateCount,ECsvCustomStatOp::Accumulate);
                    for(int32 Candidate=0;Candidate<CandidateCount;++Candidate)
                    {
                        const int32 I=UseLandscapeTree?LandscapeCandidates[Candidate]:Candidate;
                        FTriangle A,B;FBox FaceBounds(ForceInit);
                        if(UseLandscapeTree)
                        {
                            // Candidates already performed this exact expanded
                            // six-endpoint AABB test, in original face order.
                            // Do not reconstruct and retest the same enclosure.
                            for(int32 J=0;J<3;++J)
                            {A.V[J]=LandscapeStartMeters[Faces[I][J]];B.V[J]=LandscapeEndMeters[Faces[I][J]];}
                        }
                        else
                        {
                            for(int32 J=0;J<3;++J){A.V[J]=StartCm[Faces[I][J]]*.01;B.V[J]=EndCm[Faces[I][J]]*.01;FaceBounds+=A.V[J];FaceBounds+=B.V[J];}
                            if(!FaceBounds.ExpandBy(SkinCm*.01).Intersect(GroundBounds))continue;
                        }
                        ++Pairs;
                        if(Arc && (UseLandscapeTree
                            ? RaftSimHullArcPair::Separated(Faces[I],A,Ground,*Arc,LandscapeArcDerivatives)
                            : RaftSimHullArcPair::Separated(Faces[I],A,Ground,*Arc)))continue;
                        auto Hit=RaftSimSurfaceSweep::Sweep(A,B,Ground,SkinCm*.01,128,ProvenClearanceCm*.01);
                        Hit.MovingFace=I;Hit.GroundFace=GroundFace;RaftSimHullArcPair::GroundFeature(Hit,Ground);
                        if(Hit.Status!=EStatus::Clear && Hit.Status!=EStatus::Contact){Best=Hit;return;}
                        if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
                    }
                });
            if(Best.Status!=EStatus::Clear && Best.Status!=EStatus::Contact){Best.TrianglePairs=Pairs;return Best;}
        }
    }
    Best.TrianglePairs=Pairs;return Best;
}

bool FRaftSimGroundSourceRegistry::SampleGround(const FVector& WorldPositionCm,
    double& OutGroundZCm, FVector& OutGroundNormal,FHitResult* OutCapturedHit)
{
    CSV_SCOPED_TIMING_STAT(RaftSimGround,Sample);
    OutGroundZCm=0.; OutGroundNormal=FVector::UpVector;
    if(OutCapturedHit)*OutCapturedHit=FHitResult();
    if (WorldPositionCm.ContainsNaN()) return false;
    RefreshIfDirty();
    // The survey mesh and hydraulic bed share a source, but a
    // coarser hydraulic raster cannot resolve every exposed rock.
    // Query the full collision triangles at the requested XY;
    // use component bounds, not raft height, even after a fall.
    TOptional<double> CapturedGroundZCm;
    FVector CapturedNormal = FVector::UpVector;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimCapturedGround), true);
    Params.bReturnFaceIndex=OutCapturedHit!=nullptr;
    for (const TWeakObjectPtr<UStaticMeshComponent>& WeakMesh : Meshes)
    {
        UStaticMeshComponent* Mesh = WeakMesh.Get();
        if (!Mesh || !Mesh->IsQueryCollisionEnabled()) continue;
        const FBox Bounds = Mesh->Bounds.GetBox();
        if (WorldPositionCm.X < Bounds.Min.X || WorldPositionCm.X > Bounds.Max.X ||
            WorldPositionCm.Y < Bounds.Min.Y || WorldPositionCm.Y > Bounds.Max.Y) continue;
        FHitResult Hit;
        if (Mesh->LineTraceComponent(Hit,
                FVector(WorldPositionCm.X, WorldPositionCm.Y, Bounds.Max.Z + 100.0),
                FVector(WorldPositionCm.X, WorldPositionCm.Y, Bounds.Min.Z - 100.0), Params) &&
            (!CapturedGroundZCm.IsSet() || Hit.ImpactPoint.Z > CapturedGroundZCm.GetValue()))
        {
            // Component traces report geometric intersections;
            // Chaos uses an overlap-all filter and need not set
            // bBlockingHit as a world-channel trace would.
            CapturedGroundZCm = Hit.ImpactPoint.Z;
            CapturedNormal = Hit.ImpactNormal.GetSafeNormal();
            if(OutCapturedHit)*OutCapturedHit=Hit;
        }
    }
    if (CapturedGroundZCm.IsSet())
    {
        OutGroundZCm = CapturedGroundZCm.GetValue();
        OutGroundNormal = CapturedNormal.Z > 0.05 ? CapturedNormal : FVector::UpVector;
        return true;
    }
    const ALandscapeProxy* HighestLandscape = nullptr;
    TOptional<float> HighestLandscapeZCm;
    for (const TWeakObjectPtr<ALandscapeProxy>& WeakLandscape :
         Landscapes)
    {
        const ALandscapeProxy* Landscape = WeakLandscape.Get();
        if (Landscape == nullptr)
        {
            continue;
        }
        const TOptional<float> Height =
            Landscape->GetHeightAtLocation(
                WorldPositionCm, EHeightfieldSource::Complex);
        if (Height.IsSet() &&
            (!HighestLandscapeZCm.IsSet() ||
             Height.GetValue() > HighestLandscapeZCm.GetValue()))
        {
            HighestLandscape = Landscape;
            HighestLandscapeZCm = Height;
        }
    }

    if (HighestLandscape != nullptr && HighestLandscapeZCm.IsSet())
    {
        OutGroundZCm = HighestLandscapeZCm.GetValue();
        constexpr float NormalProbeOffsetCm = 50.0f;
        const TOptional<float> HeightX =
            HighestLandscape->GetHeightAtLocation(
                WorldPositionCm +
                    FVector(NormalProbeOffsetCm, 0.0f, 0.0f),
                EHeightfieldSource::Complex);
        const TOptional<float> HeightY =
            HighestLandscape->GetHeightAtLocation(
                WorldPositionCm +
                    FVector(0.0f, NormalProbeOffsetCm, 0.0f),
                EHeightfieldSource::Complex);
        OutGroundNormal = FVector::UpVector;
        if (HeightX.IsSet() && HeightY.IsSet())
        {
            OutGroundNormal = FVector(
                -(HeightX.GetValue() - OutGroundZCm) /
                    NormalProbeOffsetCm,
                -(HeightY.GetValue() - OutGroundZCm) /
                    NormalProbeOffsetCm,
                1.0f).GetSafeNormal();
        }
        // Identify the actual Complex heightfield that supplied this sample.
        // This is provenance, not a fabricated blocking trace or new collider;
        // terrain height, normal and all contact behavior stay unchanged.
        if(OutCapturedHit)
            *OutCapturedHit=FHitResult(const_cast<ALandscapeProxy*>(HighestLandscape),nullptr,
                FVector(WorldPositionCm.X,WorldPositionCm.Y,OutGroundZCm),OutGroundNormal);
        return true;
    }
    return false;
}
