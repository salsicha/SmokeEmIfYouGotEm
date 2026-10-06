#include "RaftSimOarRig.h"

#include "Materials/MaterialInstanceDynamic.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimAccessoryMesh.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterRuntimeAdapter.h"

namespace
{
using RaftSimAccessoryMesh::FAccessoryMesh;

// One stroke, as fractions: the blade drops in, drives, lifts out, and
// returns through the air.
constexpr float CatchEnd = 0.10f;
constexpr float DriveEnd = 0.55f;
constexpr float ReleaseEnd = 0.62f;
// Blade sweep, degrees, toward the bow positive. The rower's hips sit about
// 42 cm behind the oarlocks: +16 brings the handles to the chest, -24 is
// arms extended, leaning forward. A pull drives -24 -> +16, a push +16 -> -24.
constexpr float SweepChestDeg = 16.0f;
constexpr float SweepReachDeg = -24.0f;
constexpr float RestSweepDeg = -6.0f;
// Blade centre below the surface in the drive, above it in the recovery,
// and floating on it at rest.
constexpr float BladeImmersionCm = 14.0f;
constexpr float BladeClearanceCm = 12.0f;
constexpr float BladeRestCm = -2.0f;
// Impulse per oar per full stroke. Linear power is sized against the hull's
// bow-first drag (1400 N per m/s): two oars hold about 1 m/s over the water,
// slower than a full paddle crew. A pull is the rower's strongest stroke
// (back, legs and arms). Yaw has its own basis, as the crew's pivots do:
// the hull's yaw damping is far weaker than its linear drag.
constexpr float PushImpulseNs = 1000.0f;
constexpr float PullImpulseNs = 1150.0f;
constexpr float YawImpulseNms = 300.0f;
// Raft-visual X of the rower's seat and the foot bar, and of the frame's
// ends: a longer rear bay for the load, the oarlocks at X 0 (the boat's
// pivot), and a front bay ahead of the foot bar.
constexpr float SeatXCm = -42.0f;
constexpr float FootBarXCm = 17.0f;
constexpr float FrameAftXCm = -150.0f;
constexpr float FrameForeXCm = 130.0f;
constexpr float PipeRadiusCm = 2.05f;
// Default water height in the raft visual's frame when no water is sampled
// (review captures): the loaded hull settles about 12 cm below the tube tops.
constexpr float DefaultWaterLocalZ = 42.0f;

float Smooth(float T)
{
    T = FMath::Clamp(T, 0.0f, 1.0f);
    return T * T * (3.0f - 2.0f * T);
}

float BladeReachCm()
{
    return URaftSimOarRigComponent::OarLengthCm - URaftSimOarRigComponent::OarInboardCm -
        0.5f * URaftSimOarRigComponent::BladeLengthCm;
}

// Sweep, blade height relative to the water, and feather through a stroke.
void StrokePresentation(const FRaftSimOarState& Oar, float& OutSweep, float& OutBladeAboveWater, float& OutFeather)
{
    OutSweep = RestSweepDeg;
    OutBladeAboveWater = BladeRestCm;
    OutFeather = 90.0f;
    if (Oar.Direction == 0.0f && Oar.RestBlend >= 1.0f)
    {
        return;
    }
    const float Direction = Oar.Direction != 0.0f ? Oar.Direction : Oar.LastDirection;
    const float CatchSweep = Direction > 0.0f ? SweepChestDeg : SweepReachDeg;
    const float FinishSweep = Direction > 0.0f ? SweepReachDeg : SweepChestDeg;
    // Easing back to rest after the last stroke starts from that stroke's
    // catch position, where it ended.
    const float P = Oar.Direction != 0.0f ? Oar.Phase : 0.0f;
    float Sweep, Above, Feather;
    if (P < CatchEnd)
    {
        const float T = Smooth(P / CatchEnd);
        Sweep = CatchSweep;
        Above = FMath::Lerp(BladeClearanceCm, -BladeImmersionCm, T);
        Feather = FMath::Lerp(70.0f, 0.0f, T);
    }
    else if (P < DriveEnd)
    {
        Sweep = FMath::Lerp(CatchSweep, FinishSweep, Smooth((P - CatchEnd) / (DriveEnd - CatchEnd)));
        Above = -BladeImmersionCm;
        Feather = 0.0f;
    }
    else if (P < ReleaseEnd)
    {
        const float T = Smooth((P - DriveEnd) / (ReleaseEnd - DriveEnd));
        Sweep = FinishSweep;
        Above = FMath::Lerp(-BladeImmersionCm, BladeClearanceCm, T);
        Feather = FMath::Lerp(0.0f, 70.0f, T);
    }
    else
    {
        Sweep = FMath::Lerp(FinishSweep, CatchSweep, Smooth((P - ReleaseEnd) / (1.0f - ReleaseEnd)));
        Above = BladeClearanceCm;
        Feather = 70.0f;
    }
    OutSweep = FMath::Lerp(Sweep, RestSweepDeg, Oar.RestBlend);
    OutBladeAboveWater = FMath::Lerp(Above, BladeRestCm, Oar.RestBlend);
    OutFeather = FMath::Lerp(Feather, 90.0f, Oar.RestBlend);
}
}

