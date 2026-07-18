#include "RaftSimFlexibleRaftD6MeasuredExport.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "HAL/FileManager.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RaftSimFlexibleRaftModel.h"
#include "Policies/PrettyJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace RaftSimFlexD6
{

namespace
{

// --- Minimal deterministic SHA-256 (FIPS 180-4) -----------------------------

struct FSha256
{
    uint32 State[8];
    uint64 BitLength = 0;
    uint8 Buffer[64];
    uint32 BufferLength = 0;

    FSha256()
    {
        static const uint32 InitialState[8] = {
            0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
            0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u,
        };
        FMemory::Memcpy(State, InitialState, sizeof(State));
    }

    static uint32 RotateRight(uint32 Value, uint32 Bits)
    {
        return (Value >> Bits) | (Value << (32u - Bits));
    }

    void ProcessBlock(const uint8* Block)
    {
        static const uint32 K[64] = {
            0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
            0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
            0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
            0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
            0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
            0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
            0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
            0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u, 0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u,
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
            const uint32 S0 = RotateRight(W[Index - 15], 7) ^ RotateRight(W[Index - 15], 18) ^ (W[Index - 15] >> 3);
            const uint32 S1 = RotateRight(W[Index - 2], 17) ^ RotateRight(W[Index - 2], 19) ^ (W[Index - 2] >> 10);
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
        uint8 LengthBytes[8];
        for (int32 Index = 0; Index < 8; ++Index)
        {
            LengthBytes[Index] = static_cast<uint8>((TotalBits >> (56 - Index * 8)) & 0xFFu);
        }
        // Bypass Update's bit accounting for the length block.
        BitLength = TotalBits;
        for (int32 Index = 0; Index < 8; ++Index)
        {
            Buffer[BufferLength++] = LengthBytes[Index];
            if (BufferLength == 64u)
            {
                ProcessBlock(Buffer);
                BufferLength = 0;
            }
        }

        FString Hex;
        Hex.Reserve(64);
        for (int32 Index = 0; Index < 8; ++Index)
        {
            Hex += FString::Printf(TEXT("%08x"), State[Index]);
        }
        return Hex;
    }
};

FString Sha256HexOfUtf8(const FString& Text)
{
    FTCHARToUTF8 Converter(*Text);
    FSha256 Hasher;
    Hasher.Update(reinterpret_cast<const uint8*>(Converter.Get()), Converter.Length());
    return Hasher.Finalize();
}

// --- Constants ---------------------------------------------------------------

const TCHAR* CompliantTargetId = TEXT("project_chrono_or_reviewed_compliant_model");
const TCHAR* BaselineTargetId = TEXT("unreal_chaos_rigid_baseline");
const TCHAR* CompliantSidecarSchema = TEXT("raftsim.flexible_raft.d6_compliant_measured_results_sidecar.v1");
const TCHAR* BaselineSidecarSchema = TEXT("raftsim.flexible_raft.d6_chaos_measured_results_sidecar.v1");
const TCHAR* GeneratedOn = TEXT("2026-07-17");
const TCHAR* PackageRelativePath = TEXT("physics/data/calibration/flexible_raft_d6_fixture_input_package.json");
const TCHAR* ExportRelativeDir = TEXT("physics/reports/d6/ue");
const TCHAR* SummaryRelativePath = TEXT("physics/reports/d6/ue/summary.json");

const TCHAR* RequiredFixtureIds[] = {
    TEXT("static_seat_load_sag"),
    TEXT("traveling_crew_shift"),
    TEXT("rock_pinch_wrap"),
    TEXT("upstream_tube_overwash_flip"),
    TEXT("timed_high_side_save"),
    TEXT("post_contact_recovery"),
    TEXT("pressure_flow_sweeps"),
};

// --- Fixture context loaded from the committed input package ----------------

struct FD6Context
{
    FRaftSimFlexParameters Parameters;
    FRaftSimFlexRigidState InitialState;
    TArray<FRaftSimFlexCrewSeat> Seats;
    TArray<FRaftSimFlexTubeSegment> DefaultLayout;
    double FixedStepSeconds = 1.0 / 30.0;
    double TotalMassKg = 0.0;
    FVector Gravity = FVector(0.0, 0.0, -9.81);
    TSharedPtr<FJsonObject> PackageRoot;
};

FVector ReadVector(const TSharedPtr<FJsonObject>& Object)
{
    return FVector(
        Object->GetNumberField(TEXT("x")),
        Object->GetNumberField(TEXT("y")),
        Object->GetNumberField(TEXT("z")));
}

bool NearlyEqualRel(double A, double B, double RelTol)
{
    return FMath::Abs(A - B) <= RelTol * FMath::Max3(1.0, FMath::Abs(A), FMath::Abs(B));
}

bool LoadContext(const FString& RepoRootDir, FD6Context& OutContext, FString& OutError)
{
    const FString PackagePath = FPaths::Combine(RepoRootDir, PackageRelativePath);
    FString PackageText;
    if (!FFileHelper::LoadFileToString(PackageText, *PackagePath))
    {
        OutError = FString::Printf(TEXT("Missing D6 fixture input package: %s"), *PackagePath);
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(PackageText);
    if (!FJsonSerializer::Deserialize(Reader, OutContext.PackageRoot) || !OutContext.PackageRoot.IsValid())
    {
        OutError = TEXT("D6 fixture input package is not valid JSON.");
        return false;
    }

    const TSharedPtr<FJsonObject> CommonSetup = OutContext.PackageRoot->GetObjectField(TEXT("common_setup"));
    if (!CommonSetup.IsValid())
    {
        OutError = TEXT("D6 fixture input package is missing common_setup.");
        return false;
    }

    OutContext.FixedStepSeconds = CommonSetup->GetNumberField(TEXT("fixed_step_s"));

    const TSharedPtr<FJsonObject> RaftParameters = CommonSetup->GetObjectField(TEXT("raft_parameters"));
    OutContext.Parameters.MassKg = RaftParameters->GetNumberField(TEXT("mass_kg"));
    OutContext.Parameters.LengthM = RaftParameters->GetNumberField(TEXT("length_m"));
    OutContext.Parameters.WidthM = RaftParameters->GetNumberField(TEXT("width_m"));
    OutContext.Parameters.TubeRadiusM = RaftParameters->GetNumberField(TEXT("tube_radius_m"));
    OutContext.Parameters.GuideMassKg = RaftParameters->GetNumberField(TEXT("guide_mass_kg"));
    OutContext.Parameters.PassengerMassKg = RaftParameters->GetNumberField(TEXT("passenger_mass_kg"));
    OutContext.Parameters.PassengerCount =
        static_cast<int32>(RaftParameters->GetIntegerField(TEXT("passenger_count")));

    const TSharedPtr<FJsonObject> InitialState = CommonSetup->GetObjectField(TEXT("initial_state"));
    OutContext.InitialState.Position = ReadVector(InitialState->GetObjectField(TEXT("position")));
    const TSharedPtr<FJsonObject> Orientation = InitialState->GetObjectField(TEXT("orientation"));
    OutContext.InitialState.Orientation = FQuat(
        Orientation->GetNumberField(TEXT("x")),
        Orientation->GetNumberField(TEXT("y")),
        Orientation->GetNumberField(TEXT("z")),
        Orientation->GetNumberField(TEXT("w"))).GetNormalized();
    OutContext.InitialState.LinearVelocity =
        ReadVector(InitialState->GetObjectField(TEXT("linear_velocity_mps")));
    OutContext.InitialState.AngularVelocity =
        ReadVector(InitialState->GetObjectField(TEXT("angular_velocity_rad_s")));

    const TSharedPtr<FJsonObject> MassProperties = CommonSetup->GetObjectField(TEXT("mass_properties"));
    OutContext.TotalMassKg = MassProperties->GetNumberField(TEXT("total_mass_kg"));
    OutContext.Gravity = ReadVector(MassProperties->GetObjectField(TEXT("gravity")));

    const TArray<TSharedPtr<FJsonValue>>& SeatValues = CommonSetup->GetArrayField(TEXT("crew_seats"));
    for (const TSharedPtr<FJsonValue>& SeatValue : SeatValues)
    {
        const TSharedPtr<FJsonObject> SeatObject = SeatValue->AsObject();
        FRaftSimFlexCrewSeat Seat;
        Seat.SeatId = SeatObject->GetStringField(TEXT("seat_id"));
        Seat.LocalPosition = ReadVector(SeatObject->GetObjectField(TEXT("local_position")));
        Seat.OccupantMassKg = SeatObject->GetNumberField(TEXT("occupant_mass_kg"));
        Seat.bOccupied = SeatObject->GetBoolField(TEXT("occupied"));
        Seat.Role = SeatObject->GetStringField(TEXT("role"));
        OutContext.Seats.Add(Seat);
    }

    const TSharedPtr<FJsonObject> TubeLayout = CommonSetup->GetObjectField(TEXT("default_tube_layout"));
    const TArray<TSharedPtr<FJsonValue>>& SegmentValues = TubeLayout->GetArrayField(TEXT("segments"));
    for (const TSharedPtr<FJsonValue>& SegmentValue : SegmentValues)
    {
        const TSharedPtr<FJsonObject> SegmentObject = SegmentValue->AsObject();
        FRaftSimFlexTubeSegment Segment;
        Segment.SegmentId = SegmentObject->GetStringField(TEXT("segment_id"));
        Segment.LocalPosition = ReadVector(SegmentObject->GetObjectField(TEXT("local_position")));
        Segment.OutwardNormal = ReadVector(SegmentObject->GetObjectField(TEXT("outward_normal")));
        Segment.TributaryLengthM = SegmentObject->GetNumberField(TEXT("tributary_length_m"));
        Segment.RestVolumeM3 = SegmentObject->GetNumberField(TEXT("rest_volume_m3"));
        Segment.ContactAreaM2 = SegmentObject->GetNumberField(TEXT("contact_area_m2"));
        Segment.NominalPressurePa = SegmentObject->GetNumberField(TEXT("nominal_pressure_pa"));
        Segment.ComplianceM3PerPa = SegmentObject->GetNumberField(TEXT("compliance_m3_per_pa"));
        Segment.FloorCouplingFraction = SegmentObject->GetNumberField(TEXT("floor_coupling_fraction"));
        Segment.LacingCouplingFraction = SegmentObject->GetNumberField(TEXT("lacing_coupling_fraction"));
        Segment.FrameCouplingFraction = SegmentObject->GetNumberField(TEXT("frame_coupling_fraction"));
        OutContext.DefaultLayout.Add(Segment);
    }

    if (OutContext.DefaultLayout.Num() == 0 || OutContext.Seats.Num() == 0)
    {
        OutError = TEXT("D6 fixture input package has an empty layout or crew seat list.");
        return false;
    }

    // Guard: the C++ layout builder must reproduce the committed default
    // layout exactly (the pressure sweep fixture rebuilds layouts at other
    // nominal pressures through the same builder).
    const TArray<FRaftSimFlexTubeSegment> Rebuilt =
        RaftSimFlex::BuildDefaultCompliantTubeLayout(OutContext.Parameters);
    if (Rebuilt.Num() != OutContext.DefaultLayout.Num())
    {
        OutError = TEXT("C++ tube layout builder segment count differs from the committed package.");
        return false;
    }
    for (int32 Index = 0; Index < Rebuilt.Num(); ++Index)
    {
        const FRaftSimFlexTubeSegment& Built = Rebuilt[Index];
        const FRaftSimFlexTubeSegment& Recorded = OutContext.DefaultLayout[Index];
        const bool bMatches =
            Built.SegmentId == Recorded.SegmentId
            && NearlyEqualRel(Built.LocalPosition.X, Recorded.LocalPosition.X, 1.0e-9)
            && NearlyEqualRel(Built.LocalPosition.Y, Recorded.LocalPosition.Y, 1.0e-9)
            && NearlyEqualRel(Built.TributaryLengthM, Recorded.TributaryLengthM, 1.0e-9)
            && NearlyEqualRel(Built.RestVolumeM3, Recorded.RestVolumeM3, 1.0e-9)
            && NearlyEqualRel(Built.ContactAreaM2, Recorded.ContactAreaM2, 1.0e-9)
            && NearlyEqualRel(Built.NominalPressurePa, Recorded.NominalPressurePa, 1.0e-9)
            && NearlyEqualRel(Built.ComplianceM3PerPa, Recorded.ComplianceM3PerPa, 1.0e-9);
        if (!bMatches)
        {
            OutError = FString::Printf(
                TEXT("C++ tube layout builder diverges from the committed package at segment %s."),
                *Recorded.SegmentId);
            return false;
        }
    }
    return true;
}

TSharedPtr<FJsonObject> FindFixtureInput(const FD6Context& Context, const FString& FixtureId)
{
    const TArray<TSharedPtr<FJsonValue>>& Fixtures = Context.PackageRoot->GetArrayField(TEXT("fixtures"));
    for (const TSharedPtr<FJsonValue>& FixtureValue : Fixtures)
    {
        const TSharedPtr<FJsonObject> Fixture = FixtureValue->AsObject();
        if (Fixture.IsValid() && Fixture->GetStringField(TEXT("fixture_id")) == FixtureId)
        {
            return Fixture->GetObjectField(TEXT("input_contract"));
        }
    }
    return nullptr;
}

TArray<FRaftSimFlexCrewAction> ReadPhaseActions(
    const TSharedPtr<FJsonObject>& InputContract,
    const FString& PhaseId)
{
    TArray<FRaftSimFlexCrewAction> Actions;
    const TArray<TSharedPtr<FJsonValue>>& Phases = InputContract->GetArrayField(TEXT("phases"));
    for (const TSharedPtr<FJsonValue>& PhaseValue : Phases)
    {
        const TSharedPtr<FJsonObject> Phase = PhaseValue->AsObject();
        if (!Phase.IsValid() || Phase->GetStringField(TEXT("phase_id")) != PhaseId)
        {
            continue;
        }
        const TArray<TSharedPtr<FJsonValue>>& ActionValues = Phase->GetArrayField(TEXT("crew_actions"));
        for (const TSharedPtr<FJsonValue>& ActionValue : ActionValues)
        {
            const TSharedPtr<FJsonObject> ActionObject = ActionValue->AsObject();
            FRaftSimFlexCrewAction Action;
            Action.SeatId = ActionObject->GetStringField(TEXT("seat_id"));
            Action.LeanOffset = ReadVector(ActionObject->GetObjectField(TEXT("lean_offset")));
            Action.HighSideDirection =
                static_cast<int32>(ActionObject->GetIntegerField(TEXT("high_side_direction")));
            Action.bBrace = ActionObject->GetBoolField(TEXT("brace"));
            Action.bRecovery = ActionObject->GetBoolField(TEXT("recovery"));
            Actions.Add(Action);
        }
        break;
    }
    return Actions;
}

FRaftSimFlexUniformWater ReadWater(const TSharedPtr<FJsonObject>& WaterObject)
{
    FRaftSimFlexUniformWater Water;
    Water.SurfaceHeightM = WaterObject->GetNumberField(TEXT("surface_height_m"));
    Water.VelocityMps = ReadVector(WaterObject->GetObjectField(TEXT("velocity_mps")));
    Water.bWet = true;
    return Water;
}

FRaftSimFlexRockObstacle ReadObstacle(const TSharedPtr<FJsonObject>& ObstacleObject)
{
    FRaftSimFlexRockObstacle Obstacle;
    Obstacle.ObstacleId = ObstacleObject->GetStringField(TEXT("obstacle_id"));
    Obstacle.LocalPosition = ReadVector(ObstacleObject->GetObjectField(TEXT("local_position")));
    Obstacle.RadiusM = ObstacleObject->GetNumberField(TEXT("radius_m"));
    Obstacle.FrictionCoefficient = ObstacleObject->GetNumberField(TEXT("friction_coefficient"));
    return Obstacle;
}

TMap<FString, double> ReadSegmentDoubleMap(
    const TSharedPtr<FJsonObject>& InputContract,
    const FString& FieldName)
{
    TMap<FString, double> Result;
    const TSharedPtr<FJsonObject>* MapObject = nullptr;
    if (InputContract->TryGetObjectField(FieldName, MapObject) && MapObject != nullptr)
    {
        for (const auto& Pair : (*MapObject)->Values)
        {
            Result.Add(FString(*Pair.Key), Pair.Value->AsNumber());
        }
    }
    return Result;
}

// --- Fixture evaluation ------------------------------------------------------

struct FFixtureRun
{
    FString FixtureId;
    TSharedPtr<FJsonObject> Metrics;
    TSharedPtr<FJsonObject> TelemetryChannels;
};

FRaftSimFlexSeatLoadSolve SolveTube(
    const FD6Context& Context,
    const TArray<FRaftSimFlexCrewAction>& Actions,
    const TArray<FRaftSimFlexTubeSegment>& Layout,
    RaftSimFlex::EModelMode Mode)
{
    return RaftSimFlex::SolveSeatLoadCoupledTubeD2(
        Context.InitialState,
        Context.Parameters,
        Context.Seats,
        Actions,
        Layout,
        Mode,
        Context.TotalMassKg,
        Context.Gravity);
}

double SumRetainedVolumeForPrefix(const FRaftSimFlexOverwashSolve& Overwash, const TCHAR* Prefix)
{
    double Total = 0.0;
    for (const FRaftSimFlexSegmentOverwash& Segment : Overwash.SegmentOverwash)
    {
        if (Segment.SegmentId.StartsWith(Prefix, ESearchCase::CaseSensitive))
        {
            Total += Segment.RetainedWaterVolumeM3;
        }
    }
    return Total;
}

TSharedPtr<FJsonObject> BuildTelemetryChannels(
    const FRaftSimFlexSeatLoadSolve& TubeSolve,
    const FRaftSimFlexOverwashSolve* Overwash,
    const FRaftSimFlexRockContactSolve* Contacts)
{
    TSharedPtr<FJsonObject> Channels = MakeShared<FJsonObject>();

    TSharedPtr<FJsonObject> PressureChannel = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> VolumeChannel = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> FreeboardChannel = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> FloorChannel = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> LacingChannel = MakeShared<FJsonObject>();
    for (const FRaftSimFlexSegmentResponse& Response : TubeSolve.TubeSolve.SegmentResponses)
    {
        PressureChannel->SetNumberField(Response.SegmentId, Response.PressurePa);
        VolumeChannel->SetNumberField(Response.SegmentId, Response.VolumeM3);
        FreeboardChannel->SetNumberField(Response.SegmentId, Response.FreeboardLossM);
        FloorChannel->SetNumberField(Response.SegmentId, Response.FloorLoadN);
        LacingChannel->SetNumberField(Response.SegmentId, Response.ReceivedLacingLoadN);
    }
    Channels->SetObjectField(TEXT("tube.pressure_pa"), PressureChannel);
    Channels->SetObjectField(TEXT("tube.volume_m3"), VolumeChannel);
    Channels->SetObjectField(TEXT("tube.freeboard_loss_m"), FreeboardChannel);
    Channels->SetObjectField(TEXT("tube.floor_load_n"), FloorChannel);
    Channels->SetObjectField(TEXT("tube.lacing_load_n"), LacingChannel);

    TSharedPtr<FJsonObject> FluxChannel = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> EntrainedChannel = MakeShared<FJsonObject>();
    if (Overwash != nullptr)
    {
        for (const FRaftSimFlexSegmentOverwash& Segment : Overwash->SegmentOverwash)
        {
            FluxChannel->SetNumberField(Segment.SegmentId, Segment.OvertoppingFluxM3S);
        }
        EntrainedChannel->SetNumberField(TEXT("port"), SumRetainedVolumeForPrefix(*Overwash, TEXT("port_")));
        EntrainedChannel->SetNumberField(
            TEXT("starboard"), SumRetainedVolumeForPrefix(*Overwash, TEXT("starboard_")));
        EntrainedChannel->SetNumberField(TEXT("bow"), SumRetainedVolumeForPrefix(*Overwash, TEXT("bow_")));
        EntrainedChannel->SetNumberField(TEXT("stern"), SumRetainedVolumeForPrefix(*Overwash, TEXT("stern_")));
    }
    else
    {
        for (const FRaftSimFlexSegmentResponse& Response : TubeSolve.TubeSolve.SegmentResponses)
        {
            FluxChannel->SetNumberField(Response.SegmentId, 0.0);
        }
        EntrainedChannel->SetNumberField(TEXT("port"), 0.0);
        EntrainedChannel->SetNumberField(TEXT("starboard"), 0.0);
        EntrainedChannel->SetNumberField(TEXT("bow"), 0.0);
        EntrainedChannel->SetNumberField(TEXT("stern"), 0.0);
    }
    Channels->SetObjectField(TEXT("overwash.overtopping_flux_m3_s"), FluxChannel);
    Channels->SetObjectField(TEXT("overwash.entrained_water_side"), EntrainedChannel);

    Channels->SetNumberField(
        TEXT("contact.max_indentation_m"), Contacts != nullptr ? Contacts->MaxIndentationM : 0.0);
    Channels->SetNumberField(
        TEXT("contact.min_release_margin_n"), Contacts != nullptr ? Contacts->MinReleaseMarginN : 0.0);
    const double RetainedRoll = Overwash != nullptr ? Overwash->RetainedWaterRollMomentNm : 0.0;
    Channels->SetNumberField(
        TEXT("combined_roll_moment_nm"), TubeSolve.TubeSolve.RollLoadBiasNm + RetainedRoll);
    return Channels;
}

bool EvaluateFixtures(
    const FD6Context& Context,
    RaftSimFlex::EModelMode Mode,
    TArray<FFixtureRun>& OutRuns,
    FString& OutError)
{
    const double Dt = Context.FixedStepSeconds;
    const TArray<FRaftSimFlexCrewAction> NoActions;

    // static_seat_load_sag
    {
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        FFixtureRun Run;
        Run.FixtureId = TEXT("static_seat_load_sag");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("loaded_crew_mass_kg"), Neutral.CrewTelemetry.TotalCrewMassKg);
        Run.Metrics->SetNumberField(TEXT("max_seat_freeboard_loss_m"), Neutral.MaxSeatFreeboardLossM);
        Run.Metrics->SetNumberField(TEXT("port_total_freeboard_loss_m"), Neutral.PortTotalFreeboardLossM);
        Run.Metrics->SetNumberField(TEXT("raft_length_m"), Context.Parameters.LengthM);
        Run.Metrics->SetNumberField(TEXT("raft_width_m"), Context.Parameters.WidthM);
        Run.Metrics->SetNumberField(
            TEXT("starboard_total_freeboard_loss_m"), Neutral.StarboardTotalFreeboardLossM);
        Run.TelemetryChannels = BuildTelemetryChannels(Neutral, nullptr, nullptr);
        OutRuns.Add(Run);
    }

    // traveling_crew_shift
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("traveling_crew_shift"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing traveling_crew_shift input contract.");
            return false;
        }
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        const FRaftSimFlexSeatLoadSolve Port = SolveTube(
            Context, ReadPhaseActions(Input, TEXT("port_lean_requested")), Context.DefaultLayout, Mode);
        const FRaftSimFlexSeatLoadSolve Starboard = SolveTube(
            Context, ReadPhaseActions(Input, TEXT("starboard_high_side")), Context.DefaultLayout, Mode);
        FFixtureRun Run;
        Run.FixtureId = TEXT("traveling_crew_shift");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("neutral_roll_load_bias_nm"), Neutral.TubeSolve.RollLoadBiasNm);
        Run.Metrics->SetNumberField(TEXT("port_roll_load_bias_nm"), Port.TubeSolve.RollLoadBiasNm);
        Run.Metrics->SetNumberField(
            TEXT("port_total_freeboard_delta_m"),
            Port.PortTotalFreeboardLossM - Neutral.PortTotalFreeboardLossM);
        Run.Metrics->SetNumberField(
            TEXT("starboard_roll_load_bias_nm"), Starboard.TubeSolve.RollLoadBiasNm);
        Run.Metrics->SetNumberField(
            TEXT("starboard_total_freeboard_delta_m"),
            Starboard.StarboardTotalFreeboardLossM - Neutral.StarboardTotalFreeboardLossM);
        Run.TelemetryChannels = BuildTelemetryChannels(Starboard, nullptr, nullptr);
        OutRuns.Add(Run);
    }

    // rock_pinch_wrap
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("rock_pinch_wrap"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing rock_pinch_wrap input contract.");
            return false;
        }
        const TArray<TSharedPtr<FJsonValue>>& ObstacleValues = Input->GetArrayField(TEXT("obstacles"));
        TArray<FRaftSimFlexRockObstacle> Obstacles;
        for (const TSharedPtr<FJsonValue>& ObstacleValue : ObstacleValues)
        {
            Obstacles.Add(ReadObstacle(ObstacleValue->AsObject()));
        }
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        const FRaftSimFlexRockContactSolve Contacts = RaftSimFlex::EvaluateRockContactWrapPinD4(
            Neutral,
            Obstacles,
            Context.DefaultLayout,
            Context.Parameters.TubeRadiusM,
            nullptr,
            Mode,
            Dt);
        FFixtureRun Run;
        Run.FixtureId = TEXT("rock_pinch_wrap");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("contact_count"), Contacts.Contacts.Num());
        Run.Metrics->SetNumberField(TEXT("max_indentation_m"), Contacts.MaxIndentationM);
        Run.Metrics->SetNumberField(TEXT("min_release_margin_n"), Contacts.MinReleaseMarginN);
        Run.Metrics->SetNumberField(TEXT("pinned_obstacle_count"), Contacts.PinnedObstacleCount);
        Run.Metrics->SetNumberField(TEXT("wrapping_contact_count"), Contacts.WrappingContactCount);
        Run.TelemetryChannels = BuildTelemetryChannels(Neutral, nullptr, &Contacts);
        OutRuns.Add(Run);
    }

    // upstream_tube_overwash_flip
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("upstream_tube_overwash_flip"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing upstream_tube_overwash_flip input contract.");
            return false;
        }
        const FRaftSimFlexUniformWater Water = ReadWater(Input->GetObjectField(TEXT("water")));
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        const FRaftSimFlexOverwashSolve Overwash = RaftSimFlex::EvaluateOverwashFlipD3(
            Neutral, Water, Context.DefaultLayout, nullptr, Dt);
        FFixtureRun Run;
        Run.FixtureId = TEXT("upstream_tube_overwash_flip");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("reference_flip_margin_nm"), Overwash.ReferenceFlipMarginNm);
        Run.Metrics->SetBoolField(TEXT("reference_flip_risk"), Overwash.bReferenceFlipRisk);
        Run.Metrics->SetNumberField(
            TEXT("retained_water_roll_moment_nm"), Overwash.RetainedWaterRollMomentNm);
        Run.Metrics->SetNumberField(
            TEXT("total_overtopping_flux_m3_s"), Overwash.TotalOvertoppingFluxM3S);
        Run.Metrics->SetNumberField(
            TEXT("total_retained_water_mass_kg"), Overwash.TotalRetainedWaterMassKg);
        Run.TelemetryChannels = BuildTelemetryChannels(Neutral, &Overwash, nullptr);
        OutRuns.Add(Run);
    }

    // timed_high_side_save
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("timed_high_side_save"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing timed_high_side_save input contract.");
            return false;
        }
        const FRaftSimFlexUniformWater Water = ReadWater(Input->GetObjectField(TEXT("water")));
        const TMap<FString, double> RecordedRetained =
            ReadSegmentDoubleMap(Input, TEXT("previous_retained_volume_by_segment"));
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        const FRaftSimFlexOverwashSolve NeutralOverwash = RaftSimFlex::EvaluateOverwashFlipD3(
            Neutral, Water, Context.DefaultLayout, nullptr, Dt);
        const FRaftSimFlexSeatLoadSolve HighSide = SolveTube(
            Context,
            ReadPhaseActions(Input, TEXT("starboard_high_side_with_retained_water_memory")),
            Context.DefaultLayout,
            Mode);
        const FRaftSimFlexOverwashSolve HighSideOverwash = RaftSimFlex::EvaluateOverwashFlipD3(
            HighSide, Water, Context.DefaultLayout, &RecordedRetained, Dt);
        FFixtureRun Run;
        Run.FixtureId = TEXT("timed_high_side_save");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(
            TEXT("high_side_flip_margin_nm"), HighSideOverwash.ReferenceFlipMarginNm);
        Run.Metrics->SetNumberField(
            TEXT("high_side_flip_threshold_nm"), HighSideOverwash.ReferenceFlipThresholdNm);
        Run.Metrics->SetNumberField(
            TEXT("margin_delta_nm"),
            HighSideOverwash.ReferenceFlipMarginNm - NeutralOverwash.ReferenceFlipMarginNm);
        Run.Metrics->SetNumberField(TEXT("neutral_flip_margin_nm"), NeutralOverwash.ReferenceFlipMarginNm);
        Run.Metrics->SetNumberField(
            TEXT("neutral_flip_threshold_nm"), NeutralOverwash.ReferenceFlipThresholdNm);
        Run.TelemetryChannels = BuildTelemetryChannels(HighSide, &HighSideOverwash, nullptr);
        OutRuns.Add(Run);
    }

    // post_contact_recovery
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("post_contact_recovery"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing post_contact_recovery input contract.");
            return false;
        }
        const TMap<FString, double> PreviousIndentation =
            ReadSegmentDoubleMap(Input, TEXT("previous_indentation_by_segment"));
        const FRaftSimFlexSeatLoadSolve Neutral =
            SolveTube(Context, NoActions, Context.DefaultLayout, Mode);
        const FRaftSimFlexRockContactSolve Recovery = RaftSimFlex::EvaluateRockContactWrapPinD4(
            Neutral,
            TArray<FRaftSimFlexRockObstacle>(),
            Context.DefaultLayout,
            Context.Parameters.TubeRadiusM,
            &PreviousIndentation,
            Mode,
            Dt);
        FFixtureRun Run;
        Run.FixtureId = TEXT("post_contact_recovery");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("max_recovered_indentation_m"), Recovery.MaxIndentationM);
        Run.Metrics->SetNumberField(TEXT("recovering_contact_count"), Recovery.RecoveringContactCount);
        Run.Metrics->SetNumberField(TEXT("total_holding_force_n"), Recovery.TotalHoldingForceN);
        Run.TelemetryChannels = BuildTelemetryChannels(Neutral, nullptr, &Recovery);
        OutRuns.Add(Run);
    }

    // pressure_flow_sweeps
    {
        const TSharedPtr<FJsonObject> Input = FindFixtureInput(Context, TEXT("pressure_flow_sweeps"));
        if (!Input.IsValid())
        {
            OutError = TEXT("Missing pressure_flow_sweeps input contract.");
            return false;
        }
        const TArray<TSharedPtr<FJsonValue>>& PressureValues =
            Input->GetArrayField(TEXT("nominal_pressure_values_pa"));
        const TArray<TSharedPtr<FJsonValue>>& VelocityValues =
            Input->GetArrayField(TEXT("incoming_velocity_values_mps"));
        const double WaterSurfaceHeight = Input->GetNumberField(TEXT("water_surface_height_m"));
        const TArray<TSharedPtr<FJsonValue>>& ObstacleValues = Input->GetArrayField(TEXT("obstacles"));
        TArray<FRaftSimFlexRockObstacle> Obstacles;
        for (const TSharedPtr<FJsonValue>& ObstacleValue : ObstacleValues)
        {
            Obstacles.Add(ReadObstacle(ObstacleValue->AsObject()));
        }

        TArray<TSharedPtr<FJsonValue>> SweepEntries;
        TSharedPtr<FJsonObject> LastTelemetry;
        for (const TSharedPtr<FJsonValue>& PressureValue : PressureValues)
        {
            const double NominalPressure = PressureValue->AsNumber();
            const TArray<FRaftSimFlexTubeSegment> SweepLayout =
                RaftSimFlex::BuildDefaultCompliantTubeLayout(
                    Context.Parameters, 4, 2, NominalPressure);
            const FRaftSimFlexSeatLoadSolve Tube = SolveTube(Context, NoActions, SweepLayout, Mode);
            for (const TSharedPtr<FJsonValue>& VelocityValue : VelocityValues)
            {
                const double Velocity = VelocityValue->AsNumber();
                FRaftSimFlexUniformWater Water;
                Water.SurfaceHeightM = WaterSurfaceHeight;
                Water.VelocityMps = FVector(0.0, -Velocity, 0.0);
                Water.bWet = true;
                const FRaftSimFlexOverwashSolve Overwash = RaftSimFlex::EvaluateOverwashFlipD3(
                    Tube, Water, SweepLayout, nullptr, Dt);
                const FRaftSimFlexRockContactSolve Contacts = RaftSimFlex::EvaluateRockContactWrapPinD4(
                    Tube,
                    Obstacles,
                    SweepLayout,
                    Context.Parameters.TubeRadiusM,
                    nullptr,
                    Mode,
                    Dt);
                TSharedPtr<FJsonObject> Sweep = MakeShared<FJsonObject>();
                Sweep->SetNumberField(TEXT("contact_min_release_margin_n"), Contacts.MinReleaseMarginN);
                Sweep->SetNumberField(TEXT("incoming_velocity_mps"), Velocity);
                Sweep->SetNumberField(TEXT("nominal_pressure_pa"), NominalPressure);
                Sweep->SetNumberField(TEXT("overwash_flux_m3_s"), Overwash.TotalOvertoppingFluxM3S);
                Sweep->SetNumberField(
                    TEXT("retained_water_roll_moment_nm"), Overwash.RetainedWaterRollMomentNm);
                SweepEntries.Add(MakeShared<FJsonValueObject>(Sweep));
                LastTelemetry = BuildTelemetryChannels(Tube, &Overwash, &Contacts);
            }
        }
        FFixtureRun Run;
        Run.FixtureId = TEXT("pressure_flow_sweeps");
        Run.Metrics = MakeShared<FJsonObject>();
        Run.Metrics->SetNumberField(TEXT("sweep_case_count"), SweepEntries.Num());
        Run.Metrics->SetArrayField(TEXT("sweeps"), SweepEntries);
        Run.TelemetryChannels = LastTelemetry.IsValid() ? LastTelemetry : MakeShared<FJsonObject>();
        OutRuns.Add(Run);
    }

    return true;
}

