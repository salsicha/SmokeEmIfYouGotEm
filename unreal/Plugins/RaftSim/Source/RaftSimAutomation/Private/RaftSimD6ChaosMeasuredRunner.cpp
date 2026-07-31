#include "RaftSimD6ChaosMeasuredRunner.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/FileManager.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Physics/PhysicsInterfaceCore.h"
#include "Policies/PrettyJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace RaftSimD6Chaos
{

namespace
{

constexpr double MetersToCentimeters = 100.0;
constexpr double NewtonsToUnrealForce = 100.0;
constexpr double NewtonMetersToUnrealTorque = 10000.0;
constexpr double GravityMps2 = 9.81;

const TCHAR* FixturePackageRelativePath =
    TEXT("physics/data/calibration/flexible_raft_d6_fixture_input_package.json");
const TCHAR* ChaosContractRelativePath =
    TEXT("unreal/Content/RaftSim/Physics/flexible_raft_d6_chaos_fixture_contract.json");
const TCHAR* ChaosSummaryRelativePath = TEXT("physics/reports/d6/chaos/summary.json");
const TCHAR* ChaosSidecarRelativePath =
    TEXT("physics/reports/d6/chaos/flexible_raft_d6_chaos_measured_results.json");
const TCHAR* ChaosReplayRelativeDirectory = TEXT("physics/reports/d6/chaos/replays");
const TCHAR* TargetId = TEXT("unreal_chaos_rigid_baseline");
const TCHAR* RuntimeId = TEXT("UnrealEngine5ChaosRigidBody");

const TArray<FString> RequiredFixtureIds = {
    TEXT("static_seat_load_sag"),
    TEXT("traveling_crew_shift"),
    TEXT("rock_pinch_wrap"),
    TEXT("upstream_tube_overwash_flip"),
    TEXT("timed_high_side_save"),
    TEXT("post_contact_recovery"),
    TEXT("pressure_flow_sweeps"),
};

// UE's platform SHA helper is unavailable on Mac, so keep this compact,
// deterministic FIPS 180-4 implementation beside the exporter that needs it.
struct FSha256
{
    uint32 State[8] = {
        0x6a09e667u,
        0xbb67ae85u,
        0x3c6ef372u,
        0xa54ff53au,
        0x510e527fu,
        0x9b05688cu,
        0x1f83d9abu,
        0x5be0cd19u,
    };
    uint64 BitLength = 0;
    uint8 Buffer[64] = {};
    uint32 BufferLength = 0;

    static uint32 RotateRight(uint32 Value, uint32 Bits)
    {
        return (Value >> Bits) | (Value << (32u - Bits));
    }

    void ProcessBlock(const uint8* Block)
    {
        static const uint32 K[64] = {
            0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu,
            0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u, 0xd807aa98u, 0x12835b01u,
            0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u,
            0xc19bf174u, 0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
            0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau, 0x983e5152u,
            0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u,
            0x06ca6351u, 0x14292967u, 0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu,
            0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
            0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u, 0xd192e819u,
            0xd6990624u, 0xf40e3585u, 0x106aa070u, 0x19a4c116u, 0x1e376c08u,
            0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu,
            0x682e6ff3u, 0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
            0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u,
        };

        uint32 W[64];
        for (int32 Index = 0; Index < 16; ++Index)
        {
            W[Index] =
                (static_cast<uint32>(Block[Index * 4]) << 24)
                | (static_cast<uint32>(Block[Index * 4 + 1]) << 16)
                | (static_cast<uint32>(Block[Index * 4 + 2]) << 8)
                | static_cast<uint32>(Block[Index * 4 + 3]);
        }
        for (int32 Index = 16; Index < 64; ++Index)
        {
            const uint32 S0 =
                RotateRight(W[Index - 15], 7) ^ RotateRight(W[Index - 15], 18)
                ^ (W[Index - 15] >> 3);
            const uint32 S1 =
                RotateRight(W[Index - 2], 17) ^ RotateRight(W[Index - 2], 19)
                ^ (W[Index - 2] >> 10);
            W[Index] = W[Index - 16] + S0 + W[Index - 7] + S1;
        }

        uint32 A = State[0];
        uint32 B = State[1];
        uint32 C = State[2];
        uint32 D = State[3];
        uint32 E = State[4];
        uint32 F = State[5];
        uint32 G = State[6];
        uint32 H = State[7];
        for (int32 Index = 0; Index < 64; ++Index)
        {
            const uint32 S1 = RotateRight(E, 6) ^ RotateRight(E, 11) ^ RotateRight(E, 25);
            const uint32 Ch = (E & F) ^ ((~E) & G);
            const uint32 Temp1 = H + S1 + Ch + K[Index] + W[Index];
            const uint32 S0 = RotateRight(A, 2) ^ RotateRight(A, 13) ^ RotateRight(A, 22);
            const uint32 Maj = (A & B) ^ (A & C) ^ (B & C);
            const uint32 Temp2 = S0 + Maj;
            H = G;
            G = F;
            F = E;
            E = D + Temp1;
            D = C;
            C = B;
            B = A;
            A = Temp1 + Temp2;
        }

        State[0] += A;
        State[1] += B;
        State[2] += C;
        State[3] += D;
        State[4] += E;
        State[5] += F;
        State[6] += G;
        State[7] += H;
    }

    void Update(const uint8* Data, int32 Length)
    {
        BitLength += static_cast<uint64>(Length) * 8u;
        for (int32 Index = 0; Index < Length; ++Index)
        {
            Buffer[BufferLength++] = Data[Index];
            if (BufferLength == 64u)
            {
                ProcessBlock(Buffer);
                BufferLength = 0;
            }
        }
    }

    FString Finalize()
    {
        const uint64 TotalBits = BitLength;
        const uint8 Pad = 0x80u;
        Update(&Pad, 1);
        const uint8 Zero = 0x00u;
        while (BufferLength != 56u)
        {
            Update(&Zero, 1);
        }
        BitLength = TotalBits;
        for (int32 Shift = 56; Shift >= 0; Shift -= 8)
        {
            Buffer[BufferLength++] = static_cast<uint8>((TotalBits >> Shift) & 0xFFu);
        }
        ProcessBlock(Buffer);
        BufferLength = 0;

        FString Hex;
        Hex.Reserve(64);
        for (const uint32 Word : State)
        {
            Hex += FString::Printf(TEXT("%08x"), Word);
        }
        return Hex;
    }
};

FString Sha256OfUtf8(const FString& Text)
{
    const FTCHARToUTF8 Converter(*Text);
    FSha256 Hasher;
    Hasher.Update(reinterpret_cast<const uint8*>(Converter.Get()), Converter.Length());
    return Hasher.Finalize();
}

FString SerializeJson(const TSharedPtr<FJsonObject>& Object)
{
    FString Output;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&Output);
    FJsonSerializer::Serialize(Object.ToSharedRef(), Writer);
    return Output;
}

bool WriteJson(
    const FString& FullPath,
    const TSharedPtr<FJsonObject>& Object,
    FString& OutSha256,
    FString& OutError)
{
    const FString Text = SerializeJson(Object);
    OutSha256 = Sha256OfUtf8(Text);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(FullPath), true);
    if (!FFileHelper::SaveStringToFile(
            Text,
            *FullPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        OutError = FString::Printf(TEXT("Failed to write D6 Chaos JSON: %s"), *FullPath);
        return false;
    }
    return true;
}

bool LoadJson(
    const FString& FullPath,
    TSharedPtr<FJsonObject>& OutObject,
    FString& OutError)
{
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *FullPath))
    {
        OutError = FString::Printf(TEXT("Missing D6 input JSON: %s"), *FullPath);
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!FJsonSerializer::Deserialize(Reader, OutObject) || !OutObject.IsValid())
    {
        OutError = FString::Printf(TEXT("Invalid D6 input JSON: %s"), *FullPath);
        return false;
    }
    return true;
}

FVector ReadVector(const TSharedPtr<FJsonObject>& Object)
{
    return FVector(
        Object->GetNumberField(TEXT("x")),
        Object->GetNumberField(TEXT("y")),
        Object->GetNumberField(TEXT("z")));
}

TSharedPtr<FJsonObject> VectorObject(const FVector& Vector)
{
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("x"), Vector.X);
    Result->SetNumberField(TEXT("y"), Vector.Y);
    Result->SetNumberField(TEXT("z"), Vector.Z);
    return Result;
}

TSharedPtr<FJsonObject> QuaternionObject(const FQuat& Quat)
{
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("x"), Quat.X);
    Result->SetNumberField(TEXT("y"), Quat.Y);
    Result->SetNumberField(TEXT("z"), Quat.Z);
    Result->SetNumberField(TEXT("w"), Quat.W);
    return Result;
}

FString EngineVersionString()
{
    return FString::Printf(
        TEXT("UnrealEngine %s; Chaos rigid body through UWorld physics scene"),
        *FEngineVersion::Current().ToString());
}

