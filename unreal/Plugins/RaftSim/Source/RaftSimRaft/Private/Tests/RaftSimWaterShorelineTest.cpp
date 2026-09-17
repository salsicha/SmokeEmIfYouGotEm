#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterSourcePacking.h"
#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimTerrainProbeSources.h"
#include "RaftSimCapturedGroundRendering.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRiverWaterConfig.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RenderingThread.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCapturedGroundRenderingTest,"RaftSim.M4.ShorelineCapturedGroundRendering",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCapturedGroundRenderingTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Actor=World->SpawnActor<AStaticMeshActor>();
    if (!Actor) return false;
    auto* Component=Actor->GetStaticMeshComponent();
    auto* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.SM_TroublemakerCapturedGround"));
    if (!TestNotNull(TEXT("captured full-resolution source asset"),Mesh)) return false;
    Component->SetStaticMesh(Mesh);
    TestFalse(TEXT("unmarked source is unchanged"),RaftSimCapturedGroundRendering::Apply(Component));
    Actor->Tags.Add(TEXT("RaftSimPhysicalGround"));
    TestFalse(TEXT("source outside reconstructed scenario is unchanged"),RaftSimCapturedGroundRendering::Apply(Component));
    Actor->Tags.Add(TEXT("RaftSimSouthForkReconstruction20260912"));
    TestTrue(TEXT("exact captured fallback is selected"),RaftSimCapturedGroundRendering::Apply(Component));
    TestTrue(TEXT("only component rendering changes"),Component->IsDisallowNanite() && Component->GetStaticMesh()==Mesh);
    TestFalse(TEXT("repeated streaming pass is idempotent"),RaftSimCapturedGroundRendering::Apply(Component));
    Component->bDisallowNanite=false;
    Component->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    TestFalse(TEXT("unrelated tagged mesh keeps its rendering path"),RaftSimCapturedGroundRendering::Apply(Component));
    TestFalse(TEXT("unrelated mesh retains Nanite permission"),Component->IsDisallowNanite());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineTerrainProbeTest,"RaftSim.M4.ShorelineTerrainProbe",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineTerrainProbeTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Ground=World->SpawnActor<AStaticMeshActor>();
    auto* Blocker=World->SpawnActor<AStaticMeshActor>();
    if (!TestNotNull(TEXT("ground fixture"),Ground) || !TestNotNull(TEXT("blocker fixture"),Blocker) || !Cube) return false;
    for (auto* Actor : {Ground,Blocker})
    {
        auto* Mesh=Actor->GetStaticMeshComponent();
        Mesh->SetMobility(EComponentMobility::Movable);
        Mesh->SetStaticMesh(Cube);
        Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Mesh->SetCollisionResponseToAllChannels(ECR_Block);
    }
    Ground->SetActorLocation(FVector::ZeroVector);
    Blocker->SetActorLocation(FVector(0,0,200));
    const FVector Start(0,0,500),End(0,0,-500);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimTerrainProbeTest),true);
    FHitResult Hit;
    if (!TestTrue(TEXT("independent world trace reaches unrelated foreground blocker"),
        World->LineTraceSingleByChannel(Hit,Start,End,ECC_WorldStatic,Params) && Hit.GetActor()==Blocker)) return false;
    const auto CheckGround=[&](const TCHAR* Label)
    {
        int32 Budget=2;
        const bool Found=ARaftSimWaterSurfaceActor::TraceTerrainSurface(World,Start,End,Params,Budget,Hit);
        TestTrue(Label,Found && Hit.GetComponent()==Ground->GetStaticMeshComponent());
        TestEqual(TEXT("every attempted ray including skipped blocker consumes budget"),Budget,0);
        if (Found) TestTrue(TEXT("ground top is the actual collision surface"),FMath::Abs(Hit.ImpactPoint.Z-50.)<.001);
    };
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));
    TestTrue(TEXT("streaming arrival recognizes rebuilt actor source"),RaftSimTerrainProbeSources::ActorHasSource(Ground));
    CheckGround(TEXT("rebuilt actor-tagged physical ground is accepted"));
    Ground->Tags.Reset();
    Ground->GetStaticMeshComponent()->ComponentTags.Add(TEXT("RaftSimPhysicalGround"));
    TestTrue(TEXT("streaming arrival recognizes component source"),RaftSimTerrainProbeSources::ActorHasSource(Ground));
    CheckGround(TEXT("component-tagged physical ground is accepted"));
    Ground->GetStaticMeshComponent()->ComponentTags.Reset();
    Ground->Tags.Add(TEXT("RaftSimFullReachTerrain"));
    CheckGround(TEXT("legacy full-reach ground remains accepted"));
    int32 Budget=1;
    TestFalse(TEXT("one-ray budget cannot pass the foreground blocker"),
        ARaftSimWaterSurfaceActor::TraceTerrainSurface(World,Start,End,Params,Budget,Hit));
    TestEqual(TEXT("exhausted budget stays zero"),Budget,0);
    TestFalse(TEXT("zero budget performs no trace"),
        ARaftSimWaterSurfaceActor::TraceTerrainSurface(World,Start,End,Params,Budget,Hit));
    Ground->Tags.Reset(); Budget=4;
    TestFalse(TEXT("unmarked scenery is not physical ground"),
        ARaftSimWaterSurfaceActor::TraceTerrainSurface(World,Start,End,Params,Budget,Hit));
    TestFalse(TEXT("unmarked actor cannot invalidate ground misses"),RaftSimTerrainProbeSources::ActorHasSource(Ground));
    Blocker->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    auto* Sibling=NewObject<UStaticMeshComponent>(Ground);
    Sibling->SetMobility(EComponentMobility::Movable);
    Sibling->SetStaticMesh(Cube);
    Sibling->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Sibling->SetCollisionResponseToAllChannels(ECR_Block);
    Sibling->RegisterComponent();
    Sibling->SetWorldLocation(FVector(0,0,200));
    Ground->GetStaticMeshComponent()->ComponentTags.Add(TEXT("RaftSimPhysicalGround"));
    CheckGround(TEXT("unmarked sibling does not hide a component-tagged ground source"));
    TestEqual(TEXT("caller ignore state is not mutated"),Params.GetIgnoredSourceObjects().Num(),0);
    TestEqual(TEXT("caller ignored components are not mutated"),Params.GetIgnoredComponents().Num(),0);
    return true;
}

