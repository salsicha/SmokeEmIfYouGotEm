using UnrealBuildTool;

public class RaftSimCrew : ModuleRules
{
    public RaftSimCrew(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimAI" });
    }
}
