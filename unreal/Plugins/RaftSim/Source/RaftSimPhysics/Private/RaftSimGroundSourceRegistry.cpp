#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTriangleSweep.h"
#include <limits>
#include "CollisionQueryParams.h"
#include "ProfilingDebugging/CsvProfiler.h"

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
    TConstArrayView<FIntVector> Faces,double SkinCm,double ProvenClearanceCm)
{
    CSV_SCOPED_TIMING_STAT(RaftSimGround,SurfaceSweep);
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
            UE_LOG(LogTemp,Display,TEXT("Captured surface sweep source: component=%s triangles=%d ready=%d build_ms=%.3f"),
                *Mesh->GetPathName(),Cache->TriangleCount(),int32(Built),(FPlatformTime::Seconds()-Started)*1000.);
        }
        auto Hit=Cache->SweepSurface(StartCm,EndCm,Faces,SkinCm,ProvenClearanceCm);Hit.GroundComponent=Mesh;
        Pairs+=Hit.TrianglePairs;
        if(Hit.Status==EStatus::Invalid || Hit.Status==EStatus::Unresolved || Hit.Status==EStatus::InitialIntersection)
        {Hit.TrianglePairs=Pairs;return Hit;}
        if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
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
        return true;
    }
    return false;
}
