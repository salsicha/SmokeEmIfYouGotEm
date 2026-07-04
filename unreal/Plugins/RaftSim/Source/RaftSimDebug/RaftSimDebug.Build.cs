using UnrealBuildTool;

public class RaftSimDebug : ModuleRules
{
    public RaftSimDebug(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimPhysics", "RaftSimWater", "RaftSimGeo" });
    }
}
