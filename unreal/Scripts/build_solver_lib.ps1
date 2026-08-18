[CmdletBinding()]
param(
    [string]$UnrealRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$sourceRoot = Join-Path $repoRoot "physics\cpp"
$buildRoot = Join-Path $sourceRoot "build-ue"
$objectRoot = Join-Path $buildRoot "windows-x64"
$solverLibrary = Join-Path $buildRoot "raftsim_water.lib"

$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere)) {
    throw "Visual Studio Installer's vswhere.exe was not found. Install the Visual Studio C++ build tools."
}

$visualStudioRoot = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if (-not $visualStudioRoot) {
    throw "No Visual Studio installation with the x64 C++ build tools was found."
}

$vsDevCmd = Join-Path $visualStudioRoot "Common7\Tools\VsDevCmd.bat"
if (-not (Test-Path -LiteralPath $vsDevCmd)) {
    throw "Visual Studio developer environment script was not found at $vsDevCmd"
}

# Import the compiler environment into this PowerShell process. Calling the
# batch file in a child cmd.exe keeps its noisy banner out of build output.
$environmentLines = & $env:ComSpec /d /s /c `
    "`"$vsDevCmd`" -arch=x64 -host_arch=x64 >nul && set"
foreach ($line in $environmentLines) {
    $separator = $line.IndexOf("=")
    if ($separator -gt 0) {
        [Environment]::SetEnvironmentVariable(
            $line.Substring(0, $separator),
            $line.Substring($separator + 1),
            "Process")
    }
}

$compiler = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -find "VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe"
$librarian = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -find "VC\Tools\MSVC\*\bin\Hostx64\x64\lib.exe"
if (-not $compiler -or -not $librarian) {
    throw "The Visual Studio x64 compiler or librarian could not be located."
}
$zlibInclude = Join-Path $UnrealRoot "Engine\Source\ThirdParty\zlib\1.3\include"
if (-not (Test-Path -LiteralPath (Join-Path $zlibInclude "zlib.h"))) {
    throw "Unreal's zlib headers were not found under $zlibInclude"
}

New-Item -ItemType Directory -Path $objectRoot -Force | Out-Null

$sources = @(
    "chrono_bridge_fixtures.cpp",
    "chrono_coupling.cpp",
    "json.cpp",
    "numpy_io.cpp",
    "scenario.cpp",
    "solver_constriction_01.cpp",
    "solver_constriction_02.cpp",
    "solver_constriction_03.cpp",
    "solver_constriction_04.cpp",
    "solver_constriction_05.cpp",
    "solver_constriction_06.cpp",
    "solver_constriction_07.cpp",
    "solver_constriction_08.cpp",
    "solver_constriction_09.cpp",
    "solver_constriction_10.cpp",
    "solver_constriction_11.cpp",
    "solver_diagnostics.cpp",
    "solver_numerics.cpp",
    "solver_output.cpp",
    "solver_runtime.cpp"
)

$objects = @()
foreach ($sourceName in $sources) {
    $sourcePath = Join-Path $sourceRoot "src\$sourceName"
    $objectPath = Join-Path $objectRoot ([System.IO.Path]::ChangeExtension($sourceName, ".obj"))
    Write-Host "Compiling $sourceName"
    & $compiler /nologo /c /std:c++17 /EHsc /O2 /MD /DNDEBUG `
        "/I$(Join-Path $sourceRoot 'include')" "/I$zlibInclude" `
        "/Fo$objectPath" $sourcePath | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "cl.exe failed while compiling $sourceName (exit code $LASTEXITCODE)"
    }
    $objects += $objectPath
}

Write-Host "Archiving raftsim_water.lib"
& $librarian /nologo "/OUT:$solverLibrary" $objects
if ($LASTEXITCODE -ne 0) {
    throw "lib.exe failed (exit code $LASTEXITCODE)"
}

Write-Host "Built: $solverLibrary"
