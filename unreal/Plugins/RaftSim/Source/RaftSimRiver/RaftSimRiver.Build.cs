using UnrealBuildTool;

public class RaftSimRiver : ModuleRules
{
    public RaftSimRiver(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore" });
    }
}
