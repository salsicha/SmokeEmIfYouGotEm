using UnrealBuildTool;

public class RaftSimRaft : ModuleRules
{
    public RaftSimRaft(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimPhysics" });
    }
}