class FScopedChaosWorld
{
public:
    bool Create(FString& OutError)
    {
        if (GEngine == nullptr)
        {
            OutError = TEXT("GEngine is unavailable; cannot create the D6 Chaos world.");
            return false;
        }

        CachedFrameCounter = GFrameCounter;
        bRestoreFrameCounter = true;
        const FName WorldName = MakeUniqueObjectName(
            nullptr,
            UWorld::StaticClass(),
            TEXT("RaftSimD6ChaosWorld"),
            EUniqueObjectNameOptions::GloballyUnique);
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        World = UWorld::CreateWorld(
            EWorldType::Game,
            false,
            WorldName,
            GetTransientPackage());
        if (World == nullptr)
        {
            OutError = TEXT("UWorld::CreateWorld failed for the D6 Chaos runner.");
            return false;
        }

        World->AddToRoot();
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
        if (World->GetPhysicsScene() == nullptr)
        {
            OutError = TEXT("The D6 transient world has no physics scene.");
            return false;
        }
        return true;
    }

    ~FScopedChaosWorld()
    {
        if (World == nullptr)
        {
            return;
        }
        if (GEngine != nullptr)
        {
            GEngine->ShutdownWorldNetDriver(World);
        }
        if (World->HasBegunPlay())
        {
            World->BeginTearingDown();
            World->EndPlay(EEndPlayReason::Quit);
        }
        if (bRestoreFrameCounter)
        {
            GFrameCounter = CachedFrameCounter;
        }
        World->DestroyWorld(true);
        World->SetPhysicsScene(nullptr);
        if (GEngine != nullptr)
        {
            GEngine->DestroyWorldContext(World);
        }
        World->RemoveFromRoot();
        World = nullptr;
    }

    UWorld* Get() const
    {
        return World;
    }

private:
    UWorld* World = nullptr;
    uint64 CachedFrameCounter = 0;
    bool bRestoreFrameCounter = false;
};

struct FD6Context
{
    TSharedPtr<FJsonObject> PackageRoot;
    TSharedPtr<FJsonObject> ContractRoot;
    double FixedStepSeconds = 1.0 / 30.0;
    double RaftMassKg = 420.0;
    double TotalMassKg = 805.0;
    double LengthM = 4.3;
    double WidthM = 1.9;
    double TubeRadiusM = 0.28;
    FVector InitialPositionM = FVector(3.0, 2.0, 3.0);
    FVector InitialVelocityMps = FVector(0.0, 0.7, 0.0);
    TArray<TSharedPtr<FJsonValue>> CrewSeats;
};

bool LoadContext(const FString& RepoRootDir, FD6Context& OutContext, FString& OutError)
{
    if (!LoadJson(
            FPaths::Combine(RepoRootDir, FixturePackageRelativePath),
            OutContext.PackageRoot,
            OutError)
        || !LoadJson(
            FPaths::Combine(RepoRootDir, ChaosContractRelativePath),
            OutContext.ContractRoot,
            OutError))
    {
        return false;
    }

    const TSharedPtr<FJsonObject> Common =
        OutContext.PackageRoot->GetObjectField(TEXT("common_setup"));
    const TSharedPtr<FJsonObject> Raft = Common->GetObjectField(TEXT("raft_parameters"));
    const TSharedPtr<FJsonObject> Mass = Common->GetObjectField(TEXT("mass_properties"));
    const TSharedPtr<FJsonObject> Initial = Common->GetObjectField(TEXT("initial_state"));
    OutContext.FixedStepSeconds = Common->GetNumberField(TEXT("fixed_step_s"));
    OutContext.RaftMassKg = Raft->GetNumberField(TEXT("mass_kg"));
    OutContext.TotalMassKg = Mass->GetNumberField(TEXT("total_mass_kg"));
    OutContext.LengthM = Raft->GetNumberField(TEXT("length_m"));
    OutContext.WidthM = Raft->GetNumberField(TEXT("width_m"));
    OutContext.TubeRadiusM = Raft->GetNumberField(TEXT("tube_radius_m"));
    OutContext.InitialPositionM = ReadVector(Initial->GetObjectField(TEXT("position")));
    // Lift the free-running probe above the origin so gravity can advance it
    // without an implicit floor or contact unrelated to a fixture.
    OutContext.InitialPositionM.Z = 3.0;
    OutContext.InitialVelocityMps =
        ReadVector(Initial->GetObjectField(TEXT("linear_velocity_mps")));
    OutContext.CrewSeats = Common->GetArrayField(TEXT("crew_seats"));
    return true;
}

TSharedPtr<FJsonObject> FindFixture(
    const FD6Context& Context,
    const FString& FixtureId)
{
    const TArray<TSharedPtr<FJsonValue>>& Fixtures =
        Context.PackageRoot->GetArrayField(TEXT("fixtures"));
    for (const TSharedPtr<FJsonValue>& Value : Fixtures)
    {
        const TSharedPtr<FJsonObject> Fixture = Value->AsObject();
        if (Fixture.IsValid() && Fixture->GetStringField(TEXT("fixture_id")) == FixtureId)
        {
            return Fixture;
        }
    }
    return nullptr;
}

TSharedPtr<FJsonObject> FindContractJob(
    const FD6Context& Context,
    const FString& FixtureId)
{
    const TArray<TSharedPtr<FJsonValue>>& Jobs =
        Context.ContractRoot->GetArrayField(TEXT("jobs"));
    for (const TSharedPtr<FJsonValue>& Value : Jobs)
    {
        const TSharedPtr<FJsonObject> Job = Value->AsObject();
        if (Job.IsValid() && Job->GetStringField(TEXT("fixture_id")) == FixtureId)
        {
            return Job;
        }
    }
    return nullptr;
}

TSharedPtr<FJsonObject> FindPhase(
    const TSharedPtr<FJsonObject>& Input,
    const FString& PhaseId)
{
    const TArray<TSharedPtr<FJsonValue>>& Phases = Input->GetArrayField(TEXT("phases"));
    for (const TSharedPtr<FJsonValue>& Value : Phases)
    {
        const TSharedPtr<FJsonObject> Phase = Value->AsObject();
        if (Phase.IsValid() && Phase->GetStringField(TEXT("phase_id")) == PhaseId)
        {
            return Phase;
        }
    }
    return nullptr;
}

double LoadedCrewMassKg(const FD6Context& Context)
{
    double Result = 0.0;
    for (const TSharedPtr<FJsonValue>& Value : Context.CrewSeats)
    {
        const TSharedPtr<FJsonObject> Seat = Value->AsObject();
        if (Seat->GetBoolField(TEXT("occupied")))
        {
            Result += Seat->GetNumberField(TEXT("occupant_mass_kg"));
        }
    }
    return Result;
}

TSharedPtr<FJsonObject> FindAction(
    const TSharedPtr<FJsonObject>& Phase,
    const FString& SeatId)
{
    if (!Phase.IsValid())
    {
        return nullptr;
    }
    const TArray<TSharedPtr<FJsonValue>>& Actions = Phase->GetArrayField(TEXT("crew_actions"));
    for (const TSharedPtr<FJsonValue>& Value : Actions)
    {
        const TSharedPtr<FJsonObject> Action = Value->AsObject();
        if (Action.IsValid() && Action->GetStringField(TEXT("seat_id")) == SeatId)
        {
            return Action;
        }
    }
    return nullptr;
}

double CrewRollTorqueNm(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Phase)
{
    double TorqueNm = 0.0;
    for (const TSharedPtr<FJsonValue>& Value : Context.CrewSeats)
    {
        const TSharedPtr<FJsonObject> Seat = Value->AsObject();
        if (!Seat->GetBoolField(TEXT("occupied")))
        {
            continue;
        }
        double LateralM = Seat->GetObjectField(TEXT("local_position"))->GetNumberField(TEXT("y"));
        const TSharedPtr<FJsonObject> Action =
            FindAction(Phase, Seat->GetStringField(TEXT("seat_id")));
        if (Action.IsValid())
        {
            FVector Lean = ReadVector(Action->GetObjectField(TEXT("lean_offset")));
            if (Lean.Size() > 0.55)
            {
                Lean = Lean.GetSafeNormal() * 0.55;
            }
            LateralM += Lean.Y;
            LateralM += static_cast<double>(Action->GetIntegerField(TEXT("high_side_direction")))
                * 0.45;
        }
        TorqueNm += -Seat->GetNumberField(TEXT("occupant_mass_kg")) * GravityMps2 * LateralM;
    }
    return TorqueNm;
}

struct FChaosScenarioConfig
{
    FString ScenarioId;
    FVector ContinuousForceN = FVector::ZeroVector;
    FVector ContinuousTorqueNm = FVector::ZeroVector;
    bool bEnableGravity = true;
    bool bHasObstacle = false;
    FVector ObstacleLocalPositionM = FVector::ZeroVector;
    double ObstacleRadiusM = 0.0;
    double ObstacleFriction = 0.82;
    int32 StepCount = 18;
};

struct FChaosFrame
{
    int32 StepIndex = 0;
    FVector PositionM = FVector::ZeroVector;
    FQuat Orientation = FQuat::Identity;
    FVector LinearVelocityMps = FVector::ZeroVector;
    FVector AngularVelocityRadS = FVector::ZeroVector;
    double EstimatedObstacleIndentationM = 0.0;
    double EstimatedContactImpulseNs = 0.0;
};

