#pragma once
#include "CoreMinimal.h"

class UWorld;
class UStaticMesh;
struct FWorldPartitionStreamingSource;

namespace RaftSimJointReconstructionPreview
{
bool IsAllowed(const FString& MapName, bool bEphemeralProfile, bool bEditorBuild);
/** Additional residency only: never replaces normal player streaming sources. */
bool MakeTerrainResidencySource(const FBox& WorldBounds, FWorldPartitionStreamingSource& Source);
/** Additional preflight after the collision-source hash check, not provenance by itself. */
bool HasFullTerrainFallback(const UStaticMesh* Mesh, int64 VerifiedTriangles);
/** All dependencies validate before either the candidate actor or water config changes. */
bool Apply(UWorld* World, const FString& ManifestPath, bool bEphemeralProfile, FString& Error);
}
