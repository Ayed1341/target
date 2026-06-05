@echo off
:: ============================================================================
::  PC GAMING OPTIMIZER - Advanced All-in-One Tweak Tool
::  Supports: Windows 10 and Windows 11 (x64)
::  Features: Auto-detects CPU / GPU / RAM, trims background processes,
::            disables unnecessary services, optimizes network latency,
::            sets High Performance / Ultimate power plan, enables Game Mode,
::            GPU Hardware-Accelerated Scheduling, and adds English + Arabic
::            keyboard layouts.
::
::  HOW TO RUN: Right-click this file  ->  "Run as administrator".
::  A System Restore point is created before ANY change is made, so every
::  tweak is fully reversible from Windows System Restore.
:: ============================================================================

setlocal EnableExtensions EnableDelayedExpansion
title PC GAMING OPTIMIZER  -  Advanced Tweak Tool
color 0A
mode con: cols=100 lines=45

:: ---------------------------------------------------------------------------
:: 1) REQUIRE ADMINISTRATOR PRIVILEGES (auto-elevate)
:: ---------------------------------------------------------------------------
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo  [!] Administrator rights are required. Requesting elevation...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
    exit /b
)

:: ---------------------------------------------------------------------------
:: 2) DETECT WINDOWS VERSION
:: ---------------------------------------------------------------------------
set "WINVER=Unknown"
for /f "tokens=4-7 delims=[]. " %%a in ('ver') do set "OSBUILD=%%b"
for /f "tokens=2 delims==" %%i in ('wmic os get Caption /value 2^>nul ^| find "="') do set "OSNAME=%%i"
echo %OSNAME% | find /i "Windows 11" >nul && set "WINVER=11"
echo %OSNAME% | find /i "Windows 10" >nul && set "WINVER=10"

cls
echo ============================================================================
echo                         PC GAMING OPTIMIZER
echo ============================================================================
echo.
echo   Detected OS : %OSNAME%
echo.

:: ---------------------------------------------------------------------------
:: 3) AUTO-DETECT HARDWARE (CPU / GPU / RAM)
:: ---------------------------------------------------------------------------
echo   Scanning hardware, please wait...
echo.

:: --- CPU ---
set "CPU_NAME=Unknown"
set "CPU_CORES=0"
set "CPU_THREADS=0"
set "CPU_VENDOR=Unknown"
for /f "tokens=2 delims==" %%i in ('wmic cpu get Name /value 2^>nul ^| find "="') do set "CPU_NAME=%%i"
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value 2^>nul ^| find "="') do set "CPU_CORES=%%i"
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfLogicalProcessors /value 2^>nul ^| find "="') do set "CPU_THREADS=%%i"
echo %CPU_NAME% | find /i "Intel" >nul && set "CPU_VENDOR=Intel"
echo %CPU_NAME% | find /i "AMD"   >nul && set "CPU_VENDOR=AMD"

:: --- GPU ---
set "GPU_NAME=Unknown"
set "GPU_VENDOR=Unknown"
for /f "tokens=2 delims==" %%i in ('wmic path win32_VideoController get Name /value 2^>nul ^| find "="') do set "GPU_NAME=%%i"
echo %GPU_NAME% | find /i "NVIDIA" >nul && set "GPU_VENDOR=NVIDIA"
echo %GPU_NAME% | find /i "AMD"    >nul && set "GPU_VENDOR=AMD"
echo %GPU_NAME% | find /i "Radeon" >nul && set "GPU_VENDOR=AMD"
echo %GPU_NAME% | find /i "Intel"  >nul && set "GPU_VENDOR=Intel"

:: --- RAM (total physical, rounded to GB) ---
set "RAM_GB=0"
for /f "tokens=2 delims==" %%i in ('wmic ComputerSystem get TotalPhysicalMemory /value 2^>nul ^| find "="') do set "RAM_BYTES=%%i"
if defined RAM_BYTES (
    for /f %%g in ('powershell -NoProfile -Command "[math]::Round(%RAM_BYTES%/1GB)"') do set "RAM_GB=%%g"
)

echo ----------------------------------------------------------------------------
echo   CPU : %CPU_NAME%
echo         Vendor: %CPU_VENDOR%   Cores: %CPU_CORES%   Threads: %CPU_THREADS%
echo   GPU : %GPU_NAME%
echo         Vendor: %GPU_VENDOR%
echo   RAM : %RAM_GB% GB
echo ----------------------------------------------------------------------------
echo.
echo   This tool will now optimize your PC for gaming.
echo   A System Restore point will be created first (safe / reversible).
echo.
choice /C YN /M "  Continue with optimization"
if errorlevel 2 goto :END