// --- Output writing ----------------------------------------------------------

FString SerializeJson(const TSharedPtr<FJsonObject>& Object)
{
    FString Output;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&Output);
    FJsonSerializer::Serialize(Object.ToSharedRef(), Writer);
    return Output;
}

bool WriteJsonFile(const FString& FullPath, const TSharedPtr<FJsonObject>& Object, FString& OutSha256)
{
    const FString Text = SerializeJson(Object);
    OutSha256 = Sha256HexOfUtf8(Text);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(FullPath), true);
    return FFileHelper::SaveStringToFile(
        Text, *FullPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

FString EngineVersionString()
{
    return FString::Printf(
        TEXT("UnrealEngine %s SmokeEmIfYouGotEm A-3 flexible-raft C++ port"),
        *FEngineVersion::Current().ToString());
}

TSharedPtr<FJsonObject> BuildSidecar(
    const FString& Schema,
    const FString& TargetId,
    const FString& Runtime,
    const FString& Status,
    const TArray<FFixtureRun>& Runs,
    const TMap<FString, FString>& TelemetryHashes)
{
    TSharedPtr<FJsonObject> Sidecar = MakeShared<FJsonObject>();
    Sidecar->SetStringField(TEXT("schema"), Schema);
    Sidecar->SetStringField(TEXT("generated_on"), GeneratedOn);
    Sidecar->SetStringField(TEXT("status"), Status);
    Sidecar->SetBoolField(TEXT("d6_complete"), false);
    Sidecar->SetBoolField(TEXT("production_promoted"), false);
    Sidecar->SetStringField(TEXT("runtime"), Runtime);
    Sidecar->SetStringField(TEXT("target_id"), TargetId);
    Sidecar->SetStringField(TEXT("engine_version"), EngineVersionString());
    Sidecar->SetStringField(TEXT("source_fixture_input_package_path"), PackageRelativePath);
    Sidecar->SetStringField(TEXT("source_runner_summary_path"), SummaryRelativePath);
    Sidecar->SetNumberField(TEXT("fixture_count"), Runs.Num());

    TArray<TSharedPtr<FJsonValue>> FixtureIds;
    for (const TCHAR* FixtureId : RequiredFixtureIds)
    {
        FixtureIds.Add(MakeShared<FJsonValueString>(FixtureId));
    }
    Sidecar->SetArrayField(TEXT("required_fixture_ids"), FixtureIds);
    Sidecar->SetNumberField(TEXT("filled_result_count"), Runs.Num());

    TSharedPtr<FJsonObject> Results = MakeShared<FJsonObject>();
    for (const FFixtureRun& Run : Runs)
    {
        TSharedPtr<FJsonObject> Record = MakeShared<FJsonObject>();
        Record->SetStringField(TEXT("status"), TEXT("measured_engine_output"));
        Record->SetStringField(TEXT("source_report"), SummaryRelativePath);
        Record->SetStringField(TEXT("telemetry_sha256"), TelemetryHashes.FindChecked(Run.FixtureId));
        Record->SetStringField(TEXT("engine_version"), EngineVersionString());
        Record->SetStringField(TEXT("fixture_id"), Run.FixtureId);
        Record->SetStringField(TEXT("target_id"), TargetId);
        Record->SetObjectField(TEXT("metrics"), Run.Metrics);
        Results->SetObjectField(Run.FixtureId, Record);
    }
    Sidecar->SetObjectField(TEXT("results"), Results);
    return Sidecar;
}

bool ExportTarget(
    const FString& RepoRootDir,
    const FD6Context& Context,
    RaftSimFlex::EModelMode Mode,
    const FString& TargetId,
    const FString& Schema,
    const FString& Runtime,
    const FString& Status,
    const FString& SidecarFileName,
    TArray<FFixtureRun>& OutRuns,
    TMap<FString, FString>& OutTelemetryHashes,
    FString& OutSidecarPath,
    FString& OutError)
{
    if (!EvaluateFixtures(Context, Mode, OutRuns, OutError))
    {
        return false;
    }

    const FString RuntimeId = Mode == RaftSimFlex::EModelMode::Compliant
        ? TEXT("ue_custom_reduced_rigid_body_flexible_port")
        : TEXT("ue_rigid_baseline");

    for (const FFixtureRun& Run : OutRuns)
    {
        TSharedPtr<FJsonObject> Telemetry = MakeShared<FJsonObject>();
        Telemetry->SetStringField(
            TEXT("schema"), TEXT("raftsim.flexible_raft.d6_ue_fixture_telemetry.v1"));
        Telemetry->SetStringField(TEXT("runtime_id"), RuntimeId);
        Telemetry->SetStringField(TEXT("target_id"), TargetId);
        Telemetry->SetStringField(TEXT("fixture_id"), Run.FixtureId);
        Telemetry->SetStringField(TEXT("engine_version"), EngineVersionString());
        Telemetry->SetNumberField(TEXT("fixed_step_s"), Context.FixedStepSeconds);
        Telemetry->SetObjectField(TEXT("channels"), Run.TelemetryChannels);
        Telemetry->SetObjectField(TEXT("metrics"), Run.Metrics);

        const FString TelemetryPath = FPaths::Combine(
            RepoRootDir,
            ExportRelativeDir,
            TEXT("replays"),
            TargetId,
            Run.FixtureId + TEXT(".telemetry.json"));
        FString TelemetrySha;
        if (!WriteJsonFile(TelemetryPath, Telemetry, TelemetrySha))
        {
            OutError = FString::Printf(TEXT("Failed to write telemetry: %s"), *TelemetryPath);
            return false;
        }
        OutTelemetryHashes.Add(Run.FixtureId, TelemetrySha);
    }

    const TSharedPtr<FJsonObject> Sidecar =
        BuildSidecar(Schema, TargetId, Runtime, Status, OutRuns, OutTelemetryHashes);
    OutSidecarPath = FPaths::Combine(RepoRootDir, ExportRelativeDir, SidecarFileName);
    FString UnusedSha;
    if (!WriteJsonFile(OutSidecarPath, Sidecar, UnusedSha))
    {
        OutError = FString::Printf(TEXT("Failed to write sidecar: %s"), *OutSidecarPath);
        return false;
    }
    return true;
}

} // namespace

