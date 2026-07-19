#include "RaftSimRunAudioDirector.h"

#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRunManager.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Sound/SoundWaveProcedural.h"
#include "Sound/SoundAttenuation.h"

namespace
{
constexpr int32 SampleRate = 48000;
constexpr int32 SecondsPerLoop = 2;
constexpr int32 LayerCount = 8;

enum class ESynthLayer : uint8
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

float StableNoise(uint32& State)
{
    State = State * 1664525u + 1013904223u;
    return static_cast<float>((State >> 8) & 0x00FFFFFFu) / 8388607.5f - 1.0f;
}

TArray<uint8> BuildLayerPcm(ESynthLayer Layer)
{
    const int32 SampleCount = SampleRate * SecondsPerLoop;
    TArray<int16> Samples;
    Samples.SetNumUninitialized(SampleCount);
    uint32 NoiseState = 0x6d2b79f5u ^ (static_cast<uint32>(Layer) * 0x9e3779b9u);
    float Brown = 0.0f;
    float PreviousWhite = 0.0f;
    for (int32 Index = 0; Index < SampleCount; ++Index)
    {
        const float T = static_cast<float>(Index) / static_cast<float>(SampleRate);
        const float Phase = FMath::Fmod(T, 2.0f);
        const float White = StableNoise(NoiseState);
        Brown = FMath::Clamp(Brown * 0.985f + White * 0.035f, -1.0f, 1.0f);
        const float Blue = FMath::Clamp(White - PreviousWhite, -1.0f, 1.0f);
        PreviousWhite = White;
        float Signal = 0.0f;
        switch (Layer)
        {
            case ESynthLayer::River:
                Signal = Brown * 0.72f + White * 0.08f;
                break;
            case ESynthLayer::Rapid:
                Signal = White * 0.38f + Blue * 0.35f + Brown * 0.15f;
                break;
            case ESynthLayer::Foam:
                Signal = Blue * 0.42f + White * 0.18f;
                break;
            case ESynthLayer::Paddle:
            {
                const float Pulse = FMath::Exp(-18.0f * FMath::Fmod(Phase, 0.5f));
                Signal = Pulse * (White * 0.45f + FMath::Sin(2.0f * PI * 86.0f * T) * 0.32f);
                break;
            }
            case ESynthLayer::Fabric:
                Signal = FMath::Sin(2.0f * PI * (64.0f + 9.0f * Brown) * T) * 0.26f + Brown * 0.2f;
                break;
            case ESynthLayer::Crew:
            {
                const float VoiceGate = FMath::Pow(FMath::Max(0.0f, FMath::Sin(PI * Phase)), 3.0f);
                Signal = VoiceGate * (FMath::Sin(2.0f * PI * 168.0f * T) * 0.33f +
                    FMath::Sin(2.0f * PI * 252.0f * T) * 0.19f + Brown * 0.08f);
                break;
            }
            case ESynthLayer::Ambience:
            {
                const float Bird = FMath::Pow(FMath::Max(0.0f, FMath::Sin(PI * Phase * 2.0f)), 16.0f) *
                    FMath::Sin(2.0f * PI * (1250.0f + 220.0f * FMath::Sin(2.0f * PI * T)) * T);
                Signal = Brown * 0.18f + Bird * 0.14f;
                break;
            }
            case ESynthLayer::Music:
                Signal = FMath::Sin(2.0f * PI * 73.42f * T) * 0.22f +
                    FMath::Sin(2.0f * PI * 110.0f * T) * 0.14f +
                    FMath::Sin(2.0f * PI * 146.84f * T) * 0.1f;
                break;
        }
        Samples[Index] = static_cast<int16>(FMath::Clamp(Signal, -0.95f, 0.95f) * 32767.0f);
    }

    TArray<uint8> Bytes;
    Bytes.SetNumUninitialized(Samples.Num() * sizeof(int16));
    FMemory::Memcpy(Bytes.GetData(), Samples.GetData(), Bytes.Num());
    return Bytes;
}

void ConfigureWave(USoundWaveProcedural* Wave)
{
    Wave->SetSampleRate(SampleRate);
    Wave->NumChannels = 1;
    Wave->Duration = INDEFINITELY_LOOPING_DURATION;
    Wave->SoundGroup = SOUNDGROUP_Default;
    Wave->bLooping = true;
}

void ConfigureComponent(UAudioComponent* Component, bool bSpatial)
{
    Component->bAutoActivate = false;
    Component->bIsUISound = false;
    Component->bAllowSpatialization = bSpatial;
    Component->bEnableLowPassFilter = true;
    Component->SetLowPassFilterFrequency(20000.0f);
    FSoundAttenuationSettings Settings;
    Settings.bAttenuate = false;
    Settings.bSpatialize = bSpatial;
    Settings.bEnableReverbSend = true;
    Settings.ReverbSendMethod = EReverbSendMethod::Manual;
    Settings.ManualReverbSendLevel = 0.2f;
    Component->bOverrideAttenuation = true;
    Component->SetAttenuationOverrides(Settings);
}

float Decay(float Value, float DeltaSeconds, float Rate)
{
    return FMath::FInterpTo(Value, 0.0f, DeltaSeconds, Rate);
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
    for (UAudioComponent* Component : {
             RiverAudio.Get(), RapidAudio.Get(), FoamAudio.Get(), PaddleAudio.Get(),
             FabricAudio.Get(), CrewAudio.Get(), AmbienceAudio.Get(), MusicAudio.Get()})
    {
        Component->SetupAttachment(Root);
    }
    ConfigureComponent(RiverAudio, false);
    ConfigureComponent(RapidAudio, true);
    ConfigureComponent(FoamAudio, true);
    ConfigureComponent(PaddleAudio, true);
    ConfigureComponent(FabricAudio, true);
    ConfigureComponent(CrewAudio, true);
    ConfigureComponent(AmbienceAudio, false);
    ConfigureComponent(MusicAudio, false);
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
        LastHighSideCount = Raft->GetHighSideResponseCount();
        LastRescueCount = Raft->GetCompletedRescueCount();
        LastCrewCommand = static_cast<uint8>(Raft->GetActiveCrewCommand());
    }
    CrewEnvelope = 0.52f;
    InitializeProductionLayers();
}

