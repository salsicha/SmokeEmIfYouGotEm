#include "RaftSimRunAudioDirector.h"
#include "ProfilingDebugging/CsvProfiler.h"
CSV_DEFINE_CATEGORY(RaftSimTickAudio,true);

#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "RaftSimOarRig.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRunManager.h"
#include "RaftSimSynthVoice.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Sound/SoundAttenuation.h"

namespace
{
constexpr int32 LayerCount = 8;

enum class ELayer : uint8
{
    River,
    Rapid,
    Foam,
    Paddle,
    Fabric,
    Crew,
    Ambience,
    Music
};

ERaftSimSynthVoiceKind VoiceFor(ELayer Layer)
{
    switch (Layer)
    {
        case ELayer::River: return ERaftSimSynthVoiceKind::NearWater;
        case ELayer::Rapid: return ERaftSimSynthVoiceKind::Whitewater;
        case ELayer::Foam: return ERaftSimSynthVoiceKind::Spray;
        case ELayer::Paddle: return ERaftSimSynthVoiceKind::Strokes;
        case ELayer::Fabric: return ERaftSimSynthVoiceKind::Hull;
        case ELayer::Crew: return ERaftSimSynthVoiceKind::Crew;
        case ELayer::Ambience: return ERaftSimSynthVoiceKind::Ambience;
        default: return ERaftSimSynthVoiceKind::Music;
    }
}

void ConfigureComponent(UAudioComponent* Component, bool bSpatial)
{
    Component->bAutoActivate = false;
    Component->bIsUISound = false;
    Component->bAllowSpatialization = bSpatial;
    FSoundAttenuationSettings Settings;
    // Water round the boat keeps its level wherever the camera sits; it is
    // panned by where it is (port, starboard, bow), not faded by distance.
    Settings.bAttenuate = false;
    Settings.bSpatialize = bSpatial;
    Settings.NonSpatializedRadiusStart = 0.0f;
    Settings.NonSpatializedRadiusEnd = 0.0f;
    Settings.bEnableReverbSend = true;
    Settings.ReverbSendMethod = EReverbSendMethod::Manual;
    Settings.ManualReverbSendLevel = 0.2f;
    Component->bOverrideAttenuation = true;
    Component->SetAttenuationOverrides(Settings);
}

void ConfigureDistantComponent(UAudioComponent* Component)
{
    Component->bAutoActivate = false;
    Component->bIsUISound = false;
    Component->bAllowSpatialization = true;
    FSoundAttenuationSettings Settings;
    // A rapid ahead fades with distance like a real source: full within
    // 15 m, -42 dB by 250 m. The voice itself darkens with distance (air
    // and canyon absorb the highs first).
    Settings.bAttenuate = true;
    Settings.bSpatialize = true;
    Settings.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
    Settings.AttenuationShape = EAttenuationShape::Sphere;
    Settings.AttenuationShapeExtents = FVector(1500.0f, 0.0f, 0.0f);
    Settings.FalloffDistance = 23500.0f;
    Settings.dBAttenuationAtMax = -42.0f;
    Settings.bEnableReverbSend = true;
    Settings.ReverbSendMethod = EReverbSendMethod::Manual;
    Settings.ManualReverbSendLevel = 0.35f;
    Component->bOverrideAttenuation = true;
    Component->SetAttenuationOverrides(Settings);
}

float Decay(float Value, float DeltaSeconds, float Rate)
{
    // FInterpTo clamps DeltaSeconds * Rate to one. A single render/loading
    // hitch can therefore erase an event envelope in one tick, making paddle
    // and rescue transients inaudible. Exponential decay preserves the same
    // frame-rate-independent time constant without a hitch-to-zero branch.
    return Value * FMath::Exp(-Rate * FMath::Max(DeltaSeconds, 0.0f));
}

float Glide(float Value, float Target, float DeltaSeconds, float TauSeconds)
{
    return Value + (Target - Value) * (1.0f - FMath::Exp(-DeltaSeconds / FMath::Max(TauSeconds, 0.001f)));
}

void SetVoice(URaftSimSynthSoundWave* Wave, float Level, float Intensity, float Surge = 0.0f, float Distance = 0.0f)
{
    if (RaftSimSynth::FVoice* Voice = Wave ? Wave->GetVoice() : nullptr)
    {
        RaftSimSynth::FControls& Controls = Voice->GetControls();
        Controls.Level.store(Level, std::memory_order_relaxed);
        Controls.Intensity.store(Intensity, std::memory_order_relaxed);
        Controls.Surge.store(Surge, std::memory_order_relaxed);
        Controls.Distance.store(Distance, std::memory_order_relaxed);
    }
}

void Trigger(URaftSimSynthSoundWave* Wave, ERaftSimSynthEvent Event, float Strength)
{
    if (RaftSimSynth::FVoice* Voice = Wave ? Wave->GetVoice() : nullptr)
    {
        Voice->Trigger(Event, Strength);
    }
}
}