FRaftSimD6MeasuredExportResult RunMeasuredExport(const FString& RepoRootDir)
{
    FRaftSimD6MeasuredExportResult Result;

    FD6Context Context;
    if (!LoadContext(RepoRootDir, Context, Result.ErrorMessage))
    {
        return Result;
    }

    TArray<FFixtureRun> CompliantRuns;
    TMap<FString, FString> CompliantHashes;
    if (!ExportTarget(
            RepoRootDir,
            Context,
            RaftSimFlex::EModelMode::Compliant,
            CompliantTargetId,
            CompliantSidecarSchema,
            TEXT("UnrealEngine5CustomReducedRigidBodyFlexibleRaftPort"),
            TEXT("compliant_measured_results_recorded_from_ue_flexible_raft_port"),
            TEXT("flexible_raft_d6_ue_compliant_measured_results.json"),
            CompliantRuns,
            CompliantHashes,
            Result.CompliantSidecarPath,
            Result.ErrorMessage))
    {
        return Result;
    }

    TArray<FFixtureRun> BaselineRuns;
    TMap<FString, FString> BaselineHashes;
    if (!ExportTarget(
            RepoRootDir,
            Context,
            RaftSimFlex::EModelMode::RigidBaseline,
            BaselineTargetId,
            BaselineSidecarSchema,
            TEXT("UnrealEngine5RigidBaseline"),
            TEXT("chaos_baseline_measured_results_recorded_from_ue_rigid_pass"),
            TEXT("flexible_raft_d6_ue_chaos_baseline_measured_results.json"),
            BaselineRuns,
            BaselineHashes,
            Result.ChaosBaselineSidecarPath,
            Result.ErrorMessage))
    {
        return Result;
    }

    // Runner summary: provenance target for every sidecar record.
    TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
    Summary->SetStringField(TEXT("schema"), TEXT("raftsim.flexible_raft.d6_ue_runner_summary.v1"));
    Summary->SetStringField(TEXT("generated_on"), GeneratedOn);
    Summary->SetStringField(TEXT("status"), TEXT("ue_measured_results_recorded"));
    Summary->SetBoolField(TEXT("d6_complete"), false);
    Summary->SetBoolField(TEXT("production_promoted"), false);
    Summary->SetStringField(
        TEXT("runtime"), TEXT("UnrealEngine5CustomReducedRigidBodyFlexibleRaftPort"));
    Summary->SetStringField(TEXT("engine_version"), EngineVersionString());
    Summary->SetStringField(TEXT("source_fixture_input_package_path"), PackageRelativePath);
    Summary->SetNumberField(TEXT("fixture_count"), CompliantRuns.Num());

    TArray<TSharedPtr<FJsonValue>> Jobs;
    auto AddJobs = [&Jobs](
        const FString& TargetId,
        const TArray<FFixtureRun>& Runs,
        const TMap<FString, FString>& Hashes)
    {
        for (const FFixtureRun& Run : Runs)
        {
            TSharedPtr<FJsonObject> Job = MakeShared<FJsonObject>();
            Job->SetStringField(TEXT("fixture_id"), Run.FixtureId);
            Job->SetStringField(TEXT("target_id"), TargetId);
            Job->SetStringField(TEXT("status"), TEXT("measured_engine_output"));
            Job->SetStringField(
                TEXT("telemetry_path"),
                FString::Printf(
                    TEXT("%s/replays/%s/%s.telemetry.json"),
                    ExportRelativeDir,
                    *TargetId,
                    *Run.FixtureId));
            Job->SetStringField(TEXT("telemetry_sha256"), Hashes.FindChecked(Run.FixtureId));
            Jobs.Add(MakeShared<FJsonValueObject>(Job));
        }
    };
    AddJobs(CompliantTargetId, CompliantRuns, CompliantHashes);
    AddJobs(BaselineTargetId, BaselineRuns, BaselineHashes);
    Summary->SetArrayField(TEXT("jobs"), Jobs);

    TSharedPtr<FJsonObject> PromotionGate = MakeShared<FJsonObject>();
    PromotionGate->SetBoolField(TEXT("may_mark_d6_complete"), false);
    PromotionGate->SetBoolField(TEXT("may_drive_runtime_gameplay"), false);
    PromotionGate->SetStringField(
        TEXT("reason"),
        TEXT("Measured UE results feed the physics-side D6 merge and comparison harness; promotion still requires the regenerated comparison report and manual review."));
    Summary->SetObjectField(TEXT("promotion_gate"), PromotionGate);

    Result.SummaryPath = FPaths::Combine(RepoRootDir, SummaryRelativePath);
    FString UnusedSha;
    if (!WriteJsonFile(Result.SummaryPath, Summary, UnusedSha))
    {
        Result.ErrorMessage = FString::Printf(TEXT("Failed to write summary: %s"), *Result.SummaryPath);
        return Result;
    }

    Result.FixtureCount = CompliantRuns.Num();
    Result.CompliantFilledCount = CompliantRuns.Num();
    Result.BaselineFilledCount = BaselineRuns.Num();
    Result.bSuccess = true;
    return Result;
}

} // namespace RaftSimFlexD6