void ARaftSimRunAudioDirector::InitializeProductionLayers()
{
    LayerWaves.Reset();
    LayerPcm.Reset();
    const TArray<UAudioComponent*> Components = {
        RiverAudio, RapidAudio, FoamAudio, PaddleAudio,
        FabricAudio, CrewAudio, AmbienceAudio, MusicAudio};
    for (int32 LayerIndex = 0; LayerIndex < LayerCount; ++LayerIndex)
    {
        USoundWaveProcedural* Wave = NewObject<USoundWaveProcedural>(this);
        ConfigureWave(Wave);
        LayerPcm.Add(BuildLayerPcm(static_cast<ESynthLayer>(LayerIndex)));
        Wave->QueueAudio(LayerPcm.Last().GetData(), LayerPcm.Last().Num());
        LayerWaves.Add(Wave);
        Components[LayerIndex]->SetSound(Wave);
        Components[LayerIndex]->SetVolumeMultiplier(0.0f);
        Components[LayerIndex]->Play();
    }
}

void ARaftSimRunAudioDirector::RefillProceduralLayers()
{
    for (int32 Index = 0; Index < LayerWaves.Num() && Index < LayerPcm.Num(); ++Index)
    {
        USoundWaveProcedural* Wave = LayerWaves[Index];
        const TArray<uint8>& Buffer = LayerPcm[Index];
        if (Wave != nullptr && Wave->GetAvailableAudioByteCount() < Buffer.Num() / 2)
        {
            Wave->QueueAudio(Buffer.GetData(), Buffer.Num());
        }
    }
}

void ARaftSimRunAudioDirector::UpdateEventEnvelopes(float DeltaSeconds)
{
    PaddleEnvelope = Decay(PaddleEnvelope, DeltaSeconds, 5.5f);
    FabricEnvelope = Decay(FabricEnvelope, DeltaSeconds, 3.5f);
    CrewEnvelope = Decay(CrewEnvelope, DeltaSeconds, 2.4f);
    if (Raft == nullptr) return;

    const int32 Paddles = Raft->GetPaddleStrokeCount();
    const int32 HighSides = Raft->GetHighSideResponseCount();
    const int32 Rescues = Raft->GetCompletedRescueCount();
    const int32 Swimmers = Raft->GetSwimmerCount();
    const uint8 Command = static_cast<uint8>(Raft->GetActiveCrewCommand());
    if (Paddles != LastPaddleStrokeCount) PaddleEnvelope = 1.0f;
    if (HighSides != LastHighSideCount) FabricEnvelope = FMath::Max(FabricEnvelope, 0.7f);
    if (Rescues != LastRescueCount || Swimmers != LastSwimmerCount) CrewEnvelope = 1.0f;
    if (Command != LastCrewCommand) CrewEnvelope = FMath::Max(CrewEnvelope, 0.72f);
    if (Raft->GetActiveWaterContactCount() > 0)
    {
        FabricEnvelope = FMath::Max(
            FabricEnvelope,
            FMath::Clamp(Raft->GetMaximumWaterContactIndentationM() / 0.18f, 0.15f, 1.0f));
    }
    LastPaddleStrokeCount = Paddles;
    LastHighSideCount = HighSides;
    LastRescueCount = Rescues;
    LastSwimmerCount = Swimmers;
    LastCrewCommand = Command;
}

void ARaftSimRunAudioDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    RefillProceduralLayers();
    UpdateEventEnvelopes(DeltaSeconds);
    if (Raft == nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It) Raft = *It;
        return;
    }
    SetActorLocation(Raft->GetActorLocation());

    FRaftSimWaterAudioTelemetry Telemetry;
    const float RaftSpeed = Raft->GetRaftVelocity().Size();
    Telemetry.FlowSpeedMetersPerSecond = RaftSpeed;
    float Froude = 0.0f;
    if (Bridge != nullptr)
    {
        if (const URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(Raft->GetActorLocation(), Sample) && Sample.bWet)
            {
                const float FlowSpeed = Sample.VelocityMetersPerSecond.Size2D();
                Telemetry.FlowSpeedMetersPerSecond = FMath::Max(RaftSpeed, FlowSpeed);
                Froude = FlowSpeed / FMath::Sqrt(9.80665f * FMath::Max(Sample.DepthMeters, 0.1f));
                Telemetry.Aeration = FMath::Clamp((Froude - 0.6f) / 0.8f, 0.0f, 1.0f);
                Telemetry.Turbulence = Telemetry.Aeration;
            }
        }
    }
    Telemetry.PaddleCatchStrength = PaddleEnvelope;
    Telemetry.RockScrapeStrength = FabricEnvelope;
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
    const float Duck = 1.0f - CurrentParameters.CrewVoiceDuckAmount;
    MixState.RiverBed = FMath::Clamp((0.12f + CurrentParameters.RiverRoar * 0.75f) * Duck, 0.0f, 1.0f);
    MixState.RapidFeatures = FMath::Clamp(CurrentParameters.RapidFeatureIntensity * 0.82f * Duck, 0.0f, 1.0f);
    MixState.FoamAndSpray = FMath::Clamp(CurrentParameters.SprayAndFoam * 0.64f, 0.0f, 1.0f);
    MixState.Paddle = PaddleEnvelope * 0.82f;
    MixState.FabricAndImpact = FMath::Clamp(FMath::Max(
        CurrentParameters.ImpactLayer, CurrentParameters.ScrapeLayer) * 0.9f, 0.0f, 1.0f);
    MixState.CrewAndRescue = CrewEnvelope * 0.78f;
    MixState.CanyonAmbience = FMath::Clamp(0.16f + CurrentParameters.CanyonReflection * 0.35f +
        CurrentParameters.WeatherLayer * 0.18f, 0.0f, 0.72f);
    const float Progress = RunManager != nullptr ? RunManager->GetProgressFraction() : 0.0f;
    MixState.Music = FMath::Clamp(0.075f + Progress * 0.08f + Froude * 0.035f - CrewEnvelope * 0.04f,
        0.035f, 0.22f);
    MixState.ReverbStrength = CurrentParameters.CanyonReflection;
    MixState.OcclusionLowPassHz = FMath::Lerp(20000.0f, 4200.0f,
        FMath::Clamp(CurrentParameters.CanyonReflection * 0.45f + Telemetry.WeatherWetness * 0.25f, 0.0f, 1.0f));
    MixState.ActiveLayerCount = LayerWaves.Num();
    ApplyMixToComponents();
}

void ARaftSimRunAudioDirector::ApplyMixToComponents()
{
    const TArray<TPair<UAudioComponent*, float>> Layers = {
        {RiverAudio, MixState.RiverBed}, {RapidAudio, MixState.RapidFeatures},
        {FoamAudio, MixState.FoamAndSpray}, {PaddleAudio, MixState.Paddle},
        {FabricAudio, MixState.FabricAndImpact}, {CrewAudio, MixState.CrewAndRescue},
        {AmbienceAudio, MixState.CanyonAmbience}, {MusicAudio, MixState.Music}};
    for (const TPair<UAudioComponent*, float>& Layer : Layers)
    {
        if (Layer.Key != nullptr)
        {
            Layer.Key->SetVolumeMultiplier(Layer.Value);
            Layer.Key->SetLowPassFilterFrequency(MixState.OcclusionLowPassHz);
        }
    }
    if (FMath::Abs(MixState.ReverbStrength - LastAppliedReverb) > 0.03f)
    {
        for (const TPair<UAudioComponent*, float>& Layer : Layers)
        {
            if (Layer.Key != nullptr)
            {
                FSoundAttenuationSettings Settings = Layer.Key->AttenuationOverrides;
                Settings.bEnableReverbSend = true;
                Settings.ReverbSendMethod = EReverbSendMethod::Manual;
                Settings.ManualReverbSendLevel = MixState.ReverbStrength;
                Layer.Key->SetAttenuationOverrides(Settings);
            }
        }
        LastAppliedReverb = MixState.ReverbStrength;
    }
    RapidAudio->SetPitchMultiplier(0.9f + CurrentParameters.RapidFeatureIntensity * 0.35f);
    FabricAudio->SetPitchMultiplier(0.82f + FabricEnvelope * 0.3f);
    CrewAudio->SetPitchMultiplier(0.96f + CrewEnvelope * 0.08f);
}

bool ARaftSimRunAudioDirector::HasQueuedPcmForEveryLayer() const
{
    if (LayerWaves.Num() != LayerCount || LayerPcm.Num() != LayerCount)
    {
        return false;
    }
    for (int32 Index = 0; Index < LayerCount; ++Index)
    {
        if (LayerWaves[Index] == nullptr || LayerPcm[Index].IsEmpty() ||
            LayerWaves[Index]->GetAvailableAudioByteCount() <= 0)
        {
            return false;
        }
    }
    return true;
}