URaftSimOarRigComponent::URaftSimOarRigComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

float URaftSimOarRigComponent::GetRigLoadKg(ERaftSimRaftRig InRig)
{
    // Frame, towers and seat about 35 kg. The Colorado boat carries a
    // multi-day load (cooler, dry boxes, ammo cans, dry bags, spare oar);
    // the Zambezi day boat a dry box.
    switch (InRig)
    {
        case ERaftSimRaftRig::ColoradoOarRig:
            return 165.0f;
        case ERaftSimRaftRig::ZambeziOarRig:
            return 55.0f;
        default:
            return 0.0f;
    }
}

FVector URaftSimOarRigComponent::GetOarlockLocalCm(bool bLeft) const
{
    const float Side = bLeft ? -1.0f : 1.0f;
    return FVector(0.0f, Side * (RailHalfWidthCm + TowerOffsetCm), RailTopZ + TowerHeightCm);
}

FVector URaftSimOarRigComponent::GetOarDirection(bool bLeft, const FRaftSimOarState& Oar) const
{
    const float Side = bLeft ? -1.0f : 1.0f;
    const float Sweep = FMath::DegreesToRadians(Oar.SweepDeg);
    const float Drop = FMath::DegreesToRadians(Oar.DropDeg);
    return FVector(
        FMath::Cos(Drop) * FMath::Sin(Sweep),
        Side * FMath::Cos(Drop) * FMath::Cos(Sweep),
        -FMath::Sin(Drop));
}

FVector URaftSimOarRigComponent::GetRowerSeatOriginActorCm(float SeatedPelvisBottomLocalZCm) const
{
    // A centimetre of the seat pad compresses under the rower.
    constexpr float PadCompressionCm = 1.0f;
    const FVector VisualOffset = Visual ? Visual->GetRelativeLocation() : FVector(0.0f, 0.0f, -28.0f);
    return FVector(SeatXCm + VisualOffset.X, VisualOffset.Y,
        SeatTopZ + VisualOffset.Z - SeatedPelvisBottomLocalZCm - PadCompressionCm);
}

UMaterialInterface* URaftSimOarRigComponent::Tinted(const TCHAR* Path, const FLinearColor& Tint)
{
    UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, Path);
    if (!Base)
    {
        return nullptr;
    }
    UMaterialInstanceDynamic* Instance = UMaterialInstanceDynamic::Create(Base, GetOwner());
    Instance->SetVectorParameterValue(TEXT("BaseTint"), Tint);
    return Instance;
}

void URaftSimOarRigComponent::Build(
    ERaftSimRaftRig InRig, UProceduralMeshComponent* RaftVisual, const FBox& HullBoundsCm)
{
    Rig = InRig;
    Visual = RaftVisual;
    if (!Visual)
    {
        return;
    }
    // The frame is rigid, so it rests on the highest tube points under its
    // rails (the hull's rocker lifts the tube ends a little).
    float TubeTop = -TNumericLimits<float>::Max();
    if (const FProcMeshSection* Tubes = Visual->GetProcMeshSection(0))
    {
        for (const FProcMeshVertex& Vertex : Tubes->ProcVertexBuffer)
        {
            const float AbsY = FMath::Abs(static_cast<float>(Vertex.Position.Y));
            if (Vertex.Position.X > FrameAftXCm && Vertex.Position.X < FrameForeXCm &&
                AbsY > RailHalfWidthCm - 8.0f && AbsY < RailHalfWidthCm + 8.0f)
            {
                TubeTop = FMath::Max(TubeTop, static_cast<float>(Vertex.Position.Z));
            }
        }
    }
    if (TubeTop <= -TNumericLimits<float>::Max())
    {
        TubeTop = HullBoundsCm.Min.Z + 54.4f;
    }
    RailTopZ = TubeTop + PipeRadiusCm;
    // A padded seat on a pedestal 20 cm above the rails, the oarlocks 13 cm
    // above that: the handles ride at the rower's chest in the drive and
    // clear the knees in the recovery.
    SeatTopZ = RailTopZ + 20.0f;
    FloorZ = FloorAtLocalCm(FootBarXCm, HullBoundsCm);
    BuildFrameAndLoad(HullBoundsCm);
    BuildOars();
    LastLeftWaterZ = LastRightWaterZ = DefaultWaterLocalZ;
    LeftOar = RightOar = FRaftSimOarState();
    PresentOar(true, DefaultWaterLocalZ);
    PresentOar(false, DefaultWaterLocalZ);
}

