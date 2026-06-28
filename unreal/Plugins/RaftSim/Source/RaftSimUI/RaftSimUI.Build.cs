using UnrealBuildTool;

public class RaftSimUI : ModuleRules
{
    public RaftSimUI(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "UMG", "RaftSimCore" });
    }
}
