#pragma once
#include "CoreMinimal.h"

class UWorld;

namespace RaftSimJointReconstructionPreview
{
bool IsAllowed(const FString& MapName, bool bEphemeralProfile, bool bEditorBuild);
/** All dependencies validate before either the candidate actor or water config changes. */
bool Apply(UWorld* World, const FString& ManifestPath, bool bEphemeralProfile, FString& Error);
}
