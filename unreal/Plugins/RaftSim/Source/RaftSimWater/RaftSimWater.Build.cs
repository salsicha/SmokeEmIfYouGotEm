using UnrealBuildTool;

public class RaftSimWater : ModuleRules
{
    public RaftSimWater(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimPhysics" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json" });
    }
}