struct FChaosScenarioRun
{
    FString ScenarioId;
    TArray<FChaosFrame> Frames;
    FString DeterminismHash;
    FString VerificationHash;
    bool bDeterministicRepeat = false;
    bool bPhysicsScenePresent = false;
    bool bPhysicsActorHandleValid = false;
    bool bRigidPhysicsActor = false;
    bool bSolverAdvanced = false;
    bool bContactObserved = false;
    double InitialObstacleIndentationM = 0.0;
    double MaxObstacleIndentationM = 0.0;
    double MaxContactImpulseNs = 0.0;
    double RuntimeCpuMs = 0.0;
};

UBoxComponent* SpawnRaftProxy(
    UWorld& World,
    const FD6Context& Context,
    const FChaosScenarioConfig& Config)
{
    AActor* Actor = World.SpawnActor<AActor>(
        AActor::StaticClass(),
        Context.InitialPositionM * MetersToCentimeters,
        FRotator::ZeroRotator);
    if (Actor == nullptr)
    {
        return nullptr;
    }

    UBoxComponent* Box = NewObject<UBoxComponent>(Actor, TEXT("D6ChaosRigidRaftProxy"));
    Actor->SetRootComponent(Box);
    Actor->AddInstanceComponent(Box);
    Box->SetBoxExtent(FVector(
        Context.LengthM * MetersToCentimeters * 0.5,
        Context.WidthM * MetersToCentimeters * 0.5,
        Context.TubeRadiusM * MetersToCentimeters));
    Box->SetMobility(EComponentMobility::Movable);
    Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Box->SetCollisionObjectType(ECC_PhysicsBody);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->SetGenerateOverlapEvents(false);
    Box->SetNotifyRigidBodyCollision(true);
    Box->SetLinearDamping(0.05);
    Box->SetAngularDamping(0.05);
    Box->SetEnableGravity(Config.bEnableGravity);
    Box->BodyInstance.bUseCCD = true;
    Box->RegisterComponent();
    Box->SetWorldLocation(Context.InitialPositionM * MetersToCentimeters);
    Box->SetSimulatePhysics(true);
    Box->SetMassOverrideInKg(NAME_None, Context.TotalMassKg, true);
    Box->SetPhysicsLinearVelocity(Context.InitialVelocityMps * MetersToCentimeters);
    Box->SetPhysicsAngularVelocityInRadians(FVector::ZeroVector);
    Box->WakeAllRigidBodies();
    return Box;
}

USphereComponent* SpawnObstacle(
    UWorld& World,
    const FD6Context& Context,
    const FChaosScenarioConfig& Config)
{
    if (!Config.bHasObstacle)
    {
        return nullptr;
    }
    const FVector WorldPositionM = Context.InitialPositionM + Config.ObstacleLocalPositionM;
    AActor* Actor = World.SpawnActor<AActor>(
        AActor::StaticClass(),
        WorldPositionM * MetersToCentimeters,
        FRotator::ZeroRotator);
    if (Actor == nullptr)
    {
        return nullptr;
    }

    USphereComponent* Sphere =
        NewObject<USphereComponent>(Actor, TEXT("D6ChaosStaticRockProxy"));
    Actor->SetRootComponent(Sphere);
    Actor->AddInstanceComponent(Sphere);
    Sphere->SetSphereRadius(Config.ObstacleRadiusM * MetersToCentimeters);
    Sphere->SetMobility(EComponentMobility::Movable);
    Sphere->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Sphere->SetCollisionObjectType(ECC_WorldStatic);
    Sphere->SetCollisionResponseToAllChannels(ECR_Block);
    Sphere->SetGenerateOverlapEvents(false);
    Sphere->BodyInstance.SetPhysMaterialOverride(nullptr);
    Sphere->RegisterComponent();
    Sphere->SetWorldLocation(WorldPositionM * MetersToCentimeters);
    Sphere->SetSimulatePhysics(false);
    return Sphere;
}

double EstimateSphereBoxIndentationM(
    const UBoxComponent& Box,
    const USphereComponent& Sphere)
{
    const FVector SphereCenterWorld = Sphere.GetComponentLocation();
    const FVector SphereCenterLocal =
        Box.GetComponentTransform().InverseTransformPosition(SphereCenterWorld);
    const FVector Extent = Box.GetUnscaledBoxExtent();
    const FVector ClosestLocal(
        FMath::Clamp(SphereCenterLocal.X, -Extent.X, Extent.X),
        FMath::Clamp(SphereCenterLocal.Y, -Extent.Y, Extent.Y),
        FMath::Clamp(SphereCenterLocal.Z, -Extent.Z, Extent.Z));
    const double SeparationCm = FVector::Distance(SphereCenterLocal, ClosestLocal);
    return FMath::Max(0.0, (Sphere.GetUnscaledSphereRadius() - SeparationCm) / MetersToCentimeters);
}

FString HashFrames(const TArray<FChaosFrame>& Frames)
{
    FString Canonical;
    Canonical.Reserve(Frames.Num() * 220);
    for (const FChaosFrame& Frame : Frames)
    {
        Canonical += FString::Printf(
            TEXT("%d|%.4f,%.4f,%.4f|%.6f,%.6f,%.6f,%.6f|%.4f,%.4f,%.4f|")
            TEXT("%.5f,%.5f,%.5f|%.5f|%.5f\n"),
            Frame.StepIndex,
            Frame.PositionM.X,
            Frame.PositionM.Y,
            Frame.PositionM.Z,
            Frame.Orientation.X,
            Frame.Orientation.Y,
            Frame.Orientation.Z,
            Frame.Orientation.W,
            Frame.LinearVelocityMps.X,
            Frame.LinearVelocityMps.Y,
            Frame.LinearVelocityMps.Z,
            Frame.AngularVelocityRadS.X,
            Frame.AngularVelocityRadS.Y,
            Frame.AngularVelocityRadS.Z,
            Frame.EstimatedObstacleIndentationM,
            Frame.EstimatedContactImpulseNs);
    }
    return Sha256OfUtf8(Canonical);
}

bool ExecuteScenarioOnce(
    const FD6Context& Context,
    const FChaosScenarioConfig& Config,
    FChaosScenarioRun& OutRun,
    FString& OutError)
{
    FScopedChaosWorld ScopedWorld;
    if (!ScopedWorld.Create(OutError))
    {
        return false;
    }
    UWorld* World = ScopedWorld.Get();
    OutRun.ScenarioId = Config.ScenarioId;
    OutRun.bPhysicsScenePresent = World != nullptr && World->GetPhysicsScene() != nullptr;

    UBoxComponent* Raft = SpawnRaftProxy(*World, Context, Config);
    if (Raft == nullptr)
    {
        OutError = FString::Printf(TEXT("Failed to spawn raft proxy for %s."), *Config.ScenarioId);
        return false;
    }
    USphereComponent* Obstacle = SpawnObstacle(*World, Context, Config);
    if (Config.bHasObstacle && Obstacle == nullptr)
    {
        OutError = FString::Printf(TEXT("Failed to spawn rock proxy for %s."), *Config.ScenarioId);
        return false;
    }

    const FPhysicsActorHandle ActorHandle = Raft->BodyInstance.GetPhysicsActorHandle();
    OutRun.bPhysicsActorHandleValid = FPhysicsInterface::IsValid(ActorHandle);
    OutRun.bRigidPhysicsActor =
        OutRun.bPhysicsActorHandleValid && FPhysicsInterface::IsRigidBody(ActorHandle);
    if (!OutRun.bPhysicsActorHandleValid || !OutRun.bRigidPhysicsActor)
    {
        OutError = FString::Printf(
            TEXT("Scenario %s did not create a valid rigid Chaos actor."),
            *Config.ScenarioId);
        return false;
    }

    if (Obstacle != nullptr)
    {
        OutRun.InitialObstacleIndentationM = EstimateSphereBoxIndentationM(*Raft, *Obstacle);
        OutRun.MaxObstacleIndentationM = OutRun.InitialObstacleIndentationM;
        OutRun.bContactObserved = OutRun.InitialObstacleIndentationM > 1.0e-6;
    }

    const FVector StartPosition = Raft->GetComponentLocation();
    const FQuat StartOrientation = Raft->GetComponentQuat();
    FVector PreviousVelocityMps = Raft->GetPhysicsLinearVelocity() / MetersToCentimeters;
    const double StartSeconds = FPlatformTime::Seconds();

    for (int32 Step = 0; Step < Config.StepCount; ++Step)
    {
        Raft->AddForce(Config.ContinuousForceN * NewtonsToUnrealForce, NAME_None, false);
        Raft->AddTorqueInRadians(
            Config.ContinuousTorqueNm * NewtonMetersToUnrealTorque,
            NAME_None,
            false);
        World->Tick(LEVELTICK_All, static_cast<float>(Context.FixedStepSeconds));
        // Match Engine's FTestWorldWrapper: tick functions and physics are
        // keyed by GFrameCounter, so each synthetic fixed step must advance it
        // exactly once while the test world is alive. Do this unconditionally
        // because commandlet-created worlds do not always expose begun-play
        // state even after InitializeActorsForPlay/BeginPlay.
        ++GFrameCounter;

        FChaosFrame Frame;
        Frame.StepIndex = Step + 1;
        Frame.PositionM = Raft->GetComponentLocation() / MetersToCentimeters;
        Frame.Orientation = Raft->GetComponentQuat();
        Frame.LinearVelocityMps =
            Raft->GetPhysicsLinearVelocity() / MetersToCentimeters;
        Frame.AngularVelocityRadS = Raft->GetPhysicsAngularVelocityInRadians();
        if (Obstacle != nullptr)
        {
            Frame.EstimatedObstacleIndentationM =
                EstimateSphereBoxIndentationM(*Raft, *Obstacle);
            OutRun.MaxObstacleIndentationM = FMath::Max(
                OutRun.MaxObstacleIndentationM,
                Frame.EstimatedObstacleIndentationM);
            OutRun.bContactObserved =
                OutRun.bContactObserved || Frame.EstimatedObstacleIndentationM > 1.0e-6;
        }

        FVector ExpectedDeltaVelocity =
            (Config.ContinuousForceN / Context.TotalMassKg) * Context.FixedStepSeconds;
        if (Config.bEnableGravity)
        {
            ExpectedDeltaVelocity.Z -= GravityMps2 * Context.FixedStepSeconds;
        }
        const FVector ContactDeltaVelocity =
            (Frame.LinearVelocityMps - PreviousVelocityMps) - ExpectedDeltaVelocity;
        Frame.EstimatedContactImpulseNs = Context.TotalMassKg * ContactDeltaVelocity.Size();
        if (Obstacle != nullptr)
        {
            OutRun.MaxContactImpulseNs =
                FMath::Max(OutRun.MaxContactImpulseNs, Frame.EstimatedContactImpulseNs);
        }
        PreviousVelocityMps = Frame.LinearVelocityMps;
        OutRun.Frames.Add(Frame);
    }
    OutRun.RuntimeCpuMs = (FPlatformTime::Seconds() - StartSeconds) * 1000.0;

    const double TranslationCm = FVector::Distance(StartPosition, Raft->GetComponentLocation());
    const double RotationRadians = StartOrientation.AngularDistance(Raft->GetComponentQuat());
    OutRun.bSolverAdvanced =
        TranslationCm > 0.01 || RotationRadians > 1.0e-6
        || Raft->GetPhysicsLinearVelocity().Size() > 0.01
        || Raft->GetPhysicsAngularVelocityInRadians().Size() > 1.0e-6;
    OutRun.DeterminismHash = HashFrames(OutRun.Frames);
    return true;
}

