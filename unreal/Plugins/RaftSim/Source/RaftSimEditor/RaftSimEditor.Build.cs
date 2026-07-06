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
            "LevelEditor",
            "Json",
            "ImageWrapper",
            "Projects",
            "ProceduralMeshComponent",
            "RenderCore",
            "UnrealEd"
        });
    }
}