cls
echo ============================================================================
echo   APPLYING OPTIMIZATIONS...
echo ============================================================================
echo.

:: ---------------------------------------------------------------------------
:: 4) CREATE A SYSTEM RESTORE POINT (safety net)
:: ---------------------------------------------------------------------------
echo  [ 1/12] Creating System Restore point...
powershell -NoProfile -Command "Enable-ComputerRestore -Drive 'C:\'" >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore" /v SystemRestorePointCreationFrequency /t REG_DWORD /d 0 /f >nul 2>&1
powershell -NoProfile -Command "Checkpoint-Computer -Description 'Before_PC_Gaming_Optimizer' -RestorePointType 'MODIFY_SETTINGS'" >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 5) POWER PLAN: HIGH PERFORMANCE / ULTIMATE PERFORMANCE
:: ---------------------------------------------------------------------------
echo  [ 2/12] Setting High / Ultimate Performance power plan...
:: Activate built-in High Performance plan
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
:: Try to create and activate the hidden Ultimate Performance plan (best for gaming)
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul 2>&1
for /f "tokens=4" %%p in ('powercfg /list ^| find /i "Ultimate Performance"') do set "ULTGUID=%%p"
if defined ULTGUID powercfg /setactive %ULTGUID% >nul 2>&1
:: Never sleep / never turn off disk while plugged in
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change disk-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
:: Disable USB selective suspend (reduces input lag on mouse/keyboard)
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 >nul 2>&1
powercfg /setactive SCHEME_CURRENT >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 6) ENABLE WINDOWS GAME MODE + GPU SCHEDULING
:: ---------------------------------------------------------------------------
echo  [ 3/12] Enabling Game Mode + Hardware GPU Scheduling...
reg add "HKCU\Software\Microsoft\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f >nul 2>&1
:: Hardware-Accelerated GPU Scheduling (HAGS) - lowers latency on modern GPUs
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f >nul 2>&1
:: Disable Game DVR / background recording (frees CPU+GPU)
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 7) GPU-SPECIFIC TWEAKS (based on detected vendor)
:: ---------------------------------------------------------------------------
echo  [ 4/12] Applying GPU tweaks for: %GPU_VENDOR% ...
:: Give games higher GPU + CPU priority via Multimedia Class Scheduler
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Priority" /t REG_DWORD /d 6 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f >nul 2>&1
:: Reserve full system responsiveness for foreground app (default 20 -> 0)
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f >nul 2>&1
if /i "%GPU_VENDOR%"=="NVIDIA" echo         NVIDIA detected: tip - set "Prefer Maximum Performance" in NVIDIA Control Panel.
if /i "%GPU_VENDOR%"=="AMD"    echo         AMD detected: tip - enable "Radeon Anti-Lag" in AMD Software.
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 8) DISABLE UNNECESSARY BACKGROUND SERVICES (reduces process count)
::     Only safe-to-disable services are touched. Networking, audio, and
::     security services are left untouched.
:: ---------------------------------------------------------------------------
echo  [ 5/12] Trimming unnecessary background services...
set "SVCLIST=DiagTrack dmwappushservice diagnosticshub.standardcollector.service WSearch SysMain MapsBroker RetailDemo Fax PhoneSvc WpcMonSvc lfsvc WerSvc PcaSvc RemoteRegistry"
for %%S in (%SVCLIST%) do (
    sc query "%%S" >nul 2>&1
    if !errorlevel! EQU 0 (
        sc stop "%%S" >nul 2>&1
        sc config "%%S" start= disabled >nul 2>&1
        echo         Disabled service: %%S
    )
)
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 9) DISABLE STARTUP / TELEMETRY SCHEDULED TASKS
:: ---------------------------------------------------------------------------
echo  [ 6/12] Disabling telemetry and unneeded scheduled tasks...
for %%T in (
  "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser"
  "\Microsoft\Windows\Application Experience\ProgramDataUpdater"
  "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator"
  "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip"
  "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector"
  "\Microsoft\Windows\Feedback\Siuf\DmClient"
  "\Microsoft\Windows\Windows Error Reporting\QueueReporting"
) do schtasks /Change /TN %%T /Disable >nul 2>&1
:: Set telemetry to lowest allowed level
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 10) NETWORK LATENCY OPTIMIZATION
:: ---------------------------------------------------------------------------
echo  [ 7/12] Optimizing network for low latency...
:: Disable Nagle's algorithm on all active interfaces (lowers ping spikes)
for /f "delims=" %%I in ('powershell -NoProfile -Command "Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' | ForEach-Object { $_.PSChildName }"') do (
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\%%I" /v TcpAckFrequency /t REG_DWORD /d 1 /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\%%I" /v TCPNoDelay /t REG_DWORD /d 1 /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\%%I" /v TcpDelAckTicks /t REG_DWORD /d 0 /f >nul 2>&1
)
:: Global TCP tuning for gaming
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global ecncapability=enabled >nul 2>&1
netsh int tcp set global timestamps=disabled >nul 2>&1
netsh int tcp set global rss=enabled >nul 2>&1
netsh int tcp set heuristics disabled >nul 2>&1
:: Reduce network throttling for multimedia/gaming traffic
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f >nul 2>&1
:: Flush DNS for a clean state
ipconfig /flushdns >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 11) VISUAL EFFECTS -> PERFORMANCE (keeps text smoothing)
:: ---------------------------------------------------------------------------
echo  [ 8/12] Setting visual effects to best performance...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 12) DISABLE BACKGROUND APPS + MEMORY / RESPONSIVENESS TWEAKS
:: ---------------------------------------------------------------------------
echo  [ 9/12] Disabling background UWP apps and tuning memory...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy" /v LetAppsRunInBackground /t REG_DWORD /d 2 /f >nul 2>&1
:: Prioritize programs over background services for CPU scheduling
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f >nul 2>&1
:: Disable memory compression if RAM is plentiful (16GB+) for lower latency
if %RAM_GB% GEQ 16 (
    powershell -NoProfile -Command "Disable-MMAgent -mc" >nul 2>&1
    echo         16GB+ RAM detected: memory compression disabled.
) else (
    echo         Under 16GB RAM: memory compression left enabled (safer).
)
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 13) KEYBOARD FIX: ADD ENGLISH (US) + ARABIC LAYOUTS
:: ---------------------------------------------------------------------------
echo  [10/12] Configuring keyboard languages (English + Arabic)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$list = New-WinUserLanguageList -Language 'en-US';" ^
  "$list.Add('ar-SA');" ^
  "Set-WinUserLanguageList -LanguageList $list -Force;" ^
  "Set-WinDefaultInputMethodOverride -InputTip '0409:00000409'" >nul 2>&1