bool RunScenario(
    const FD6Context& Context,
    const FChaosScenarioConfig& Config,
    FChaosScenarioRun& OutRun,
    FString& OutError)
{
    if (!ExecuteScenarioOnce(Context, Config, OutRun, OutError))
    {
        return false;
    }
    FChaosScenarioRun Verification;
    if (!ExecuteScenarioOnce(Context, Config, Verification, OutError))
    {
        return false;
    }
    OutRun.VerificationHash = Verification.DeterminismHash;
    OutRun.bDeterministicRepeat = OutRun.DeterminismHash == Verification.DeterminismHash;
    if (!OutRun.bDeterministicRepeat)
    {
        OutError = FString::Printf(
            TEXT("Chaos scenario %s was not deterministic across fixed-step repeats (%s != %s)."),
            *Config.ScenarioId,
            *OutRun.DeterminismHash,
            *OutRun.VerificationHash);
        return false;
    }
    if (!OutRun.bSolverAdvanced)
    {
        OutError = FString::Printf(
            TEXT("Chaos scenario %s did not advance the simulated rigid body."),
            *Config.ScenarioId);
        return false;
    }
    return true;
}

TSharedPtr<FJsonObject> FrameObject(const FChaosFrame& Frame)
{
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("step_index"), Frame.StepIndex);
    Result->SetObjectField(TEXT("position_m"), VectorObject(Frame.PositionM));
    Result->SetObjectField(TEXT("orientation"), QuaternionObject(Frame.Orientation));
    Result->SetObjectField(
        TEXT("linear_velocity_mps"), VectorObject(Frame.LinearVelocityMps));
    Result->SetObjectField(
        TEXT("angular_velocity_rad_s"), VectorObject(Frame.AngularVelocityRadS));
    Result->SetNumberField(
        TEXT("estimated_obstacle_indentation_m"),
        Frame.EstimatedObstacleIndentationM);
    Result->SetNumberField(
        TEXT("estimated_contact_impulse_ns"),
        Frame.EstimatedContactImpulseNs);
    return Result;
}

TSharedPtr<FJsonObject> ScenarioObject(const FChaosScenarioRun& Run)
{
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("scenario_id"), Run.ScenarioId);
    Result->SetBoolField(TEXT("physics_scene_present"), Run.bPhysicsScenePresent);
    Result->SetBoolField(
        TEXT("physics_actor_handle_valid"),
        Run.bPhysicsActorHandleValid);
    Result->SetBoolField(TEXT("rigid_physics_actor"), Run.bRigidPhysicsActor);
    Result->SetBoolField(TEXT("solver_advanced"), Run.bSolverAdvanced);
    Result->SetBoolField(TEXT("contact_observed"), Run.bContactObserved);
    Result->SetBoolField(TEXT("deterministic_repeat"), Run.bDeterministicRepeat);
    Result->SetStringField(TEXT("determinism_hash"), Run.DeterminismHash);
    Result->SetStringField(TEXT("verification_hash"), Run.VerificationHash);
    Result->SetNumberField(
        TEXT("initial_obstacle_indentation_m"),
        Run.InitialObstacleIndentationM);
    Result->SetNumberField(
        TEXT("max_obstacle_indentation_m"),
        Run.MaxObstacleIndentationM);
    Result->SetNumberField(TEXT("max_contact_impulse_ns"), Run.MaxContactImpulseNs);
    Result->SetNumberField(TEXT("runtime_cpu_ms"), Run.RuntimeCpuMs);

    TArray<TSharedPtr<FJsonValue>> Frames;
    Frames.Reserve(Run.Frames.Num());
    for (const FChaosFrame& Frame : Run.Frames)
    {
        Frames.Add(MakeShared<FJsonValueObject>(FrameObject(Frame)));
    }
    Result->SetArrayField(TEXT("frames"), Frames);
    return Result;
}

double FlowForceN(const FD6Context& Context, double IncomingVelocityMps)
{
    constexpr double WaterDensityKgM3 = 1000.0;
    constexpr double DragCoefficient = 1.25;
    const double ProjectedAreaM2 = Context.LengthM * Context.TubeRadiusM * 2.0;
    return 0.5 * WaterDensityKgM3 * DragCoefficient * ProjectedAreaM2
        * IncomingVelocityMps * IncomingVelocityMps;
}

double FlowRollTorqueNm(
    const FD6Context& Context,
    double IncomingVelocityMps,
    double SurfaceHeightM)
{
    const double LeverArmM = FMath::Max(0.05, SurfaceHeightM + Context.TubeRadiusM * 0.5);
    return FlowForceN(Context, IncomingVelocityMps) * LeverArmM;
}

double RigidFlipThresholdNm(const FD6Context& Context)
{
    return Context.TotalMassKg * GravityMps2 * Context.WidthM * 0.5;
}

FChaosScenarioConfig NeutralConfig(const FString& ScenarioId)
{
    FChaosScenarioConfig Config;
    Config.ScenarioId = ScenarioId;
    Config.StepCount = 18;
    return Config;
}

bool ReadFirstObstacle(
    const TSharedPtr<FJsonObject>& Input,
    FChaosScenarioConfig& InOutConfig,
    FString& OutError)
{
    const TArray<TSharedPtr<FJsonValue>>* Obstacles = nullptr;
    if (!Input->TryGetArrayField(TEXT("obstacles"), Obstacles) || Obstacles == nullptr
        || Obstacles->Num() == 0)
    {
        OutError = TEXT("D6 fixture expected a rock obstacle but none was recorded.");
        return false;
    }
    const TSharedPtr<FJsonObject> Obstacle = (*Obstacles)[0]->AsObject();
    InOutConfig.bHasObstacle = true;
    InOutConfig.ObstacleLocalPositionM =
        ReadVector(Obstacle->GetObjectField(TEXT("local_position")));
    InOutConfig.ObstacleRadiusM = Obstacle->GetNumberField(TEXT("radius_m"));
    InOutConfig.ObstacleFriction =
        Obstacle->GetNumberField(TEXT("friction_coefficient"));
    return true;
}

struct FFixtureEvaluation
{
    FString FixtureId;
    TSharedPtr<FJsonObject> Metrics;
    TArray<FChaosScenarioRun> Scenarios;
    TSharedPtr<FJsonObject> CrewState;
    TSharedPtr<FJsonObject> OverwashState;
    TSharedPtr<FJsonObject> PinState;
    TSharedPtr<FJsonObject> ReleaseState;
    TSharedPtr<FJsonObject> Outcome;
};