namespace
{
TArray<FProcMeshVertex> Grid(int32 Nx, int32 Ny, double Angle=0., double Sign=1.)
{
    TArray<FProcMeshVertex> V; V.SetNum(Nx*Ny);
    for (int32 Y=0; Y<Ny; ++Y) for (int32 X=0; X<Nx; ++X)
    {
        auto& P=V[Y*Nx+X];
        P.Position=FVector(FMath::Cos(Angle)*X-FMath::Sin(Angle)*Y,
            Sign*(FMath::Sin(Angle)*X+FMath::Cos(Angle)*Y),1.);
        P.Normal=FVector::UpVector;
        P.Color=FColor(17,81,123,255);
        P.UV0=FVector2D(X,Y); P.UV1=FVector2D(-2,3); P.UV2=FVector2D(.2,.4);
    }
    return V;
}
double Area(const TArray<FProcMeshVertex>& V, const TArray<uint32>& T)
{
    double A=0.;
    for (int32 I=0; I<T.Num(); I+=3)
        A+=FMath::Abs(FVector::CrossProduct(V[T[I+1]].Position-V[T[I]].Position,
            V[T[I+2]].Position-V[T[I]].Position).Z)*.5;
    return A;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterSourcePackingTest,"RaftSim.M4.SurfaceSourcePacking",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterSourcePackingTest::RunTest(const FString&)
{
    constexpr int32 N=225*225;
    TArray<FVector> Positions,Normals; Positions.SetNum(N); Normals.SetNum(N);
    TArray<FLinearColor> Colors; Colors.SetNum(N);
    TArray<FVector2D> UVs,Flow,Wake; UVs.SetNum(N); Flow.SetNum(N); Wake.SetNum(N);
    TArray<FProcMeshTangent> Tangents; Tangents.SetNum(N);
    TArray<FProcMeshVertex> Packed,Reference; Reference.SetNum(N);
    for (double Sign:{-1.,1.})
    {
        for (int32 I=0; I<N; ++I)
        {
            Positions[I]=FVector(1.e8+(I%225)*100.125,Sign*(-7.e7+(I/225)*100.25),100.+I*.013);
            Normals[I]=FVector(.01*(I%13),Sign*.03*(I%7),1.).GetSafeNormal();
            Colors[I]=FLinearColor((I%257)/256.f,((I%19)-3)/16.f,(I%23)/13.f,(I%5)/4.f);
            UVs[I]=FVector2D((I%225)*.2,(I/225)*.3);
            Flow[I]=FVector2D(-2.-I*.0001,Sign*3.); Wake[I]=FVector2D(I%7,(I%11)*.13);
            Tangents[I]=FProcMeshTangent(FVector(1.,Sign*.01*(I%17),0.).GetSafeNormal(),I%2!=0);
            auto& V=Reference[I]; // Independent previous production packing.
            V.Position=Positions[I]; V.Normal=Normals[I]; V.Color=Colors[I].ToFColor(false);
            V.UV0=UVs[I]; V.UV1=Flow[I]; V.UV2=Wake[I]; V.UV3=FVector2D::ZeroVector; V.Tangent=Tangents[I];
        }
        for (bool Concurrent:{false,true})
        {
            Packed.SetNum(N); for (auto& V:Packed) V.UV3=FVector2D(99.,-21.);
            if (!RaftSimWaterSourcePacking::Pack(Positions,Normals,Colors,UVs,Flow,Wake,Tangents,Packed,Concurrent)) return false;
            bool Same=Packed.Num()==N;
            for (int32 I=0; Same && I<N; ++I)
            {
                const auto& A=Packed[I]; const auto& B=Reference[I];
                Same=A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                    A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==B.UV3 &&
                    A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
            }
            TestTrue(TEXT("all 50,625 serial/parallel vertices exactly preserve positions, normals and all optical channels"),Same);
        }
    }
    TArray<FVector2D> SurfaceTransport;
    SurfaceTransport.SetNum(N);
    for (int32 I=0;I<N;++I) SurfaceTransport[I]=FVector2D(-3.+I*.0001,1.2-I*.00003);
    for (bool Concurrent:{false,true})
    {
        TestTrue(TEXT("effective surface transport packs"),RaftSimWaterSourcePacking::Pack(
            Positions,Normals,Colors,UVs,Flow,Wake,Tangents,Packed,Concurrent,SurfaceTransport));
        bool Same=true;
        for (int32 I=0;I<N;++I)
            Same &= Packed[I].UV3==SurfaceTransport[I] && Packed[I].UV1==Flow[I] &&
                Packed[I].UV2==Wake[I] && Packed[I].Position==Positions[I] && Packed[I].Color==Colors[I].ToFColor(false);
        TestTrue(TEXT("surface-return UV3 is exact without replacing bulk UV1, wake, geometry or foam amount"),Same);
    }
    // Exercise fresh storage, reuse, shrink, empty and regrowth. Poison all
    // fields so omitted assignments cannot inherit apparently valid defaults.
    for (bool Concurrent:{false,true}) for (int32 Count:{0,1,17,N,31,0,N})
    {
        Packed.SetNum(Count);
        for (auto& V:Packed)
        {
            V.Position=FVector(-999); V.Normal=FVector(-777); V.Color=FColor(1,2,3,4);
            V.UV0=V.UV1=V.UV2=V.UV3=FVector2D(123,-456);
            V.Tangent=FProcMeshTangent(FVector(-11),true);
        }
        TestTrue(TEXT("complete packing across buffer size changes"),RaftSimWaterSourcePacking::Pack(
            MakeArrayView(Positions).Left(Count),MakeArrayView(Normals).Left(Count),
            MakeArrayView(Colors).Left(Count),MakeArrayView(UVs).Left(Count),
            MakeArrayView(Flow).Left(Count),MakeArrayView(Wake).Left(Count),
            MakeArrayView(Tangents).Left(Count),Packed,Concurrent,MakeArrayView(SurfaceTransport).Left(Count)));
        TArray<FProcMeshVertex> Copied; Copied.SetNum(Count+3);
        const auto Suffix=Copied.Last();
        RaftSimWaterVertexCopy::Prefix(Packed,Copied);
        bool Same=Packed.Num()==Count;
        for (int32 I=0;I<Count;++I)
        {
            const auto& A=Packed[I]; const auto& B=Reference[I]; const auto& C=Copied[I];
            Same &= A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==SurfaceTransport[I] &&
                A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
            Same &= C.Position==A.Position && C.Normal==A.Normal && C.Color==A.Color &&
                C.UV0==A.UV0 && C.UV1==A.UV1 && C.UV2==A.UV2 && C.UV3==A.UV3 &&
                C.Tangent.TangentX==A.Tangent.TangentX && C.Tangent.bFlipTangentY==A.Tangent.bFlipTangentY;
        }
        Same &= Copied.Last().Position==Suffix.Position && Copied.Last().UV3==Suffix.UV3;
        TestTrue(TEXT("every packed/copied value matches independent reference and suffix remains intact"),Same);
    }
    SurfaceTransport.Pop();
    TestFalse(TEXT("partial surface transport is rejected before mutation"),RaftSimWaterSourcePacking::Pack(
        Positions,Normals,Colors,UVs,Flow,Wake,Tangents,Packed,false,SurfaceTransport));
    TestEqual(TEXT("rejected transport leaves output intact"),Packed.Last().UV3,FVector2D(-3.+(N-1)*.0001,1.2-(N-1)*.00003));
    const auto Last=Packed.Last().Position;
    Colors.Pop();
    TestFalse(TEXT("mismatched source attributes are rejected"),
        RaftSimWaterSourcePacking::Pack(Positions,Normals,Colors,UVs,Flow,Wake,Tangents,Packed));
    TestTrue(TEXT("rejected packing leaves output intact"),Packed.Num()==N && Packed.Last().Position==Last);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterShorelineTest,"RaftSim.M4.CartesianShorelineGeometry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterShorelineTest::RunTest(const FString&)
{
    TArray<FProcMeshVertex> V; TArray<uint32> T;
    TArray<uint8> Available; Available.Init(1,4);
    for (double Angle : {0.,.37,UE_DOUBLE_PI/2.,UE_DOUBLE_PI}) for (double Sign : {-1.,1.}) for (int32 Mask=0; Mask<16; ++Mask)
    {
        TArray<uint8> Wet; TArray<float> H, Bed;
        int32 WetCount=0;
        for (int32 I=0; I<4; ++I)
        { const bool W=Mask&(1<<I); Wet.Add(W); H.Add(W?1.f:0.f); Bed.Add(W?0.f:2.f); WetCount+=W; }
        if (!TestTrue(TEXT("all cell patterns build"),RaftSimWaterShoreline::Build(2,2,Grid(2,2,Angle,Sign),Wet,Available,H,Bed,V,T))) return false;
        const bool Opposite=Mask==6 || Mask==9;
        const double Expected=WetCount==0?0.:WetCount==1?.125:WetCount==2?(Opposite?.25:.5):WetCount==3?.875:1.;
        TestTrue(TEXT("area is invariant under rotation and geographic reflection"),FMath::Abs(Area(V,T)-Expected)<1.e-10);
        TestEqual(TEXT("shared-edge storage is below three source grids"),V.Num(),8);
        for (int32 I=0; I<T.Num(); I+=3)
            TestTrue(TEXT("every rotated/reflected water triangle faces the overhead camera"),
                FVector::CrossProduct(V[T[I+1]].Position-V[T[I]].Position,
                    V[T[I+2]].Position-V[T[I]].Position).Z<0.);
        for (uint32 I : T)
        {
            TestTrue(TEXT("no dry source vertex is referenced"),I>=4 || Wet[I]);
            TestTrue(TEXT("shore water is horizontal, never interpolated up dry terrain"),FMath::Abs(V[I].Position.Z-1.)<1.e-12);
            TestEqual(TEXT("linear foam encoding survives clipping"),V[I].Color.R,uint8(17));
            TestTrue(TEXT("actual field current survives clipping"),V[I].UV1.Equals(FVector2D(-2,3)));
        }
        if (Opposite)
        {
            TestEqual(TEXT("diagonal channels remain two triangles"),T.Num(),6);
            for (int32 A=0; A<3; ++A) for (int32 B=3; B<6; ++B)
                TestNotEqual(TEXT("disconnected channels share no node"),T[A],T[B]);
        }
    }
    // A dry island is not connected to outer-bank row bounds. Verify every
    // triangle centroid against the hole, and every edge against its center.
    const int32 Nx=9, Ny=9;
    TArray<uint8> Wet; Wet.Init(1,Nx*Ny); Available.Init(1,Nx*Ny);
    TArray<float> H, Bed; H.Init(1.f,Nx*Ny); Bed.Init(0.f,Nx*Ny);
    for (int32 Y=3; Y<=5; ++Y) for (int32 X=3; X<=5; ++X)
    { Wet[Y*Nx+X]=0; H[Y*Nx+X]=0; Bed[Y*Nx+X]=2; }
    TestTrue(TEXT("interior island builds"),RaftSimWaterShoreline::Build(Nx,Ny,Grid(Nx,Ny),Wet,Available,H,Bed,V,T));
    for (int32 I=0; I<T.Num(); I+=3)
    {
        const FVector C=(V[T[I]].Position+V[T[I+1]].Position+V[T[I+2]].Position)/3.;
        TestFalse(TEXT("no triangle spans the dry island"), C.X>2.5 && C.X<5.5 && C.Y>2.5 && C.Y<5.5 &&
            C.X>3. && C.X<5. && C.Y>3. && C.Y<5.);
    }
    TestTrue(TEXT("wet polygon area excludes island"),FMath::Abs(Area(V,T)-55.5)<1.e-10);
    // Rising measured bed: eta=1, bed rises 0->4, hence x=.25.
    Wet={1,0,1,0}; Available.Init(1,4); H={1,0,1,0}; Bed={0,4,0,4};
    TestTrue(TEXT("measured bank crossing builds"),RaftSimWaterShoreline::Build(2,2,Grid(2,2),Wet,Available,H,Bed,V,T));
    TestTrue(TEXT("crossing touches rising bed at exact free surface"),FMath::Abs(Area(V,T)-.25)<1.e-12);
    Bed={0,0,0,0};
    TestTrue(TEXT("advancing dry front builds"),RaftSimWaterShoreline::Build(2,2,Grid(2,2),Wet,Available,H,Bed,V,T));
    TestTrue(TEXT("unresolved front uses half-cell convention"),FMath::Abs(Area(V,T)-.5)<1.e-12);
    Available[1]=0;
    TestTrue(TEXT("unknown corner is handled"),RaftSimWaterShoreline::Build(2,2,Grid(2,2),Wet,Available,H,Bed,V,T));
    TestTrue(TEXT("unknown terrain never gets an extrapolated surface"),T.IsEmpty());
    // Diagnostic cost at a 224 m / 1 m presentation grid. This is not the
    // complete render/physics frame gate, which still requires playable motion.
    constexpr int32 BenchN=225;
    Wet.Init(1,BenchN*BenchN); Available.Init(1,BenchN*BenchN);
    H.Init(1.f,BenchN*BenchN); Bed.Init(0.f,BenchN*BenchN);
    for (int32 Y=0; Y<BenchN; ++Y) for (int32 X=0; X<BenchN; ++X)
        if (FMath::Square(X-112)+FMath::Square(Y-112)<25*25)
        { Wet[Y*BenchN+X]=0; H[Y*BenchN+X]=0; Bed[Y*BenchN+X]=2; }
    const auto BenchSource=Grid(BenchN,BenchN);
    TArray<double> Costs;
    for (int32 Iteration=0; Iteration<32; ++Iteration)
    {
        auto Input=BenchSource;
        const double Start=FPlatformTime::Seconds();
        if (!RaftSimWaterShoreline::Build(BenchN,BenchN,MoveTemp(Input),Wet,Available,H,Bed,V,T)) return false;
        Costs.Add((FPlatformTime::Seconds()-Start)*1000.);
    }
    Costs.Sort();
    AddInfo(FString::Printf(TEXT("Shore clipping only, 225x225: median_ms=%.3f p95_ms=%.3f vertices=%d triangles=%d; not full-frame acceptance"),
        Costs[16],Costs[30],V.Num(),T.Num()/3));
    RaftSimWaterShoreline::FTopologyCache Cache;
    TArray<int32> Offsets;
    TArray<double> CachedCosts;
    for (int32 Iteration=0; Iteration<32; ++Iteration)
    {
        auto Input=BenchSource;
        for (auto& P : Input) { P.Position.Z+=Iteration*.07; P.Color.R=Iteration; }
        bool Rebuilt=false;
        const double Start=FPlatformTime::Seconds();
        if (!Cache.Update(BenchN,BenchN,MoveTemp(Input),Wet,Available,H,Bed,V,T,Offsets,Rebuilt)) return false;
        CachedCosts.Add((FPlatformTime::Seconds()-Start)*1000.);
        TestEqual(TEXT("only first stable-grid frame constructs triangles"),Rebuilt,Iteration==0);
    }
    CachedCosts.Sort();
    AddInfo(FString::Printf(TEXT("Cached shore update, same 225x225: median_ms=%.3f p95_ms=%.3f rebuilds=%llu reuses=%llu; not full-frame acceptance"),
        CachedCosts[16],CachedCosts[30],Cache.GetRebuildCount(),Cache.GetReuseCount()));
    TArray<double> MovingBankCosts;
    for (int32 Iteration=0; Iteration<32; ++Iteration)
    {
        for (int32 I=0; I<H.Num(); ++I) if (Wet[I]) H[I]=1.f+.001f*(Iteration+1);
        auto Input=BenchSource; bool Rebuilt=false;
        const double Start=FPlatformTime::Seconds();
        if (!Cache.Update(BenchN,BenchN,MoveTemp(Input),Wet,Available,H,Bed,V,T,Offsets,Rebuilt)) return false;
        MovingBankCosts.Add((FPlatformTime::Seconds()-Start)*1000.);
        TestFalse(TEXT("moving nondegenerate bank reuses exact triangle connectivity"),Rebuilt);
        TArray<FProcMeshVertex> Reference; TArray<uint32> ReferenceTriangles;
        auto ReferenceInput=BenchSource;
        if (!RaftSimWaterShoreline::Build(BenchN,BenchN,MoveTemp(ReferenceInput),Wet,Available,H,Bed,Reference,ReferenceTriangles)) return false;
        TestTrue(TEXT("moving-bank indices match independent fresh construction"),T==ReferenceTriangles);
        bool Same=true;
        for (uint32 I : T) Same &= V[I].Position==Reference[I].Position && V[I].UV0==Reference[I].UV0;
        TestTrue(TEXT("moving-bank geometry and crossings stay bit-exact"),Same);
    }
    MovingBankCosts.Sort();
    AddInfo(FString::Printf(TEXT("Changing-bank exact update, same 225x225: median_ms=%.3f p95_ms=%.3f; 32 full fresh-build comparisons, not full-frame acceptance"),
        MovingBankCosts[16],MovingBankCosts[30]));
    AddInfo(TEXT("128 rotated/reflected cell configurations; measured banks, finite-volume front, unknown coverage and internal island checked."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineExactCacheTest,"RaftSim.M4.ShorelineExactCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineExactCacheTest::RunTest(const FString&)
{
    constexpr int32 N=9;
    auto Source=Grid(N,N,0.,-1.);
    TArray<uint8> Wet,Available; Wet.Init(1,N*N); Available.Init(1,N*N);
    TArray<float> H,Bed; H.Init(1.f,N*N); Bed.Init(0.f,N*N);
    for (int32 Y=3; Y<=5; ++Y) for (int32 X=3; X<=5; ++X)
    { Wet[Y*N+X]=0; H[Y*N+X]=0; Bed[Y*N+X]=2; }
    RaftSimWaterShoreline::FTopologyCache Cache;
    TArray<FProcMeshVertex> Cached,Reference;
    TArray<uint32> CachedTriangles,ReferenceTriangles;
    TArray<int32> CachedOffsets,ReferenceOffsets;
    RaftSimWaterShoreline::FTopologyCache CompactCache;
    TArray<FProcMeshVertex> Compact;
    TArray<uint32> CompactTriangles;
    TArray<int32> CompactOffsets;
    for (int32 Step=0; Step<12; ++Step)
    {
        if (Step==3) H[0]+=.1f; // Interior depth does not change any shore crossing.
        if (Step==4) H[3*N+2]+=.1f;
        if (Step==5) Available[0]=0;
        if (Step==6) { Wet[4*N+4]=1; H[4*N+4]=.1f; }
        if (Step==7) for (auto& V : Source) { V.Position.X+=10000.; V.Position.Y-=20000.; }
        if (Step==8) for (auto& V : Source) { const double X=V.Position.X; V.Position.X=-V.Position.Y; V.Position.Y=X; }
        if (Step==9) { Wet.Init(0,N*N); H.Init(0.f,N*N); }
        if (Step==11) { Wet.Init(1,N*N); H.Init(1.f,N*N); Available.Init(1,N*N); }
        for (int32 I=0; I<Source.Num(); ++I)
        {
            auto& V=Source[I];
            V.Position.Z=2.+.13*Step+.005*I;
            V.Normal=FVector(.01*Step,.005*I,1).GetSafeNormal();
            V.Color=FColor(Step+I,100+Step,27,255);
            V.UV0=FVector2D(I%N+.01*Step,I/N-.02*Step);
            V.UV1=FVector2D(-Step,I); V.UV2=FVector2D(.2*Step,.3*I); V.UV3=FVector2D(I,Step);
            V.Tangent=FProcMeshTangent(FVector(1,.01*Step,0).GetSafeNormal(),Step%2!=0);
        }
        auto Input=Source; bool Rebuilt=false;
        if (!TestTrue(TEXT("cached update succeeds"),Cache.Update(N,N,MoveTemp(Input),Wet,Available,H,Bed,
            Cached,CachedTriangles,CachedOffsets,Rebuilt))) return false;
        const bool ExpectedRebuild=Step==0 || (Step>=5 && Step<=9) || Step==11;
        TestEqual(TEXT("reuse is exact, with all topology-affecting changes invalidating"),Rebuilt,ExpectedRebuild);
        auto ReferenceInput=Source;
        if (!RaftSimWaterShoreline::Build(N,N,MoveTemp(ReferenceInput),Wet,Available,H,Bed,Reference,ReferenceTriangles,&ReferenceOffsets)) return false;
        TestTrue(TEXT("cached indices exactly equal a fresh build"),CachedTriangles==ReferenceTriangles);
        TestTrue(TEXT("cell lookup exactly equals a fresh build"),CachedOffsets==ReferenceOffsets);
        bool Same=true;
        for (uint32 I : CachedTriangles)
        {
            const auto& A=Cached[I]; const auto& B=Reference[I];
            Same &= A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==B.UV3 &&
                A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
        }
        TestTrue(TEXT("every drawn vertex attribute is bit-exact with the fresh build"),Same);
        auto CompactInput=Source; bool CompactRebuilt=false;
        if (!CompactCache.Update(N,N,MoveTemp(CompactInput),Wet,Available,H,Bed,
            Compact,CompactTriangles,CompactOffsets,CompactRebuilt,true)) return false;
        TestEqual(TEXT("compact CPU shore invalidates on the same exact inputs"),CompactRebuilt,ExpectedRebuild);
        TestEqual(TEXT("compact CPU shore carries only source grid plus encountered edges"),
            Compact.Num(),N*N+CompactCache.GetEdges().Num());
        TestTrue(TEXT("compact shore preserves triangle count and cell owners"),
            CompactTriangles.Num()==ReferenceTriangles.Num() && CompactOffsets==ReferenceOffsets);
        bool SameCompact=CompactTriangles.Num()==ReferenceTriangles.Num();
        for (int32 I=0; SameCompact && I<CompactTriangles.Num(); ++I)
        {
            const auto& A=Compact[CompactTriangles[I]]; const auto& B=Reference[ReferenceTriangles[I]];
            SameCompact=A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==B.UV3 &&
                A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
        }
        TestTrue(TEXT("dense CPU shore preserves every actual triangle corner and attribute exactly"),SameCompact);
        for (int32 I=0; I<N*N; ++I)
            TestTrue(TEXT("dense CPU shore retains original grid positions and indices"),Compact[I].Position==Source[I].Position);
        if (Step==4)
        {
            TestFalse(TEXT("reserve sentinel is absent from the active draw list"),CachedTriangles.Contains(uint32(N*N)));
            TestEqual(TEXT("topology rebuild does not rewrite an initialized unused reserve node"),Cached[N*N].Position.Z,2.);
        }
    }
    const auto Before=CachedTriangles;
    const uint64 BeforeBuilds=Cache.GetRebuildCount();
    H[0]=-1.f; auto Invalid=Source; bool Rebuilt=true;
    TestFalse(TEXT("invalid hydraulic state rejected before modifying mesh/cache"),Cache.Update(N,N,MoveTemp(Invalid),Wet,Available,H,Bed,
        Cached,CachedTriangles,CachedOffsets,Rebuilt));
    TestTrue(TEXT("failed update preserves valid indices and cache"),CachedTriangles==Before && Cache.GetRebuildCount()==BeforeBuilds);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineMovingBankCacheTest,"RaftSim.M4.ShorelineMovingBankCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineMovingBankCacheTest::RunTest(const FString&)
{
    int32 Compared=0, Reused=0, MembershipChanges=0, WindingChanges=0;
    for (bool Compact : {false,true}) for (double Sign : {-1.,1.})
    for (double Angle : {0.,.37,UE_DOUBLE_PI/2.}) for (int32 Shape=0; Shape<3; ++Shape)
    for (int32 Mask=0; Mask<16; ++Mask)
    {
        auto Source=Grid(2,2,Angle,Sign);
        if (Shape==1) Source[3].Position=Source[0].Position+FVector(.3,Sign*.2,0.); // Concave/folded input.
        if (Shape==2) for (auto& V : Source) V.Position*=.0001; // Existing degeneracy gate.
        RaftSimWaterShoreline::FTopologyCache Cache;
        TArray<uint8> Wet,Available; Available.Init(1,4);
        TArray<float> H,Bed;
        for (int32 I=0; I<4; ++I) { Wet.Add(bool(Mask&(1<<I))); H.Add(0.f); Bed.Add(Wet[I]?0.f:4.f); }
        TArray<FProcMeshVertex> V,Reference;
        TArray<uint32> T,ReferenceT,Previous;
        TArray<int32> Offsets,ReferenceOffsets;
        for (float Depth : {1.e-6f,.01f,.5f,3.9f,1.e-6f,2.f,4.1f,.5f})
        {
            for (int32 I=0; I<4; ++I)
            {
                H[I]=Wet[I]?Depth:0.f;
                Source[I].Position.Z=Depth+I*.03;
                Source[I].UV0=FVector2D(Depth,I); Source[I].UV1=FVector2D(I,-Depth);
                Source[I].UV2=FVector2D(Depth*.2,I*.3); Source[I].Color=FColor(I,Depth*20,81,255);
            }
            auto Input=Source; bool Rebuilt=false;
            if (!Cache.Update(2,2,MoveTemp(Input),Wet,Available,H,Bed,V,T,Offsets,Rebuilt,Compact)) return false;
            auto ReferenceInput=Source;
            if (!RaftSimWaterShoreline::Build(2,2,MoveTemp(ReferenceInput),Wet,Available,H,Bed,
                Reference,ReferenceT,&ReferenceOffsets,nullptr,Compact)) return false;
            if (!TestTrue(TEXT("moving-bank candidates preserve fresh connectivity and cell lookup"),T==ReferenceT && Offsets==ReferenceOffsets)) return false;
            bool Same=V.Num()==Reference.Num();
            for (uint32 I : T)
            {
                const auto& A=V[I]; const auto& B=Reference[I];
                Same &= A.Position==B.Position && A.Normal==B.Normal && A.Color==B.Color &&
                    A.UV0==B.UV0 && A.UV1==B.UV1 && A.UV2==B.UV2 && A.UV3==B.UV3 &&
                    A.Tangent.TangentX==B.Tangent.TangentX && A.Tangent.bFlipTangentY==B.Tangent.bFlipTangentY;
            }
            if (!TestTrue(TEXT("every moving-bank drawn attribute matches fresh construction exactly"),Same)) return false;
            if (Depth!=1.e-6f && T!=Previous)
            {
                TestTrue(TEXT("changed membership or winding always forces reconstruction"),Rebuilt);
                if (T.Num()!=Previous.Num()) ++MembershipChanges;
                else ++WindingChanges;
            }
            Previous=T; ++Compared; Reused+=!Rebuilt;
        }
    }
    TestTrue(TEXT("exercise nondegenerate moving-crossing reuse"),Reused>0);
    TestTrue(TEXT("exercise previously omitted triangles becoming visible"),MembershipChanges>0);
    TestTrue(TEXT("exercise winding changes on non-convex source cells"),WindingChanges>0);
    AddInfo(FString::Printf(TEXT("Moving-bank fresh-build comparisons=%d reuse=%d membership_changes=%d winding_changes=%d; no tolerance or geometry gate changed"),
        Compared,Reused,MembershipChanges,WindingChanges));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineRasterTest,"RaftSim.M4.ShorelineRasterMembership",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineRasterTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Actor=World->SpawnActor<AActor>();
    auto* Mesh=NewObject<URaftSimShorelineMeshComponent>(Actor);
    Actor->SetRootComponent(Mesh); Mesh->RegisterComponent();
    auto* CameraActor=World->SpawnActor<AActor>();
    auto* Capture=NewObject<USceneCaptureComponent2D>(CameraActor);
    CameraActor->SetRootComponent(Capture);
    auto* Target=NewObject<UTextureRenderTarget2D>(Capture);
    Target->RenderTargetFormat=RTF_RGBA32f;
    Target->InitAutoFormat(64,64); Target->UpdateResourceImmediate(true);
    Capture->TextureTarget=Target; Capture->CaptureSource=SCS_SceneDepth;
    Capture->bCaptureEveryFrame=false; Capture->bCaptureOnMovement=false;
    Capture->FOVAngle=60.f;
    Capture->PrimitiveRenderMode=ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
    Capture->RegisterComponent(); Capture->ShowOnlyComponent(Mesh);
    Capture->SetWorldLocationAndRotation(FVector(400,-400,1000),FRotator(-90,0,0));
    const auto ReadMembership = [&](const TCHAR* Label) -> int32
    {
        World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
        Capture->CaptureScene(); FlushRenderingCommands();
        TArray<FLinearColor> Pixels;
        FReadSurfaceDataFlags Flags(RCM_MinMax); Flags.SetLinearToGamma(false);
        if (!TestTrue(TEXT("actual rendered scene-depth readback succeeds"),
            Target->GameThread_GetRenderTargetResource()->ReadLinearColorPixels(Pixels,Flags))) return -1;
        int32 Count=0; float Min=MAX_flt, Max=-MAX_flt;
        for (const auto& P : Pixels)
        { Count+=P.R>900.f && P.R<1100.f; Min=FMath::Min(Min,P.R); Max=FMath::Max(Max,P.R); }
        AddInfo(FString::Printf(TEXT("Raster %s: count=%d depth_min=%g depth_max=%g center=%g"),
            Label,Count,Min,Max,Pixels.IsEmpty()?-1.f:Pixels[32*64+32].R));
        return Count;
    };
    // A stock engine primitive independently verifies the camera, depth units,
    // visibility filtering and readback before testing the custom proxy.
    auto* ControlActor=World->SpawnActor<AActor>();
    auto* Control=NewObject<UStaticMeshComponent>(ControlActor);
    ControlActor->SetRootComponent(Control);
    Control->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Control->RegisterComponent();
    Control->SetWorldLocation(FVector(400,-400,0));
    Control->SetWorldScale3D(FVector(8,8,.1));
    Capture->ShowOnlyComponents.Reset(); Capture->ShowOnlyComponent(Control);
    TestTrue(TEXT("stock primitive proves the raster capture is operational"),ReadMembership(TEXT("stock cube"))>1000);
    Capture->ShowOnlyComponents.Reset(); Capture->ShowOnlyComponent(Mesh);
    constexpr int32 N=9;
    TArray<uint8> Wet,Available; Available.Init(1,N*N);
    TArray<float> H,Bed;
    for (bool CompactCrests : {false,true}) for (double Sign : {-1.,1.})
    {
    Capture->SetWorldLocationAndRotation(FVector(400,Sign*400,1000),FRotator(-90,0,0));
    TArray<int32> Counts;
    FPrimitiveSceneProxy* Proxy=nullptr;
    for (int32 Step=0; Step<5; ++Step)
    {
        Wet.Init(Step==1?0:1,N*N); H.Init(Step==1?0.f:1.f,N*N); Bed.Init(0.f,N*N);
        if (Step==2 || Step==3) for (int32 Y=3; Y<=5; ++Y) for (int32 X=3; X<=5; ++X)
        { Wet[Y*N+X]=0; H[Y*N+X]=0; Bed[Y*N+X]=2; }
        auto Input=Grid(N,N,0.,Sign);
        for (auto& V : Input) { V.Position.X*=100.; V.Position.Y*=100.; V.Position.Z=Step==3?10.:0.; }
        TArray<float> Coarse,Shore; Coarse.Init(0,N*N); Shore.Init(1,N*N);
        FRaftSimShorelineCrestInput Crests;
        Crests.SourceCrestCm=Coarse; Crests.SourceShoreWeight=Shore; Crests.ProfileKey={0.};
        Crests.HeightAtWorldXYCm=[](const FVector2D&) { return 0.f; };
        if (!Mesh->SetClippedWaterMesh(N,N,MoveTemp(Input),Wet,Available,H,Bed,CompactCrests?&Crests:nullptr)) return false;
        World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
        if (Step==0) Proxy=Mesh->GetSceneProxy();
        TestTrue(TEXT("raster test keeps one actual rendering proxy"),Proxy && Mesh->GetSceneProxy()==Proxy);
        Counts.Add(ReadMembership(*FString::Printf(TEXT("shore step %d"),Step)));
        if (Step==0)
        {
            Capture->SetWorldLocationAndRotation(FVector(400,Sign*400,-1000),FRotator(90,0,0));
            TestEqual(TEXT("single-sided surface faces up, not down"),ReadMembership(TEXT("shore underside")),0);
            Capture->SetWorldLocationAndRotation(FVector(400,Sign*400,1000),FRotator(-90,0,0));
        }
    }
    TestTrue(TEXT("full active index buffer actually draws water"),Counts[0]>1000);
    TestEqual(TEXT("all-dry update draws no stale GPU triangles"),Counts[1],0);
    TestTrue(TEXT("rewet island remains a rendered hole"),Counts[2]>Counts[0]/2 && Counts[2]<Counts[0]);
    TestTrue(TEXT("cached height update retains correct active triangles"),FMath::Abs(Counts[3]-Counts[2])<100);
    TestEqual(TEXT("full rewet restores the original raster membership"),Counts[4],Counts[0]);
    TestTrue(TEXT("raster test exercised cached topology"),Mesh->GetTopologyReuseCount()>0);
    AddInfo(FString::Printf(TEXT("D3D scene-depth water pixels full/dry/island/cached-height/full: %d/%d/%d/%d/%d"),
        Counts[0],Counts[1],Counts[2],Counts[3],Counts[4]));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelinePersistentProxyTest,"RaftSim.M4.ShorelinePersistentProxy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelinePersistentProxyTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Actor=World->SpawnActor<AActor>();
    auto* Mesh=NewObject<URaftSimShorelineMeshComponent>(Actor);
    Actor->SetRootComponent(Mesh); Mesh->RegisterComponent();
    TArray<uint32> Full={0,2,1,1,2,3};
    TestTrue(TEXT("first water mesh accepted"),Mesh->SetWaterMesh(Grid(2,2),MoveTemp(Full),12));
    World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
    auto* Initial=Mesh->GetSceneProxy();
    if (!TestNotNull(TEXT("actual RHI scene proxy exists"),Initial)) return false;
    for (int32 Step=0; Step<30; ++Step)
    {
        TArray<uint32> Changed=Step%3==0?TArray<uint32>{}:Step%3==1?TArray<uint32>{0,2,1}:TArray<uint32>{0,2,1,1,2,3};
        const int32 Expected=Changed.Num();
        auto Vertices=Grid(2,2); for (auto& Vtx : Vertices) Vtx.Position.X+=Step*2.;
        TestTrue(TEXT("membership/recenter update accepted"),Mesh->SetWaterMesh(MoveTemp(Vertices),MoveTemp(Changed),12));
        World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
        TestTrue(TEXT("same proxy across dry-out, re-wet and translation"),Mesh->GetSceneProxy()==Initial);
        TestEqual(TEXT("active triangle count never retains old dry triangles"),Mesh->GetWaterIndices().Num(),Expected);
    }
    TArray<uint32> Invalid={0,2,99};
    TestFalse(TEXT("out-of-range update rejected"),Mesh->SetWaterMesh(Grid(2,2),MoveTemp(Invalid),12));
    TestEqual(TEXT("rejection preserves last valid data"),Mesh->GetWaterIndices().Num(),6);
    return true;
}

#if RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianShorelineSurfaceTest,"RaftSim.M4.CartesianShorelineSurface",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianShorelineSurfaceTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); FlushRenderingCommands(); };
    auto* Surface=World->SpawnActor<ARaftSimWaterSurfaceActor>();
    auto* RiverConfig=World->SpawnActor<ARaftSimRiverWaterConfig>();
    RiverConfig->CookedFieldsDir=TEXT("tmp/cartesian-atlas-fixture-v1/dry_island");
    RiverConfig->bLiveSolverOwnsRuntimeRendering=true;
    RiverConfig->bEnableLiveSolverVolumeCore=true;
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>(Surface);
    FRaftSimWaterRuntimeConfig Config; Config.bRequireAcceptedReportManifest=false; Config.bEnableDeterministicCapture=false;
    Water->Configure(Config);
    if (!Water->ConfigureRiverCoordinateMap(TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")) ||
        !Water->ConfigureRiverWindow(TEXT("tmp/cartesian-atlas-fixture-v1/dry_island"),TEXT("analytic"),
            FVector2D(-5420.,3612.),FVector2D(16.,16.),.035f,false)) return false;
    Surface->WaterAdapter=Water; Surface->VertexSpacingMeters=1.f;
    Surface->CurvedGridLengthMeters=20.f; Surface->CurvedGridWidthMeters=20.f;
    Surface->bFixedCurvedGrid=true; Surface->FixedCurvedGridCenterStationMeters=-5420.f;
    Surface->FixedCartesianGridCenterNorthMeters=3612.f;
    // The analytic source is 24 m wide, not the 224 m production window.
    // Keep a visible interior with its own two-meter edge feather; the normal
    // production 36 m feather and all physical/acceptance thresholds stay unchanged.
    Surface->CurvedGridEdgeBlendMeters=2.f;
    Surface->BuildGrid();
    TestTrue(TEXT("explicit production config enables the single carrier"),
        Surface->bLiveVolumeCoreEnabled && Surface->bSingleLiveWaterSurfaceEnabled);
    Surface->ResolvedPresentationHydraulicReliefScale=0.f;
    Surface->ResolvedPresentationStandingWaveScale=0.f;
    auto* HiddenBase=Surface->SurfaceMesh->GetProcMeshSection(0);
    auto* HiddenFoam=Surface->RapidFoamMesh->GetProcMeshSection(0);
    if (!TestNotNull(TEXT("legacy base exists but is hidden"),HiddenBase) ||
        !TestNotNull(TEXT("legacy foam exists but is hidden"),HiddenFoam)) return false;
    // Sentinels distinguish actually skipping an unused upload from merely
    // drawing it invisibly. No source geometry or visible channels are changed.
    HiddenBase->ProcVertexBuffer[0].Position.Z=-12345.;
    HiddenFoam->ProcVertexBuffer[0].Position.Z=-23456.;
    Surface->RefreshSurface();
    auto* Mesh=Surface->CartesianShorelineMesh.Get();
    Water->ConfigureRaftSupportSurface(true,1.f,0.f,1.f);
    TestTrue(TEXT("actual refresh publishes Cartesian clipped carrier"),Surface->IsLiveVolumeCoreVisible());
    const auto* PackingStorage=Surface->CartesianSourcePackingScratch.GetData();
    TestEqual(TEXT("normal publication retains the complete current source prefix"),
        Surface->CartesianSourcePackingScratch.Num(),Surface->GridStationN*Surface->GridLateralN);
    TestFalse(TEXT("old uncut procedural carrier is hidden"),Surface->LiveVolumeCoreMesh->IsVisible());
    TestTrue(TEXT("actual clipped mesh has water triangles"),Mesh && Mesh->GetWaterIndices().Num()>0);
    int32 Dry=0;
    for (int32 I=0; I<Surface->CartesianShoreWet.Num(); ++I)
        if (!Surface->CartesianShoreWet[I])
        {
            ++Dry;
            TestFalse(TEXT("actual rendered triangles never reference dry grid vertices"),Mesh->GetWaterIndices().Contains(uint32(I)));
        }
    TestTrue(TEXT("real fixture includes internal dry terrain"),Dry>=9);
    FVector Point;
    TestFalse(TEXT("spray carrier cannot anchor inside dry island"),Surface->SampleVisibleCarrierAtRiverCoordinates(
        FVector2D(-5432.,3600.)+FVector2D(9.,9.),Point));
    int32 CheckedTriangles=0;
    FVector GroundProbe=FVector::ZeroVector;
    bool bHaveGroundProbe=false;
    double MaximumAnchorErrorCm=0.;
    const auto& CV=Mesh->GetWaterVertices(); const auto& CT=Mesh->GetWaterIndices();
    for (int32 I=0; I<CT.Num(); I+=3)
    {
        const FVector Expected=(CV[CT[I]].Position+CV[CT[I+1]].Position+CV[CT[I+2]].Position)/3.;
        // Actual Cartesian map: world east=x, north=-y, centimeters.
        const FVector2D Field(Expected.X*.01,-Expected.Y*.01);
        if (!TestTrue(TEXT("every actual clipped triangle supports a presentation anchor"),
            Surface->SampleVisibleCarrierAtRiverCoordinates(Field,Point))) return false;
        MaximumAnchorErrorCm=FMath::Max(MaximumAnchorErrorCm,FVector::Distance(Point,Expected));
        float SupportHeight=0.f; bool bSupportWet=false;
        TestTrue(TEXT("world support wrapper addresses the actual triangle"),
            Surface->SampleCartesianCarrierSupport(Expected,SupportHeight,bSupportWet) && bSupportWet);
        TestTrue(TEXT("world support uses submitted geometry with lift removed exactly once"),
            FMath::Abs(SupportHeight*100.-(Expected.Z-Surface->GetResolvedLiveSurfaceRenderLiftCm()))<.001);
        FRaftSimWaterSample Raw,Support;
        if (Water->SampleWaterAtWorldPosition(Expected,Raw) && Raw.bWet)
        {
            if (!bHaveGroundProbe) { GroundProbe=Expected; bHaveGroundProbe=true; }
            TestTrue(TEXT("production registration routes live wet raft probes to this carrier"),
                Water->SampleRaftSupportSurfaceAtWorldPosition(Expected,Support));
            TestEqual(TEXT("registered provider is the actual actor query"),Support.SurfaceHeightMeters,SupportHeight);
        }
        ++CheckedTriangles;
    }
    TestTrue(TEXT("anchor uses the drawn triangle, not the former lattice diagonal"),MaximumAnchorErrorCm<1.e-5);
    AddInfo(FString::Printf(TEXT("Actual Cartesian carrier triangles sampled: %d; maximum_anchor_error_cm=%.9g"),CheckedTriangles,MaximumAnchorErrorCm));
    World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
    auto* Proxy=Mesh->GetSceneProxy();
    if (!TestNotNull(TEXT("actual carrier has a rendering proxy"),Proxy)) return false;
    Surface->RefreshSurface(); Surface->UpdateLiveVolumeCoreInterpolation(.016f);
    TestTrue(TEXT("refresh/interpolation reuse packing allocation while rewriting current attributes"),
        PackingStorage && Surface->CartesianSourcePackingScratch.GetData()==PackingStorage);
    TestEqual(TEXT("single core never refreshes hidden base render buffer"),
        HiddenBase->ProcVertexBuffer[0].Position.Z,-12345.);
    TestEqual(TEXT("single core never refreshes hidden raised foam render buffer"),
        HiddenFoam->ProcVertexBuffer[0].Position.Z,-23456.);
    TestFalse(TEXT("legacy base section remains hidden"),Surface->SurfaceMesh->IsMeshSectionVisible(0));
    TestFalse(TEXT("legacy foam remains hidden"),Surface->RapidFoamMesh->IsVisible());
    World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
    TestTrue(TEXT("refresh and per-frame interpolation preserve carrier proxy"),Mesh->GetSceneProxy()==Proxy);
    TestTrue(TEXT("actual interpolation reuses exact shore topology"),Mesh->GetTopologyReuseCount()>0);
    float Height=0.f; bool bWet=false; FVector DryWorld;
    Water->RiverToWorldPosition(FVector2D(-5423.,3609.),Water->GetRiverVerticalDatumM(),DryWorld);
    TestTrue(TEXT("in-grid clipped dry point is an explicit support rejection, not analytic fallback"),
        Surface->SampleCartesianCarrierSupport(DryWorld,Height,bWet) && !bWet);
    TestFalse(TEXT("off-grid provider is unavailable"),
        Surface->SampleCartesianCarrierSupport(DryWorld+FVector(100000.,0.,0.),Height,bWet));
    // Physical collision can resolve rock finer than the hydraulic lattice.
    // Exercise the actual carrier/provider, not just a height comparison helper.
    if (!TestTrue(TEXT("fixture has a wet ground-contact probe"),bHaveGroundProbe)) return false;
    Surface->SampleCartesianCarrierSupport(GroundProbe,Height,bWet);
    const double WaterZ=Height*100.;
    auto* Ground=World->SpawnActor<AStaticMeshActor>();
    if (!TestNotNull(TEXT("physical ground fixture"),Ground)) return false;
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));
    auto* GroundMesh=Ground->GetStaticMeshComponent();
    GroundMesh->SetMobility(EComponentMobility::Movable);
    GroundMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    GroundMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    GroundMesh->SetCollisionResponseToAllChannels(ECR_Block);
    Ground->SetActorLocation(FVector(GroundProbe.X,GroundProbe.Y,WaterZ));
    FHitResult GroundHit;
    FCollisionQueryParams GroundParams(SCENE_QUERY_STAT(RaftSimGroundWaterTest),true);
    if (!TestTrue(TEXT("independent complex trace verifies rock above the carrier"),
        GroundMesh->LineTraceComponent(GroundHit,GroundProbe+FVector(0,0,1000),
            GroundProbe-FVector(0,0,1000),GroundParams) && GroundHit.ImpactPoint.Z>WaterZ)) return false;
    TestTrue(TEXT("rock-occluded water is dry, not unavailable or fallback"),
        Surface->SampleCartesianCarrierSupport(GroundProbe,Height,bWet) && !bWet);
    FRaftSimWaterSample RockSupport;
    TestTrue(TEXT("registered raft provider also rejects buried water"),
        Water->SampleRaftSupportSurfaceAtWorldPosition(GroundProbe,RockSupport) && !RockSupport.bWet);
    const FVector2D GroundField(GroundProbe.X*.01,-GroundProbe.Y*.01);
    TestFalse(TEXT("spray cannot anchor to water hidden inside physical rock"),
        Surface->SampleVisibleCarrierAtRiverCoordinates(GroundField,Point));
    Ground->SetActorLocation(FVector(GroundProbe.X,GroundProbe.Y,WaterZ-50.-.01));
    TestTrue(TEXT("positive 0.01 cm film is not culled by a ground clearance threshold"),
        Surface->SampleCartesianCarrierSupport(GroundProbe,Height,bWet) && bWet);
    TestTrue(TEXT("positive film keeps the shared spray anchor"),
        Surface->SampleVisibleCarrierAtRiverCoordinates(GroundField,Point));
    Ground->SetActorLocation(FVector(GroundProbe.X,GroundProbe.Y,WaterZ));
    GroundMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TestTrue(TEXT("disabled ground collision cannot occlude contact"),
        Surface->SampleCartesianCarrierSupport(GroundProbe,Height,bWet) && bWet);
    Mesh->SetVisibility(false);
    TestFalse(TEXT("hidden carrier does not supply stale support"),Surface->SampleCartesianCarrierSupport(DryWorld,Height,bWet));
    return true;
}
#endif
#endif
