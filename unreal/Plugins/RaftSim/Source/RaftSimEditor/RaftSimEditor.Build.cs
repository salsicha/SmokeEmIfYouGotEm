using UnrealBuildTool;

public class RaftSimEditor : ModuleRules
{
    public RaftSimEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        // The decomposed editor subsystems use private helper namespaces that must
        // remain isolated at translation-unit boundaries.
        bUseUnity = false;

        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "Slate",
            "SlateCore",
            "ToolMenus",
            "AssetRegistry",
            "RaftSimAutomation",
            "RaftSimCore",
            "RaftSimDebug",
            "RaftSimGeo",
            "RaftSimRiver",
            "RaftSimUI"
        });

        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Landscape",
            "LandscapeEditor",
            "LevelEditor",
            "Chaos",
            "GeometryCollectionEngine",
            "GeometryCore",
            "GeometryFramework",
            "GeometryScriptingCore",
            "Json",
            "ImageWrapper",
            "InputCore",
            "MeshUtilities",
            "EnhancedInput",
            "RaftSimRaft",
            "RaftSimWater",
            "Projects",
            "ProceduralMeshComponent",
            "ProceduralVegetation",
            "PCG",
            "PlanarCut",
            "RenderCore",
            "RHI",
            "UnrealEd"
        });
    }
}
