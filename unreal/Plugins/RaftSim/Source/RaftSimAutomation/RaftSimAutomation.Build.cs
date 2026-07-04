using UnrealBuildTool;

public class RaftSimAutomation : ModuleRules
{
    public RaftSimAutomation(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimWater", "RaftSimPhysics" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "Projects" });
    }
}
