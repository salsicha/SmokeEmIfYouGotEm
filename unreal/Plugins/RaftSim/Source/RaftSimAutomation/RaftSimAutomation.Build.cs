using UnrealBuildTool;

public class RaftSimAutomation : ModuleRules
{
    public RaftSimAutomation(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimWater", "RaftSimPhysics", "RaftSimCrew", "RaftSimRaft" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "Projects" });
    }
}