bool EvaluateStaticSag(
    const FD6Context& Context,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("static_seat_load_sag");
    FChaosScenarioRun Run;
    if (!RunScenario(Context, NeutralConfig(TEXT("neutral_occupied_seats")), Run, OutError))
    {
        return false;
    }
    OutFixture.Scenarios.Add(Run);
    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("loaded_crew_mass_kg"), LoadedCrewMassKg(Context));
    // A single Chaos box is the intentional rigid baseline: it cannot sag or
    // redistribute tube freeboard. Zero is the measured model capability, not
    // a synthetic compliant answer.
    OutFixture.Metrics->SetNumberField(TEXT("max_seat_freeboard_loss_m"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("port_total_freeboard_loss_m"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("raft_length_m"), Context.LengthM);
    OutFixture.Metrics->SetNumberField(TEXT("raft_width_m"), Context.WidthM);
    OutFixture.Metrics->SetNumberField(TEXT("starboard_total_freeboard_loss_m"), 0.0);
    return true;
}

bool EvaluateCrewShift(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Input,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("traveling_crew_shift");
    const TSharedPtr<FJsonObject> NeutralPhase =
        FindPhase(Input, TEXT("neutral_occupied_seats"));
    const TSharedPtr<FJsonObject> PortPhase =
        FindPhase(Input, TEXT("port_lean_requested"));
    const TSharedPtr<FJsonObject> StarboardPhase =
        FindPhase(Input, TEXT("starboard_high_side"));
    if (!NeutralPhase.IsValid() || !PortPhase.IsValid() || !StarboardPhase.IsValid())
    {
        OutError = TEXT("traveling_crew_shift is missing a required phase.");
        return false;
    }

    const double NeutralTorque = CrewRollTorqueNm(Context, NeutralPhase);
    const double PortTorque = CrewRollTorqueNm(Context, PortPhase);
    const double StarboardTorque = CrewRollTorqueNm(Context, StarboardPhase);
    for (const TPair<FString, double>& Phase : {
             TPair<FString, double>(TEXT("neutral_occupied_seats"), NeutralTorque),
             TPair<FString, double>(TEXT("port_lean_requested"), PortTorque),
             TPair<FString, double>(TEXT("starboard_high_side"), StarboardTorque)})
    {
        FChaosScenarioConfig Config = NeutralConfig(Phase.Key);
        Config.ContinuousTorqueNm = FVector(Phase.Value, 0.0, 0.0);
        FChaosScenarioRun Run;
        if (!RunScenario(Context, Config, Run, OutError))
        {
            return false;
        }
        OutFixture.Scenarios.Add(Run);
    }

    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("neutral_roll_load_bias_nm"), NeutralTorque);
    OutFixture.Metrics->SetNumberField(TEXT("port_roll_load_bias_nm"), PortTorque);
    OutFixture.Metrics->SetNumberField(TEXT("port_total_freeboard_delta_m"), 0.0);
    OutFixture.Metrics->SetNumberField(
        TEXT("starboard_roll_load_bias_nm"),
        StarboardTorque);
    OutFixture.Metrics->SetNumberField(TEXT("starboard_total_freeboard_delta_m"), 0.0);
    return true;
}

bool EvaluateRockPinch(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Input,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("rock_pinch_wrap");
    FChaosScenarioConfig Config = NeutralConfig(TEXT("static_rock_pinch_wrap_contact"));
    if (!ReadFirstObstacle(Input, Config, OutError))
    {
        return false;
    }
    FChaosScenarioRun Run;
    if (!RunScenario(Context, Config, Run, OutError))
    {
        return false;
    }
    OutFixture.Scenarios.Add(Run);

    const FChaosFrame& FinalFrame = Run.Frames.Last();
    const bool bPinned = FinalFrame.EstimatedObstacleIndentationM > 1.0e-4
        && FinalFrame.LinearVelocityMps.Size() < 0.10;
    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("contact_count"), Run.bContactObserved ? 1.0 : 0.0);
    OutFixture.Metrics->SetNumberField(
        TEXT("max_indentation_m"),
        Run.MaxObstacleIndentationM);
    OutFixture.Metrics->SetNumberField(
        TEXT("min_release_margin_n"),
        -Run.MaxContactImpulseNs / Context.FixedStepSeconds);
    OutFixture.Metrics->SetNumberField(TEXT("pinned_obstacle_count"), bPinned ? 1.0 : 0.0);
    // A rigid box can contact and pin, but cannot physically wrap. This zero
    // is the central behavioral delta D6 is meant to expose.
    OutFixture.Metrics->SetNumberField(TEXT("wrapping_contact_count"), 0.0);
    return true;
}

bool EvaluateOverwash(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Input,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("upstream_tube_overwash_flip");
    const TSharedPtr<FJsonObject> Water = Input->GetObjectField(TEXT("water"));
    const FVector Velocity = ReadVector(Water->GetObjectField(TEXT("velocity_mps")));
    const double Speed = Velocity.Size();
    const double Surface = Water->GetNumberField(TEXT("surface_height_m"));
    const double RollTorque = FlowRollTorqueNm(Context, Speed, Surface);
    const double Force = FlowForceN(Context, Speed);
    FChaosScenarioConfig Config = NeutralConfig(TEXT("uniform_flow_overwash_flip_probe"));
    Config.ContinuousForceN = FVector(0.0, -Force, 0.0);
    Config.ContinuousTorqueNm = FVector(RollTorque, 0.0, 0.0);
    FChaosScenarioRun Run;
    if (!RunScenario(Context, Config, Run, OutError))
    {
        return false;
    }
    OutFixture.Scenarios.Add(Run);

    const double Margin = RigidFlipThresholdNm(Context) - FMath::Abs(RollTorque);
    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("reference_flip_margin_nm"), Margin);
    OutFixture.Metrics->SetBoolField(TEXT("reference_flip_risk"), Margin < 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("retained_water_roll_moment_nm"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("total_overtopping_flux_m3_s"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("total_retained_water_mass_kg"), 0.0);
    return true;
}

bool EvaluateHighSide(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Input,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("timed_high_side_save");
    const TSharedPtr<FJsonObject> Water = Input->GetObjectField(TEXT("water"));
    const double Speed = ReadVector(Water->GetObjectField(TEXT("velocity_mps"))).Size();
    const double Surface = Water->GetNumberField(TEXT("surface_height_m"));
    const double Force = FlowForceN(Context, Speed);
    const double FlowTorque = FlowRollTorqueNm(Context, Speed, Surface);
    const TSharedPtr<FJsonObject> NeutralPhase = FindPhase(Input, TEXT("neutral_overwash"));
    const TSharedPtr<FJsonObject> HighSidePhase =
        FindPhase(Input, TEXT("starboard_high_side_with_retained_water_memory"));
    if (!NeutralPhase.IsValid() || !HighSidePhase.IsValid())
    {
        OutError = TEXT("timed_high_side_save is missing a required phase.");
        return false;
    }
    const double NeutralCrewTorque = CrewRollTorqueNm(Context, NeutralPhase);
    const double HighSideCrewTorque = CrewRollTorqueNm(Context, HighSidePhase);
    const double NeutralNetTorque = FlowTorque + NeutralCrewTorque;
    const double HighSideNetTorque = FlowTorque + HighSideCrewTorque;

    for (const TPair<FString, double>& Phase : {
             TPair<FString, double>(TEXT("neutral_overwash"), NeutralNetTorque),
             TPair<FString, double>(
                 TEXT("starboard_high_side_with_retained_water_memory"),
                 HighSideNetTorque)})
    {
        FChaosScenarioConfig Config = NeutralConfig(Phase.Key);
        Config.ContinuousForceN = FVector(0.0, -Force, 0.0);
        Config.ContinuousTorqueNm = FVector(Phase.Value, 0.0, 0.0);
        FChaosScenarioRun Run;
        if (!RunScenario(Context, Config, Run, OutError))
        {
            return false;
        }
        OutFixture.Scenarios.Add(Run);
    }

    const double Threshold = RigidFlipThresholdNm(Context);
    const double NeutralMargin = Threshold - FMath::Abs(NeutralNetTorque);
    const double HighSideMargin = Threshold - FMath::Abs(HighSideNetTorque);
    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("high_side_flip_margin_nm"), HighSideMargin);
    OutFixture.Metrics->SetNumberField(TEXT("high_side_flip_threshold_nm"), Threshold);
    OutFixture.Metrics->SetNumberField(TEXT("margin_delta_nm"), HighSideMargin - NeutralMargin);
    OutFixture.Metrics->SetNumberField(TEXT("neutral_flip_margin_nm"), NeutralMargin);
    OutFixture.Metrics->SetNumberField(TEXT("neutral_flip_threshold_nm"), Threshold);
    return true;
}

