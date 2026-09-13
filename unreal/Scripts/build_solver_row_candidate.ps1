[CmdletBinding()]
param([string]$OutputName = 'troublemaker-row-solver-20260912', [switch]$Resume)
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if ($OutputName -notmatch '^troublemaker-row-solver-[a-z0-9-]+$') { throw 'Expected a bounded candidate directory name' }
$buildRoot = Join-Path $repoRoot "tmp/$OutputName"
if ((Test-Path -LiteralPath $buildRoot) -and -not $Resume) { throw 'Retain the existing candidate build; inspect before rebuilding.' }
$vsRoot = 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools'
$vsDev = Join-Path $vsRoot 'Common7/Tools/VsDevCmd.bat'
$lines = & $env:ComSpec /d /s /c "`"$vsDev`" -arch=x64 -host_arch=x64 >nul && set"
foreach ($line in $lines) {
    $separator = $line.IndexOf('=')
    if ($separator -gt 0) {
        [Environment]::SetEnvironmentVariable($line.Substring(0,$separator),$line.Substring($separator+1),'Process')
    }
}
$cmake = Join-Path $vsRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$zlib = 'C:/Program Files/Epic Games/UE_5.8/Engine/Source/ThirdParty/zlib/1.3'
& $cmake -S (Join-Path $repoRoot 'physics/cpp') -B $buildRoot -G Ninja -DCMAKE_BUILD_TYPE=Release "-DZLIB_INCLUDE_DIR=$zlib/include" "-DZLIB_LIBRARY=$zlib/lib/Win64/Release/zlibstatic.lib"
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed' }
& $cmake --build $buildRoot --target raftsim_water_solver raftsim_cartesian_cook raftsim_water_tests raftsim_cartesian_domain_tests --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Candidate build failed' }
& $cmake --build $buildRoot --target test
if ($LASTEXITCODE -ne 0) { throw 'Native candidate regressions failed' }
