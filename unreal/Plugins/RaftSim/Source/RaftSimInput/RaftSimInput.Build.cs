using UnrealBuildTool;

public class RaftSimInput : ModuleRules
{
    public RaftSimInput(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "EnhancedInput", "RaftSimCore" });
    }
}
