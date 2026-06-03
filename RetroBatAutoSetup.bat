@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===========================================================================
REM  RetroBat Auto Setup - Windows launcher
REM  Place this file in the RetroBat root folder and run it.
REM
REM  Responsibilities:
REM    * Verify PowerShell is available.
REM    * Self-elevate to Administrator (needed for some emulator installs and
REM      hardware queries) while preserving the working directory and arguments.
REM    * Invoke the PowerShell orchestrator with ExecutionPolicy Bypass for this
REM      process only (no machine-wide policy changes).
REM
REM  Usage:
REM    RetroBatAutoSetup.bat              Run the full setup pipeline.
REM    RetroBatAutoSetup.bat /watch       Run the controller hotswap watcher.
REM    RetroBatAutoSetup.bat /noinstall   Skip auto-installing missing emulators.
REM    RetroBatAutoSetup.bat /nogit       Skip the git commit/push phase.
REM    (flags may be combined, e.g.  RetroBatAutoSetup.bat /noinstall /nogit)
REM ===========================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "PS_SCRIPT=%ROOT%\scripts\RetroBatAutoSetup.ps1"
set "LOGDIR=%ROOT%\Logs"

title RetroBat Auto Setup

echo.
echo  ============================================================
echo    RetroBat Auto Setup
echo    Root: %ROOT%
echo  ============================================================
echo.

REM --- Ensure the Logs directory exists for early failures -------------------
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

REM --- Verify the orchestrator script is present -----------------------------
if not exist "%PS_SCRIPT%" (
    echo [ERROR] Orchestrator not found: "%PS_SCRIPT%"
    echo         Ensure the 'scripts' folder is alongside this launcher.
    echo [%date% %time%] FATAL launcher: missing %PS_SCRIPT% >> "%LOGDIR%\Setup.log"
    pause
    exit /b 2
)

REM --- Locate PowerShell -----------------------------------------------------
set "PWSH="
where pwsh.exe >nul 2>&1 && set "PWSH=pwsh.exe"
if not defined PWSH (
    where powershell.exe >nul 2>&1 && set "PWSH=powershell.exe"
)
if not defined PWSH (
    echo [ERROR] PowerShell was not found on this system.
    echo [%date% %time%] FATAL launcher: PowerShell not found >> "%LOGDIR%\Setup.log"
    pause
    exit /b 3
)

REM --- Translate launcher flags into PowerShell parameters -------------------
set "PS_ARGS=-RetroBatRoot ""%ROOT%"""
set "MODE=Setup"

:parse_args
if "%~1"=="" goto args_done
set "ARG=%~1"
if /i "!ARG!"=="/watch"     set "MODE=Watch"
if /i "!ARG!"=="-watch"     set "MODE=Watch"
if /i "!ARG!"=="/noinstall" set "PS_ARGS=!PS_ARGS! -SkipInstall"
if /i "!ARG!"=="-noinstall" set "PS_ARGS=!PS_ARGS! -SkipInstall"
if /i "!ARG!"=="/nogit"     set "PS_ARGS=!PS_ARGS! -SkipGit"
if /i "!ARG!"=="-nogit"     set "PS_ARGS=!PS_ARGS! -SkipGit"
shift
goto parse_args
:args_done
set "PS_ARGS=!PS_ARGS! -Mode !MODE!"

REM --- Self-elevate to Administrator if not already elevated ------------------
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [INFO] Requesting administrator privileges...
    REM Re-launch this script elevated, forwarding all original arguments.
    set "ELEV_VBS=%TEMP%\retrobat_elevate_%RANDOM%.vbs"
    > "!ELEV_VBS!" echo Set UAC = CreateObject^("Shell.Application"^)
    >> "!ELEV_VBS!" echo UAC.ShellExecute "%~f0", "%*", "%ROOT%", "runas", 1
    cscript //nologo "!ELEV_VBS!"
    del "!ELEV_VBS!" >nul 2>&1
    exit /b 0
)

echo [INFO] Running with administrator privileges.
echo [INFO] Launcher mode: !MODE!
echo [%date% %time%] Launcher invoked. Mode=!MODE! Args=!PS_ARGS! >> "%LOGDIR%\Setup.log"
echo.

REM --- Invoke the orchestrator -----------------------------------------------
"%PWSH%" -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" !PS_ARGS!
set "RC=%errorlevel%"

echo.
if "%RC%"=="0" (
    echo [DONE] RetroBat Auto Setup finished successfully. See "%LOGDIR%".
) else (
    echo [WARN] RetroBat Auto Setup exited with code %RC%. Check the logs in "%LOGDIR%".
)

REM Keep the window open only for interactive (non-watch) runs.
if /i not "!MODE!"=="Watch" (
    echo.
    pause
)

endlocal & exit /b %RC%
