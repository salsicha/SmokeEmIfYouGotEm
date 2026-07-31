#pragma once

class UMaterial;

namespace RaftSimPhotorealMaterials
{

/**
 * Author the project-owned, service-free skin used only by the dormant
 * offline MetaHuman archetype diagnostic adapter.
 */
UMaterial* BuildOfflineMetaHumanSkinMaterial();

/**
 * Duplicate Epic's installed baked MetaHuman head shader into a project-owned
 * masked variant whose only graph change crops the conventional wardrobe
 * shoulder apron below a runtime-supplied pre-skinned height.
 */
UMaterial* BuildCroppedMetaHumanFaceMaterial();

} // namespace RaftSimPhotorealMaterials