ARaftSimRunAudioDirector::ARaftSimRunAudioDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    RiverAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RiverBed"));
    RapidAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RapidFeatures"));
    FoamAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("FoamAndSpray"));
    PaddleAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("Paddle"));
    FabricAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("FabricAndImpact"));
    CrewAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("CrewAndRescue"));
    AmbienceAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("CanyonAmbience"));
    MusicAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("AdaptiveMusic"));
    RiverAudioStarboard = CreateDefaultSubobject<UAudioComponent>(TEXT("RiverBedStarboard"));
    RapidAudioStarboard = CreateDefaultSubobject<UAudioComponent>(TEXT("RapidFeaturesStarboard"));
    DistantRapidAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("DistantRapid"));
    for (UAudioComponent* Component : {
             RiverAudio.Get(), RapidAudio.Get(), FoamAudio.Get(), PaddleAudio.Get(),
             FabricAudio.Get(), CrewAudio.Get(), AmbienceAudio.Get(), MusicAudio.Get(),
             RiverAudioStarboard.Get(), RapidAudioStarboard.Get(), DistantRapidAudio.Get()})
    {
        Component->SetupAttachment(Root);
    }
    // Where each sound sits round the boat (the actor follows the raft's
    // position and heading): water along both tubes, whitewater a little
    // further out and ahead, spray over the bow.
    RiverAudio->SetRelativeLocation(FVector(0.0f, -220.0f, 0.0f));
    RiverAudioStarboard->SetRelativeLocation(FVector(0.0f, 220.0f, 0.0f));
    RapidAudio->SetRelativeLocation(FVector(80.0f, -320.0f, 0.0f));
    RapidAudioStarboard->SetRelativeLocation(FVector(80.0f, 320.0f, 0.0f));
    FoamAudio->SetRelativeLocation(FVector(200.0f, 0.0f, 40.0f));
    PaddleAudio->SetRelativeLocation(FVector(20.0f, 0.0f, 0.0f));
    CrewAudio->SetRelativeLocation(FVector(-100.0f, 0.0f, 80.0f));
    DistantRapidAudio->SetUsingAbsoluteLocation(true);
    ConfigureComponent(RiverAudio, true);
    ConfigureComponent(RiverAudioStarboard, true);
    ConfigureComponent(RapidAudio, true);
    ConfigureComponent(RapidAudioStarboard, true);
    ConfigureComponent(FoamAudio, true);
    ConfigureComponent(PaddleAudio, true);
    ConfigureComponent(FabricAudio, true);
    ConfigureComponent(CrewAudio, true);
    ConfigureComponent(AmbienceAudio, false);
    ConfigureComponent(MusicAudio, false);
    ConfigureDistantComponent(DistantRapidAudio);
}

