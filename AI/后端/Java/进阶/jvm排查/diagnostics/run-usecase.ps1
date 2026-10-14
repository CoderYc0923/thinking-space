# Run one case from jvm-dump-usecases
# Usage:
#   .\run-usecase.ps1
#   .\run-usecase.ps1 Deadlock
#   .\run-usecase.ps1 GCThrashing -Xmx 64m
#   .\run-usecase.ps1 MetaspaceOOM -MaxMetaspaceSize 32m
# Optional:
#   $env:DIAG_JAVA = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"

param(
    [Parameter(Position = 0)]
    [string]$CaseName = "",

    [string]$Xmx = "",
    [string]$Xms = "",
    [string]$MaxMetaspaceSize = "",
    [string]$ExtraJvmArgs = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\jvm-dump-usecases")).Path
$Jar       = Join-Path $RepoRoot "target\application.jar"

$Cases = @(
    "InfiniteLoop", "InfiniteWait", "MemoryLeak", "SingleThreadHighMemoryUsage",
    "ThreadLeak", "ClassloaderLeak", "Log4j", "CrashOnError", "NonFinalized",
    "Deadlock", "GCThrashing", "MetaspaceOOM", "OffHeapLeak",
    "ConnectionPoolExhaustion", "ThreadPoolSaturation", "StackOverflow", "FileDescriptorLeak"
)

function Resolve-Java {
    if ($env:DIAG_JAVA -and (Test-Path $env:DIAG_JAVA)) { return $env:DIAG_JAVA }

    $fixed = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"
    if (Test-Path $fixed) { return $fixed }

    $hit = Get-Item "D:\Java\jdks\jdk-21*\bin\java.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.FullName }

    # This project is Java 8 bytecode; Java 8 also works
    $j8 = "D:\Java\jdks\jdk-8.0.504.1-hotspot\bin\java.exe"
    if (Test-Path $j8) { return $j8 }

    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

if (-not $CaseName) {
    Write-Host "Usage: .\run-usecase.ps1 <CaseName> [-Xmx 64m] [-MaxMetaspaceSize 32m]" -ForegroundColor Yellow
    Write-Host "Available cases:" -ForegroundColor Cyan
    $Cases | ForEach-Object { Write-Host ("  " + $_) }
    Write-Host ""
    Write-Host "Tutorial: ..\jvm-dump-usecases实操教程.md"
    exit 0
}

if ($Cases -notcontains $CaseName) {
    Write-Host "Unknown case: $CaseName" -ForegroundColor Red
    Write-Host "Run without args to list cases." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $Jar)) {
    Write-Host "JAR not found: $Jar" -ForegroundColor Red
    Write-Host "Run: cd ..\jvm-dump-usecases; mvn -DskipTests package" -ForegroundColor Yellow
    exit 1
}

$JavaExe = Resolve-Java
if (-not $JavaExe) {
    Write-Host "java not found. Set DIAG_JAVA or install JDK." -ForegroundColor Red
    exit 1
}

$jvmArgs = New-Object System.Collections.Generic.List[string]
if ($Xms) { $jvmArgs.Add("-Xms$Xms") }
if ($Xmx) { $jvmArgs.Add("-Xmx$Xmx") }
if ($MaxMetaspaceSize) { $jvmArgs.Add("-XX:MaxMetaspaceSize=$MaxMetaspaceSize") }
if ($ExtraJvmArgs) {
    foreach ($a in ($ExtraJvmArgs -split "\s+")) {
        if ($a) { $jvmArgs.Add($a) }
    }
}

# Sensible defaults for a few heavy cases if user did not pass sizes
if ($CaseName -eq "GCThrashing" -and -not $Xmx) {
    $jvmArgs.Add("-Xmx64m")
    $jvmArgs.Add("-Xms64m")
}
if ($CaseName -eq "MetaspaceOOM" -and -not $MaxMetaspaceSize) {
    $jvmArgs.Add("-XX:MaxMetaspaceSize=32m")
}
if ($CaseName -eq "MemoryLeak" -and -not $Xmx) {
    $jvmArgs.Add("-Xmx256m")
    $jvmArgs.Add("-XX:+HeapDumpOnOutOfMemoryError")
    $dumpDir = Join-Path $ScriptDir "usecases"
    if (-not (Test-Path $dumpDir)) { New-Item -ItemType Directory -Path $dumpDir | Out-Null }
    $jvmArgs.Add("-XX:HeapDumpPath=$(Join-Path $dumpDir 'memoryleak.hprof')")
}

$JdkBin = Split-Path $JavaExe -Parent

Write-Host "=== jvm-dump-usecases ===" -ForegroundColor Cyan
Write-Host "JAVA : $JavaExe"
Write-Host "JAR  : $Jar"
Write-Host "CASE : $CaseName"
Write-Host "ARGS : $($jvmArgs -join ' ')"
Write-Host "After start, another terminal:" -ForegroundColor Yellow
Write-Host "  & '$JdkBin\jps.exe' -l"
Write-Host "  & '$JdkBin\jstack.exe' <pid>"
Write-Host ""

$allArgs = @()
$allArgs += $jvmArgs
$allArgs += @("-jar", $Jar, $CaseName)

& $JavaExe @allArgs

Write-Host ""
Write-Host "Process ended." -ForegroundColor Green
