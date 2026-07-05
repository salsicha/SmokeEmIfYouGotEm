#include "RaftSimChronoRuntimeAdapter.h"

void URaftSimChronoRuntimeAdapter::ConfigureRaftBody(const FRaftSimRaftBodyConfig& InConfig)
{
    RaftConfig = InConfig;
    AuthorityIntegrationPolicy.SelectedRuntime = InConfig.Runtime;
}

void URaftSimChronoRuntimeAdapter::ConfigureAuthorityIntegrationPolicy(const FRaftSimRaftAuthorityIntegrationPolicy& InPolicy)
{
    AuthorityIntegrationPolicy = InPolicy;
    RaftConfig.Runtime = InPolicy.SelectedRuntime;
}

void URaftSimChronoRuntimeAdapter::SetKinematicState(const FRaftSimRaftKinematicState& InState)
{
    KinematicState = InState;
}

bool URaftSimChronoRuntimeAdapter::StepRaftDynamics(float SubstepSeconds)
{
    if (SubstepSeconds <= 0.0f)
    {
        return false;
    }

    const FVector TranslationDelta = KinematicState.LinearVelocityMetersPerSecond * SubstepSeconds * 100.0f;
    KinematicState.WorldTransform.AddToTranslation(TranslationDelta);
    return true;
}
