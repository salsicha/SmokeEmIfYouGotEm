#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "ProceduralMeshComponent.h"

bool ARaftSimRaftActor::SampleRenderedCrewSupport(const TArray<FVector>& Points,
    TArray<double>& Floor, TArray<double>& Solid) const
{
    if (!RaftVisual || Points.IsEmpty()) return false;
    Floor.Init(-DBL_MAX, Points.Num());
    Solid.Init(-DBL_MAX, Points.Num());
    FBox Bounds(ForceInit);
    for (const FVector& P : Points) { if (P.ContainsNaN()) return false; Bounds += P; }
    const FTransform ToActor = RaftVisual->GetRelativeTransform();
    for (int32 SectionIndex : {0, 1})
    {
        const FProcMeshSection* Section = RaftVisual->GetProcMeshSection(SectionIndex);
        if (!Section) return false;
        for (int32 I = 0; I + 2 < Section->ProcIndexBuffer.Num(); I += 3)
        {
            const FVector A = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I]].Position));
            const FVector B = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+1]].Position));
            const FVector C = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+2]].Position));
            if (FMath::Max3(A.X,B.X,C.X) < Bounds.Min.X || FMath::Min3(A.X,B.X,C.X) > Bounds.Max.X ||
                FMath::Max3(A.Y,B.Y,C.Y) < Bounds.Min.Y || FMath::Min3(A.Y,B.Y,C.Y) > Bounds.Max.Y) continue;
            const double D = (B.Y-C.Y)*(A.X-C.X)+(C.X-B.X)*(A.Y-C.Y);
            if (FMath::Abs(D) < 1.e-8) continue;
            for (int32 J = 0; J < Points.Num(); ++J)
            {
                const FVector& P = Points[J];
                const double U = ((B.Y-C.Y)*(P.X-C.X)+(C.X-B.X)*(P.Y-C.Y))/D;
                const double V = ((C.Y-A.Y)*(P.X-C.X)+(A.X-C.X)*(P.Y-C.Y))/D;
                const double W = 1-U-V;
                if (FMath::Min3(U,V,W) < -1.e-6) continue;
                const double Z = U*A.Z+V*B.Z+W*C.Z;
                Solid[J] = FMath::Max(Solid[J], Z);
                if (SectionIndex == 1) Floor[J] = FMath::Max(Floor[J], Z);
            }
        }
    }
    return !Floor.Contains(-DBL_MAX);
}

bool ARaftSimCrewAvatarActor::TryGetRenderedPose(ERaftSimCrewAvatarAction Action,
    float Phase, FRaftSimCrewAvatarPose& OutPose) const
{
    if (!bHasRenderedPose || Action != CurrentAction || !FMath::IsNearlyEqual(Phase, AnimationPhase)) return false;
    OutPose = LastRenderedPose;
    return true;
}