void ARaftSimRunAudioDirector::BeginPlay()
{
    Super::BeginPlay();
    if (const UGameInstance* GI = GetGameInstance())
    {
        Bridge = GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    }
    if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It) Raft = *It;
    if (TActorIterator<ARaftSimRunManager> It(GetWorld()); It) RunManager = *It;
    if (TActorIterator<ARaftSimPresentationDirector> It(GetWorld()); It) PresentationDirector = *It;
    if (Raft != nullptr)
    {
        LastSwimmerCount = Raft->GetSwimmerCount();
        LastPaddleStrokeCount = Raft->GetPaddleStrokeCount();
        LastCrewCatchCount = Raft->GetCrewStrokeCatchCount();
        LastHighSideCount = Raft->GetHighSideResponseCount();
        LastRescueCount = Raft->GetCompletedRescueCount();
        LastCrewCommand = static_cast<uint8>(Raft->GetActiveCrewCommand());
        LastVerticalSpeed = Raft->GetRaftVelocity().Z;
    }
    CrewEnvelope = 0.52f;
    InitializeProductionLayers();
}

void ARaftSimRunAudioDirector::InitializeProductionLayers()
{
    LayerWaves.Reset();
    ExtraWaves.Reset();
    const TArray<UAudioComponent*> Components = {
        RiverAudio, RapidAudio, FoamAudio, PaddleAudio,
        FabricAudio, CrewAudio, AmbienceAudio, MusicAudio};
    auto Start = [this](UAudioComponent* Component, ERaftSimSynthVoiceKind Kind, uint32 Seed)
    {
        URaftSimSynthSoundWave* Wave = NewObject<URaftSimSynthSoundWave>(this);
        Wave->InitializeVoice(Kind, Seed);
        Component->SetSound(Wave);
        Component->SetVolumeMultiplier(1.0f);
        Component->Play();
        return Wave;
    };
    for (int32 LayerIndex = 0; LayerIndex < LayerCount; ++LayerIndex)
    {
        LayerWaves.Add(Start(Components[LayerIndex], VoiceFor(static_cast<ELayer>(LayerIndex)), 101u + LayerIndex));
    }
    // Different seeds: the two sides of the boat never play the same water.
    ExtraWaves.Add(Start(RiverAudioStarboard, ERaftSimSynthVoiceKind::NearWater, 211u));
    ExtraWaves.Add(Start(RapidAudioStarboard, ERaftSimSynthVoiceKind::Whitewater, 223u));
    ExtraWaves.Add(Start(DistantRapidAudio, ERaftSimSynthVoiceKind::Whitewater, 227u));
}

float ARaftSimRunAudioDirector::SampleWhitewater(const FVector& WorldCm, float* OutSpeed) const
{
    const URaftSimWaterRuntimeAdapter* Water = Bridge != nullptr ? Bridge->GetWaterRuntime() : nullptr;
    FRaftSimWaterSample Sample;
    if (Water == nullptr || !Water->SampleWaterAtWorldPosition(WorldCm, Sample) || !Sample.bWet)
    {
        return 0.0f;
    }
    const float Speed = Sample.VelocityMetersPerSecond.Size2D();
    if (OutSpeed != nullptr)
    {
        *OutSpeed = Speed;
    }
    // Water breaks white where the flow goes supercritical (hydraulic jumps,
    // tongues, holes) and where the surface stands steep in waves.
    const float Froude = Speed / FMath::Sqrt(9.80665f * FMath::Max(Sample.DepthMeters, 0.1f));
    const float Aerated = FMath::Clamp((Froude - 0.7f) / 0.7f, 0.0f, 1.0f);
    const float Steep = FMath::Clamp((1.0f - Sample.SurfaceNormal.Z) / 0.05f, 0.0f, 1.0f);
    return FMath::Max(Aerated, 0.8f * Steep);
}

