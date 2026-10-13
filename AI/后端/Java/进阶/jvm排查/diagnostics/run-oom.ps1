# Scenario A: Memory Leak / OOM
# Usage:
#   .\run-oom.ps1
# Optional JDK override:
#   $env:DIAG_JAVA = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"; .\run-oom.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LabRoot   = (Resolve-Path (Join-Path $ScriptDir "..\diagnostic-lab")).Path
$Jar       = Join-Path $LabRoot "target\diagnostic-lab-1.0-SNAPSHOT.jar"
$DumpPath  = Join-Path $ScriptDir "oomdump.hprof"
# Real main class (README wrongly adds .demo)
$MainClass = "dev.abykov.pets.diagnostic_lab.MainApp"

function Resolve-Java21 {
    if ($env:DIAG_JAVA -and (Test-Path $env:DIAG_JAVA)) {
        return $env:DIAG_JAVA
    }

    $fixed = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"
    if (Test-Path $fixed) {
        return $fixed
    }

    $hit = Get-Item "D:\Java\jdks\jdk-21*\bin\java.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) {
        return $hit.FullName
    }

    if ($env:JAVA_HOME) {
        $fromHome = Join-Path $env:JAVA_HOME "bin\java.exe"
        if (Test-Path $fromHome) {
            $verText = & $fromHome -version 2>&1 | Out-String
            if ($verText -match 'version "?1[7-9]' -or $verText -match 'version "?2[0-9]') {
                return $fromHome
            }
        }
    }

    $allJava = @(Get-Command java -All -ErrorAction SilentlyContinue)
    foreach ($cmd in $allJava) {
        $verText = & $cmd.Source -version 2>&1 | Out-String
        if ($verText -match 'version "?1[7-9]' -or $verText -match 'version "?2[0-9]') {
            return $cmd.Source
        }
    }

    return $null
}

if (-not (Test-Path $Jar)) {
    Write-Host "JAR not found: $Jar" -ForegroundColor Red
    Write-Host "Run in diagnostic-lab: mvn -DskipTests package" -ForegroundColor Yellow
    exit 1
}

$JavaExe = Resolve-Java21
if (-not $JavaExe) {
    Write-Host "Need JDK 17+. PATH java is probably Java 8." -ForegroundColor Red
    Write-Host 'Set: $env:DIAG_JAVA = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"' -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Memory Leak / OOM ===" -ForegroundColor Cyan
Write-Host "JAVA: $JavaExe"
Write-Host "JAR : $Jar"
Write-Host "DUMP: $DumpPath"
Write-Host "HEAP: -Xms256m -Xmx256m"
Write-Host "After start, open another terminal: jps -l" -ForegroundColor Yellow
Write-Host ""

& $JavaExe `
  -Xms256m `
  -Xmx256m `
  -XX:+HeapDumpOnOutOfMemoryError `
  "-XX:HeapDumpPath=$DumpPath" `
  -cp $Jar `
  $MainClass `
  memory

Write-Host ""
Write-Host "Process ended. If OOM happened, check dump:" -ForegroundColor Green
Write-Host $DumpPath -ForegroundColor Green
