#if WITH_EDITOR
#include "AssetCompilingManager.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Engine/GameInstance.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "PhysicsEngine/BodySetup.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSurfaceActor.h"
#include "TimerManager.h"

namespace
{
TAutoConsoleVariable<int32> CTerrainSubdivision(TEXT("raftsim.TroublemakerTerrainSubdivision"), 3,
    TEXT("Transient bed-alignment review: 0 retains four-metre terrain; 3 refines the local patch to half-metre edges."));

// Only refine the rapid patch, including a zero-weight perimeter outside the
// bed feather. Midpoint vertices are shared across adjacent triangles. At the
// coarse/fine perimeter they retain the original linear edge, so a T junction
// does not open a height crack. The rest of the four-kilometre tile is untouched.
int32 RefineRapidTerrain(FMeshDescription& Mesh, int32 Passes)
{
    FStaticMeshAttributes A(Mesh);
    auto UVs = A.GetVertexInstanceUVs();
    auto Positions = A.GetVertexPositions();
    auto Colors = A.GetVertexInstanceColors();
    auto Normals = A.GetVertexInstanceNormals();
    auto Tangents = A.GetVertexInstanceTangents();
    auto Signs = A.GetVertexInstanceBinormalSigns();
    TArray<FTriangleID> Selected;
    for (FTriangleID Triangle : Mesh.Triangles().GetElementIDs())
    {
        FVector2f Minimum(FLT_MAX, FLT_MAX), Maximum(-FLT_MAX, -FLT_MAX);
        for (FVertexInstanceID VI : Mesh.GetTriangleVertexInstances(Triangle))
        {
            const FVector2f UV = UVs.Get(VI, 0);
            const FVector2f SL(8064.0f + UV.Y * 4032.0f, -256.0f + UV.X * 512.0f);
            Minimum.X = FMath::Min(Minimum.X, SL.X); Minimum.Y = FMath::Min(Minimum.Y, SL.Y);
            Maximum.X = FMath::Max(Maximum.X, SL.X); Maximum.Y = FMath::Max(Maximum.Y, SL.Y);
        }
        if (Maximum.X >= 8244 && Minimum.X <= 8476 && Maximum.Y >= -44 && Minimum.Y <= 44)
            Selected.Add(Triangle);
    }
    const int32 InitialCount = Selected.Num();
    for (int32 Pass = 0; Pass < Passes; ++Pass)
    {
        TMap<FIntPoint, FVertexID> EdgeVertices;
        TArray<FTriangleID> Children;
        Children.Reserve(Selected.Num() * 4);
        for (FTriangleID Triangle : Selected)
        {
            const auto Corners = Mesh.GetTriangleVertexInstances(Triangle);
            const FVertexInstanceID V0 = Corners[0], V1 = Corners[1], V2 = Corners[2];
            const FPolygonGroupID Group = Mesh.GetTrianglePolygonGroup(Triangle);
            const auto Midpoint = [&](FVertexInstanceID Left, FVertexInstanceID Right)
            {
                const FVertexID L = Mesh.GetVertexInstanceVertex(Left), R = Mesh.GetVertexInstanceVertex(Right);
                const FIntPoint Key(FMath::Min(L.GetValue(), R.GetValue()), FMath::Max(L.GetValue(), R.GetValue()));
                FVertexID Vertex;
                if (const FVertexID* Existing = EdgeVertices.Find(Key)) Vertex = *Existing;
                else
                {
                    const FVector3f Position = (Positions[L] + Positions[R]) * 0.5f;
                    Vertex = Mesh.CreateVertex(); Positions[Vertex] = Position;
                    EdgeVertices.Add(Key, Vertex);
                }
                const FVertexInstanceID VI = Mesh.CreateVertexInstance(Vertex);
                for (int32 Channel = 0; Channel < UVs.GetNumChannels(); ++Channel)
                    UVs.Set(VI, Channel, (UVs.Get(Left, Channel) + UVs.Get(Right, Channel)) * 0.5f);
                Colors[VI] = (Colors[Left] + Colors[Right]) * 0.5f;
                Normals[VI] = (Normals[Left] + Normals[Right]).GetSafeNormal();
                Tangents[VI] = (Tangents[Left] + Tangents[Right]).GetSafeNormal();
                Signs[VI] = Signs[Left];
                return VI;
            };
            const FVertexInstanceID M01 = Midpoint(V0, V1), M12 = Midpoint(V1, V2), M20 = Midpoint(V2, V0);
            const auto Add = [&](FVertexInstanceID X, FVertexInstanceID Y, FVertexInstanceID Z)
            {
                const FVertexInstanceID IDs[] = {X, Y, Z};
                Children.Add(Mesh.CreateTriangle(Group, MakeArrayView(IDs)));
            };
            Add(V0, M01, M20); Add(M01, V1, M12); Add(M20, M12, V2); Add(M01, M12, M20);
            Mesh.DeleteTriangle(Triangle);
        }
        Selected = MoveTemp(Children);
    }
    UE_LOG(LogTemp, Display, TEXT("Troublemaker terrain refinement: passes=%d source_triangles=%d refined_triangles=%d"),
        Passes, InitialCount, Selected.Num());
    // Static-mesh tangent generation addresses triangle corners densely.
    // Deleting parent faces leaves sparse IDs until explicitly compacted.
    FElementIDRemappings Remappings;
    Mesh.Compact(Remappings);
    return Selected.Num();
}

// Evidence-only repair of the mismatch between the old four-metre scenery
// bed and the new interpreted rapid bed. Duplicate the loaded mesh into the
// transient package: neither source assets nor the map are saved/modified.
void ApplyTroublemakerTerrainReview(UWorld* World)
{
    if (!World || !World->IsGameWorld() ||
        !World->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"))) return;
    const UGameInstance* Game = World->GetGameInstance();
    auto* Bridge = Game ? Game->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    auto* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (!Water || !Water->HasRiverCoordinateMap()) return;
    int32 ChangedMeshes = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("RaftSimFullReachTerrain"))) continue;
        UStaticMeshComponent* Component = It->GetStaticMeshComponent();
        UStaticMesh* Original = Component ? Component->GetStaticMesh() : nullptr;
        if (!Original || Original->GetName() != TEXT("SM_south_fork_02_Terrain")) continue;
        const FMeshDescription* Source = Original->GetMeshDescription(0);
        if (!Source) { UE_LOG(LogTemp, Error, TEXT("Troublemaker terrain review: missing mesh description")); continue; }
        FMeshDescription Description = *Source;
        RefineRapidTerrain(Description, FMath::Clamp(CTerrainSubdivision.GetValueOnGameThread(), 0, 3));
        FStaticMeshAttributes Attributes(Description);
        auto Positions = Attributes.GetVertexPositions();
        const FTransform Transform = Component->GetComponentTransform();
        int32 Changed = 0;
        double MaxDeltaM = 0;
        for (const FVertexID Vertex : Description.Vertices().GetElementIDs())
        {
            FVector Position = Transform.TransformPosition(FVector(Positions[Vertex]));
            // Preserve the authored station/lateral identity. Nearest-axis
            // projection is not an inverse on wide bank tiles around bends:
            // (8472,84) was misidentified as (8332,-14), proposing a 7.5 m
            // excavation of unrelated dry ground. The source UVs retain the
            // exact tile row/column even where projected cross-sections fold.
            const auto Instances = Description.GetVertexVertexInstanceIDs(Vertex);
            if (Instances.IsEmpty()) continue;
            const FVector2f UV = Attributes.GetVertexInstanceUVs().Get(Instances[0], 0);
            const FVector2D River(8064.0 + UV.Y * 4032.0, -256.0 + UV.X * 512.0);
            // Match the entire active bed, including both wet and dry banks,
            // then feather to unchanged scenery outside the rapid. This is
            // not an added lip following the instantaneous waterline.
            const float Along = FMath::SmoothStep(8250.0f, 8280.0f, float(River.X)) *
                (1.0f - FMath::SmoothStep(8440.0f, 8470.0f, float(River.X)));
            const float Across = 1.0f - FMath::SmoothStep(30.0f, 39.0f, FMath::Abs(float(River.Y)));
            const float Weight = Along * Across;
            if (Weight <= 0.0f) continue;
            FRaftSimWaterSample Sample;
            if (!Water->SampleWaterFieldAtRiverCoordinates(River, Sample) ||
                !FMath::IsFinite(Sample.BedHeightMeters)) continue;
            const double DeltaM = (Sample.BedHeightMeters - Position.Z / 100.0) * Weight;
            if (FMath::Abs(DeltaM) < 0.001) continue;
            // Reject a datum/coordinate error instead of burying the scene.
            if (FMath::Abs(DeltaM) > 5.0)
            {
                UE_LOG(LogTemp, Error, TEXT("Troublemaker terrain review rejected: s=%.3f l=%.3f terrain_z=%.3f bed_z=%.3f weight=%.3f delta_m=%.3f"),
                    River.X, River.Y, Position.Z / 100.0, Sample.BedHeightMeters, Weight, DeltaM);
                return;
            }
            Position.Z += DeltaM * 100.0;
            Positions[Vertex] = FVector3f(Transform.InverseTransformPosition(Position));
            MaxDeltaM = FMath::Max(MaxDeltaM, FMath::Abs(DeltaM));
            ++Changed;
        }
        if (!Changed) continue;
        UStaticMesh* Candidate = DuplicateObject<UStaticMesh>(Original, GetTransientPackage());
        Candidate->ClearFlags(RF_Public | RF_Standalone);
        Candidate->SetFlags(RF_Transient);
        Candidate->CreateMeshDescription(0, MoveTemp(Description));
        Candidate->CommitMeshDescription(0);
        Candidate->GetSourceModel(0).BuildSettings.bRecomputeNormals = true;
        Candidate->GetSourceModel(0).BuildSettings.bRecomputeTangents = true;
        Candidate->Build(false);
        FAssetCompilingManager::Get().FinishAllCompilation();
        if (UBodySetup* Body = Candidate->GetBodySetup())
        {
            Body->InvalidatePhysicsData();
            Body->CreatePhysicsMeshes();
        }
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetStaticMesh(Candidate);
        Component->SetMobility(EComponentMobility::Static);
        UE_LOG(LogTemp, Display,
            TEXT("Troublemaker terrain review: actor=%s changed_vertices=%d max_delta_m=%.3f transient=1 saved=0"),
            *It->GetName(), Changed, MaxDeltaM);
        ++ChangedMeshes;
    }
    if (ChangedMeshes > 0)
    {
        for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
            It->InvalidateTerrainProbes();
    }
    UE_LOG(LogTemp, Display, TEXT("Troublemaker terrain review complete: meshes=%d"), ChangedMeshes);
}

FAutoConsoleCommandWithWorld GTroublemakerTerrainReview(
    TEXT("RaftSim.ReviewTroublemakerTerrain"),
    TEXT("Transient Troublemaker terrain/solver-bed alignment experiment after three seconds. No assets saved. Not a performance test."),
    FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
    {
        if (!World) return;
        const TWeakObjectPtr<UWorld> WeakWorld(World);
        FTimerHandle Timer;
        World->GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateLambda([WeakWorld]()
        {
            if (WeakWorld.IsValid()) ApplyTroublemakerTerrainReview(WeakWorld.Get());
        }), 3.0f, false);
    }));
}
#endif
