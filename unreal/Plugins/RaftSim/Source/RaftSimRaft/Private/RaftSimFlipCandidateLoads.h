#pragma once
#include "RaftSimFlipTestEnvironment.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimOverwashLoads.h"

// Lab-only candidate: use the game's D2/D3 evaluation and external-impulse
// integration API. Normal gameplay and its existing capsize policy are not
// changed by this experiment. No quaternion or angular rate is prescribed.
namespace RaftSimFlipCandidateLoads
{
struct FDiagnostics {int32 WetUpperFaces=0;double MinimumFaceOffsetM=DBL_MAX,MaximumIncomingNormalMps=0.;};
inline RaftSimOverwashLoads::FLoad Evaluate(URaftSimChronoRuntimeAdapter& Runtime,
    const RaftSimFlipTestEnvironment::FScene& Scene,double Seconds,double Dt,FDiagnostics* Diagnostics=nullptr)
{
    const auto& K=Runtime.GetKinematicState();FRaftSimFlexRigidState State;
    State.Position=K.WorldTransform.GetLocation()*.01;State.Orientation=K.WorldTransform.GetRotation().GetNormalized();
    State.LinearVelocity=K.LinearVelocityMetersPerSecond;State.AngularVelocity=K.AngularVelocityRadiansPerSecond;
    const auto& P=Runtime.GetFlexibleParameters();
    const auto Layout=RaftSimFlex::BuildDefaultCompliantTubeLayout(P,4,2,18000.);
    const auto Mode=Runtime.GetRaftBodyConfig().bEnableCompliantContacts ? RaftSimFlex::EModelMode::Compliant : RaftSimFlex::EModelMode::RigidBaseline;
    const auto Seats=RaftSimFlex::SolveSeatLoadCoupledTubeD2(State,P,Runtime.GetFlexibleSeats(),{},Layout,Mode);
    TMap<FString,FRaftSimFlexUniformWater> Fields;
    for(const auto& S:Seats.TubeSolve.SegmentResponses)
    {
        const FVector Point=State.WorldPoint(S.LocalPosition)*100.;FRaftSimFlexUniformWater Water;
        Water.bWet=Scene.Wet(Point);Water.SurfaceHeightM=Scene.Surface(Point,Seconds);Water.VelocityMps=Scene.Velocity(Point,Seconds);
        Fields.Add(S.SegmentId,Water);
    }
    const double R=P.TubeRadiusM*FMath::Lerp(.82,1.,double(Runtime.GetFlexiblePressureFraction()));
    FRaftSimFlexUniformWater Dry;Dry.bWet=false;
    const auto Wet=RaftSimFlex::EvaluateOverwashFlipD3(Seats,Dry,Layout,
        &Runtime.GetFlexibleRetainedVolumeBySegment(),Dt,R,.45,1.20,1000.,9.81,&Fields,8.,2.*P.TubeRadiusM,.035,R);
    RaftSimOverwashLoads::FLoad Total;
    for(const auto& S:Wet.SegmentOverwash)
    {
        const auto* Tube=Layout.FindByPredicate([&](const auto& T){return T.SegmentId==S.SegmentId;});
        if(Tube)
        {
            const FVector Face=S.LocalPosition+FVector(0,0,R);
            const FVector FaceWorld=State.WorldPoint(Face)*100.;
            const FVector Relative=Scene.Velocity(FaceWorld,Seconds)-State.PointVelocity(Face);
            auto Patch=S;
            if(Scene.bPillowRock)
            {
                // D3's vertical tube-crest overflow is not the immersion of a
                // TILTED upper patch. The latter admits current into the boat
                // before the circular tube's highest WORLD-Z point is covered.
                // Sample the actual transformed upper patch and its normal.
                Patch.bWet=Scene.Wet(FaceWorld);
                Patch.OvertoppingDepthM=FMath::Max(0.,Scene.Surface(FaceWorld,Seconds)-FaceWorld.Z*.01);
                const FVector Outward=State.Orientation.RotateVector(Tube->OutwardNormal);
                const double Incoming=-FVector::DotProduct(Relative,State.Orientation.GetUpVector());
                Patch.bUpstreamExposed=Patch.bWet && FVector::DotProduct(Relative,Outward)<0. && Incoming>1.e-6;
                if(Diagnostics && Patch.bUpstreamExposed)
                {Diagnostics->MinimumFaceOffsetM=FMath::Min(Diagnostics->MinimumFaceOffsetM,-Patch.OvertoppingDepthM);
                 Diagnostics->MaximumIncomingNormalMps=FMath::Max(Diagnostics->MaximumIncomingNormalMps,Incoming);
                 if(Patch.OvertoppingDepthM>1.e-6)++Diagnostics->WetUpperFaces;}
            }
            const auto Load=Scene.bPillowRock ? RaftSimOverwashLoads::ScoopingFace(Patch,*Tube,State.Orientation,R,Relative)
                : RaftSimOverwashLoads::UpperFace(S,*Tube,State.Orientation,R);
            Total.ForceN+=Load.ForceN;Total.TorqueNm+=Load.TorqueNm;
        }
    }
    return Total;
}
}
