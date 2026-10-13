# Scenario B: Deadlock (hang / no response / wide timeouts)
# Usage:
#   .\run-deadlock.ps1
# Optional JDK override:
#   $env:DIAG_JAVA = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"; .\run-deadlock.ps1
#
# After start, open another terminal (use same JDK bin):
#   jps -l
#   jstack <pid> > .\threads.txt
#   # or: jcmd <pid> Thread.print > .\threads.txt
# Search in threads.txt: "Found one Java-level deadlock" / BLOCKED

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LabRoot   = (Resolve-Path (Join-Path $ScriptDir "..\diagnostic-lab")).Path
$Jar       = Join-Path $LabRoot "target\diagnostic-lab-1.0-SNAPSHOT.jar"
$ThreadOut = Join-Path $ScriptDir "threads.txt"
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

$JdkBin = Split-Path $JavaExe -Parent

Write-Host "=== Deadlock / Hang ===" -ForegroundColor Cyan
Write-Host "JAVA: $JavaExe"
Write-Host "JAR : $Jar"
Write-Host "Process stays alive after deadlock (non-daemon blocked threads)." -ForegroundColor Yellow
Write-Host "Open another terminal, then:" -ForegroundColor Yellow
Write-Host "  & '$JdkBin\jps.exe' -l"
Write-Host "  & '$JdkBin\jstack.exe' <pid> | Out-File -Encoding utf8 '$ThreadOut'"
Write-Host "Look for: Found one Java-level deadlock / BLOCKED"
Write-Host ""

# Two threads cross-lock lock1/lock2; main returns but JVM stays up.
& $JavaExe `
  -cp $Jar `
  $MainClass `
  deadlock

Write-Host ""
Write-Host "Process ended (Ctrl+C or kill). Thread dump path if you saved it:" -ForegroundColor Green
Write-Host $ThreadOut -ForegroundColor Green
