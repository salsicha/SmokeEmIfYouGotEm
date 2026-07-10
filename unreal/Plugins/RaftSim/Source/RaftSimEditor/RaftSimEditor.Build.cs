using UnrealBuildTool;

public class RaftSimEditor : ModuleRules
{
    public RaftSimEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

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
            "Json",
            "ImageWrapper",
            "MeshUtilities",
            "Projects",
            "ProceduralMeshComponent",
            "RenderCore",
            "UnrealEd"
        });
    }
}
