#pragma once
#include "CoreMinimal.h"

class UWorld;
struct FWorldPartitionStreamingSource;

namespace RaftSimJointReconstructionPreview
{
bool IsAllowed(const FString& MapName, bool bEphemeralProfile, bool bEditorBuild);
/** Additional residency only: never replaces normal player streaming sources. */
bool MakeTerrainResidencySource(const FBox& WorldBounds, FWorldPartitionStreamingSource& Source);
/** All dependencies validate before either the candidate actor or water config changes. */
bool Apply(UWorld* World, const FString& ManifestPath, bool bEphemeralProfile, FString& Error);
}