void ARaftSimRunAudioDirector::UpdateEventEnvelopes(float DeltaSeconds)
{
    PaddleEnvelope = Decay(PaddleEnvelope, DeltaSeconds, 5.5f);
    FabricEnvelope = Decay(FabricEnvelope, DeltaSeconds, 3.5f);
    CrewEnvelope = Decay(CrewEnvelope, DeltaSeconds, 2.4f);
    if (Raft == nullptr) return;

    URaftSimSynthSoundWave* Strokes = LayerWaves.IsValidIndex(3) ? LayerWaves[3].Get() : nullptr;
    URaftSimSynthSoundWave* Hull = LayerWaves.IsValidIndex(4) ? LayerWaves[4].Get() : nullptr;
    const int32 Paddles = Raft->GetPaddleStrokeCount();
    const int32 CrewCatches = Raft->GetCrewStrokeCatchCount();
    const int32 HighSides = Raft->GetHighSideResponseCount();
    const int32 Rescues = Raft->GetCompletedRescueCount();
    const int32 Swimmers = Raft->GetSwimmerCount();
    const uint8 Command = static_cast<uint8>(Raft->GetActiveCrewCommand());
    // Each blade's catch plays as it actually enters the water: the guide's
    // own stroke, the crew's planted blades, or an oar.
    if (Paddles != LastPaddleStrokeCount)
    {
        PaddleEnvelope = 1.0f;
        Trigger(Strokes, ERaftSimSynthEvent::PaddleCatch, 0.9f);
    }
    if (CrewCatches != LastCrewCatchCount)
    {
        PaddleEnvelope = FMath::Max(PaddleEnvelope, 0.8f);
        PaddleAudio->SetRelativeLocation(FVector(40.0f, 0.0f, 0.0f));
        Trigger(Strokes, ERaftSimSynthEvent::PaddleCatch, 1.0f);
    }
    if (const URaftSimOarRigComponent* Oars = Raft->IsSoloOarRig() ? Raft->GetOarRig() : nullptr)
    {
        for (const bool bLeft : {true, false})
        {
            const int32 Side = bLeft ? 0 : 1;
            const int32 Catches = Oars->GetCatchCount(bLeft);
            const int32 Releases = Oars->GetReleaseCount(bLeft);
            if (Catches != LastOarCatches[Side])
            {
                PaddleEnvelope = 1.0f;
                PaddleAudio->SetRelativeLocation(FVector(0.0f, bLeft ? -230.0f : 230.0f, -20.0f));
                Trigger(Strokes, ERaftSimSynthEvent::OarCatch, FMath::Max(Oars->GetLastCatchEffort(bLeft), 0.4f));
            }
            if (Releases != LastOarReleases[Side])
            {
                Trigger(Strokes, ERaftSimSynthEvent::OarRelease, 0.8f);
            }
            LastOarCatches[Side] = Catches;
            LastOarReleases[Side] = Releases;
        }
    }
    if (HighSides != LastHighSideCount)
    {
        FabricEnvelope = FMath::Max(FabricEnvelope, 0.7f);
        Trigger(Hull, ERaftSimSynthEvent::HullSlap, 0.5f);
    }
    if (Rescues != LastRescueCount || Swimmers != LastSwimmerCount) CrewEnvelope = 1.0f;
    if (Command != LastCrewCommand) CrewEnvelope = FMath::Max(CrewEnvelope, 0.72f);
    if (Raft->GetActiveWaterContactCount() > 0)
    {
        FabricEnvelope = FMath::Max(
            FabricEnvelope,
            FMath::Clamp(Raft->GetMaximumWaterContactIndentationM() / 0.18f, 0.15f, 1.0f));
    }
    // The hull meeting water or rock: a slam when the boat's fall is
    // stopped hard (dropping off a wave into the trough), a thump and slap
    // when it first strikes rock, and a scrape while it drags.
    SlamCooldown -= DeltaSeconds;
    const float VerticalSpeed = Raft->GetRaftVelocity().Z;
    const float Arrest = (VerticalSpeed - LastVerticalSpeed) / FMath::Max(DeltaSeconds, 0.005f);
    if (LastVerticalSpeed < -0.35f && Arrest > 5.0f && SlamCooldown <= 0.0f)
    {
        const float Strength = FMath::Clamp(-LastVerticalSpeed / 1.5f, 0.2f, 1.0f);
        Trigger(Hull, ERaftSimSynthEvent::HullThump, Strength);
        Trigger(Hull, ERaftSimSynthEvent::HullSlap, 0.6f * Strength);
        FabricEnvelope = FMath::Max(FabricEnvelope, Strength);
        SlamCooldown = 0.35f;
    }
    LastVerticalSpeed = VerticalSpeed;
    const int32 RockContacts = Raft->GetWrappingRockContactCount() + Raft->GetRecoveringRockContactCount() +
        Raft->GetPinnedRockObstacleCount();
    if (RockContacts > LastRockContactCount)
    {
        Trigger(Hull, ERaftSimSynthEvent::HullThump, 0.9f);
        Trigger(Hull, ERaftSimSynthEvent::HullSlap, 0.5f);
        FabricEnvelope = FMath::Max(FabricEnvelope, 0.9f);
    }
    const float ScrapeTarget = RockContacts > 0
        ? FMath::Clamp(0.35f + Raft->GetRaftVelocity().Size2D() / 2.0f, 0.0f, 1.0f)
        : 0.0f;
    Scrape = Glide(Scrape, ScrapeTarget, DeltaSeconds, ScrapeTarget > Scrape ? 0.05f : 0.25f);
    LastRockContactCount = RockContacts;
    LastPaddleStrokeCount = Paddles;
    LastCrewCatchCount = CrewCatches;
    LastHighSideCount = HighSides;
    LastRescueCount = Rescues;
    LastSwimmerCount = Swimmers;
    LastCrewCommand = Command;
}