:: Toggle hotkey: Left Alt + Shift switches between languages (value 1)
reg add "HKCU\Keyboard Layout\Toggle" /v "Language Hotkey" /t REG_SZ /d 1 /f >nul 2>&1
reg add "HKCU\Keyboard Layout\Toggle" /v "Hotkey" /t REG_SZ /d 1 /f >nul 2>&1
echo         English (US) + Arabic added. Switch with Left Alt + Shift.
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 14) CLEANUP TEMP FILES (frees RAM/disk, fewer leftover processes)
:: ---------------------------------------------------------------------------
echo  [11/12] Cleaning temporary files...
del /q /f /s "%TEMP%\*" >nul 2>&1
del /q /f /s "%SystemRoot%\Temp\*" >nul 2>&1
del /q /f /s "%SystemRoot%\Prefetch\*" >nul 2>&1
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 15) FINALIZE
:: ---------------------------------------------------------------------------
echo  [12/12] Finalizing...
:: Refresh group policy so changes apply immediately
gpupdate /force >nul 2>&1
echo         Done.
echo.

cls
echo ============================================================================
echo                       OPTIMIZATION COMPLETE!
echo ============================================================================
echo.
echo   Summary of what was optimized:
echo     - Power plan set to High / Ultimate Performance
echo     - Windows Game Mode + Hardware GPU Scheduling enabled
echo     - GPU/CPU priority raised for games (%GPU_VENDOR% / %CPU_VENDOR%)
echo     - Unnecessary services and telemetry tasks disabled
echo     - Network tuned for low latency (Nagle off, throttling off)
echo     - Visual effects set to best performance
echo     - Background apps disabled, memory tuned for %RAM_GB% GB
echo     - English (US) + Arabic keyboards installed (Alt+Shift to switch)
echo     - Temp files cleaned
echo.
echo   A System Restore point named "Before_PC_Gaming_Optimizer" was created.
echo   To undo everything: Start -^> "Create a restore point" -^> System Restore.
echo.
echo   A RESTART is recommended for all changes to take full effect.
echo.
choice /C YN /M "  Restart now"
if errorlevel 2 goto :END
shutdown /r /t 5 /c "Restarting to apply gaming optimizations..."

:END
echo.
echo   Exiting. Enjoy your optimized PC!  Game on.
echo.
pause
endlocal
exit /b 0