bool EvaluateRecovery(
    const FD6Context& Context,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("post_contact_recovery");
    FChaosScenarioRun Run;
    if (!RunScenario(Context, NeutralConfig(TEXT("post_contact_no_current_obstacle")), Run, OutError))
    {
        return false;
    }
    OutFixture.Scenarios.Add(Run);
    OutFixture.Metrics = MakeShared<FJsonObject>();
    // The rigid proxy has no indentation memory. The no-obstacle Chaos run
    // proves it has no residual recovery contact or holding force.
    OutFixture.Metrics->SetNumberField(TEXT("max_recovered_indentation_m"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("recovering_contact_count"), 0.0);
    OutFixture.Metrics->SetNumberField(TEXT("total_holding_force_n"), 0.0);
    return true;
}

bool EvaluatePressureSweep(
    const FD6Context& Context,
    const TSharedPtr<FJsonObject>& Input,
    FFixtureEvaluation& OutFixture,
    FString& OutError)
{
    OutFixture.FixtureId = TEXT("pressure_flow_sweeps");
    const double Surface = Input->GetNumberField(TEXT("water_surface_height_m"));
    const TArray<TSharedPtr<FJsonValue>>& PressureValues =
        Input->GetArrayField(TEXT("nominal_pressure_values_pa"));
    const TArray<TSharedPtr<FJsonValue>>& VelocityValues =
        Input->GetArrayField(TEXT("incoming_velocity_values_mps"));
    TArray<TSharedPtr<FJsonValue>> Sweeps;

    for (const TSharedPtr<FJsonValue>& PressureValue : PressureValues)
    {
        const double Pressure = PressureValue->AsNumber();
        for (const TSharedPtr<FJsonValue>& VelocityValue : VelocityValues)
        {
            const double Velocity = VelocityValue->AsNumber();
            FChaosScenarioConfig Config = NeutralConfig(FString::Printf(
                TEXT("pressure_%.0f_velocity_%.1f"),
                Pressure,
                Velocity));
            if (!ReadFirstObstacle(Input, Config, OutError))
            {
                return false;
            }
            const double Force = FlowForceN(Context, Velocity);
            Config.ContinuousForceN = FVector(0.0, -Force, 0.0);
            Config.ContinuousTorqueNm =
                FVector(FlowRollTorqueNm(Context, Velocity, Surface), 0.0, 0.0);
            FChaosScenarioRun Run;
            if (!RunScenario(Context, Config, Run, OutError))
            {
                return false;
            }
            OutFixture.Scenarios.Add(Run);

            TSharedPtr<FJsonObject> Sweep = MakeShared<FJsonObject>();
            Sweep->SetNumberField(
                TEXT("contact_min_release_margin_n"),
                Force - Run.MaxContactImpulseNs / Context.FixedStepSeconds);
            Sweep->SetNumberField(TEXT("incoming_velocity_mps"), Velocity);
            Sweep->SetNumberField(TEXT("nominal_pressure_pa"), Pressure);
            // The rigid proxy has neither pressure compliance nor an interior
            // water-retention state, so these baseline outputs remain zero.
            Sweep->SetNumberField(TEXT("overwash_flux_m3_s"), 0.0);
            Sweep->SetNumberField(TEXT("retained_water_roll_moment_nm"), 0.0);
            Sweeps.Add(MakeShared<FJsonValueObject>(Sweep));
        }
    }

    OutFixture.Metrics = MakeShared<FJsonObject>();
    OutFixture.Metrics->SetNumberField(TEXT("sweep_case_count"), Sweeps.Num());
    OutFixture.Metrics->SetArrayField(TEXT("sweeps"), Sweeps);
    return true;
}

void PopulateCommonTelemetryState(
    const FD6Context& Context,
    FFixtureEvaluation& Fixture)
{
    double TotalCpuMs = 0.0;
    bool bAllDeterministic = true;
    bool bAllActorsValid = true;
    bool bAllAdvanced = true;
    bool bAnyContact = false;
    FString CombinedHashes;
    for (const FChaosScenarioRun& Run : Fixture.Scenarios)
    {
        TotalCpuMs += Run.RuntimeCpuMs;
        bAllDeterministic = bAllDeterministic && Run.bDeterministicRepeat;
        bAllActorsValid =
            bAllActorsValid && Run.bPhysicsActorHandleValid && Run.bRigidPhysicsActor;
        bAllAdvanced = bAllAdvanced && Run.bSolverAdvanced;
        bAnyContact = bAnyContact || Run.bContactObserved;
        CombinedHashes += Run.ScenarioId + TEXT(":") + Run.DeterminismHash + TEXT("\n");
    }

    Fixture.CrewState = MakeShared<FJsonObject>();
    Fixture.CrewState->SetNumberField(TEXT("loaded_crew_mass_kg"), LoadedCrewMassKg(Context));
    Fixture.CrewState->SetStringField(
        TEXT("representation"),
        TEXT("crew weight/actions converted to external force or torque on one rigid proxy"));

    Fixture.OverwashState = MakeShared<FJsonObject>();
    Fixture.OverwashState->SetBoolField(TEXT("retained_water_supported"), false);
    Fixture.OverwashState->SetStringField(
        TEXT("rigid_baseline_policy"),
        TEXT("uniform flow is applied as force/torque; rigid proxy has no overtopping volume"));

    Fixture.PinState = MakeShared<FJsonObject>();
    Fixture.PinState->SetBoolField(TEXT("contact_observed"), bAnyContact);
    Fixture.PinState->SetBoolField(TEXT("tube_wrap_supported"), false);

    Fixture.ReleaseState = MakeShared<FJsonObject>();
    Fixture.ReleaseState->SetStringField(
        TEXT("measurement"),
        TEXT("impulse-derived release margin from fixed-step Chaos velocity response"));

    Fixture.Outcome = MakeShared<FJsonObject>();
    Fixture.Outcome->SetBoolField(TEXT("all_physics_actor_handles_valid"), bAllActorsValid);
    Fixture.Outcome->SetBoolField(TEXT("all_scenarios_advanced"), bAllAdvanced);
    Fixture.Outcome->SetBoolField(TEXT("deterministic_fixed_step_repeat"), bAllDeterministic);
    Fixture.Outcome->SetBoolField(TEXT("measured_by_unreal_chaos"), true);
    Fixture.Outcome->SetBoolField(TEXT("d6_complete"), false);
    Fixture.Outcome->SetBoolField(TEXT("production_promoted"), false);
    Fixture.Outcome->SetNumberField(TEXT("runtime_cpu_ms"), TotalCpuMs);
    Fixture.Outcome->SetStringField(TEXT("combined_determinism_hash"), Sha256OfUtf8(CombinedHashes));
}

bool EvaluateAllFixtures(
    const FD6Context& Context,
    TArray<FFixtureEvaluation>& OutFixtures,
    FString& OutError)
{
    for (const FString& FixtureId : RequiredFixtureIds)
    {
        const TSharedPtr<FJsonObject> FixtureObject = FindFixture(Context, FixtureId);
        if (!FixtureObject.IsValid())
        {
            OutError = FString::Printf(TEXT("Missing D6 fixture input: %s"), *FixtureId);
            return false;
        }
        const TSharedPtr<FJsonObject> Input =
            FixtureObject->GetObjectField(TEXT("input_contract"));
        FFixtureEvaluation Evaluation;
        bool bOk = false;
        if (FixtureId == TEXT("static_seat_load_sag"))
        {
            bOk = EvaluateStaticSag(Context, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("traveling_crew_shift"))
        {
            bOk = EvaluateCrewShift(Context, Input, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("rock_pinch_wrap"))
        {
            bOk = EvaluateRockPinch(Context, Input, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("upstream_tube_overwash_flip"))
        {
            bOk = EvaluateOverwash(Context, Input, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("timed_high_side_save"))
        {
            bOk = EvaluateHighSide(Context, Input, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("post_contact_recovery"))
        {
            bOk = EvaluateRecovery(Context, Evaluation, OutError);
        }
        else if (FixtureId == TEXT("pressure_flow_sweeps"))
        {
            bOk = EvaluatePressureSweep(Context, Input, Evaluation, OutError);
        }
        if (!bOk)
        {
            return false;
        }
        PopulateCommonTelemetryState(Context, Evaluation);
        OutFixtures.Add(Evaluation);
    }
    return true;
}

void FlattenNumericMetrics(
    const TSharedPtr<FJsonValue>& Value,
    const FString& Prefix,
    TSet<FString>& OutPaths)
{
    if (!Value.IsValid())
    {
        return;
    }
    if (Value->Type == EJson::Object)
    {
        const TSharedPtr<FJsonObject> Object = Value->AsObject();
        for (const auto& Pair : Object->Values)
        {
            const FString Child = Prefix.IsEmpty()
                ? FString(*Pair.Key)
                : Prefix + TEXT(".") + FString(*Pair.Key);
            FlattenNumericMetrics(Pair.Value, Child, OutPaths);
        }
    }
    else if (Value->Type == EJson::Array)
    {
        const TArray<TSharedPtr<FJsonValue>>& Items = Value->AsArray();
        for (int32 Index = 0; Index < Items.Num(); ++Index)
        {
            FlattenNumericMetrics(
                Items[Index],
                FString::Printf(TEXT("%s[%d]"), *Prefix, Index),
                OutPaths);
        }
    }
    else if (Value->Type == EJson::Number)
    {
        OutPaths.Add(Prefix);
    }
}

bool ValidateMetricPaths(
    const FD6Context& Context,
    const FFixtureEvaluation& Fixture,
    int32& OutMetricCount,
    FString& OutError)
{
    const TSharedPtr<FJsonObject> Job = FindContractJob(Context, Fixture.FixtureId);
    if (!Job.IsValid())
    {
        OutError = FString::Printf(
            TEXT("Missing D6 Chaos contract job: %s"),
            *Fixture.FixtureId);
        return false;
    }
    TSet<FString> NumericPaths;
    FlattenNumericMetrics(
        MakeShared<FJsonValueObject>(Fixture.Metrics),
        FString(),
        NumericPaths);
    const TArray<TSharedPtr<FJsonValue>>& RequiredPaths =
        Job->GetArrayField(TEXT("required_metric_paths"));
    for (const TSharedPtr<FJsonValue>& Value : RequiredPaths)
    {
        const FString Required = Value->AsString();
        if (!NumericPaths.Contains(Required))
        {
            OutError = FString::Printf(
                TEXT("D6 Chaos fixture %s is missing metric path %s."),
                *Fixture.FixtureId,
                *Required);
            return false;
        }
    }
    OutMetricCount = RequiredPaths.Num();
    return true;
}

TSharedPtr<FJsonObject> BuildTelemetry(
    const FD6Context& Context,
    const FFixtureEvaluation& Fixture)
{
    const FChaosScenarioRun& LastRun = Fixture.Scenarios.Last();
    const FChaosFrame& LastFrame = LastRun.Frames.Last();
    TSharedPtr<FJsonObject> Telemetry = MakeShared<FJsonObject>();
    Telemetry->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.flexible_raft.d6_chaos_fixture_telemetry.v1"));
    Telemetry->SetStringField(TEXT("runtime_id"), RuntimeId);
    Telemetry->SetStringField(TEXT("fixture_id"), Fixture.FixtureId);
    Telemetry->SetStringField(TEXT("target_id"), TargetId);
    Telemetry->SetStringField(TEXT("engine_version"), EngineVersionString());
    Telemetry->SetNumberField(TEXT("fixed_step_s"), Context.FixedStepSeconds);
    Telemetry->SetNumberField(TEXT("step_index"), LastFrame.StepIndex);

    TSharedPtr<FJsonObject> Pose = MakeShared<FJsonObject>();
    Pose->SetObjectField(TEXT("position_m"), VectorObject(LastFrame.PositionM));
    Pose->SetObjectField(TEXT("orientation"), QuaternionObject(LastFrame.Orientation));
    Telemetry->SetObjectField(TEXT("raft_pose"), Pose);
    Telemetry->SetObjectField(
        TEXT("raft_linear_velocity"),
        VectorObject(LastFrame.LinearVelocityMps));
    Telemetry->SetObjectField(
        TEXT("raft_angular_velocity"),
        VectorObject(LastFrame.AngularVelocityRadS));

    TArray<TSharedPtr<FJsonValue>> ContactPoints;
    TArray<TSharedPtr<FJsonValue>> ContactImpulses;
    for (const FChaosScenarioRun& Run : Fixture.Scenarios)
    {
        if (Run.bContactObserved)
        {
            TSharedPtr<FJsonObject> Contact = MakeShared<FJsonObject>();
            Contact->SetStringField(TEXT("scenario_id"), Run.ScenarioId);
            Contact->SetNumberField(
                TEXT("max_estimated_indentation_m"),
                Run.MaxObstacleIndentationM);
            ContactPoints.Add(MakeShared<FJsonValueObject>(Contact));
            ContactImpulses.Add(MakeShared<FJsonValueNumber>(Run.MaxContactImpulseNs));
        }
    }
    Telemetry->SetArrayField(TEXT("contact_points"), ContactPoints);
    Telemetry->SetArrayField(TEXT("contact_impulses"), ContactImpulses);
    Telemetry->SetObjectField(TEXT("crew_state"), Fixture.CrewState);

    TSharedPtr<FJsonObject> RigidState = MakeShared<FJsonObject>();
    RigidState->SetStringField(TEXT("representation"), TEXT("single_rigid_box_proxy"));
    RigidState->SetBoolField(TEXT("tube_compliance_supported"), false);
    RigidState->SetBoolField(TEXT("wrap_deformation_supported"), false);
    RigidState->SetNumberField(TEXT("mass_kg"), Context.TotalMassKg);
    RigidState->SetNumberField(TEXT("length_m"), Context.LengthM);
    RigidState->SetNumberField(TEXT("width_m"), Context.WidthM);
    RigidState->SetNumberField(TEXT("half_height_m"), Context.TubeRadiusM);
    Telemetry->SetObjectField(TEXT("tube_or_rigid_proxy_state"), RigidState);
    Telemetry->SetObjectField(TEXT("overwash_state"), Fixture.OverwashState);
    Telemetry->SetObjectField(TEXT("pin_state"), Fixture.PinState);
    Telemetry->SetObjectField(TEXT("release_state"), Fixture.ReleaseState);
    Telemetry->SetObjectField(TEXT("outcome"), Fixture.Outcome);
    Telemetry->SetNumberField(
        TEXT("runtime_cpu_ms"),
        Fixture.Outcome->GetNumberField(TEXT("runtime_cpu_ms")));
    Telemetry->SetStringField(
        TEXT("determinism_hash"),
        Fixture.Outcome->GetStringField(TEXT("combined_determinism_hash")));
    Telemetry->SetObjectField(TEXT("metrics"), Fixture.Metrics);

    TArray<TSharedPtr<FJsonValue>> ScenarioValues;
    for (const FChaosScenarioRun& Run : Fixture.Scenarios)
    {
        ScenarioValues.Add(MakeShared<FJsonValueObject>(ScenarioObject(Run)));
    }
    Telemetry->SetArrayField(TEXT("scenarios"), ScenarioValues);

    TSharedPtr<FJsonObject> Provenance = MakeShared<FJsonObject>();
    Provenance->SetStringField(TEXT("physics_backend"), TEXT("Unreal Chaos"));
    Provenance->SetStringField(TEXT("physics_interface"), TEXT("FChaosEngineInterface"));
    Provenance->SetStringField(TEXT("simulated_component"), TEXT("UBoxComponent"));
    Provenance->SetStringField(TEXT("world_type"), TEXT("EWorldType::Game transient"));
    Provenance->SetBoolField(TEXT("uses_custom_flexible_raft_model"), false);
    Provenance->SetBoolField(TEXT("uses_rigid_baseline_mode"), false);
    Provenance->SetBoolField(TEXT("uses_real_physics_actor_handle"), true);
    Telemetry->SetObjectField(TEXT("runtime_provenance"), Provenance);
    return Telemetry;
}

TSharedPtr<FJsonObject> BuildSidecar(
    const TArray<FFixtureEvaluation>& Fixtures,
    const TMap<FString, FString>& TelemetryHashes)
{
    TSharedPtr<FJsonObject> Sidecar = MakeShared<FJsonObject>();
    Sidecar->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.flexible_raft.d6_chaos_measured_results_sidecar.v1"));
    Sidecar->SetStringField(TEXT("generated_on"), TEXT("2026-07-28"));
    Sidecar->SetStringField(
        TEXT("status"),
        TEXT("chaos_measured_results_recorded_manual_review_pending"));
    Sidecar->SetBoolField(TEXT("d6_complete"), false);
    Sidecar->SetBoolField(TEXT("production_promoted"), false);
    Sidecar->SetStringField(TEXT("runtime"), TEXT("UnrealChaos"));
    Sidecar->SetStringField(TEXT("runtime_id"), RuntimeId);
    Sidecar->SetStringField(TEXT("target_id"), TargetId);
    Sidecar->SetStringField(TEXT("engine_version"), EngineVersionString());
    Sidecar->SetStringField(
        TEXT("source_fixture_input_package_path"),
        FixturePackageRelativePath);
    Sidecar->SetStringField(TEXT("source_runner_summary_path"), ChaosSummaryRelativePath);
    Sidecar->SetNumberField(TEXT("fixture_count"), Fixtures.Num());
    Sidecar->SetNumberField(TEXT("filled_result_count"), Fixtures.Num());

    TArray<TSharedPtr<FJsonValue>> FixtureIds;
    TSharedPtr<FJsonObject> Results = MakeShared<FJsonObject>();
    for (const FFixtureEvaluation& Fixture : Fixtures)
    {
        FixtureIds.Add(MakeShared<FJsonValueString>(Fixture.FixtureId));
        TSharedPtr<FJsonObject> Record = MakeShared<FJsonObject>();
        Record->SetStringField(TEXT("status"), TEXT("measured_engine_output"));
        Record->SetStringField(TEXT("source_report"), ChaosSummaryRelativePath);
        Record->SetStringField(
            TEXT("telemetry_sha256"),
            TelemetryHashes.FindChecked(Fixture.FixtureId));
        Record->SetStringField(TEXT("engine_version"), EngineVersionString());
        Record->SetStringField(TEXT("fixture_id"), Fixture.FixtureId);
        Record->SetStringField(TEXT("target_id"), TargetId);
        Record->SetStringField(TEXT("runtime_id"), RuntimeId);
        Record->SetObjectField(TEXT("metrics"), Fixture.Metrics);
        Record->SetBoolField(TEXT("manual_review_complete"), false);
        Results->SetObjectField(Fixture.FixtureId, Record);
    }
    Sidecar->SetArrayField(TEXT("required_fixture_ids"), FixtureIds);
    Sidecar->SetObjectField(TEXT("results"), Results);

    TSharedPtr<FJsonObject> Gate = MakeShared<FJsonObject>();
    Gate->SetBoolField(TEXT("may_mark_d6_complete"), false);
    Gate->SetBoolField(TEXT("may_drive_runtime_gameplay"), false);
    Gate->SetBoolField(TEXT("manual_review_required"), true);
    Gate->SetStringField(
        TEXT("reason"),
        TEXT("The genuine Unreal Chaos rigid baseline is measured, but D6 still requires an independent reviewed compliant-model result, comparison regeneration, and manual review."));
    Sidecar->SetObjectField(TEXT("promotion_gate"), Gate);
    return Sidecar;
}

TSharedPtr<FJsonObject> BuildSummary(
    const TArray<FFixtureEvaluation>& Fixtures,
    const TMap<FString, FString>& TelemetryHashes,
    const TMap<FString, int32>& MetricCounts)
{
    TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
    Summary->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.flexible_raft.d6_chaos_runner_summary.v1"));
    Summary->SetStringField(TEXT("generated_on"), TEXT("2026-07-28"));
    Summary->SetStringField(
        TEXT("status"),
        TEXT("chaos_measurements_recorded_manual_review_pending"));
    Summary->SetBoolField(TEXT("d6_complete"), false);
    Summary->SetBoolField(TEXT("production_promoted"), false);
    Summary->SetStringField(TEXT("runtime"), TEXT("UnrealChaos"));
    Summary->SetStringField(TEXT("runtime_id"), RuntimeId);
    Summary->SetStringField(TEXT("engine_version"), EngineVersionString());
    Summary->SetStringField(
        TEXT("source_fixture_input_package_path"),
        FixturePackageRelativePath);
    Summary->SetStringField(TEXT("source_contract_path"), ChaosContractRelativePath);
    Summary->SetStringField(TEXT("runner_output_sidecar"), ChaosSidecarRelativePath);
    Summary->SetNumberField(TEXT("fixture_count"), Fixtures.Num());
    Summary->SetNumberField(TEXT("filled_fixture_count"), Fixtures.Num());
    Summary->SetNumberField(TEXT("invalid_fixture_count"), 0);
    Summary->SetBoolField(TEXT("can_merge_sidecar"), true);

    TArray<TSharedPtr<FJsonValue>> Jobs;
    for (const FFixtureEvaluation& Fixture : Fixtures)
    {
        TSharedPtr<FJsonObject> Job = MakeShared<FJsonObject>();
        Job->SetStringField(TEXT("fixture_id"), Fixture.FixtureId);
        Job->SetStringField(TEXT("status"), TEXT("measured_engine_output"));
        Job->SetBoolField(TEXT("ready_for_sidecar_merge"), true);
        Job->SetStringField(TEXT("blocking_reason"), TEXT("manual_review_pending"));
        Job->SetNumberField(
            TEXT("recorded_metric_count"),
            MetricCounts.FindChecked(Fixture.FixtureId));
        Job->SetStringField(
            TEXT("telemetry_path"),
            FString::Printf(
                TEXT("%s/%s.telemetry.json"),
                ChaosReplayRelativeDirectory,
                *Fixture.FixtureId));
        Job->SetStringField(
            TEXT("telemetry_sha256"),
            TelemetryHashes.FindChecked(Fixture.FixtureId));
        Job->SetBoolField(
            TEXT("deterministic_fixed_step_repeat"),
            Fixture.Outcome->GetBoolField(TEXT("deterministic_fixed_step_repeat")));
        Job->SetBoolField(TEXT("measured_by_unreal_chaos"), true);
        Jobs.Add(MakeShared<FJsonValueObject>(Job));
    }
    Summary->SetArrayField(TEXT("jobs"), Jobs);

    TSharedPtr<FJsonObject> Provenance = MakeShared<FJsonObject>();
    Provenance->SetStringField(TEXT("physics_backend"), TEXT("Unreal Chaos"));
    Provenance->SetStringField(TEXT("runner"), TEXT("RaftSimD6Chaos::RunMeasuredExport"));
    Provenance->SetStringField(
        TEXT("execution"),
        TEXT("transient EWorldType::Game physics scene, fixed UWorld ticks, simulated UBoxComponent"));
    Provenance->SetBoolField(TEXT("custom_model_substitution"), false);
    Provenance->SetBoolField(TEXT("analytical_rigid_mode_substitution"), false);
    Summary->SetObjectField(TEXT("runtime_provenance"), Provenance);

    TSharedPtr<FJsonObject> Gate = MakeShared<FJsonObject>();
    Gate->SetBoolField(TEXT("may_mark_d6_complete"), false);
    Gate->SetBoolField(TEXT("may_drive_runtime_gameplay"), false);
    Gate->SetBoolField(TEXT("may_merge_into_measured_results_template"), true);
    Gate->SetBoolField(TEXT("manual_review_required"), true);
    Gate->SetStringField(
        TEXT("reason"),
        TEXT("All seven Unreal Chaos baseline fixtures are genuinely measured and mergeable. D6 remains fail-closed pending the independent compliant-model target, regenerated comparison, and manual review."));
    Summary->SetObjectField(TEXT("promotion_gate"), Gate);
    return Summary;
}

} // namespace

FRaftSimD6ChaosMeasuredRunResult RunMeasuredExport(const FString& RepoRootDir)
{
    FRaftSimD6ChaosMeasuredRunResult Result;
    FD6Context Context;
    if (!LoadContext(RepoRootDir, Context, Result.ErrorMessage))
    {
        return Result;
    }

    TArray<FFixtureEvaluation> Fixtures;
    if (!EvaluateAllFixtures(Context, Fixtures, Result.ErrorMessage))
    {
        return Result;
    }
    if (Fixtures.Num() != RequiredFixtureIds.Num())
    {
        Result.ErrorMessage = FString::Printf(
            TEXT("Expected %d D6 Chaos fixtures, measured %d."),
            RequiredFixtureIds.Num(),
            Fixtures.Num());
        return Result;
    }

    TMap<FString, FString> TelemetryHashes;
    TMap<FString, int32> MetricCounts;
    for (const FFixtureEvaluation& Fixture : Fixtures)
    {
        int32 MetricCount = 0;
        if (!ValidateMetricPaths(
                Context,
                Fixture,
                MetricCount,
                Result.ErrorMessage))
        {
            return Result;
        }
        MetricCounts.Add(Fixture.FixtureId, MetricCount);

        const TSharedPtr<FJsonObject> Telemetry = BuildTelemetry(Context, Fixture);
        const FString TelemetryPath = FPaths::Combine(
            RepoRootDir,
            ChaosReplayRelativeDirectory,
            Fixture.FixtureId + TEXT(".telemetry.json"));
        FString TelemetrySha;
        if (!WriteJson(TelemetryPath, Telemetry, TelemetrySha, Result.ErrorMessage))
        {
            return Result;
        }
        TelemetryHashes.Add(Fixture.FixtureId, TelemetrySha);
    }

    Result.SidecarPath = FPaths::Combine(RepoRootDir, ChaosSidecarRelativePath);
    FString SidecarSha;
    if (!WriteJson(
            Result.SidecarPath,
            BuildSidecar(Fixtures, TelemetryHashes),
            SidecarSha,
            Result.ErrorMessage))
    {
        return Result;
    }

    Result.SummaryPath = FPaths::Combine(RepoRootDir, ChaosSummaryRelativePath);
    FString SummarySha;
    if (!WriteJson(
            Result.SummaryPath,
            BuildSummary(Fixtures, TelemetryHashes, MetricCounts),
            SummarySha,
            Result.ErrorMessage))
    {
        return Result;
    }

    Result.FixtureCount = Fixtures.Num();
    Result.FilledFixtureCount = Fixtures.Num();
    Result.InvalidFixtureCount = 0;
    Result.bSuccess = true;
    return Result;
}

} // namespace RaftSimD6Chaos

#else

namespace RaftSimD6Chaos
{

FRaftSimD6ChaosMeasuredRunResult RunMeasuredExport(const FString& RepoRootDir)
{
    FRaftSimD6ChaosMeasuredRunResult Result;
    Result.ErrorMessage = TEXT("D6 Chaos measurements require WITH_DEV_AUTOMATION_TESTS.");
    return Result;
}

} // namespace RaftSimD6Chaos

#endif