void ARaftSimRunAudioDirector::UpdateDistantRapid(float DeltaSeconds)
{
    // Survey the water round the boat out to 150 m and keep the spot that
    // would sound loudest from here: the most whitewater, the fastest water,
    // the nearest. Water within 16 m is the near layer's. A survey starts at
    // most every 0.3 s and is spread over frames: all 112 water samples in one
    // frame cost ~11 ms, a visible hitch whenever it ran.
    static constexpr float RingsMeters[] = {16.0f, 26.0f, 40.0f, 58.0f, 80.0f, 110.0f, 150.0f};
    constexpr int32 Bearings = 16;
    constexpr int32 SurveySamples = UE_ARRAY_COUNT(RingsMeters) * Bearings;
    constexpr int32 SamplesPerFrame = 4;
    DistantSearchSeconds -= DeltaSeconds;
    if (DistantSurveyIndex == 0 && DistantSearchSeconds <= 0.0f)
    {
        DistantSearchSeconds = 0.3f;
        SurveyCenter = Raft->GetActorLocation();
        SurveyBestLoudness = 0.0f;
        SurveyBestWhitewater = 0.0f;
        SurveyBest = FVector::ZeroVector;
        DistantSurveyIndex = 1;
    }
    for (int32 Step = 0; DistantSurveyIndex > 0 && Step < SamplesPerFrame; ++Step)
    {
        const int32 Sample = DistantSurveyIndex - 1;
        const float Ring = RingsMeters[Sample / Bearings];
        const int32 Bearing = Sample % Bearings;
        const float Angle = (Bearing + 0.5f * (static_cast<int32>(Ring) % 2)) * UE_TWO_PI / Bearings;
        const FVector Point = SurveyCenter + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Ring * 100.0f;
        float Speed = 0.0f;
        const float Whitewater = SampleWhitewater(Point, &Speed);
        if (Whitewater >= 0.15f)
        {
            const float Loudness = Whitewater * Whitewater * FMath::Clamp(Speed / 3.0f, 0.3f, 1.5f) /
                (1.0f + Ring / 25.0f);
            if (Loudness > SurveyBestLoudness)
            {
                SurveyBestLoudness = Loudness;
                SurveyBestWhitewater = Whitewater;
                SurveyBest = Point;
            }
        }
        if (++DistantSurveyIndex <= SurveySamples)
        {
            continue;
        }
        DistantSurveyIndex = 0;
        DistantTargetLevel = SurveyBestLoudness > 0.01f
            ? FMath::Clamp(FMath::Sqrt(SurveyBestLoudness) * 1.6f, 0.0f, 1.0f) : 0.0f;
        DistantTargetIntensity = SurveyBestWhitewater;
        if (SurveyBestLoudness > 0.01f)
        {
            DistantTarget = SurveyBest;
            if (!bHasDistantLocation)
            {
                DistantLocation = SurveyBest;
                bHasDistantLocation = true;
            }
        }
    }
    if (bHasDistantLocation)
    {
        // The source glides between surveyed spots instead of jumping.
        DistantLocation = FMath::Lerp(DistantLocation, DistantTarget, 1.0f - FMath::Exp(-DeltaSeconds / 1.2f));
        DistantRapidAudio->SetWorldLocation(DistantLocation);
    }
    DistantLevel = Glide(DistantLevel, DistantTargetLevel, DeltaSeconds, 1.0f);
    MixState.DistantRapidDistanceMeters = bHasDistantLocation
        ? static_cast<float>(FVector::Dist(DistantLocation, Raft->GetActorLocation()) / 100.0)
        : 0.0f;
}