void ARaftSimCrewAvatarActor::FitFeetToRenderedRaft(FRaftSimCrewAvatarPose& Pose)
{
    // Falling/swimming/rescue/reentry keep their authored airborne trajectories.
    if (CurrentAction > ERaftSimCrewAvatarAction::HighSideStarboard || !HasProductionRiverBoots()) return;
    ARaftSimRaftActor* Raft = Cast<ARaftSimRaftActor>(GetAttachParentActor());
    if (!Raft) { bFootPlacementBound = false; FootPlacementRaft.Reset(); return; }
    if (FootPlacementRaft.Get() != Raft) { bFootPlacementBound = false; FootPlacementRaft = Raft; }
    const FTransform ToRaft = GetActorTransform().GetRelativeTransform(Raft->GetActorTransform());
    const auto Idle = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::SeatedIdle, 0, SeatSide);
    FVector Feet[2] = {Idle.LeftFootCm, Idle.RightFootCm};
    UStaticMeshComponent* Boots[2] = {ProductionLeftBoot, ProductionRightBoot};
    const double Inboard = SeatSide < 0 ? 1.0 : -1.0;
    const double ProfileZ = GetBodyProportionScale().Z;
    for (int32 Foot = 0; Foot < 2; ++Foot)
    {
        const FBox Source = Boots[Foot]->GetStaticMesh()->GetBoundingBox();
        const FVector Scale = Boots[Foot]->GetRelativeScale3D();
        const FRotator Yaw(0, Foot == 0 ? -28.0 : 28.0, 0);
        // Conservative full boot footprint; does not require stripped cooked
        // render buffers. Actual tread vertices are checked independently in UE.
        TArray<FVector> Offsets;
        for (int32 X = 0; X <= 4; ++X) for (int32 Y = 0; Y <= 2; ++Y)
            Offsets.Add(Yaw.RotateVector(FVector(FMath::Lerp(Source.Min.X,Source.Max.X,X/4.0)*Scale.X,
                FMath::Lerp(Source.Min.Y,Source.Max.Y,Y/2.0)*Scale.Y,0)));
        const auto Sample = [&](const FVector& Local, double& Z, bool bRequireFloor) -> bool
        {
            TArray<FVector> Points;
            for (const FVector& Offset : Offsets) Points.Add(ToRaft.TransformPosition(Local+Offset));
            TArray<double> Floor, Solid;
            if (!Raft->SampleRenderedCrewSupport(Points, Floor, Solid)) return false;
            Z = -DBL_MAX;
            for (int32 J = 0; J < Points.Num(); ++J)
            {
                if (bRequireFloor && Solid[J] > Floor[J]+0.5) return false;
                Z = FMath::Max(Z, Solid[J]);
            }
            return FMath::IsFinite(Z);
        };
        bool bFound = false;
        double SupportZ = 0;
        if (bFootPlacementBound)
        {
            Feet[Foot] = BoundFootLocalCm[Foot];
            bFound = Sample(Feet[Foot], SupportZ, false);
        }
        else
        {
            // Prefer the nearest inboard floor position, not the top of an
            // overlapping tube/thwart. Fore/aft changes are a last resort.
            const FVector Authored = Feet[Foot];
            for (int32 Aft = 0; Aft <= 8 && !bFound; Aft += 2)
                for (int32 Shift = 0; Shift <= 24 && !bFound; ++Shift)
                {
                    Feet[Foot] = Authored+FVector(-Aft,Inboard*Shift,0);
                    bFound = Sample(Feet[Foot], SupportZ, true);
                }
        }
        if (!bFound) return; // No invented support plane or geometry fallback.
        const FVector RaftPoint = ToRaft.TransformPosition(Feet[Foot]);
        const FVector SupportLocal = ToRaft.InverseTransformPosition(FVector(RaftPoint.X,RaftPoint.Y,SupportZ));
        Feet[Foot].Z = SupportLocal.Z - Source.Min.Z*ProfileZ + 0.1;
    }
    if (!bFootPlacementBound)
    {
        BoundFootLocalCm[0] = Feet[0]; BoundFootLocalCm[1] = Feet[1]; bFootPlacementBound = true;
        UE_LOG(LogTemp,Display,TEXT("CREW_FOOT_BIND actor=%s left=%s right=%s"),
            *GetName(),*Feet[0].ToString(),*Feet[1].ToString());
    }
    const auto FitLeg = [](const FVector& Hip, const FVector& RestHip, const FVector& RestKnee,
        const FVector& RestFoot, const FVector& Foot, FVector& Knee)
    {
        const double Upper = FVector::Distance(RestHip,RestKnee), Lower = FVector::Distance(RestKnee,RestFoot);
        const FVector Axis = (Foot-Hip).GetSafeNormal();
        const double Distance = FVector::Distance(Hip,Foot);
        if (Distance < 1.e-4 || Distance >= Upper+Lower || Distance <= FMath::Abs(Upper-Lower)) return false;
        const double Along = (Upper*Upper-Lower*Lower+Distance*Distance)/(2*Distance);
        FVector Bend = Knee-Hip-Axis*FVector::DotProduct(Knee-Hip,Axis);
        Bend = Bend.GetSafeNormal();
        if (Bend.IsNearlyZero()) return false;
        Knee = Hip+Along*Axis+FMath::Sqrt(FMath::Max(0.0,Upper*Upper-Along*Along))*Bend;
        return true;
    };
    FVector LeftKnee = Pose.LeftKneeCm, RightKnee = Pose.RightKneeCm;
    if (!FitLeg(Pose.LeftHipCm,Idle.LeftHipCm,Idle.LeftKneeCm,Idle.LeftFootCm,Feet[0],LeftKnee) ||
        !FitLeg(Pose.RightHipCm,Idle.RightHipCm,Idle.RightKneeCm,Idle.RightFootCm,Feet[1],RightKnee)) return;
    Pose.LeftFootCm = Feet[0]; Pose.RightFootCm = Feet[1];
    Pose.LeftKneeCm = LeftKnee; Pose.RightKneeCm = RightKnee;
    Pose.bFeetPlanted = true;
}
