using UnrealBuildTool;
using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using EpicGames.Core;

public class RaftSimWater : ModuleRules
{
    public RaftSimWater(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json" });

        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_NAME=\"raftsim_water_cpp_v1\"");
        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_HEADER_ONLY_BRIDGE=1");
        PublicIncludePaths.Add(Path.GetFullPath(Path.Combine(ModuleDirectory, "../../../../../physics/cpp/include")));

        // Live game water: link the first-party FV solver static library.
        // Windows builds produce an MSVC .lib via build_solver_lib.ps1;
        // macOS/Linux produce an archive via build_solver_lib.sh. Guarded so
        // the module still compiles before the lib exists on a fresh checkout.
        string SolverLibName = Target.Platform == UnrealTargetPlatform.Win64
            ? "raftsim_water.lib"
            : "libraftsim_water.a";
        string SolverLib = Path.GetFullPath(
            Path.Combine(ModuleDirectory, "../../../../../physics/cpp/build-ue", SolverLibName));
        if (File.Exists(SolverLib))
        {
            PublicAdditionalLibraries.Add(SolverLib);
            // Rebuilding the first-party archive must invalidate cached UBT
            // dependency state; otherwise a successful editor build can keep
            // running the previous solver after build_solver_lib.ps1.
            ExternalDependencies.Add(SolverLib);
            // ExternalDependencies invalidates the UBT makefile but does not
            // reliably dirty already-linked modular DLLs when this archive is
            // rebuilt outside UBT. Put its content identity in the compile
            // environment so every linked consumer actually rebuilds.
            using (var SolverStream = File.OpenRead(SolverLib))
            using (var SolverHash = System.Security.Cryptography.SHA256.Create())
            {
                string SolverDigest = BitConverter.ToString(
                    SolverHash.ComputeHash(SolverStream)).Replace("-", "").ToLowerInvariant();
                PublicDefinitions.Add("RAFTSIM_LIVE_SOLVER_BUILD_SHA256=\"" + SolverDigest + "\"");
            }
            PublicDefinitions.Add("RAFTSIM_HAS_LIVE_SOLVER=1");
            bEnableExceptions = true;
            // The solver archive inflates compressed .npy payloads; macOS
            // resolves zlib from the system SDK but Linux links against the
            // engine's bundled zlib, so declare it for both.
            AddEngineThirdPartyPrivateStaticDependencies(Target, "zlib");
        }
        else
        {
            PublicDefinitions.Add("RAFTSIM_HAS_LIVE_SOLVER=0");
        }