void ARaftSimRunAudioDirector::Tick(float DeltaSeconds)
{
    CSV_SCOPED_TIMING_STAT(RaftSimTickAudio,Tick);
    Super::Tick(DeltaSeconds);
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.25f);
    UpdateEventEnvelopes(Dt);
    if (Raft == nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It) Raft = *It;
        return;
    }
    SetActorLocationAndRotation(Raft->GetActorLocation(), FRotator(0.0f, Raft->GetActorRotation().Yaw, 0.0f));

    FRaftSimWaterAudioTelemetry Telemetry;
    const FVector RaftVelocity = Raft->GetRaftVelocity();
    Telemetry.FlowSpeedMetersPerSecond = RaftVelocity.Size();
    FVector WaterVelocity = FVector::ZeroVector;
    float Froude = 0.0f;
    if (const URaftSimWaterRuntimeAdapter* Water = Bridge != nullptr ? Bridge->GetWaterRuntime() : nullptr)
    {
        FRaftSimWaterSample Sample;
        if (Water->SampleWaterAtWorldPosition(Raft->GetActorLocation(), Sample) && Sample.bWet)
        {
            WaterVelocity = Sample.VelocityMetersPerSecond;
            const float FlowSpeed = WaterVelocity.Size2D();
            Telemetry.FlowSpeedMetersPerSecond = FMath::Max(Telemetry.FlowSpeedMetersPerSecond, FlowSpeed);
            Froude = FlowSpeed / FMath::Sqrt(9.80665f * FMath::Max(Sample.DepthMeters, 0.1f));
            Telemetry.Aeration = FMath::Clamp((Froude - 0.6f) / 0.8f, 0.0f, 1.0f);
            // Turbulence is its own measure, not the aeration again: shear
            // across the boat (eddy lines, boils) and a broken, tilted
            // surface (waves).
            // Four extra field samples; the turbulence they feed glides over
            // 0.4 s, so refreshing the shear every other frame is enough.
            bSampleShearThisFrame = !bSampleShearThisFrame;
            if (bSampleShearThisFrame)
            {
                LastShear = 0.0f;
                for (const FVector& Offset : {FVector(300.0f, 0.0f, 0.0f), FVector(-300.0f, 0.0f, 0.0f),
                         FVector(0.0f, 300.0f, 0.0f), FVector(0.0f, -300.0f, 0.0f)})
                {
                    FRaftSimWaterSample Near;
                    if (Water->SampleWaterAtWorldPosition(Raft->GetActorLocation() + Offset, Near) && Near.bWet)
                    {
                        LastShear = FMath::Max(LastShear, static_cast<float>((Near.VelocityMetersPerSecond - WaterVelocity).Size2D()) / 3.0f);
                    }
                }
            }
            const float Shear = LastShear;
            const float Tilt = FMath::Clamp((1.0f - Sample.SurfaceNormal.Z) / 0.06f, 0.0f, 1.0f);
            Telemetry.Turbulence = FMath::Clamp(FMath::Max(Shear / 0.8f, Tilt), 0.0f, 1.0f);
        }
    }
    LocalTurbulence = Glide(LocalTurbulence, Telemetry.Turbulence, Dt, 0.4f);
    Telemetry.Turbulence = LocalTurbulence;
    // Water past the tubes: the boat moving through it, or it through
    // rocks and eddies round the boat.
    const float Relative = static_cast<float>((RaftVelocity - WaterVelocity).Size2D());
    HullFlow = Glide(HullFlow,
        FMath::Clamp(Relative / 2.5f + 0.35f * LocalTurbulence + 0.08f * WaterVelocity.Size2D(), 0.0f, 1.0f), Dt, 0.3f);
    const float HeaveTarget = FMath::Clamp(FMath::Abs(RaftVelocity.Z) / 0.5f, 0.0f, 1.0f);
    Heave = Glide(Heave, HeaveTarget, Dt, HeaveTarget > Heave ? 0.15f : 0.8f);
    Telemetry.PaddleCatchStrength = PaddleEnvelope;
    Telemetry.RockScrapeStrength = Scrape;
    Telemetry.RaftImpactImpulse = FabricEnvelope * 2500.0f;
    Telemetry.CrewVoiceActivity = CrewEnvelope;
    if (PresentationDirector != nullptr)
    {
        const FRaftSimPresentationEnvironmentState Environment =
            PresentationDirector->GetEnvironmentState();
        Telemetry.WeatherWetness = Environment.WeatherWetness;
        Telemetry.CanyonEnclosure = Environment.CanyonEnclosure;
    }
    CurrentParameters = RaftSimAudio::BuildWaterAudioParameters(Telemetry);
    UpdateDistantRapid(Dt);

    // A crew call dips the water only a little: the former 75 % duck pumped
    // the river under every command.
    const float Duck = 1.0f - 0.5f * CurrentParameters.CrewVoiceDuckAmount;
    MixState.RiverBed = FMath::Clamp((0.55f + 0.45f * HullFlow) * Duck, 0.0f, 1.0f);
    MixState.RapidFeatures = FMath::Clamp(CurrentParameters.RapidFeatureIntensity * 1.3f * Duck, 0.0f, 1.0f);
    // A loud rapid alongside masks the one ahead.
    MixState.DistantRapid = DistantLevel * (1.0f - 0.6f * MixState.RapidFeatures);
    MixState.FoamAndSpray = FMath::Clamp(CurrentParameters.SprayAndFoam * 0.9f + FabricEnvelope * 0.4f, 0.0f, 1.0f);
    // Rushing water buries the paddle: from the stern seat a stroke is
    // inaudible inside a rapid, and only a soft plunk in flat pools
    // (2026-08-10 playtest: "the rushing of the water should be loud
    // enough you can't hear the paddles at all").
    const float WaterLoudness = FMath::Clamp(
        CurrentParameters.RiverRoar * 0.5f + CurrentParameters.RapidFeatureIntensity * 0.9f +
            MixState.DistantRapid * 0.3f,
        0.0f, 1.0f);
    const float StrokeLevel = 1.0f - 0.75f * WaterLoudness;
    MixState.Paddle = PaddleEnvelope * 0.34f * StrokeLevel;
    MixState.PaddleStrokeEnvelope = PaddleEnvelope;
    MixState.FabricAndImpact = FMath::Clamp(FMath::Max(
        CurrentParameters.ImpactLayer, CurrentParameters.ScrapeLayer) * 0.9f, 0.0f, 1.0f);
    MixState.CrewAndRescue = CrewEnvelope * 0.78f;
    MixState.CanyonAmbience = FMath::Clamp(0.16f + CurrentParameters.CanyonReflection * 0.35f +
        CurrentParameters.WeatherLayer * 0.18f, 0.0f, 0.72f);
    const float Progress = RunManager != nullptr ? RunManager->GetProgressFraction() : 0.0f;
    MixState.Music = FMath::Clamp(0.075f + Progress * 0.08f + Froude * 0.035f - CrewEnvelope * 0.04f,
        0.035f, 0.22f);
    MixState.ReverbStrength = CurrentParameters.CanyonReflection;
    // No blanket low-pass: canyon walls reflect sound, they do not muffle the
    // river. Distance darkens the distant rapid inside its own voice.
    MixState.OcclusionLowPassHz = 20000.0f;
    MixState.ActiveLayerCount = LayerWaves.Num();

    const float RapidSurge = 0.4f + 0.6f * LocalTurbulence;
    SetVoice(LayerWaves[0], MixState.RiverBed, HullFlow, Heave);
    SetVoice(ExtraWaves[0], MixState.RiverBed, HullFlow, Heave);
    SetVoice(LayerWaves[1], MixState.RapidFeatures, CurrentParameters.RapidFeatureIntensity, RapidSurge);
    SetVoice(ExtraWaves[1], MixState.RapidFeatures, CurrentParameters.RapidFeatureIntensity, RapidSurge);
    SetVoice(ExtraWaves[2], MixState.DistantRapid, DistantTargetIntensity, 0.6f,
        MixState.DistantRapidDistanceMeters);
    SetVoice(LayerWaves[2], MixState.FoamAndSpray,
        FMath::Max(CurrentParameters.SprayAndFoam, 0.6f * FabricEnvelope));
    SetVoice(LayerWaves[3], StrokeLevel, 0.0f);
    SetVoice(LayerWaves[4], 0.9f, Scrape);
    SetVoice(LayerWaves[5], MixState.CrewAndRescue, 0.0f);
    SetVoice(LayerWaves[6], MixState.CanyonAmbience, 0.0f);
    SetVoice(LayerWaves[7], MixState.Music, 0.0f);
    ApplyMixToComponents();
    MixLogSeconds -= Dt;
    if (MixLogSeconds <= 0.0f)
    {
        // Throttled mix diagnostic: what the water sounds like and why, from
        // the session log alone.
        MixLogSeconds = 2.0f;
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim audio mix: river=%.2f flow=%.2f heave=%.2f rapid=%.2f turb=%.2f "
                 "distant=%.2f@%.0fm spray=%.2f strokes=%.2f scrape=%.2f"),
            MixState.RiverBed, HullFlow, Heave, MixState.RapidFeatures, LocalTurbulence,
            MixState.DistantRapid, MixState.DistantRapidDistanceMeters, MixState.FoamAndSpray,
            StrokeLevel, Scrape);
    }
}