float URaftSimOarRigComponent::FloorAtLocalCm(float LocalX, const FBox& HullBoundsCm) const
{
    float Floor = -TNumericLimits<float>::Max();
    if (const FProcMeshSection* FloorSection = Visual ? Visual->GetProcMeshSection(1) : nullptr)
    {
        for (const FProcMeshVertex& Vertex : FloorSection->ProcVertexBuffer)
        {
            if (FMath::Abs(Vertex.Position.X - LocalX) < 25.0f && FMath::Abs(Vertex.Position.Y) < 35.0f)
            {
                Floor = FMath::Max(Floor, static_cast<float>(Vertex.Position.Z));
            }
        }
    }
    return Floor > -TNumericLimits<float>::Max() ? Floor : HullBoundsCm.Min.Z + 18.0f;
}

float URaftSimOarRigComponent::GetFootBarLocalZ() const
{
    // The foot bar hangs below the rails on drop legs, where the rower's
    // feet brace with the knees bent below the oar handles.
    return FMath::Max(RailTopZ - 24.0f, FloorZ + 10.0f);
}

void URaftSimOarRigComponent::BuildFrameAndLoad(const FBox& HullBoundsCm)
{
    if (!Frame)
    {
        Frame = NewObject<UProceduralMeshComponent>(GetOwner(), TEXT("OarFrame"));
        Frame->SetupAttachment(Visual);
        Frame->RegisterComponent();
        Frame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Frame->SetCastShadow(true);
    }
    const bool bColorado = Rig == ERaftSimRaftRig::ColoradoOarRig;
    FAccessoryMesh Metal, Pad, Boxes, Cooler, BagWhite, BagYellow, BagBlue, Straps, Deck, Cans, SpareShaft,
        SpareBlade;
    const FVector X = FVector::ForwardVector;
    const FVector Y = FVector::RightVector;
    const FVector Z = FVector::UpVector;
    const float R = RailHalfWidthCm;
    // Side rails over the tube centres, and the cross bars that make the
    // bays: the rear end, the two seat bars, the front of the cockpit and
    // the front end.
    for (const float Side : {-1.0f, 1.0f})
    {
        Metal.Tube(FVector(FrameAftXCm, Side * R, RailTopZ), FVector(FrameForeXCm, Side * R, RailTopZ),
            PipeRadiusCm, 10);
    }
    for (const float BarX : {FrameAftXCm, SeatXCm - 20.0f, SeatXCm + 20.0f, 62.0f, FrameForeXCm})
    {
        Metal.Tube(FVector(BarX, -R, RailTopZ), FVector(BarX, R, RailTopZ), PipeRadiusCm, 10);
        for (const float Side : {-1.0f, 1.0f})
        {
            // Cast fittings at the joints.
            Metal.Box(FVector(BarX, Side * R, RailTopZ), X, Y, Z, FVector(3.4f, 3.4f, 3.0f));
        }
    }
    const float FootBarZ = GetFootBarLocalZ();
    Metal.Tube(FVector(FootBarXCm, -R, FootBarZ), FVector(FootBarXCm, R, FootBarZ), PipeRadiusCm, 10);
    Pad.Tube(FVector(FootBarXCm, -28.0f, FootBarZ), FVector(FootBarXCm, 28.0f, FootBarZ), 3.0f, 10);
    for (const float Side : {-1.0f, 1.0f})
    {
        Metal.Tube(FVector(FootBarXCm, Side * R, FootBarZ), FVector(FootBarXCm, Side * R, RailTopZ),
            PipeRadiusCm * 0.9f, 8);
        // Oar tower: an arm out from the rail, the upright and its brace,
        // and the open oarlock on its shank at the top.
        const FVector Lock = GetOarlockLocalCm(Side < 0.0f);
        const FVector TowerBase(0.0f, Side * (R + TowerOffsetCm), RailTopZ);
        Metal.Tube(FVector(-4.0f, Side * R, RailTopZ), TowerBase, PipeRadiusCm, 10);
        Metal.Tube(TowerBase, Lock - FVector(0.0f, 0.0f, 9.0f), PipeRadiusCm, 10);
        Metal.Tube(FVector(-24.0f, Side * R, RailTopZ),
            FVector(0.0f, Side * (R + TowerOffsetCm), RailTopZ + 0.6f * TowerHeightCm), PipeRadiusCm * 0.85f, 8);
        Metal.Tube(Lock - FVector(0.0f, 0.0f, 9.0f), Lock - FVector(0.0f, 0.0f, 3.9f), 1.2f, 8);
        Metal.Tube(Lock + FVector(-3.6f, 0.0f, -3.9f), Lock + FVector(3.6f, 0.0f, -3.9f), 1.0f, 8);
        Metal.Tube(Lock + FVector(-3.6f, 0.0f, -3.9f), Lock + FVector(-4.0f, 0.0f, 5.5f), 0.9f, 8);
        Metal.Tube(Lock + FVector(3.6f, 0.0f, -3.9f), Lock + FVector(4.0f, 0.0f, 5.5f), 0.9f, 8);
    }
    // The seat: a moulded seat with a foam pad on a pedestal between the two
    // seat bars.
    const float PedestalBottom = RailTopZ + PipeRadiusCm;
    const float PedestalTop = SeatTopZ - 4.0f;
    Metal.Box(FVector(SeatXCm, 0.0f, 0.5f * (PedestalBottom + PedestalTop)), X, Y, Z,
        FVector(17.0f, 21.0f, 0.5f * (PedestalTop - PedestalBottom)));
    Boxes.Box(FVector(SeatXCm, 0.0f, PedestalTop + 0.6f), X, Y, Z, FVector(20.0f, 25.0f, 0.6f));
    Pad.Box(FVector(SeatXCm, 0.0f, SeatTopZ - 1.7f), X, Y, Z, FVector(19.0f, 24.0f, 1.7f));

    // Cam straps: flat webbing over a load, down to the rails each side.
    auto Strap = [&Straps, R, this](float StrapX, float TopZ, float HalfWidth)
    {
        Straps.Box(FVector(StrapX, 0.0f, TopZ + 0.5f), FVector::ForwardVector, FVector::RightVector,
            FVector::UpVector, FVector(2.2f, HalfWidth, 0.35f));
        for (const float Side : {-1.0f, 1.0f})
        {
            const FVector Top(StrapX, Side * HalfWidth, TopZ + 0.5f);
            const FVector Rail(StrapX, Side * R, RailTopZ + PipeRadiusCm);
            const FVector Along = (Rail - Top).GetSafeNormal();
            Straps.Box(0.5f * (Top + Rail), Along, FVector::ForwardVector,
                FVector::CrossProduct(Along, FVector::ForwardVector),
                FVector(0.5f * FVector::Distance(Top, Rail), 2.2f, 0.35f));
        }
    };
    auto DryBag = [](FAccessoryMesh& Bag, const FVector& Center, float Radius, float HalfLength)
    {
        // A roll-top bag lying across the bay, fuller in the middle, with
        // its rolled mouth and buckle at one end.
        for (int32 Segment = 0; Segment < 4; ++Segment)
        {
            const float Y0 = FMath::Lerp(-HalfLength, HalfLength, Segment / 4.0f);
            const float Y1 = FMath::Lerp(-HalfLength, HalfLength, (Segment + 1) / 4.0f);
            const float Bulge = Segment == 0 || Segment == 3 ? 0.9f : 1.0f;
            Bag.Tube(Center + FVector(0, Y0, 0), Center + FVector(0, Y1, 0), Radius * Bulge, 14);
        }
        Bag.Box(Center + FVector(0, HalfLength + 2.5f, 0), FVector::ForwardVector, FVector::RightVector,
            FVector::UpVector, FVector(2.2f, 3.0f, Radius * 0.8f));
    };

    const float RearBayX = 0.5f * (FrameAftXCm + SeatXCm - 20.0f);
    const float RearFloor = FloorAtLocalCm(RearBayX, HullBoundsCm);
    if (bColorado)
    {
        // Rear bay: the trip cooler on the floor and dry bags piled on it,
        // cammed down to the rails.
        const float CoolerTop = FMath::Max(RailTopZ + 6.0f, RearFloor + 46.0f);
        Cooler.Box(FVector(RearBayX, 0.0f, 0.5f * (RearFloor + CoolerTop)), X, Y, Z,
            FVector(25.0f, 34.0f, 0.5f * (CoolerTop - RearFloor)));
        Cooler.Box(FVector(RearBayX, 0.0f, CoolerTop + 1.2f), X, Y, Z, FVector(26.0f, 35.0f, 1.2f));
        DryBag(BagWhite, FVector(RearBayX - 14.0f, -2.0f, CoolerTop + 15.0f), 13.5f, 27.0f);
        DryBag(BagYellow, FVector(RearBayX + 10.0f, 1.0f, CoolerTop + 14.0f), 12.5f, 25.0f);
        DryBag(BagBlue, FVector(RearBayX - 2.0f, -1.0f, CoolerTop + 33.0f), 11.0f, 22.0f);
        Strap(RearBayX - 12.0f, CoolerTop + 29.0f, 30.0f);
        Strap(RearBayX + 12.0f, CoolerTop + 27.0f, 28.0f);
        // Front bay: a plywood deck across the rails with two ammo cans and
        // a dry box strapped on it.
        const float DeckX = 0.5f * (62.0f + FrameForeXCm);
        const float DeckTop = RailTopZ + PipeRadiusCm + 2.0f;
        Deck.Box(FVector(DeckX, 0.0f, DeckTop - 1.0f), X, Y, Z,
            FVector(0.5f * (FrameForeXCm - 62.0f) - 2.0f, R + 2.0f, 1.0f));
        for (const float CanY : {-34.0f, -16.0f})
        {
            Cans.Box(FVector(DeckX - 4.0f, CanY, DeckTop + 9.0f), X, Y, Z, FVector(14.0f, 8.0f, 9.0f));
            Cans.Box(FVector(DeckX - 4.0f, CanY, DeckTop + 18.6f), X, Y, Z, FVector(10.0f, 3.0f, 0.8f));
        }
        Boxes.Box(FVector(DeckX, 26.0f, DeckTop + 12.0f), X, Y, Z, FVector(20.0f, 18.0f, 12.0f));
        Strap(DeckX - 4.0f, DeckTop + 24.0f, 44.0f);
        // The spare oar lies along the left side on the cross bars, blade
        // forward on the deck.
        const float SpareY = -(R - 12.0f);
        const float SpareZ = RailTopZ + PipeRadiusCm + 2.4f;
        const FVector SpareStart(FrameAftXCm + 2.0f, SpareY, SpareZ);
        const FVector SpareThroat = SpareStart + X * (OarLengthCm - BladeLengthCm);
        SpareShaft.Tube(SpareStart, SpareThroat, 2.4f, 10);
        SpareBlade.Box(SpareThroat + X * (0.5f * BladeLengthCm), X, Y, Z,
            FVector(0.5f * BladeLengthCm, 0.5f * BladeWidthCm, 0.7f));
    }
    else
    {
        // The Zambezi day boat travels light: a small dry box in the rear
        // bay for the first-aid kit and lunch, cammed to the frame.
        const float BoxTopZ = FMath::Max(RailTopZ - 2.0f, RearFloor + 30.0f);
        Boxes.Box(FVector(RearBayX, 0.0f, 0.5f * (RearFloor + BoxTopZ)), X, Y, Z,
            FVector(20.0f, 30.0f, 0.5f * (BoxTopZ - RearFloor)));
        Strap(RearBayX, BoxTopZ, 31.0f);
    }
    Metal.Commit(Frame, 0);
    Pad.Commit(Frame, 1);
    Boxes.Commit(Frame, 2);
    Cooler.Commit(Frame, 3);
    BagWhite.Commit(Frame, 4);
    BagYellow.Commit(Frame, 5);
    BagBlue.Commit(Frame, 6);
    Straps.Commit(Frame, 7);
    Deck.Commit(Frame, 8);
    Cans.Commit(Frame, 9);
    SpareShaft.Commit(Frame, 10);
    SpareBlade.Commit(Frame, 11);
    UMaterialInterface* Steel = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel.M_RaftSim_GalvanizedSteel"));
    const TCHAR* Fabric = TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD");
    const TCHAR* HardShell = TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet");
    Frame->SetMaterial(0, Steel);
    Frame->SetMaterial(1, Tinted(Fabric, FLinearColor(0.020f, 0.022f, 0.026f)));
    Frame->SetMaterial(2, Steel);
    Frame->SetMaterial(3, Tinted(HardShell, FLinearColor(0.62f, 0.60f, 0.55f)));
    Frame->SetMaterial(4, Tinted(Fabric, FLinearColor(0.60f, 0.60f, 0.58f)));
    Frame->SetMaterial(5, Tinted(Fabric, FLinearColor(0.48f, 0.30f, 0.004f)));
    Frame->SetMaterial(6, Tinted(Fabric, FLinearColor(0.010f, 0.050f, 0.20f)));
    Frame->SetMaterial(7, Tinted(Fabric, FLinearColor(0.012f, 0.045f, 0.20f)));
    Frame->SetMaterial(8, LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber")));
    Frame->SetMaterial(9, Tinted(HardShell, FLinearColor(0.045f, 0.055f, 0.025f)));
    Frame->SetMaterial(10, LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft")));
    Frame->SetMaterial(11, LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade")));
}

void URaftSimOarRigComponent::BuildOars()
{
    const bool bColorado = Rig == ERaftSimRaftRig::ColoradoOarRig;
    UMaterialInterface* Wood = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber"));
    for (const bool bLeft : {true, false})
    {
        TObjectPtr<UProceduralMeshComponent>& Mesh = bLeft ? LeftOarMesh : RightOarMesh;
        if (!Mesh)
        {
            Mesh = NewObject<UProceduralMeshComponent>(GetOwner(), bLeft ? TEXT("PortOar") : TEXT("StarboardOar"));
            Mesh->SetupAttachment(Visual);
            Mesh->RegisterComponent();
            Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Mesh->SetCastShadow(true);
        }
        // Oar-local: X from the oarlock out toward the blade, the blade's
        // width along Z (square to the water at zero feather).
        FAccessoryMesh Shaft, Grip, Blade, Fittings;
        const float Outboard = OarLengthCm - OarInboardCm;
        const float Throat = Outboard - BladeLengthCm;
        Shaft.Tube(FVector(-OarInboardCm + 20.0f, 0, 0), FVector(Throat + 6.0f, 0, 0), 2.4f, 12);
        Grip.Tube(FVector(-OarInboardCm, 0, 0), FVector(-OarInboardCm + 20.0f, 0, 0), 2.2f, 12);
        Grip.Tube(FVector(-OarInboardCm - 0.6f, 0, 0), FVector(-OarInboardCm, 0, 0), 1.6f, 12);
        // The blade: a tapered throat into a flat blade with a thickened
        // spine, wooden on the Zambezi, composite on the Colorado.
        Blade.Box(FVector(Throat + 4.0f, 0, 0), FVector::ForwardVector, FVector::RightVector, FVector::UpVector,
            FVector(5.0f, 1.6f, 0.30f * BladeWidthCm));
        Blade.Box(FVector(Throat + 0.5f * BladeLengthCm + 4.0f, 0, 0), FVector::ForwardVector,
            FVector::RightVector, FVector::UpVector,
            FVector(0.5f * BladeLengthCm - 4.0f, bColorado ? 0.55f : 0.85f, 0.5f * BladeWidthCm));
        Blade.Tube(FVector(Throat, 0, 0), FVector(Outboard - 3.0f, 0, 0), bColorado ? 1.1f : 1.4f, 8);
        // Where the shaft rides the oarlock: a rope wrap, the oar stop just
        // inboard of it, and the oar right that holds the blade square.
        Fittings.Tube(FVector(-9.0f, 0, 0), FVector(15.0f, 0, 0), 2.9f, 12);
        Fittings.Tube(FVector(-12.5f, 0, 0), FVector(-10.0f, 0, 0), 3.6f, 12);
        Fittings.Box(FVector(-11.2f, 0, 3.6f), FVector::ForwardVector, FVector::RightVector, FVector::UpVector,
            FVector(1.3f, 1.6f, 1.6f));
        Shaft.Commit(Mesh, 0);
        Grip.Commit(Mesh, 1);
        Blade.Commit(Mesh, 2);
        Fittings.Commit(Mesh, 3);
        Mesh->SetMaterial(0, bColorado
            ? LoadObject<UMaterialInterface>(nullptr,
                  TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"))
            : Wood);
        Mesh->SetMaterial(1, bColorado
            ? LoadObject<UMaterialInterface>(nullptr,
                  TEXT("/Game/RaftSim/Materials/M_RaftSim_BootRubber.M_RaftSim_BootRubber"))
            : Wood);
        Mesh->SetMaterial(2, bColorado
            ? LoadObject<UMaterialInterface>(nullptr,
                  TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"))
            : Wood);
        Mesh->SetMaterial(3, Tinted(TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftRigging.M_RaftSim_RaftRigging"),
            FLinearColor(0.50f, 0.48f, 0.42f)));
    }
}

float URaftSimOarRigComponent::SampleWaterLocalZ(bool bLeft, const FRaftSimOarState& Oar) const
{
    const float Fallback = bLeft ? LastLeftWaterZ : LastRightWaterZ;
    const ARaftSimRaftActor* Raft = Cast<ARaftSimRaftActor>(GetOwner());
    const URaftSimWaterRuntimeAdapter* Water =
        Raft && Raft->Bridge ? Raft->Bridge->GetWaterRuntime() : nullptr;
    if (!Water || !Visual)
    {
        return Fallback;
    }
    const FTransform VisualToWorld = Visual->GetComponentTransform();
    const FVector BladeWorld = VisualToWorld.TransformPosition(
        GetOarlockLocalCm(bLeft) + GetOarDirection(bLeft, Oar) * BladeReachCm());
    FRaftSimWaterSample Sample;
    if (!Water->SampleWaterAtWorldPosition(BladeWorld, Sample) || !Sample.bWet)
    {
        return Fallback;
    }
    const FVector SurfaceWorld(BladeWorld.X, BladeWorld.Y, Sample.SurfaceHeightMeters * 100.0f);
    return static_cast<float>(VisualToWorld.InverseTransformPosition(SurfaceWorld).Z);
}

void URaftSimOarRigComponent::UpdateOarPresentation(bool bLeft, const FRaftSimOarState& Oar)
{
    UProceduralMeshComponent* Mesh = bLeft ? LeftOarMesh : RightOarMesh;
    if (!Mesh)
    {
        return;
    }
    const FVector Direction = GetOarDirection(bLeft, Oar);
    const FQuat Square = FRotationMatrix::MakeFromXZ(Direction, FVector::UpVector).ToQuat();
    // Feathering turns the blade flat with its leading edge up on both
    // sides (the oars mirror).
    const FQuat Feather(FVector::ForwardVector,
        FMath::DegreesToRadians(Oar.FeatherDeg) * (bLeft ? -1.0f : 1.0f));
    Mesh->SetRelativeLocationAndRotation(GetOarlockLocalCm(bLeft), Square * Feather);
}

void URaftSimOarRigComponent::SetOarIntents(float Left, float Right)
{
    LeftIntent = FMath::Clamp(Left, -1.0f, 1.0f);
    RightIntent = FMath::Clamp(Right, -1.0f, 1.0f);
}

void URaftSimOarRigComponent::AdvanceOar(
    FRaftSimOarState& Oar, float Intent, float DeltaSeconds, ARaftSimRaftActor* Raft, bool bLeft, bool bDrive)
{
    constexpr float IntentThreshold = 0.2f;
    if (Oar.Direction == 0.0f)
    {
        if (FMath::Abs(Intent) < IntentThreshold)
        {
            Oar.RestBlend = FMath::Min(1.0f, Oar.RestBlend + DeltaSeconds * 2.5f);
            return;
        }
        Oar.Direction = FMath::Sign(Intent);
        Oar.LastDirection = Oar.Direction;
        Oar.Effort = FMath::Abs(Intent);
        Oar.Phase = 0.0f;
    }
    Oar.RestBlend = FMath::Max(0.0f, Oar.RestBlend - DeltaSeconds * 4.0f);
    const float Start = Oar.Phase;
    const float End = Start + DeltaSeconds / StrokeSeconds;
    // The blade meets the water halfway through the catch and leaves it
    // halfway through the release.
    constexpr float EntryPhase = 0.5f * CatchEnd;
    constexpr float ExitPhase = 0.5f * (DriveEnd + ReleaseEnd);
    if (Start < EntryPhase && End >= EntryPhase)
    {
        ++CatchCounts[bLeft ? 0 : 1];
    }
    if (Start < ExitPhase && End >= ExitPhase)
    {
        ++ReleaseCounts[bLeft ? 0 : 1];
    }
    const float Overlap = FMath::Max(0.0f, FMath::Min(End, DriveEnd) - FMath::Max(Start, CatchEnd));
    if (Overlap > 0.0f && bDrive && Raft && Raft->RaftAdapter && Visual)
    {
        // Drive this slice of the stroke through the blade: along the bow
        // axis, at the blade's station abeam, so opposed oars pivot the boat
        // and a single oar both drives and turns it.
        float Purchase = 1.0f;
        if (const URaftSimWaterRuntimeAdapter* Water = Raft->Bridge ? Raft->Bridge->GetWaterRuntime() : nullptr)
        {
            const FVector BladeWorld = Visual->GetComponentTransform().TransformPosition(
                GetOarlockLocalCm(bLeft) + GetOarDirection(bLeft, Oar) * BladeReachCm());
            FRaftSimWaterSample Sample;
            Purchase = Water->SampleWaterAtWorldPosition(BladeWorld, Sample) && Sample.bWet &&
                    Sample.DepthMeters > 0.10f
                ? 1.0f
                : 0.0f;
            if (Purchase > 0.0f && Raft->RaftAdapter->GetLastGroundedSupportPointCount() >= 3)
            {
                // Aground, the oars only work the boat off a gravel touch;
                // they cannot row it across a bar.
                Purchase = FMath::Min(Purchase, Raft->GetPaddleWaterPurchase());
            }
        }
        if (Purchase > 0.0f)
        {
            const float Fraction = Overlap / (DriveEnd - CatchEnd);
            const float Side = bLeft ? -1.0f : 1.0f;
            const FVector Forward = Raft->GetActorForwardVector();
            const float Stroke = Oar.Direction;
            // A tired rower's strokes carry less (RaftSimCrewFatigue).
            const float Strength = ARaftSimRaftActor::StrokeStrengthForStamina(Raft->GetCrewStamina(TEXT("guide")));
            float LinearNs = (Stroke > 0.0f ? PushImpulseNs : PullImpulseNs) * Fraction * Oar.Effort *
                Purchase * Raft->GetPaddlePropulsionShortfall(Forward * Stroke) * Strength;
            // A push on the right oar drives the right side forward and
            // swings the bow left; a pull swings it right.
            float YawNms = -Side * Stroke * YawImpulseNms * Fraction * Oar.Effort * Purchase * Strength;
            if (Raft->ActiveCrewCommand == ERaftSimCrewCommand::Stop &&
                Raft->ManualOarIntents.IsNearlyZero() && Raft->TransientOarSeconds <= 0.f && Raft->OarSteerSeconds <= 0.f)
            {
                // A stroke can outlast the stop target. Never let its remaining drive
                // reverse the boat or accelerate it after the velocity changes sign.
                const float Speed = FVector::DotProduct(Raft->GetRaftVelocity(), Forward);
                const float Mass = Raft->RaftAdapter->GetRaftBodyConfig().MassKg;
                LinearNs = Speed * Stroke < 0.f ? FMath::Min(LinearNs, .5f * Mass * FMath::Abs(Speed)) : 0.f;
                YawNms = 0.f;
            }
            Raft->RaftAdapter->AddExternalImpulse(Forward * Stroke * LinearNs, FVector(0.0f, 0.0f, YawNms));
        }
    }
    Oar.Phase = End;
    if (Oar.Phase >= 1.0f)
    {
        ++CompletedStrokeCount;
        if (FMath::Abs(Intent) >= IntentThreshold)
        {
            Oar.Direction = FMath::Sign(Intent);
            Oar.LastDirection = Oar.Direction;
            Oar.Effort = FMath::Abs(Intent);
            Oar.Phase = FMath::Frac(Oar.Phase);
        }
        else
        {
            Oar.Direction = 0.0f;
            Oar.Phase = 0.0f;
        }
    }
}

void URaftSimOarRigComponent::PresentOar(bool bLeft, float WaterLocalZ)
{
    FRaftSimOarState& Oar = bLeft ? LeftOar : RightOar;
    float Above = 0.0f;
    StrokePresentation(Oar, Oar.SweepDeg, Above, Oar.FeatherDeg);
    // Each blade follows its own patch of water: the drop angle puts the
    // blade centre at the stroke's depth below (or height above) the surface
    // under it.
    const float SinDrop = FMath::Clamp(
        (GetOarlockLocalCm(bLeft).Z - (WaterLocalZ + Above)) / BladeReachCm(), -0.25f, 0.85f);
    Oar.DropDeg = FMath::RadiansToDegrees(FMath::Asin(SinDrop));
    UpdateOarPresentation(bLeft, Oar);
}

void URaftSimOarRigComponent::TickRig(
    float DeltaSeconds, ARaftSimRaftActor* Raft, ARaftSimCrewAvatarActor* Rower, bool bRowerAboard)
{
    if (!Visual)
    {
        return;
    }
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.1f);
    const bool bBracing = bRowerAboard && Raft &&
        (Raft->ActiveCrewCommand == ERaftSimCrewCommand::HighSide || Raft->ActiveCrewCommand == ERaftSimCrewCommand::GetDown ||
         (Rower && Rower->HasHighSideTransfer()));
    AdvanceOar(LeftOar, bRowerAboard && !bBracing ? LeftIntent : 0.0f, Dt, Raft, true, bRowerAboard && !bBracing);
    AdvanceOar(RightOar, bRowerAboard && !bBracing ? RightIntent : 0.0f, Dt, Raft, false, bRowerAboard && !bBracing);
    LastLeftWaterZ = SampleWaterLocalZ(true, LeftOar);
    LastRightWaterZ = SampleWaterLocalZ(false, RightOar);
    PresentOar(true, LastLeftWaterZ);
    PresentOar(false, LastRightWaterZ);
    if (bRowerAboard && !bBracing)
    {
        PoseRower(Rower, false);
    }
    else if (Rower && Rower->HasExternalPose())
    {
        Rower->ClearExternalPose();
    }
}

void URaftSimOarRigComponent::PoseRower(ARaftSimCrewAvatarActor* Rower, bool bApplyNow) const
{
    if (!Rower || !Visual || !Rower->GetRootComponent())
    {
        return;
    }
    // Both hands grip their handles just inboard of the ends, in the
    // avatar's frame (it sits on the raft root, unrotated).
    const FVector ToAvatar = Visual->GetRelativeLocation() - Rower->GetRootComponent()->GetRelativeLocation();
    constexpr float GripInsetCm = 8.0f;
    const FVector LeftAxis = GetOarDirection(true, LeftOar);
    const FVector RightAxis = GetOarDirection(false, RightOar);
    const FVector LeftGrip = GetOarlockLocalCm(true) - LeftAxis * (OarInboardCm - GripInsetCm) + ToAvatar;
    const FVector RightGrip = GetOarlockLocalCm(false) - RightAxis * (OarInboardCm - GripInsetCm) + ToAvatar;
    const FVector FootBar = FVector(FootBarXCm, 0.0f, GetFootBarLocalZ()) + ToAvatar;
    Rower->SetExternalPose(URaftSimCrewAvatarPoseLibrary::EvaluateRowingPose(
        LeftGrip, LeftAxis, RightGrip, RightAxis, FootBar), bApplyNow);
}

void URaftSimOarRigComponent::PoseForValidation(
    float Phase, float LeftDirection, float RightDirection, ARaftSimCrewAvatarActor* Rower)
{
    for (const bool bLeft : {true, false})
    {
        FRaftSimOarState& Oar = bLeft ? LeftOar : RightOar;
        const float Direction = bLeft ? LeftDirection : RightDirection;
        Oar.Direction = FMath::Sign(Direction);
        Oar.LastDirection = Oar.Direction != 0.0f ? Oar.Direction : 1.0f;
        Oar.Effort = FMath::Abs(Direction);
        Oar.Phase = FMath::Frac(Phase);
        Oar.RestBlend = Oar.Direction != 0.0f ? 0.0f : 1.0f;
        PresentOar(bLeft, DefaultWaterLocalZ);
    }
    PoseRower(Rower, true);
}