        // Shipping builds need the same hash-verified fields used in editor.
        // Stage only runtime JSON/NumPy products, never raw DEM/imagery/source
        // acquisitions. ResolveRuntimeDataPath maps the preserved repo-relative
        // path under RaftSimRuntimeData beside the packaged executable.
        string RepoRoot = Path.GetFullPath(Path.Combine(ModuleDirectory, "../../../../.."));
        var RuntimeDestinations = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        string[] RuntimeRoots =
        {
            "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics",
            "physics/data/real_world/south_fork_american_chili_bar/cooked_flow_fields",
            "physics/data/real_world/south_fork_american_chili_bar/scenario_meat_grinder/cooked_flow_fields",
            "physics/data/real_world/south_fork_american_chili_bar/scenario_troublemaker/cooked_flow_fields",
            "physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow"
        };
        foreach (string RelativeRoot in RuntimeRoots)
        {
            string SourceRoot = Path.Combine(RepoRoot, RelativeRoot);
            if (!Directory.Exists(SourceRoot))
            {
                continue;
            }
            foreach (string SourceFile in Directory.GetFiles(SourceRoot, "*", SearchOption.AllDirectories))
            {
                string Extension = Path.GetExtension(SourceFile).ToLowerInvariant();
                if (Extension != ".json" && Extension != ".npy")
                {
                    continue;
                }
                string RepoRelative = Path.GetRelativePath(RepoRoot, SourceFile).Replace('\\', '/');
                RuntimeDestinations.Add(RepoRelative);
                RuntimeDependencies.Add(
                    "$(TargetOutputDir)/RaftSimRuntimeData/" + RepoRelative,
                    SourceFile,
                    StagedFileType.NonUFS);
            }
        }
        string CoordinateMapRelative =
            "physics/data/real_world/south_fork_american_chili_bar/production_corridor/photoreal_environment/river_coordinate_map.json";
        string CoordinateMapSource = Path.Combine(RepoRoot, CoordinateMapRelative);
        if (File.Exists(CoordinateMapSource))
        {
            RuntimeDestinations.Add(CoordinateMapRelative);
            RuntimeDependencies.Add(
                "$(TargetOutputDir)/RaftSimRuntimeData/" + CoordinateMapRelative,
                CoordinateMapSource,
                StagedFileType.NonUFS);
        }
        StageVerifiedRuntimeBundle(RepoRoot,
            "physics/data/runtime_bundles/south_fork_saved_scene_v1", RuntimeDestinations);
    }

    private static string CheckedRelativePath(string Value)
    {
        if (String.IsNullOrEmpty(Value) || Path.IsPathRooted(Value) || Value.Contains('\\') || Value.Contains(':'))
        {
            throw new BuildException("Runtime bundle requires portable relative paths: " + Value);
        }
        foreach (string Part in Value.Split('/'))
        {
            if (Part.Length == 0 || Part == "." || Part == "..")
            {
                throw new BuildException("Runtime bundle path is not canonical: " + Value);
            }
        }
        return Value;
    }

    private void VerifyRuntimeFile(string FileName, string ExpectedHash)
    {
        // Include every source in makefile invalidation: cached rules must not
        // let later source changes bypass the hash check on the next build.
        ExternalDependencies.Add(FileName);
        if (!File.Exists(FileName))
        {
            throw new BuildException("Missing required runtime bundle input: " + FileName);
        }
        using var Stream = File.OpenRead(FileName);
        using var Hasher = SHA256.Create();
        string ActualHash = BitConverter.ToString(Hasher.ComputeHash(Stream)).Replace("-", "").ToLowerInvariant();
        if (!String.Equals(ActualHash, ExpectedHash, StringComparison.Ordinal))
        {
            throw new BuildException("Changed runtime bundle input (fetch LFS data or regenerate the verified bundle): " + FileName);
        }
    }

    private void StageVerifiedRuntimeBundle(string RepoRoot, string RelativeBundle,
        HashSet<string> Destinations)
    {
        string BundleRoot = Path.Combine(RepoRoot, CheckedRelativePath(RelativeBundle));
        string ManifestFile = Path.Combine(BundleRoot, "manifest.json");
        ExternalDependencies.Add(ManifestFile);
        if (!File.Exists(ManifestFile))
        {
            throw new BuildException("Required saved-scene runtime bundle is missing: " + ManifestFile);
        }
        JsonObject Manifest = JsonObject.Read(new FileReference(ManifestFile));
        if (Manifest.GetStringField("schema") != "raftsim.runtime_data_bundle.v1")
        {
            throw new BuildException("Unsupported runtime bundle schema: " + ManifestFile);
        }
        foreach (JsonObject Binding in Manifest.GetObjectArrayField("saved_scene_assets"))
        {
            string RelativeFile = CheckedRelativePath(Binding.GetStringField("path"));
            VerifyRuntimeFile(Path.Combine(RepoRoot, RelativeFile), Binding.GetStringField("sha256"));
        }
        JsonObject[] Files = Manifest.GetObjectArrayField("files");
        if (Files.Length == 0)
        {
            throw new BuildException("Empty saved-scene runtime bundle: " + ManifestFile);
        }
        foreach (JsonObject File in Files)
        {
            string Destination = CheckedRelativePath(File.GetStringField("destination"));
            string Source = CheckedRelativePath(File.GetStringField("source"));
            string Hash = File.GetStringField("sha256");
            string Extension = Path.GetExtension(Destination);
            if ((Extension != ".json" && Extension != ".npy") ||
                Source != "files/" + Hash + Extension || !Destinations.Add(Destination))
            {
                throw new BuildException("Invalid or duplicate runtime bundle destination: " + Destination);
            }
            string SourceFile = Path.Combine(BundleRoot, Source);
            VerifyRuntimeFile(SourceFile, Hash);
            if (new FileInfo(SourceFile).Length != File.GetDoubleField("size_bytes"))
            {
                throw new BuildException("Runtime bundle size mismatch: " + SourceFile);
            }
            // Logical legacy paths are preserved inside the standalone package;
            // all source bytes come from the versioned bundle, never repo tmp.
            RuntimeDependencies.Add("$(TargetOutputDir)/RaftSimRuntimeData/" + Destination,
                SourceFile, StagedFileType.NonUFS);
        }
    }
}