void ARaftSimRunAudioDirector::ApplyMixToComponents()
{
    if (FMath::Abs(MixState.ReverbStrength - LastAppliedReverb) > 0.03f)
    {
        for (UAudioComponent* Component : {
                 RiverAudio.Get(), RapidAudio.Get(), FoamAudio.Get(), PaddleAudio.Get(),
                 FabricAudio.Get(), CrewAudio.Get(), AmbienceAudio.Get(), MusicAudio.Get(),
                 RiverAudioStarboard.Get(), RapidAudioStarboard.Get(), DistantRapidAudio.Get()})
        {
            if (Component != nullptr)
            {
                FSoundAttenuationSettings Settings = Component->AttenuationOverrides;
                Settings.bEnableReverbSend = true;
                Settings.ReverbSendMethod = EReverbSendMethod::Manual;
                Settings.ManualReverbSendLevel = Component == DistantRapidAudio
                    ? FMath::Max(0.35f, MixState.ReverbStrength)
                    : MixState.ReverbStrength;
                Component->SetAttenuationOverrides(Settings);
            }
        }
        LastAppliedReverb = MixState.ReverbStrength;
    }
}

bool ARaftSimRunAudioDirector::HasStreamingVoiceForEveryLayer() const
{
    if (LayerWaves.Num() != LayerCount)
    {
        return false;
    }
    for (const TObjectPtr<URaftSimSynthSoundWave>& Wave : LayerWaves)
    {
        if (Wave == nullptr || Wave->GetVoice() == nullptr)
        {
            return false;
        }
    }
    return true;
}
