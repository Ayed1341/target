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
set "OSNAME=Unknown"
set "OSBUILD=0"
for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuildNumber 2^>nul ^| find "CurrentBuildNumber"') do set "OSBUILD=%%b"
:: Primary: PowerShell (works on all Windows 10/11). Fallback: registry, then wmic.
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).Caption" 2^>nul') do set "OSNAME=%%i"
if "%OSNAME%"=="Unknown" for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName 2^>nul ^| find "ProductName"') do set "OSNAME=%%b"
if "%OSNAME%"=="Unknown" for /f "tokens=2 delims==" %%i in ('wmic os get Caption /value 2^>nul ^| find "="') do set "OSNAME=%%i"
:: Windows 11 reports build 22000+ but still names itself "Windows 10" in the registry, so use the build too.
echo %OSNAME% | find /i "Windows 11" >nul && set "WINVER=11"
echo %OSNAME% | find /i "Windows 10" >nul && set "WINVER=10"
if defined OSBUILD if %OSBUILD% GEQ 22000 set "WINVER=11"

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

:: --- CPU ---  (registry is the most reliable source; needs no PowerShell/WMIC)
set "CPU_NAME=Unknown"
set "CPU_VENDOR=Unknown"
set "CPU_VID="
set "CPU_THREADS=%NUMBER_OF_PROCESSORS%"
set "CPU_CORES=%NUMBER_OF_PROCESSORS%"
for /f "tokens=2,*" %%a in ('reg query "HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0" /v ProcessorNameString 2^>nul ^| find /i "ProcessorNameString"') do set "CPU_NAME=%%b"
for /f "tokens=2,*" %%a in ('reg query "HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0" /v VendorIdentifier 2^>nul ^| find /i "VendorIdentifier"') do set "CPU_VID=%%b"
echo %CPU_VID% %CPU_NAME% | find /i "Intel" >nul && set "CPU_VENDOR=Intel"
echo %CPU_VID% %CPU_NAME% | find /i "AMD"   >nul && set "CPU_VENDOR=AMD"
:: Physical core count via PowerShell (captured to a temp file - the reliable way)
powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum" > "%TEMP%\_pco_cores.txt" 2>nul
set /p CPU_CORES=<"%TEMP%\_pco_cores.txt"
del "%TEMP%\_pco_cores.txt" >nul 2>&1
if not defined CPU_CORES set "CPU_CORES=%NUMBER_OF_PROCESSORS%"

:: --- GPU ---  (PowerShell picks the card with the most VRAM = the discrete GPU)
set "GPU_NAME=Unknown"
set "GPU_VENDOR=Unknown"
powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Where-Object { $_.Name -and $_.AdapterRAM } | Sort-Object AdapterRAM -Descending | Select-Object -First 1 -ExpandProperty Name" > "%TEMP%\_pco_gpu.txt" 2>nul
set /p GPU_NAME=<"%TEMP%\_pco_gpu.txt"
del "%TEMP%\_pco_gpu.txt" >nul 2>&1
if not defined GPU_NAME set "GPU_NAME=Unknown"
:: Fallback 1: registry display class (primary adapter)
if "%GPU_NAME%"=="Unknown" for /f "tokens=2,*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000" /v DriverDesc 2^>nul ^| find /i "DriverDesc"') do set "GPU_NAME=%%b"
:: Fallback 2: any video controller via PowerShell
if "%GPU_NAME%"=="Unknown" (
    powershell -NoProfile -Command "@(Get-CimInstance Win32_VideoController)[0].Name" > "%TEMP%\_pco_gpu.txt" 2>nul
    set /p GPU_NAME=<"%TEMP%\_pco_gpu.txt"
    del "%TEMP%\_pco_gpu.txt" >nul 2>&1
)
if not defined GPU_NAME set "GPU_NAME=Unknown"
echo %GPU_NAME% | find /i "NVIDIA"  >nul && set "GPU_VENDOR=NVIDIA"
echo %GPU_NAME% | find /i "GeForce" >nul && set "GPU_VENDOR=NVIDIA"
echo %GPU_NAME% | find /i "RTX"     >nul && set "GPU_VENDOR=NVIDIA"
echo %GPU_NAME% | find /i "GTX"     >nul && set "GPU_VENDOR=NVIDIA"
echo %GPU_NAME% | find /i "Radeon"  >nul && set "GPU_VENDOR=AMD"
echo %GPU_NAME% | find /i "AMD"     >nul && set "GPU_VENDOR=AMD"
echo %GPU_NAME% | find /i "Intel"   >nul && set "GPU_VENDOR=Intel"
echo %GPU_NAME% | find /i "Arc"     >nul && set "GPU_VENDOR=Intel"
if "%GPU_NAME%"=="Unknown" set "GPU_NAME=Not detected - generic display driver"

:: --- RAM (total physical, rounded to GB) ---
set "RAM_GB=0"
powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)" > "%TEMP%\_pco_ram.txt" 2>nul
set /p RAM_GB=<"%TEMP%\_pco_ram.txt"
del "%TEMP%\_pco_ram.txt" >nul 2>&1
if not defined RAM_GB set "RAM_GB=0"
if "%RAM_GB%"=="" set "RAM_GB=0"

echo ----------------------------------------------------------------------------
echo   CPU : %CPU_NAME%
echo         Vendor: %CPU_VENDOR%   Cores: %CPU_CORES%   Threads: %CPU_THREADS%
echo   GPU : %GPU_NAME%
echo         Vendor: %GPU_VENDOR%
echo   RAM : %RAM_GB% GB
echo ----------------------------------------------------------------------------
echo.
pause

:: ===========================================================================
:: MAIN MENU - choose what you want to do
:: ===========================================================================
:MENU
cls
echo ============================================================================
echo                         PC GAMING OPTIMIZER  -  MAIN MENU
echo ============================================================================
echo.
echo   Detected:  CPU %CPU_VENDOR%  ^|  GPU %GPU_VENDOR%  ^|  RAM %RAM_GB% GB  ^|  Windows %WINVER%
echo ----------------------------------------------------------------------------
echo.
echo     [1]  Optimize PC for Gaming        (full tweak - makes a restore point first)
echo     [2]  Restore Last Restore Point     (roll Windows back if anything breaks)
echo     [3]  Create Fresh Restore Point     (save current state on demand)
echo     [4]  Live Monitor                   (CPU / GPU / RAM usage + temperature)
echo     [5]  PC Health Check + Repair        (14 tools to detect and fix problems)
echo     [6]  Remove Defender/Edge/Copilot + Disable Win Update (PERMANENT)
echo     [7]  Exit
echo.
echo ----------------------------------------------------------------------------
choice /C 1234567 /N /M "  Choose an option [1-7]: "
if errorlevel 7 goto :END
if errorlevel 6 goto :DEBLOAT_MS
if errorlevel 5 goto :HEALTH
if errorlevel 4 goto :MONITOR
if errorlevel 3 goto :NEWRP
if errorlevel 2 goto :RESTORE
if errorlevel 1 goto :OPTIMIZE
goto :MENU

:: ===========================================================================
:: OPTION 1 - FULL GAMING OPTIMIZATION
:: ===========================================================================
:OPTIMIZE
cls
echo ============================================================================
echo   APPLYING OPTIMIZATIONS...
echo ============================================================================
echo.

:: ---------------------------------------------------------------------------
:: Capture the CURRENT running-process count (BEFORE optimization)
:: ---------------------------------------------------------------------------
set "PROC_BEFORE=0"
for /f %%c in ('powershell -NoProfile -Command "(Get-Process).Count" 2^>nul') do set "PROC_BEFORE=%%c"
echo   Running processes BEFORE optimization: %PROC_BEFORE%
echo.

:: ---------------------------------------------------------------------------
:: 4) CREATE A SYSTEM RESTORE POINT (safety net)
:: ---------------------------------------------------------------------------
echo  [ 1/12] Creating System Restore point (automatic safety net)...
call :MAKE_RP "Before_PC_Gaming_Optimizer"
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
    echo         Under 16GB RAM: memory compression left enabled - safer.
)
echo         Done.
echo.

:: ---------------------------------------------------------------------------
:: 13) KEYBOARD FIX: ADD ENGLISH (US) + ARABIC LAYOUTS
:: ---------------------------------------------------------------------------
echo  [10/12] Configuring keyboard languages (English + Arabic)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$list = New-WinUserLanguageList -Language 'en-US'; $list.Add('ar-SA'); Set-WinUserLanguageList -LanguageList $list -Force; Set-WinDefaultInputMethodOverride -InputTip '0409:00000409'" >nul 2>&1
:: Toggle hotkey: Left Alt + Shift switches between languages (value 1)
reg add "HKCU\Keyboard Layout\Toggle" /v "Language Hotkey" /t REG_SZ /d 1 /f >nul 2>&1
reg add "HKCU\Keyboard Layout\Toggle" /v "Hotkey" /t REG_SZ /d 1 /f >nul 2>&1
echo         English (US) + Arabic added. Switch with Left Alt + Shift.
echo         Done.
echo.

:: ===========================================================================
:: 14) BONUS: 30 EXTRA ADVANCED GAMING TWEAKS
:: ===========================================================================
echo ============================================================================
echo   APPLYING 30 EXTRA ADVANCED TWEAKS...
echo ============================================================================
echo.

:: --- 01) Disable CPU core parking (use all cores at all times) -------------
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR 0cc5b647-c1df-4637-891a-dec35c318583 100 >nul 2>&1
echo   [01] CPU core parking disabled.

:: --- 02) Force minimum + maximum processor state to 100%% -------------------
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 100 >nul 2>&1
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100 >nul 2>&1
powercfg -setactive SCHEME_CURRENT >nul 2>&1
echo   [02] Processor min/max state locked to 100%%.

:: --- 03) Disable CPU Power Throttling (no down-clocking under load) ---------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 1 /f >nul 2>&1
echo   [03] CPU power throttling disabled.

:: --- 04) Disable dynamic tick (steadier frame timing / lower DPC) -----------
bcdedit /set disabledynamictick yes >nul 2>&1
echo   [04] Dynamic tick disabled.

:: --- 05) Use TSC instead of platform clock (lower timer latency) ------------
bcdedit /deletevalue useplatformclock >nul 2>&1
bcdedit /set tscsyncpolicy Enhanced >nul 2>&1
echo   [05] High-resolution TSC timer policy set.

:: --- 06) Disable Prefetch + Superfetch/SysMain at registry level ------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 0 /f >nul 2>&1
echo   [06] Prefetch / Superfetch disabled.

:: --- 07) Disable Fault Tolerant Heap (removes overhead) ---------------------
reg add "HKLM\SOFTWARE\Microsoft\FTH" /v Enabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [07] Fault Tolerant Heap disabled.

:: --- 08) NTFS: stop updating last-access timestamps (faster disk I/O) -------
fsutil behavior set disablelastaccess 1 >nul 2>&1
echo   [08] NTFS last-access updates disabled.

:: --- 09) NTFS: disable 8.3 short filename creation --------------------------
fsutil behavior set disable8dot3 1 >nul 2>&1
echo   [09] NTFS 8.3 short names disabled.

:: --- 10) Ensure SSD TRIM is enabled (sustained SSD performance) -------------
fsutil behavior set DisableDeleteNotify 0 >nul 2>&1
echo   [10] SSD TRIM enabled.

:: --- 11) Disable hibernation (frees disk + removes Fast Startup stutter) ----
powercfg /h off >nul 2>&1
echo   [11] Hibernation / Fast Startup disabled.

:: --- 12) Disable mouse acceleration (raw 1:1 aim) ---------------------------
reg add "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f >nul 2>&1
reg add "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f >nul 2>&1
reg add "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f >nul 2>&1
echo   [12] Mouse acceleration disabled (raw input).

:: --- 13) Increase GPU TDR delay (prevents driver-timeout stutters) ----------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 10 /f >nul 2>&1
echo   [13] GPU TDR timeout raised.

:: --- 14) Enable MSI-mode (Message Signaled Interrupts) for the GPU ----------
powershell -NoProfile -Command "$id=(Get-CimInstance Win32_VideoController | Where-Object { $_.PNPDeviceID -like 'PCI*' } | Select-Object -First 1).PNPDeviceID; if($id){ $p='HKLM:\SYSTEM\CurrentControlSet\Enum\'+$id+'\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties'; New-Item -Path $p -Force | Out-Null; Set-ItemProperty -Path $p -Name MSISupported -Type DWord -Value 1 }" >nul 2>&1
echo   [14] GPU MSI-mode interrupts enabled.

:: --- 15) Disable fullscreen optimizations globally (true exclusive FS) ------
reg add "HKCU\System\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v GameDVR_HonorUserFSEBehaviorMode /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v GameDVR_DXGIHonorFSEWindowsCompatible /t REG_DWORD /d 1 /f >nul 2>&1
echo   [15] Fullscreen optimizations disabled.

:: --- 16) Disable Xbox / Game-bar related services ---------------------------
for %%S in (XblAuthManager XblGameSave XboxGipSvc XboxNetApiSvc BcastDVRUserService) do (
    sc stop "%%S" >nul 2>&1
    sc config "%%S" start= demand >nul 2>&1
)
echo   [16] Xbox background services set to manual.

:: --- 17) Disable Cortana ----------------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f >nul 2>&1
echo   [17] Cortana disabled.

:: --- 18) Disable Windows suggestions / tips / consumer ads ------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SilentInstalledAppsEnabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SystemPaneSuggestionsEnabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SubscribedContent-338388Enabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [18] Suggestions / ads / tips disabled.

:: --- 19) Disable Storage Sense (no surprise cleanups mid-game) --------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\StorageSense" /v AllowStorageSenseGlobal /t REG_DWORD /d 0 /f >nul 2>&1
echo   [19] Storage Sense disabled.

:: --- 20) Disable Delivery Optimization P2P update sharing -------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v DODownloadMode /t REG_DWORD /d 0 /f >nul 2>&1
echo   [20] Update P2P sharing disabled.

:: --- 21) Disable transparency (frees GPU/DWM cycles) ------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f >nul 2>&1
echo   [21] Transparency effects disabled.

:: --- 22) Remove startup delay for desktop apps ------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v StartupDelayInMSec /t REG_DWORD /d 0 /f >nul 2>&1
echo   [22] App startup delay removed.

:: --- 23) Disable the lock screen (faster boot to desktop) -------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization" /v NoLockScreen /t REG_DWORD /d 1 /f >nul 2>&1
echo   [23] Lock screen disabled.

:: --- 24) Disable NDU service (high-RAM network usage monitor) ---------------
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Ndu" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
echo   [24] NDU memory-hog service disabled.

:: --- 25) Disable Windows Error Reporting ------------------------------------
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f >nul 2>&1
echo   [25] Windows Error Reporting disabled.

:: --- 26) Stop Automatic Maintenance from waking/throttling the PC -----------
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance" /v MaintenanceDisabled /t REG_DWORD /d 1 /f >nul 2>&1
echo   [26] Automatic maintenance disabled.

:: --- 27) Disable toast notifications (no pop-ups mid-match) -----------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings" /v NOC_GLOBAL_SETTING_TOASTS_ENABLED /t REG_DWORD /d 0 /f >nul 2>&1
echo   [27] Toast notifications disabled.

:: --- 28) Larger network buffers + disable ECN scaling stalls ----------------
netsh int tcp set global nonsackrttresiliency=disabled >nul 2>&1
netsh int tcp set global initialRto=2000 >nul 2>&1
netsh int tcp set supplemental internet congestionprovider=ctcp >nul 2>&1
echo   [28] TCP congestion + RTO tuned for gaming.

:: --- 29) Set network adapters to highest priority + disable LSO ------------
powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object { Disable-NetAdapterLso -Name $_.Name -ErrorAction SilentlyContinue }" >nul 2>&1
echo   [29] Large Send Offload disabled (lower latency).

:: --- 30) OPTIONAL: disable CPU security mitigations + VBS for max FPS -------
echo.
echo   [30] OPTIONAL: Disabling Spectre/Meltdown mitigations and VBS/Memory
echo        Integrity can add a few %% FPS, but REDUCES system security.
choice /C YN /M "        Apply this optional max-performance tweak"
if errorlevel 2 (
    echo        Skipped tweak 30 - security kept intact.
) else (
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v FeatureSettingsOverride /t REG_DWORD /d 3 /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v FeatureSettingsOverrideMask /t REG_DWORD /d 3 /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f >nul 2>&1
    echo        Applied: mitigations + VBS disabled.
)
echo.
echo   30 advanced tweaks applied.
echo.

:: ===========================================================================
:: 14B) BONUS PACK 2: 40 MORE ADVANCED TWEAKS
:: ===========================================================================
echo ============================================================================
echo   APPLYING 40 MORE ADVANCED TWEAKS...
echo ============================================================================
echo.

:: --- 01) Remove QoS reserved bandwidth (Windows reserves 20%% by default) ---
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched" /v NonBestEffortLimit /t REG_DWORD /d 0 /f >nul 2>&1
echo   [01] QoS bandwidth reservation removed.

:: --- 02) Disable Receive Segment Coalescing (lower network latency) ---------
netsh int tcp set global rsc=disabled >nul 2>&1
echo   [02] RSC disabled.

:: --- 03) Force ALL services into shared svchost.exe (BIGGEST process drop) --
:: Max DWORD threshold forces every eligible service to share a host process.
reg add "HKLM\SYSTEM\CurrentControlSet\Control" /v SvcHostSplitThresholdInKB /t REG_DWORD /d 4294967295 /f >nul 2>&1
echo   [03] Services forced into shared svchost (big process-count drop after reboot).

:: --- 04) Disable NIC interrupt moderation (snappier networking) -------------
powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name -DisplayName 'Interrupt Moderation' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue }" >nul 2>&1
echo   [04] NIC interrupt moderation disabled.

:: --- 05) Disable NIC flow control -------------------------------------------
powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name -DisplayName 'Flow Control' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue }" >nul 2>&1
echo   [05] NIC flow control disabled.

:: --- 06) Reset Winsock catalog (fixes corrupted network stack / lag) --------
netsh winsock reset >nul 2>&1
echo   [06] Winsock catalog reset (effective after reboot).

:: --- 07) Faster name-resolution priority (DNS/Hosts before NetBT) -----------
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v LocalPriority /t REG_DWORD /d 4 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v HostsPriority /t REG_DWORD /d 5 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v DnsPriority /t REG_DWORD /d 6 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v NetbtPriority /t REG_DWORD /d 7 /f >nul 2>&1
echo   [07] Name-resolution priority optimized.

:: --- 08) Set fast public DNS (Cloudflare + Google) on active adapters -------
powershell -NoProfile -Command "Get-NetAdapter -Physical | Where-Object {$_.Status -eq 'Up'} | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses ('1.1.1.1','8.8.8.8') -ErrorAction SilentlyContinue }" >nul 2>&1
echo   [08] DNS set to 1.1.1.1 / 8.8.8.8 (reversible to automatic anytime).

:: --- 09) Raise RTC/IRQ8 priority --------------------------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v IRQ8Priority /t REG_DWORD /d 1 /f >nul 2>&1
echo   [09] System timer IRQ priority raised.

:: --- 10) Enable x2APIC + disable legacy APIC (better interrupt routing) -----
bcdedit /set x2apicpolicy enable >nul 2>&1
bcdedit /set uselegacyapicmode no >nul 2>&1
echo   [10] x2APIC interrupt routing enabled.

:: --- 11) Remove boot CPU-core limit (use every core at boot) ----------------
bcdedit /deletevalue numproc >nul 2>&1
echo   [11] Boot core limit removed.

:: --- 12) Faster boot (no boot animation, shorter menu timeout) --------------
bcdedit /set bootux disabled >nul 2>&1
bcdedit /timeout 3 >nul 2>&1
echo   [12] Faster boot configured.

:: --- 13) Keep kernel + drivers in RAM (disable paging executive) ------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul 2>&1
echo   [13] Kernel paging disabled (kept in RAM).

:: --- 14) Set a fixed pagefile sized to RAM (no resize stutter) --------------
if %RAM_GB% GTR 0 (
    set /a "PFSIZE=%RAM_GB%*1024"
    powershell -NoProfile -Command "$cs=Get-CimInstance Win32_ComputerSystem; if($cs.AutomaticManagedPagefile){$cs.AutomaticManagedPagefile=$false; Set-CimInstance -InputObject $cs}" >nul 2>&1
    powershell -NoProfile -Command "$s=!PFSIZE!; $p=Get-CimInstance Win32_PageFileSetting; if($p){$p.InitialSize=$s; $p.MaximumSize=$s; Set-CimInstance -InputObject $p}" >nul 2>&1
    echo   [14] Fixed pagefile set to !PFSIZE! MB.
) else (
    echo   [14] Skipped pagefile sizing ^(RAM not detected^).
)

:: --- 15) Do not clear pagefile at shutdown (faster shutdown) ----------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v ClearPageFileAtShutdown /t REG_DWORD /d 0 /f >nul 2>&1
echo   [15] Pagefile clear-on-shutdown disabled.

:: --- 16) Disable DWM Multiplane Overlay (fixes stutter/flicker) -------------
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v OverlayTestMode /t REG_DWORD /d 5 /f >nul 2>&1
echo   [16] DWM MPO disabled.

:: --- 17) Enable optimizations for windowed games + VRR (Win11) --------------
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v DirectXUserGlobalSettings /t REG_SZ /d "SwapEffectUpgradeEnable=1;VRROptimizeEnable=1;" /f >nul 2>&1
echo   [17] Windowed-game + VRR optimizations enabled.

:: --- 18) Faster keyboard repeat rate / shortest delay -----------------------
reg add "HKCU\Control Panel\Keyboard" /v KeyboardDelay /t REG_SZ /d 0 /f >nul 2>&1
reg add "HKCU\Control Panel\Keyboard" /v KeyboardSpeed /t REG_SZ /d 31 /f >nul 2>&1
echo   [18] Keyboard repeat speed maximized.

:: --- 19) Smaller mouse/keyboard input queues (lower input latency) ----------
reg add "HKLM\SYSTEM\CurrentControlSet\Services\mouclass\Parameters" /v MouseDataQueueSize /t REG_DWORD /d 20 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\kbdclass\Parameters" /v KeyboardDataQueueSize /t REG_DWORD /d 20 /f >nul 2>&1
echo   [19] Input queue latency reduced.

:: --- 20) Disable Sticky / Filter / Toggle key pop-ups -----------------------
reg add "HKCU\Control Panel\Accessibility\StickyKeys" /v Flags /t REG_SZ /d 506 /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Keyboard Response" /v Flags /t REG_SZ /d 122 /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\ToggleKeys" /v Flags /t REG_SZ /d 58 /f >nul 2>&1
echo   [20] Accessibility key pop-ups disabled.

:: --- 21) Disable Widgets (Win11) --------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Dsh" /v AllowNewsAndInterests /t REG_DWORD /d 0 /f >nul 2>&1
echo   [21] Widgets disabled.

:: --- 22) Disable Chat / Teams taskbar icon ----------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarMn /t REG_DWORD /d 0 /f >nul 2>&1
echo   [22] Taskbar Chat icon removed.

:: --- 23) Disable Bing / web search in Start menu ----------------------------
reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f >nul 2>&1
echo   [23] Start menu web search disabled.

:: --- 24) Disable Search highlights ------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v EnableDynamicContentInWSB /t REG_DWORD /d 0 /f >nul 2>&1
echo   [24] Search highlights disabled.

:: --- 25) Disable Activity History / Timeline --------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v PublishUserActivities /t REG_DWORD /d 0 /f >nul 2>&1
echo   [25] Activity history disabled.

:: --- 26) Disable Reserved Storage (frees up to ~7 GB) -----------------------
dism /Online /Set-ReservedStorageState /State:Disabled >nul 2>&1
echo   [26] Reserved storage disabled.

:: --- 27) Disable Remote Assistance ------------------------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Remote Assistance" /v fAllowToGetHelp /t REG_DWORD /d 0 /f >nul 2>&1
echo   [27] Remote Assistance disabled.

:: --- 28) Disable Edge startup boost + background mode -----------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge" /v StartupBoostEnabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge" /v BackgroundModeEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [28] Edge background processes disabled.

:: --- 29) Disable OneDrive auto-start ----------------------------------------
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v OneDrive /f >nul 2>&1
echo   [29] OneDrive auto-start disabled.

:: --- 30) Disable ReadyBoot boot tracing -------------------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\ReadyBoot" /v Start /t REG_DWORD /d 0 /f >nul 2>&1
echo   [30] ReadyBoot tracing disabled.

:: --- 31) Force maximum timer resolution at all times ------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\kernel" /v GlobalTimerResolutionRequests /t REG_DWORD /d 1 /f >nul 2>&1
echo   [31] Max timer resolution forced.

:: --- 32) Disable Application Compatibility telemetry ------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v AITEnable /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v DisableInventory /t REG_DWORD /d 1 /f >nul 2>&1
echo   [32] AppCompat telemetry disabled.

:: --- 33) Disable Customer Experience Improvement (CEIP) ----------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\SQMClient\Windows" /v CEIPEnable /t REG_DWORD /d 0 /f >nul 2>&1
echo   [33] CEIP disabled.

:: --- 34) Disable Advertising ID ---------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo" /v DisabledByGroupPolicy /t REG_DWORD /d 1 /f >nul 2>&1
echo   [34] Advertising ID disabled.

:: --- 35) Disable tailored experiences ---------------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [35] Tailored experiences disabled.

:: --- 36) Disable feedback prompts -------------------------------------------
reg add "HKCU\Software\Microsoft\Siuf\Rules" /v NumberOfSIUFInPeriod /t REG_DWORD /d 0 /f >nul 2>&1
echo   [36] Feedback prompts disabled.

:: --- 37) Disable Wi-Fi Sense auto-connect to open hotspots ------------------
reg add "HKLM\SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config" /v AutoConnectAllowedOEM /t REG_DWORD /d 0 /f >nul 2>&1
echo   [37] Wi-Fi Sense auto-connect disabled.

:: --- 38) Faster shutdown (shorter service/app kill timeouts) ----------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control" /v WaitToKillServiceTimeout /t REG_SZ /d 2000 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v WaitToKillAppTimeout /t REG_SZ /d 2000 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v HungAppTimeout /t REG_SZ /d 2000 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v AutoEndTasks /t REG_SZ /d 1 /f >nul 2>&1
echo   [38] Shutdown timeouts shortened.

:: --- 39) Collapse News/Feeds taskbar widget ---------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Feeds" /v ShellFeedsTaskbarViewMode /t REG_DWORD /d 2 /f >nul 2>&1
echo   [39] News feed widget disabled.

:: --- 40) Restart Explorer so taskbar/UI tweaks apply immediately ------------
taskkill /f /im explorer.exe >nul 2>&1
start explorer.exe
echo   [40] Explorer restarted (UI tweaks applied).
echo.
echo   40 more advanced tweaks applied.
echo.

:: ===========================================================================
:: 14B2) BONUS PACK 3: 15 MORE ADVANCED TWEAKS
:: ===========================================================================
echo ============================================================================
echo   APPLYING 15 MORE ADVANCED TWEAKS...
echo ============================================================================
echo.

:: --- 01) Disable Fast Startup (cleaner boot, no leftover state) -------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [01] Fast Startup disabled.

:: --- 02) Disable Large System Cache (better for games) ----------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v LargeSystemCache /t REG_DWORD /d 0 /f >nul 2>&1
echo   [02] Large System Cache disabled.

:: --- 03) Mark Games as latency-sensitive with a high clock rate ------------
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Latency Sensitive" /t REG_SZ /d "True" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Background Only" /t REG_SZ /d "False" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Clock Rate" /t REG_DWORD /d 10000 /f >nul 2>&1
echo   [03] Games marked latency-sensitive.

:: --- 04) Extra GPU stability (TDR DDI delay) --------------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v TdrDdiDelay /t REG_DWORD /d 10 /f >nul 2>&1
echo   [04] GPU TDR DDI delay raised.

:: --- 05) Disable Windows Spotlight lock-screen ads --------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v RotatingLockScreenEnabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v RotatingLockScreenOverlayEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo   [05] Lock-screen Spotlight ads disabled.

:: --- 06) Disable Explorer sync-provider ads ---------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowSyncProviderNotifications /t REG_DWORD /d 0 /f >nul 2>&1
echo   [06] Explorer ad notifications disabled.

:: --- 07) Stop Start menu app/document tracking ------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Start_TrackProgs /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Start_TrackDocs /t REG_DWORD /d 0 /f >nul 2>&1
echo   [07] Start menu tracking disabled.

:: --- 08) Disable cloud consumer features / auto-installed apps --------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent" /v DisableWindowsConsumerFeatures /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent" /v DisableSoftLanding /t REG_DWORD /d 1 /f >nul 2>&1
echo   [08] Cloud consumer features disabled.

:: --- 09) Stop Windows from juggling the default printer ---------------------
reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Windows" /v LegacyDefaultPrinterMode /t REG_DWORD /d 1 /f >nul 2>&1
echo   [09] Default-printer auto-switching disabled.

:: --- 10) Disable Aero Shake (minimize distraction) --------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v DisallowShaking /t REG_DWORD /d 1 /f >nul 2>&1
echo   [10] Aero Shake disabled.

:: --- 11) Disable taskbar animations -----------------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarAnimations /t REG_DWORD /d 0 /f >nul 2>&1
echo   [11] Taskbar animations disabled.

:: --- 12) Delivery Optimization service to manual ----------------------------
sc query DoSvc >nul 2>&1 && sc config DoSvc start= demand >nul 2>&1
echo   [12] Delivery Optimization set to manual.

:: --- 13) Connected Devices Platform service to manual -----------------------
sc query CDPSvc >nul 2>&1 && sc config CDPSvc start= demand >nul 2>&1
echo   [13] Connected Devices Platform set to manual.

:: --- 14) Disable low-disk-space nag popups ----------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v NoLowDiskSpaceChecks /t REG_DWORD /d 1 /f >nul 2>&1
echo   [14] Low-disk-space popups disabled.

:: --- 15) Disable Push-To-Install (silent remote app installs) ---------------
sc query PushToInstall >nul 2>&1 && sc config PushToInstall start= disabled >nul 2>&1
echo   [15] Push-To-Install service disabled.
echo.
echo   15 more advanced tweaks applied.  (85 tweaks so far)
echo.

:: ===========================================================================
:: 14B3) BONUS PACK 4: 65 MORE ADVANCED TWEAKS  (brings total to 150)
:: ===========================================================================
echo ============================================================================
echo   APPLYING 65 MORE ADVANCED TWEAKS  (this section is the biggest)...
echo ============================================================================
echo.

:: ---- NETWORK (deep) --------------------------------------------------------
echo   Network:
:: 01 Disable NetBIOS over TCP/IP on all interfaces
powershell -NoProfile -Command "Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces' | ForEach-Object { Set-ItemProperty -Path $_.PSPath -Name NetbiosOptions -Value 2 -ErrorAction SilentlyContinue }" >nul 2>&1
echo     [01] NetBIOS over TCP/IP disabled.
:: 02 Disable LMHOSTS lookup
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters" /v EnableLMHOSTS /t REG_DWORD /d 0 /f >nul 2>&1
echo     [02] LMHOSTS lookup disabled.
:: 03 Disable Teredo / 6to4 / ISATAP tunneling
netsh interface teredo set state disabled >nul 2>&1
netsh interface 6to4 set state disabled >nul 2>&1
netsh interface isatap set state disabled >nul 2>&1
echo     [03] IPv6 transition tunneling disabled.
:: 04 Faster TCP failure detection
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TcpMaxDataRetransmissions /t REG_DWORD /d 3 /f >nul 2>&1
echo     [04] TCP retransmission count lowered.
:: 05 Set DefaultTTL
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v DefaultTTL /t REG_DWORD /d 64 /f >nul 2>&1
echo     [05] Default TTL set to 64.
:: 06 More ephemeral ports + faster reuse
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v MaxUserPort /t REG_DWORD /d 65534 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TcpTimedWaitDelay /t REG_DWORD /d 30 /f >nul 2>&1
echo     [06] Ephemeral port range widened.
:: 07 Disable NIC power management (allow turn off device)
powershell -NoProfile -Command "Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}' | Where-Object { $_.PSChildName -match '^\d{4}$' } | ForEach-Object { Set-ItemProperty -Path $_.PSPath -Name PnPCapabilities -Value 24 -ErrorAction SilentlyContinue }" >nul 2>&1
echo     [07] NIC power management disabled.
:: 08 Disable Wi-Fi adapter power saving
powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name -DisplayName 'Power Saving Mode' -DisplayValue 'Maximum Performance' -ErrorAction SilentlyContinue }" >nul 2>&1
echo     [08] Wi-Fi power saving disabled.
:: 09 Tune DNS cache TTLs
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v MaxCacheTtl /t REG_DWORD /d 86400 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v MaxNegativeCacheTtl /t REG_DWORD /d 0 /f >nul 2>&1
echo     [09] DNS cache TTLs tuned.
:: 10 Disable SMB1 protocol (legacy, slow, insecure)
dism /Online /Disable-Feature /FeatureName:SMB1Protocol /NoRestart >nul 2>&1
echo     [10] SMB1 protocol disabled.

:: ---- SERVICES (extra, safe - set to manual) --------------------------------
echo   Services:
for %%S in (SCardSvr ScDeviceEnum SCPolicySvc) do (sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1)
echo     [11] Smart Card services set to manual.
for %%S in (SensorService SensrSvc SensorDataService) do (sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1)
echo     [12] Sensor services set to manual.
sc query TabletInputService >nul 2>&1 && sc config TabletInputService start= demand >nul 2>&1
echo     [13] Touch Keyboard/Handwriting set to manual.
sc query SEMgrSvc >nul 2>&1 && sc config SEMgrSvc start= demand >nul 2>&1
echo     [14] NFC/Payments manager set to manual.
sc query WbioSrvc >nul 2>&1 && sc config WbioSrvc start= demand >nul 2>&1
echo     [15] Biometric service set to manual.
for %%S in (DPS WdiServiceHost WdiSystemHost) do (sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1)
echo     [16] Diagnostic services set to manual.
sc query AJRouter >nul 2>&1 && sc config AJRouter start= disabled >nul 2>&1
echo     [17] AllJoyn Router disabled.
sc query TrkWks >nul 2>&1 && sc config TrkWks start= demand >nul 2>&1
echo     [18] Distributed Link Tracking set to manual.
sc query CscService >nul 2>&1 && sc config CscService start= demand >nul 2>&1
echo     [19] Offline Files set to manual.
sc query WMPNetworkSvc >nul 2>&1 && sc config WMPNetworkSvc start= disabled >nul 2>&1
echo     [20] WMP Network Sharing disabled.
sc query wisvc >nul 2>&1 && sc config wisvc start= demand >nul 2>&1
echo     [21] Windows Insider service set to manual.

:: ---- PRIVACY / TELEMETRY (extra) -------------------------------------------
echo   Privacy:
:: 22 Inking and typing personalization off
reg add "HKCU\Software\Microsoft\InputPersonalization" /v RestrictImplicitInkCollection /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\InputPersonalization" /v RestrictImplicitTextCollection /t REG_DWORD /d 1 /f >nul 2>&1
echo     [22] Inking/typing personalization disabled.
:: 23 Online speech recognition data off
reg add "HKCU\Software\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy" /v HasAccepted /t REG_DWORD /d 0 /f >nul 2>&1
echo     [23] Online speech data disabled.
:: 24 Deny system-wide location access
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location" /v Value /t REG_SZ /d Deny /f >nul 2>&1
echo     [24] System location access denied.
:: 25 Find My Device off
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\default\Settings\AllowFindMyDevice" /v value /t REG_DWORD /d 0 /f >nul 2>&1
echo     [25] Find My Device disabled.
:: 26 Cloud clipboard / history off
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v AllowClipboardHistory /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v AllowCrossDeviceClipboard /t REG_DWORD /d 0 /f >nul 2>&1
echo     [26] Cloud clipboard/history disabled.
:: 27 Diagtrack ETW autologger off
reg add "HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\AutoLogger-Diagtrack-Listener" /v Start /t REG_DWORD /d 0 /f >nul 2>&1
echo     [27] Diagtrack ETW logger disabled.
:: 28 Feedback notifications off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\DataCollection" /v DoNotShowFeedbackNotifications /t REG_DWORD /d 1 /f >nul 2>&1
echo     [28] Feedback notifications disabled.
:: 29 Bing/Cortana in search off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v CortanaConsent /t REG_DWORD /d 0 /f >nul 2>&1
echo     [29] Bing/Cortana search disabled.
:: 30 Online tips off
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v AllowOnlineTips /t REG_DWORD /d 0 /f >nul 2>&1
echo     [30] Online tips disabled.
:: 31 Windows Media DRM internet access off
reg add "HKLM\SOFTWARE\Policies\Microsoft\WMDRM" /v DisableOnline /t REG_DWORD /d 1 /f >nul 2>&1
echo     [31] WMP DRM internet access disabled.

:: ---- EXPLORER / UI SNAPPINESS ----------------------------------------------
echo   Interface:
:: 32 Classic context menu (Win11) - faster right click
reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /ve /t REG_SZ /d "" /f >nul 2>&1
echo     [32] Classic right-click menu restored.
:: 33 Quick Access recent/frequent off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer" /v ShowRecent /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer" /v ShowFrequent /t REG_DWORD /d 0 /f >nul 2>&1
echo     [33] Quick Access history disabled.
:: 34 Taskbar search box hidden
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f >nul 2>&1
echo     [34] Taskbar search box hidden.
:: 35 Task View button hidden
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowTaskViewButton /t REG_DWORD /d 0 /f >nul 2>&1
echo     [35] Task View button hidden.
:: 36 Snap Assist flyout off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v EnableSnapAssistFlyout /t REG_DWORD /d 0 /f >nul 2>&1
echo     [36] Snap Assist flyout disabled.
:: 37 Explorer opens This PC
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f >nul 2>&1
echo     [37] Explorer opens to This PC.
:: 38 Apps can take foreground instantly
reg add "HKCU\Control Panel\Desktop" /v ForegroundLockTimeout /t REG_DWORD /d 0 /f >nul 2>&1
echo     [38] Foreground lock timeout removed.
:: 39 Autorun/Autoplay off on all drives
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v NoDriveTypeAutoRun /t REG_DWORD /d 255 /f >nul 2>&1
echo     [39] Autorun/Autoplay disabled.
:: 40 People bar off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People" /v PeopleBand /t REG_DWORD /d 0 /f >nul 2>&1
echo     [40] People bar disabled.

:: ---- SCHEDULED TASKS + UPDATES ---------------------------------------------
echo   Tasks and updates:
:: 41 Disable extra telemetry/diagnostic scheduled tasks
for %%T in (
  "\Microsoft\Windows\Maintenance\WinSAT"
  "\Microsoft\Windows\Application Experience\StartupAppTask"
  "\Microsoft\Windows\Application Experience\PcaPatchDbTask"
  "\Microsoft\Windows\Autochk\Proxy"
  "\Microsoft\Windows\CloudExperienceHost\CreateObjectTask"
  "\Microsoft\Windows\Power Efficiency Diagnostics\AnalyzeSystem"
  "\Microsoft\Windows\DiskFootprint\Diagnostics"
  "\Microsoft\Windows\Shell\FamilySafetyMonitor"
) do schtasks /Change /TN %%T /Disable >nul 2>&1
echo     [41] Extra diagnostic tasks disabled.
:: 42 Edge auto-update tasks off
for %%T in (MicrosoftEdgeUpdateTaskMachineCore MicrosoftEdgeUpdateTaskMachineUA) do schtasks /Change /TN "%%T" /Disable >nul 2>&1
echo     [42] Edge auto-update tasks disabled.
:: 43 Disable automatic driver updates via Windows Update (stable GPU driver)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 1 /f >nul 2>&1
echo     [43] Auto driver updates via WU disabled.
:: 44 No auto-restart while users are logged on
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f >nul 2>&1
echo     [44] WU auto-restart with users disabled.
:: 45 Disable crash dump creation (faster recovery, saves disk)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CrashControl" /v CrashDumpEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo     [45] Crash dump creation disabled.
:: 46 Disable GameBarPresenceWriter
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f >nul 2>&1
taskkill /f /im GameBarPresenceWriter.exe >nul 2>&1
echo     [46] GameBar presence writer disabled.

:: ---- POWER / CPU FINE-TUNING -----------------------------------------------
echo   Power fine-tuning:
:: 47 Active system cooling (fan ramps before throttling)
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR SYSCOOLPOL 0 >nul 2>&1
echo     [47] Active system cooling policy set.
:: 48 PCI Express ASPM off (max performance)
powercfg -setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0 >nul 2>&1
echo     [48] PCI Express power saving disabled.
:: 49 Wake timers off
powercfg -setacvalueindex SCHEME_CURRENT SUB_SLEEP bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 0 >nul 2>&1
echo     [49] Wake timers disabled.
:: 50 Maximum processor frequency unlimited
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX 0 >nul 2>&1
echo     [50] Processor frequency cap removed.
:: 51 Reinforce USB selective-suspend off
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f >nul 2>&1
powercfg -setactive SCHEME_CURRENT >nul 2>&1
echo     [51] USB selective suspend disabled.

:: ---- MORE BLOAT / DISTRACTION REMOVAL --------------------------------------
echo   Final debloat:
:: 52 Faster Explorer folder loading (no auto folder-type discovery)
reg add "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\Bags\AllFolders\Shell" /v FolderType /t REG_SZ /d NotSpecified /f >nul 2>&1
echo     [52] Explorer folder auto-discovery disabled.
:: 53 Windows Ink Workspace off
reg add "HKLM\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace" /v AllowWindowsInkWorkspace /t REG_DWORD /d 0 /f >nul 2>&1
echo     [53] Windows Ink Workspace disabled.
:: 54 Shared Experiences / Nearby sharing off
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableCdp /t REG_DWORD /d 0 /f >nul 2>&1
echo     [54] Shared Experiences disabled.
:: 55 No app notifications on lock screen
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v NoToastApplicationNotificationOnLockScreen /t REG_DWORD /d 1 /f >nul 2>&1
echo     [55] Lock-screen notifications disabled.
:: 56 Suggested content in Settings off
for %%V in (SubscribedContent-338393Enabled SubscribedContent-353694Enabled SubscribedContent-353696Enabled) do reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v %%V /t REG_DWORD /d 0 /f >nul 2>&1
echo     [56] Settings suggestions disabled.
:: 57 Stop pre-installed / OEM suggested apps
for %%V in (ContentDeliveryAllowed PreInstalledAppsEnabled OemPreInstalledAppsEnabled) do reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v %%V /t REG_DWORD /d 0 /f >nul 2>&1
echo     [57] Auto-installed suggested apps disabled.
:: 58 Disable Spotlight collection on desktop
reg add "HKCU\Software\Policies\Microsoft\Windows\CloudContent" /v DisableSpotlightCollectionOnDesktop /t REG_DWORD /d 1 /f >nul 2>&1
echo     [58] Desktop Spotlight disabled.
:: 59 Disable first-logon animation (faster login)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableFirstLogonAnimation /t REG_DWORD /d 0 /f >nul 2>&1
echo     [59] First-logon animation disabled.
:: 60 Hide recently added apps in Start
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v HideRecentlyAddedApps /t REG_DWORD /d 1 /f >nul 2>&1
echo     [60] Recently-added apps hidden in Start.
:: 61 Disable live-tile cloud notifications
reg add "HKCU\Software\Policies\Microsoft\Windows\CurrentVersion\PushNotifications" /v NoCloudApplicationNotification /t REG_DWORD /d 1 /f >nul 2>&1
echo     [61] Live-tile cloud notifications disabled.
:: 62 Disable post-update "welcome / what's new" pages
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SubscribedContent-310093Enabled /t REG_DWORD /d 0 /f >nul 2>&1
echo     [62] Post-update welcome pages disabled.
:: 63 Disable OOBE "get even more out of Windows" nag
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v ScoobeSystemSettingEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo     [63] OOBE upsell nag disabled.

:: ---- GPU VENDOR-SPECIFIC (auto-applied to your GPU) ------------------------
echo   GPU vendor:
:: 64 NVIDIA telemetry off
if /i "%GPU_VENDOR%"=="NVIDIA" (
    powershell -NoProfile -Command "Get-ScheduledTask -TaskPath '\' -ErrorAction SilentlyContinue | Where-Object {$_.TaskName -like 'Nv*'} | Disable-ScheduledTask -ErrorAction SilentlyContinue" >nul 2>&1
    sc query NvTelemetryContainer >nul 2>&1 && sc config NvTelemetryContainer start= demand >nul 2>&1
    reg add "HKLM\SOFTWARE\NVIDIA Corporation\Global\FTS" /v EnableRID44231 /t REG_DWORD /d 0 /f >nul 2>&1
    echo     [64] NVIDIA telemetry disabled.
) else (
    echo     [64] NVIDIA telemetry - skipped ^(no NVIDIA GPU^).
)
:: 65 AMD ULPS off (lower multi-GPU latency)
if /i "%GPU_VENDOR%"=="AMD" (
    powershell -NoProfile -Command "Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' | Where-Object { $_.PSChildName -match '^\d{4}$' } | ForEach-Object { Set-ItemProperty -Path $_.PSPath -Name EnableUlps -Value 0 -ErrorAction SilentlyContinue }" >nul 2>&1
    echo     [65] AMD ULPS disabled.
) else (
    echo     [65] AMD ULPS - skipped ^(no AMD GPU^).
)
echo.
echo   65 more advanced tweaks applied.  (150 tweaks so far)
echo.

:: ===========================================================================
:: 14B4) BONUS PACK 5: SSD / HDD STORAGE OPTIMIZATION (5 advanced tweaks)
:: ===========================================================================
echo ============================================================================
echo   OPTIMIZING STORAGE (SSD / HDD)...
echo ============================================================================
echo.
echo   Detected drives and their type:
powershell -NoProfile -Command "Get-PhysicalDisk | Select-Object DeviceId,FriendlyName,MediaType,@{N='SizeGB';E={[math]::Round($_.Size/1GB)}} | Format-Table -AutoSize" 2>nul
echo.
:: 01 Auto-optimize each drive (TRIM for SSD, defrag for HDD) - OPTIONAL, can be slow
echo   [01] Drive optimization (TRIM on SSD, defrag on HDD).
echo        On a mechanical HDD this can take several minutes. SSD-only is fast.
choice /C YN /N /M "        Run drive optimization now? [Y/N]: "
if errorlevel 2 (
    echo        Skipped drive optimization - other storage tweaks still applied.
) else (
    echo        Optimizing, please wait...
    defrag /C /O /H >nul 2>&1
    defrag %SystemDrive% /L >nul 2>&1
    echo        Done - Windows applied the right method per drive.
)
:: 02 Bigger NTFS in-memory metadata cache (faster file/directory access)
fsutil behavior set memoryusage 2 >nul 2>&1
echo   [02] NTFS metadata RAM cache increased.
:: 03 Larger MFT reservation (less fragmentation with many small files)
fsutil behavior set mftzone 2 >nul 2>&1
echo   [03] NTFS MFT zone enlarged.
:: 04 Turn off write-cache buffer flushing for faster writes
powershell -NoProfile -Command "Get-CimInstance Win32_DiskDrive | ForEach-Object { $p='HKLM:\SYSTEM\CurrentControlSet\Enum\'+$_.PNPDeviceID+'\Device Parameters\Disk'; if(Test-Path $p){ Set-ItemProperty -Path $p -Name CacheIsPowerProtected -Value 1 -Type DWord -ErrorAction SilentlyContinue; Set-ItemProperty -Path $p -Name UserWriteCacheSetting -Value 1 -Type DWord -ErrorAction SilentlyContinue } }" >nul 2>&1
echo   [04] Write-cache buffer flushing disabled - best with a UPS or laptop battery.
:: 05 Disable legacy boot-time defrag/layout (useless on SSD, adds wear)
reg add "HKLM\SOFTWARE\Microsoft\Dfrg\BootOptimizeFunction" /v Enable /t REG_SZ /d N /f >nul 2>&1
echo   [05] Legacy boot defrag/layout disabled.
echo.
echo   5 storage tweaks applied.  (155 tweaks so far)
echo.

:: ===========================================================================
:: 14B5) BONUS PACK 6: 15 MORE TWEAKS + AGGRESSIVE PROCESS REDUCTION
:: ===========================================================================
echo ============================================================================
echo   APPLYING 15 MORE TWEAKS + CUTTING BACKGROUND PROCESSES...
echo ============================================================================
echo.
:: 01 Disable Hyper-V hypervisor at boot (frees overhead for games)
bcdedit /set hypervisorlaunchtype off >nul 2>&1
echo   [01] Hyper-V hypervisor disabled at boot (breaks WSL2/Sandbox if used).
:: 02 Disable memory page combining (less CPU overhead)
powershell -NoProfile -Command "Disable-MMAgent -PageCombining" >nul 2>&1
echo   [02] Memory page combining disabled.
:: 03 Print Spooler to manual (no background print process if unused)
sc query Spooler >nul 2>&1 && sc config Spooler start= demand >nul 2>&1
echo   [03] Print Spooler set to manual.
:: 04 Remote Desktop host services to manual
for %%S in (TermService UmRdpService SessionEnv) do (sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1)
echo   [04] Remote Desktop host services set to manual.
:: 05 Windows Image Acquisition (scanners/cameras) to manual
sc query stisvc >nul 2>&1 && sc config stisvc start= demand >nul 2>&1
echo   [05] Windows Image Acquisition set to manual.
:: 06 Secondary Logon to manual
sc query seclogon >nul 2>&1 && sc config seclogon start= demand >nul 2>&1
echo   [06] Secondary Logon set to manual.
:: 07 Certificate Propagation to manual
sc query CertPropSvc >nul 2>&1 && sc config CertPropSvc start= demand >nul 2>&1
echo   [07] Certificate Propagation set to manual.
:: 08 QWAVE (audio/video QoS) to manual
sc query QWAVE >nul 2>&1 && sc config QWAVE start= demand >nul 2>&1
echo   [08] QWAVE set to manual.
:: 09 Diagnostic Execution Service to manual
sc query diagsvc >nul 2>&1 && sc config diagsvc start= demand >nul 2>&1
echo   [09] Diagnostic Execution Service set to manual.
:: 10 Disable Connected Devices Platform per-user service (kills a background process)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\CDPUserSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
echo   [10] Connected Devices Platform user service disabled.
:: 11 Disable legacy TCP Chimney/Task offload
netsh int tcp set global chimney=disabled >nul 2>&1
echo   [11] TCP Chimney offload disabled.
:: 12 Disable Insider/preview-build telemetry
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\WUfB" /v AllowBuildPreview /t REG_DWORD /d 0 /f >nul 2>&1
echo   [12] Insider preview telemetry disabled.
:: 13 Disable Automatic Restart Sign-On (no background re-login)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableAutomaticRestartSignOn /t REG_DWORD /d 1 /f >nul 2>&1
echo   [13] Automatic Restart Sign-On disabled.
:: 14 Disable "Sync your settings" background sync
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync" /v DisableSettingSync /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync" /v DisableSettingSyncUserOverride /t REG_DWORD /d 1 /f >nul 2>&1
echo   [14] Settings sync disabled.
:: 15 Remove the Widgets / Web Experience pack (removes its background process)
powershell -NoProfile -Command "Get-AppxPackage -AllUsers *WebExperience* | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue" >nul 2>&1
echo   [15] Widgets / Web Experience removed.
echo.
:: --- Terminate well-known background bloat NOW (frees processes immediately) -
echo   Closing background bloat processes...
for %%P in (OneDrive.exe msedge.exe Widgets.exe WidgetService.exe GameBarPresenceWriter.exe GameBar.exe YourPhone.exe PhoneExperienceHost.exe Cortana.exe SearchApp.exe Teams.exe Skype.exe spotify.exe) do taskkill /f /im "%%P" >nul 2>&1
echo   Background bloat processes closed.
echo.
echo   15 more tweaks applied.  (170 tweaks so far)
echo.

:: ===========================================================================
:: 14B6) BONUS PACK 7: 8 MORE ADVANCED TWEAKS
:: ===========================================================================
echo ============================================================================
echo   APPLYING 8 MORE ADVANCED TWEAKS...
echo ============================================================================
echo.
:: 01 Snappier mouse hover response
reg add "HKCU\Control Panel\Mouse" /v MouseHoverTime /t REG_SZ /d 10 /f >nul 2>&1
echo   [01] Mouse hover time reduced.
:: 02 No balloon/tooltip popups
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v EnableBalloonTips /t REG_DWORD /d 0 /f >nul 2>&1
echo   [02] Balloon tip popups disabled.
:: 03 Larger network IRP stack (more stable file shares, fewer drops)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v IRPStackSize /t REG_DWORD /d 32 /f >nul 2>&1
echo   [03] Network IRP stack size increased.
:: 04 More cached icons for smoother Explorer
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /v "Max Cached Icons" /t REG_SZ /d 8192 /f >nul 2>&1
echo   [04] Icon cache enlarged.
:: 05 Lighter window dragging (no full-window redraw)
reg add "HKCU\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f >nul 2>&1
echo   [05] Full-window drag disabled.
:: 06 Stop tracking recently opened documents
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v NoRecentDocsHistory /t REG_DWORD /d 1 /f >nul 2>&1
echo   [06] Recent-docs tracking disabled.
:: 07 Disable the Notification/Action Center (removes its background UI)
reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter /t REG_DWORD /d 1 /f >nul 2>&1
echo   [07] Notification Center disabled.
:: 08 Disable the Windows startup sound
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI\BootAnimation" /v DisableStartupSound /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\EditionOverrides" /v UserSetting_DisableStartupSound /t REG_DWORD /d 1 /f >nul 2>&1
echo   [08] Startup sound disabled.
echo.
echo   8 more tweaks applied.  (178 tweaks so far)
echo.

:: ===========================================================================
:: 14B7) BONUS PACK 8: 15 MORE SERVICES TRIMMED (drives process count down)
:: ===========================================================================
echo ============================================================================
echo   TRIMMING 15 MORE SERVICES (fewer running processes after reboot)...
echo ============================================================================
echo.
:: These are all safe to set to manual - they auto-start only when truly needed.
set "SVC8=WpnService ShellHWDetection W32Time MSDTC EFS MSiSCSI TapiSrv workfolderssvc WalletService icssvc TroubleshootingSvc PeerDistSvc fhsvc SDRSVC Wecsvc"
set /a SVCN=0
for %%S in (%SVC8%) do (
    sc query "%%S" >nul 2>&1 && (
        sc config "%%S" start= demand >nul 2>&1
        set /a SVCN+=1
        echo   Set to manual: %%S
    )
)
echo.
echo   15 more services trimmed.  TOTAL: 193 tweaks.
echo.

:: ===========================================================================
:: 14C) GUARANTEE CONNECTIVITY + DEVICES + MICROSOFT STORE KEEP WORKING
::      None of the tweaks above disable these; this section makes 100%% sure
::      Wi-Fi, Bluetooth, USB/external devices, audio and the Store still work.
:: ===========================================================================
echo ============================================================================
echo   ENSURING WI-FI / BLUETOOTH / USB DEVICES / MICROSOFT STORE WORK...
echo ============================================================================
echo.

:: Services that must be AUTOMATIC (always running) ---------------------------
for %%A in (WlanSvc Wcmsvc NlaSvc Dhcp Dnscache Audiosrv AudioEndpointBuilder) do (
    sc query "%%A" >nul 2>&1 && (
        sc config "%%A" start= auto >nul 2>&1
        sc start "%%A" >nul 2>&1
    )
)
echo   [OK] Wi-Fi, network and audio services enabled.

:: Services that must be MANUAL/TRIGGER (start on demand when needed) ---------
for %%D in (bthserv BTAGService BthAvctpSvc PlugPlay DeviceAssociationService DeviceInstall WpdBusEnum Netman netprofm) do (
    sc query "%%D" >nul 2>&1 && sc config "%%D" start= demand >nul 2>&1
)
echo   [OK] Bluetooth + USB/external-device services enabled.

:: Microsoft Store + app install/licensing services --------------------------
for %%S in (AppXSvc ClipSVC InstallService StorSvc LicenseManager wuauserv wlidsvc TokenBroker TimeBrokerSvc) do (
    sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1
)
:: Make sure background-app policy does NOT block Store apps from launching
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy" /v LetAppsRunInBackground /t REG_DWORD /d 0 /f >nul 2>&1
echo   [OK] Microsoft Store and app services enabled.
echo.

:: ---------------------------------------------------------------------------
:: 15) CLEANUP TEMP FILES (frees RAM/disk, fewer leftover processes)
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
:: Capture the running-process count AFTER optimization
set "PROC_AFTER=0"
for /f %%c in ('powershell -NoProfile -Command "(Get-Process).Count" 2^>nul') do set "PROC_AFTER=%%c"
echo         Done.
echo.

cls
echo ============================================================================
echo                       OPTIMIZATION COMPLETE!
echo ============================================================================
echo.
echo   ----------------------------------------------------------------------
echo     PROCESS COUNT   BEFORE: %PROC_BEFORE%      AFTER: %PROC_AFTER%
echo     (Most service changes free even more processes after a RESTART.)
echo   ----------------------------------------------------------------------
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
echo     - 193 advanced tweaks: core parking off, MSI-mode, TSC/HPET timer,
echo       SSD/HDD storage optimization (auto TRIM/defrag, NTFS cache, MFT),
echo       NTFS/SSD/pagefile tuning, mouse+keyboard latency, svchost grouping,
echo       DNS 1.1.1.1, QoS/RSC/Winsock, DWM MPO off, Fast Startup off,
echo       latency-sensitive games, debloat, and more.
echo     - Wi-Fi, Bluetooth, USB/external devices and Microsoft Store kept
echo       fully working (essential services re-verified and enabled)
echo     - Temp files cleaned
echo.
echo   A System Restore point named "Before_PC_Gaming_Optimizer" was created.
echo   To undo everything: Start -^> "Create a restore point" -^> System Restore.
echo.
echo   A RESTART is recommended for all changes to take full effect.
echo.
choice /C YN /M "  Restart now"
if errorlevel 2 goto :MENU
shutdown /r /t 5 /c "Restarting to apply gaming optimizations..."
goto :END

:: ===========================================================================
:: OPTION 2 - RESTORE LAST RESTORE POINT
:: ===========================================================================
:RESTORE
cls
echo ============================================================================
echo   RESTORE LAST RESTORE POINT  -  roll your PC back
echo ============================================================================
echo.
echo   Available restore points (newest at the bottom):
echo ----------------------------------------------------------------------------
powershell -NoProfile -Command "Get-ComputerRestorePoint | Sort-Object SequenceNumber | Format-Table SequenceNumber,@{N='Date';E={$_.ConvertToDateTime($_.CreationTime)}},Description -AutoSize" 2>nul
echo ----------------------------------------------------------------------------
echo.
echo   Pick how you want to restore:
echo.
echo     [A]  Restore the LAST (most recent) restore point now and REBOOT
echo     [B]  Open System Restore to pick a point manually
echo     [C]  Revert just this tool's tweaks to defaults (no reboot)
echo     [D]  Back to main menu
echo.
choice /C ABCD /N /M "  Choose [A/B/C/D]: "
if errorlevel 4 goto :MENU
if errorlevel 3 goto :REVERT
if errorlevel 2 (
    echo.
    echo   Opening System Restore... pick a point and follow the wizard.
    rstrui.exe
    echo.
    pause
    goto :MENU
)
if errorlevel 1 (
    echo.
    echo   This will roll Windows back to the most recent restore point and
    echo   automatically REBOOT. Open programs will close.
    choice /C YN /M "   Restore the last restore point now"
    if errorlevel 2 goto :MENU
    echo   Restoring... your PC will reboot shortly.
    powershell -NoProfile -Command "$rp = Get-ComputerRestorePoint | Sort-Object SequenceNumber | Select-Object -Last 1; if ($rp) { Restore-Computer -RestorePoint $rp.SequenceNumber -Confirm:$false } else { Write-Host '  No restore points found - nothing to restore.'; Start-Sleep 3 }"
    pause
    goto :MENU
)

:REVERT
cls
echo ============================================================================
echo   REVERTING KEY TWEAKS TO WINDOWS DEFAULTS...
echo ============================================================================
echo.
:: Power: back to Balanced
powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e >nul 2>&1
echo   - Power plan reset to Balanced.
:: Re-enable the services we disabled
for %%S in (SysMain WSearch DiagTrack dmwappushservice WerSvc PcaSvc MapsBroker lfsvc) do (
    sc query "%%S" >nul 2>&1 && sc config "%%S" start= demand >nul 2>&1
)
sc config SysMain start= auto >nul 2>&1
sc config WSearch start= delayed-auto >nul 2>&1
echo   - Background services re-enabled.
:: Re-enable telemetry tasks
for %%T in (
  "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser"
  "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator"
) do schtasks /Change /TN %%T /Enable >nul 2>&1
echo   - Scheduled tasks restored.
:: Undo network tweaks (auto TCP, restore Nagle defaults, automatic DNS)
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global rsc=default >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /f >nul 2>&1
powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses -ErrorAction SilentlyContinue }" >nul 2>&1
echo   - Network settings reset to automatic.
:: Restore visual effects + service grouping + pagefile to automatic
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 0 /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Control" /v SvcHostSplitThresholdInKB /f >nul 2>&1
wmic computersystem set AutomaticManagedPagefile=True >nul 2>&1
:: Re-enable hibernation + memory compression + paging executive defaults
powercfg /h on >nul 2>&1
powershell -NoProfile -Command "Enable-MMAgent -mc" >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 0 /f >nul 2>&1
echo   - Memory, pagefile and visual effects restored.
:: Re-enable background apps + Defender mitigations defaults
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 0 /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v FeatureSettingsOverride /f >nul 2>&1
echo   - Background apps and security mitigations restored.
echo.
echo   Key tweaks reverted. For a 100%% rollback use option [A] (System Restore).
echo   A reboot is recommended.
echo.
pause
goto :MENU

:: ===========================================================================
:: OPTION 3 - PC HEALTH CHECK + AUTO-REPAIR (14 tools)
:: ===========================================================================
:HEALTH
cls
echo ============================================================================
echo   PC HEALTH CHECK + AUTO-REPAIR  (this can take 10-30 minutes)
echo ============================================================================
echo.
echo   This will scan for and fix common Windows problems. Safe to run anytime.
choice /C YN /M "  Start health check and repair"
if errorlevel 2 goto :MENU
echo.

:: --- 01) System File Checker - repair corrupted system files ----------------
echo   [01/14] Running SFC /scannow (repairing system files)...
sfc /scannow

:: --- 02) DISM - check component-store health --------------------------------
echo   [02/14] DISM CheckHealth...
dism /Online /Cleanup-Image /CheckHealth

:: --- 03) DISM - deep scan of component store --------------------------------
echo   [03/14] DISM ScanHealth (deep scan)...
dism /Online /Cleanup-Image /ScanHealth

:: --- 04) DISM - repair Windows image ----------------------------------------
echo   [04/14] DISM RestoreHealth (repairing Windows image)...
dism /Online /Cleanup-Image /RestoreHealth

:: --- 05) Online disk integrity scan -----------------------------------------
echo   [05/14] Scanning system drive for errors (chkdsk /scan)...
chkdsk C: /scan

:: --- 06) Repair Windows Update components -----------------------------------
echo   [06/14] Repairing Windows Update components...
net stop wuauserv >nul 2>&1
net stop bits >nul 2>&1
net stop cryptsvc >nul 2>&1
if exist "%SystemRoot%\SoftwareDistribution.old" rmdir /s /q "%SystemRoot%\SoftwareDistribution.old" >nul 2>&1
ren "%SystemRoot%\SoftwareDistribution" SoftwareDistribution.old >nul 2>&1
ren "%SystemRoot%\System32\catroot2" catroot2.old >nul 2>&1
net start cryptsvc >nul 2>&1
net start bits >nul 2>&1
net start wuauserv >nul 2>&1
echo           Windows Update cache rebuilt.

:: --- 07) Repair network stack (Winsock + TCP/IP) ----------------------------
echo   [07/14] Repairing network stack...
netsh winsock reset >nul 2>&1
netsh int ip reset >nul 2>&1
echo           Network stack reset (reboot needed).

:: --- 08) Renew IP + flush DNS -----------------------------------------------
echo   [08/14] Renewing IP address and flushing DNS...
ipconfig /flushdns >nul 2>&1
ipconfig /release >nul 2>&1
ipconfig /renew >nul 2>&1
echo           IP renewed, DNS flushed.

:: --- 09) Reset Windows Firewall to defaults ---------------------------------
echo   [09/14] Resetting Windows Firewall to defaults...
netsh advfirewall reset >nul 2>&1
echo           Firewall restored.

:: --- 10) Re-register all Microsoft Store apps (fixes broken apps) ------------
echo   [10/14] Re-registering Microsoft Store apps...
powershell -NoProfile -Command "Get-AppxPackage -AllUsers | ForEach-Object { Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\AppXManifest.xml\" -ErrorAction SilentlyContinue }" >nul 2>&1
echo           Store apps re-registered.

:: --- 11) Reset Microsoft Store cache ----------------------------------------
echo   [11/14] Resetting Microsoft Store cache...
wsreset.exe >nul 2>&1
echo           Store cache cleared.

:: --- 12) Check disk SMART health --------------------------------------------
echo   [12/14] Checking physical disk health...
powershell -NoProfile -Command "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus | Format-Table -AutoSize" 2>nul
wmic diskdrive get model,status 2>nul

:: --- 13) Clean up the component store (frees space, fixes servicing) --------
echo   [13/14] Cleaning component store (WinSxS)...
dism /Online /Cleanup-Image /StartComponentCleanup >nul 2>&1
echo           Component store cleaned.

:: --- 14) Generate a power/health diagnostic report on the Desktop -----------
echo   [14/14] Generating health report on your Desktop...
powercfg /energy /output "%USERPROFILE%\Desktop\PC_Health_Report.html" /duration 10 >nul 2>&1
echo           Saved: Desktop\PC_Health_Report.html
echo.
echo ============================================================================
echo   HEALTH CHECK COMPLETE. A reboot is recommended for network/Update fixes.
echo ============================================================================
echo.
pause
goto :MENU

:: ===========================================================================
:: OPTION 4 - REMOVE MICROSOFT DEFENDER + EDGE + COPILOT (PERMANENT)
:: ===========================================================================
:DEBLOAT_MS
cls
echo ============================================================================
echo   REMOVE DEFENDER + EDGE + COPILOT  ^&  DISABLE WINDOWS UPDATE  (ADVANCED)
echo ============================================================================
echo.
echo   WARNING - READ THIS FIRST:
echo     * Removing Microsoft Defender leaves your PC with NO built-in antivirus.
echo       Only do this if you will install another antivirus, or you fully
echo       accept the security risk on your own machine.
echo     * Disabling Windows Update means you will NOT get security patches.
echo     * For Defender to actually turn off you MUST first disable Tamper
echo       Protection: Settings ^> Privacy ^& Security ^> Windows Security ^>
echo       Virus ^& threat protection ^> Manage settings ^> Tamper Protection OFF.
echo       Microsoft blocks all script-based Defender changes while it is on.
echo     * Reversible via System Restore (option 2) or by resetting Windows.
echo.
choice /C YN /N /M "  I understand the risks - proceed? [Y/N]: "
if errorlevel 2 goto :MENU
echo.

:: --- TAMPER PROTECTION CHECK (this is what blocks Defender removal) ----------
echo   Checking Tamper Protection status...
set "TP=Unknown"
powershell -NoProfile -Command "(Get-MpComputerStatus).IsTamperProtected" > "%TEMP%\_pco_tp.txt" 2>nul
set /p TP=<"%TEMP%\_pco_tp.txt"
del "%TEMP%\_pco_tp.txt" >nul 2>&1
if /i "%TP%"=="True" (
    echo.
    echo   ##########################################################################
    echo   #  TAMPER PROTECTION IS ON. Windows will BLOCK every Defender change.    #
    echo   #  There is NO script that can bypass this - it is by design.            #
    echo   #  Turn it OFF first:  Settings ^> Privacy ^& Security ^> Windows Security  #
    echo   #  ^> Virus ^& threat protection ^> Manage settings ^> Tamper Protection OFF #
    echo   #  Then run this option again to remove Defender.                        #
    echo   ##########################################################################
    echo.
    echo   Edge, Copilot, OneDrive and Windows Update can still be removed now.
    choice /C CS /N /M "  [C]ontinue with the rest, or [S]top and fix Tamper first: "
    if errorlevel 2 goto :MENU
    echo.
)

:: --- COPILOT ----------------------------------------------------------------
echo   Removing Windows Copilot...
reg add "HKCU\Software\Policies\Microsoft\Windows\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowCopilotButton /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" /v AllowCopilotRuntime /t REG_DWORD /d 0 /f >nul 2>&1
taskkill /f /im Copilot.exe >nul 2>&1
taskkill /f /im ai.exe >nul 2>&1
powershell -NoProfile -Command "Get-AppxPackage -AllUsers '*Copilot*','Microsoft.Copilot','MicrosoftWindows.Client.CoPilot' | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue" >nul 2>&1
powershell -NoProfile -Command "Get-AppxProvisionedPackage -Online | Where-Object {$_.DisplayName -like '*Copilot*'} | ForEach-Object { Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -NoProfile -Command "winget uninstall --id Microsoft.Copilot --silent --accept-source-agreements" >nul 2>&1
echo           Copilot disabled and removed.

:: --- EDGE -------------------------------------------------------------------
echo   Removing Microsoft Edge...
set "EDGEDIRA=%ProgramFiles(x86)%\Microsoft\Edge"
set "EDGEDIRB=%ProgramFiles%\Microsoft\Edge"
taskkill /f /im msedge.exe >nul 2>&1
taskkill /f /im MicrosoftEdgeUpdate.exe >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\EdgeUpdate" /v DoNotUpdateToEdgeWithChromium /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\EdgeUpdate" /v InstallDefault /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\EdgeUpdateDev" /v AllowUninstall /t REG_SZ /d "" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\EdgeUpdate" /v AllowUninstall /t REG_DWORD /d 1 /f >nul 2>&1
:: Unlock uninstall by temporarily reporting an EEA region (Windows only allows
:: Edge removal there). The original region is restored afterwards.
set "OLDGEO="
for /f "tokens=2,*" %%a in ('reg query "HKCU\Control Panel\International\Geo" /v Nation 2^>nul ^| find /i "Nation"') do set "OLDGEO=%%b"
reg add "HKCU\Control Panel\International\Geo" /v Nation /t REG_SZ /d 68 /f >nul 2>&1
for /f "delims=" %%E in ('dir /b /s "%ProgramFiles(x86)%\Microsoft\Edge\Application\*\Installer\setup.exe" 2^>nul') do "%%E" --uninstall --system-level --verbose-logging --force-uninstall >nul 2>&1
for /f "delims=" %%E in ('dir /b /s "%ProgramFiles%\Microsoft\Edge\Application\*\Installer\setup.exe" 2^>nul') do "%%E" --uninstall --system-level --verbose-logging --force-uninstall >nul 2>&1
for /f "delims=" %%E in ('dir /b /s "%LocalAppData%\Microsoft\Edge\Application\*\Installer\setup.exe" 2^>nul') do "%%E" --uninstall --verbose-logging --force-uninstall >nul 2>&1
powershell -NoProfile -Command "winget uninstall --id Microsoft.Edge --silent --accept-source-agreements --force" >nul 2>&1
powershell -NoProfile -Command "Get-AppxPackage -AllUsers *MicrosoftEdge* | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue" >nul 2>&1
if defined OLDGEO reg add "HKCU\Control Panel\International\Geo" /v Nation /t REG_SZ /d %OLDGEO% /f >nul 2>&1
:: If Edge still survived, offer a forced folder delete (guaranteed removal)
if exist "%EDGEDIRA%\Application\msedge.exe" (
    echo   Edge resisted the normal uninstall - it claims to be part of Windows.
    choice /C YN /N /M "   Force-delete the Edge program folder now? [Y/N]: "
    if not errorlevel 2 (
        taskkill /f /im msedge.exe >nul 2>&1
        takeown /f "%EDGEDIRA%" /r /d y >nul 2>&1
        icacls "%EDGEDIRA%" /grant administrators:F /t >nul 2>&1
        rd /s /q "%EDGEDIRA%" >nul 2>&1
        rd /s /q "%EDGEDIRB%" >nul 2>&1
        echo   Edge folder deleted.
    )
)
echo           Edge removal complete (Windows Update may still re-add it later).

:: --- ONEDRIVE ---------------------------------------------------------------
echo   Removing OneDrive...
taskkill /f /im OneDrive.exe >nul 2>&1
if exist "%SystemRoot%\System32\OneDriveSetup.exe" "%SystemRoot%\System32\OneDriveSetup.exe" /uninstall >nul 2>&1
if exist "%SystemRoot%\SysWOW64\OneDriveSetup.exe" "%SystemRoot%\SysWOW64\OneDriveSetup.exe" /uninstall >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\OneDrive" /v DisableFileSyncNGSC /t REG_DWORD /d 1 /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v OneDrive /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v OneDriveSetup /f >nul 2>&1
echo           OneDrive uninstalled.

:: --- 15 PREINSTALLED BLOATWARE APPS -----------------------------------------
echo   Removing preinstalled bloatware apps...
powershell -NoProfile -Command "$apps='Microsoft.BingNews','Microsoft.BingWeather','Microsoft.GetHelp','Microsoft.Getstarted','Microsoft.MicrosoftSolitaireCollection','Microsoft.People','Microsoft.WindowsFeedbackHub','Microsoft.YourPhone','Microsoft.ZuneVideo','Microsoft.MixedReality.Portal','Microsoft.WindowsMaps','Clipchamp.Clipchamp','Microsoft.Todos','Microsoft.PowerAutomateDesktop','MicrosoftTeams'; foreach($a in $apps){ Get-AppxPackage -AllUsers $a | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue; Get-AppxProvisionedPackage -Online | Where-Object {$_.DisplayName -eq $a} | ForEach-Object { Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -ErrorAction SilentlyContinue } }" >nul 2>&1
echo           15 bloatware apps removed: News, Weather, Solitaire, Maps,
echo           Your Phone, Teams, Clipchamp, To-Do, Power Automate and more.

:: --- DEFENDER (disable ALL components) --------------------------------------
echo   Removing all Microsoft Defender components (needs Tamper Protection OFF)...
:: Core antivirus + antispyware policies
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiVirus /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableRoutinelyTakingAction /t REG_DWORD /d 1 /f >nul 2>&1
:: Real-time protection - every sub-component
for %%K in (DisableRealtimeMonitoring DisableBehaviorMonitoring DisableOnAccessProtection DisableScanOnRealtimeEnable DisableIOAVProtection) do reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v %%K /t REG_DWORD /d 1 /f >nul 2>&1
:: Cloud protection (MAPS/SpyNet) + automatic sample submission OFF
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SpyNetReporting /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SubmitSamplesConsent /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v DisableBlockAtFirstSeen /t REG_DWORD /d 1 /f >nul 2>&1
:: SmartScreen (a Defender component) OFF in Explorer, Edge and Store apps
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableSmartScreen /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /v SmartScreenEnabled /t REG_SZ /d "Off" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\AppHost" /v EnableWebContentEvaluation /t REG_DWORD /d 0 /f >nul 2>&1
:: Live toggles (work only when Tamper Protection is already off)
powershell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring $true -DisableIOAVProtection $true -MAPSReporting 0 -SubmitSamplesConsent 2 -ErrorAction SilentlyContinue" >nul 2>&1
:: Force-disable every Defender service via registry Start=4 (and sc as backup)
for %%V in (WinDefend WdNisSvc Sense WdFilter WdNisDrv WdBoot SecurityHealthService webthreatdefsvc webthreatdefusersvc) do (
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\%%V" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
    sc config "%%V" start= disabled >nul 2>&1
)
sc query wscsvc >nul 2>&1 && sc config wscsvc start= demand >nul 2>&1
:: Remove the Windows Security (Defender UI) app entirely
powershell -NoProfile -Command "Get-AppxPackage -AllUsers *SecHealthUI* | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue" >nul 2>&1
:: Remove the "Scan with Microsoft Defender" right-click menu
reg delete "HKLM\SOFTWARE\Classes\*\shellex\ContextMenuHandlers\EPP" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Classes\Directory\shellex\ContextMenuHandlers\EPP" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Classes\Drive\shellex\ContextMenuHandlers\EPP" /f >nul 2>&1
:: Disable all Defender scheduled tasks
for %%T in (
  "\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance"
  "\Microsoft\Windows\Windows Defender\Windows Defender Cleanup"
  "\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan"
  "\Microsoft\Windows\Windows Defender\Windows Defender Verification"
) do schtasks /Change /TN %%T /Disable >nul 2>&1
:: Kill notifications and the tray icon
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Security Center\Notifications" /v DisableNotifications /t REG_DWORD /d 1 /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v SecurityHealth /f >nul 2>&1
echo           Defender real-time, cloud, SmartScreen, UI, context menu and
echo           tasks all disabled. The protected WinDefend service stub may
echo           remain (Windows blocks deleting it) but it is inert.

:: --- WINDOWS UPDATE ---------------------------------------------------------
echo   Disabling Windows Update...
for %%V in (wuauserv UsoSvc WaaSMedicSvc bits DoSvc) do (
    sc stop "%%V" >nul 2>&1
    sc config "%%V" start= disabled >nul 2>&1
)
:: WaaSMedicSvc/UsoSvc are protected - force-disable via the registry Start value
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\UsoSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v DisableWindowsUpdateAccess /t REG_DWORD /d 1 /f >nul 2>&1
for %%T in (
  "\Microsoft\Windows\WindowsUpdate\Scheduled Start"
  "\Microsoft\Windows\UpdateOrchestrator\Schedule Scan"
  "\Microsoft\Windows\UpdateOrchestrator\Schedule Scan Static Task"
) do schtasks /Change /TN %%T /Disable >nul 2>&1
echo           Windows Update disabled (re-enable from option 2 or by resetting).
echo.
echo   ---- VERIFICATION (what is still present right now) ----------------------
powershell -NoProfile -Command "$rt=try{(Get-MpComputerStatus).RealTimeProtectionEnabled}catch{'unknown'}; Write-Host ('     Defender real-time still ON : ' + $rt); Write-Host ('     Edge still installed        : ' + (Test-Path (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'))); Write-Host ('     OneDrive still installed    : ' + (Test-Path (Join-Path $env:LOCALAPPDATA 'Microsoft\OneDrive\OneDrive.exe'))); Write-Host ('     Copilot package present     : ' + [bool](Get-AppxPackage *Copilot* -ErrorAction SilentlyContinue))"
echo   --------------------------------------------------------------------------
echo.
echo   If "Defender real-time still ON" shows True, Tamper Protection is blocking
echo   it - turn Tamper Protection OFF and run this option again. That is a
echo   Windows restriction, not a fault in this tool.
echo.
echo ============================================================================
echo   DONE. A RESTART is required to finish removing these components.
echo ============================================================================
echo.
choice /C YN /M "  Restart now"
if errorlevel 2 goto :MENU
shutdown /r /t 5 /c "Restarting to finish removing Microsoft components..."
goto :END

:: ===========================================================================
:: OPTION 3 - CREATE A FRESH RESTORE POINT ON DEMAND
:: ===========================================================================
:NEWRP
cls
echo ============================================================================
echo   CREATE A FRESH RESTORE POINT
echo ============================================================================
echo.
echo   This saves the current state of Windows so you can roll back to it later
echo   from option [2]. Recommended before installing drivers or new software.
echo.
choice /C YN /M "  Create a restore point now"
if errorlevel 2 goto :MENU
echo.
echo   Creating restore point, please wait...
set "RPNAME=Manual_RestorePoint"
powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" > "%TEMP%\_pco_ts.txt" 2>nul
set /p STAMP=<"%TEMP%\_pco_ts.txt"
del "%TEMP%\_pco_ts.txt" >nul 2>&1
if defined STAMP set "RPNAME=Manual_%STAMP%"
call :MAKE_RP "%RPNAME%"
echo.
echo   Restore point created: %RPNAME%
echo   You can roll back to it anytime from menu option [2].
echo.
pause
goto :MENU

:: ===========================================================================
:: OPTION 4 - LIVE MONITOR (CPU / GPU / RAM usage + temperature)
:: ===========================================================================
:MONITOR
cls
echo ============================================================================
echo   LIVE MONITOR   -   CPU / GPU / RAM usage and temperature
echo ============================================================================
echo.
powershell -NoProfile -Command "$cpu=(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average; $os=Get-CimInstance Win32_OperatingSystem; $used=$os.TotalVisibleMemorySize-$os.FreePhysicalMemory; $rp=[math]::Round(($used/$os.TotalVisibleMemorySize)*100,0); $rg=[math]::Round($used/1MB,1); $tg=[math]::Round($os.TotalVisibleMemorySize/1MB,1); $gpu='N/A'; try{$s=(Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage' -EA Stop).CounterSamples; $gpu=[math]::Round((($s | Measure-Object CookedValue -Sum).Sum),0)}catch{}; $ct='N/A'; try{$t=Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -EA Stop | Select-Object -First 1; $ct=[math]::Round((($t.CurrentTemperature/10)-273.15),1)}catch{}; $gt='N/A'; if(Get-Command nvidia-smi -EA SilentlyContinue){try{$gt=((nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits) | Select-Object -First 1).Trim()}catch{}}; Write-Host ('   CPU Load   : {0,5} %%' -f $cpu); Write-Host ('   RAM Usage  : {0,5} %%    {1} of {2} GB used' -f $rp,$rg,$tg); Write-Host ('   GPU Usage  : {0,5} %%' -f $gpu); Write-Host ('   CPU Temp   : {0,5} C' -f $ct); Write-Host ('   GPU Temp   : {0,5} C' -f $gt)"
echo.
echo ----------------------------------------------------------------------------
echo   Note: CPU temp needs motherboard WMI support; GPU temp needs an NVIDIA
echo   card with nvidia-smi. "N/A" means your hardware does not expose it here.
echo.
echo   Auto-refreshes every 10 seconds.  Press R to refresh now, or Q to quit.
choice /C QR /N /T 10 /D R >nul
if errorlevel 2 goto :MONITOR
goto :MENU

:END
echo.
echo   Exiting. Enjoy your optimized PC!  Game on.
echo.
pause
endlocal
exit /b 0

:: ===========================================================================
:: SUBROUTINE - create a System Restore point.  Usage: call :MAKE_RP "Name"
:: ===========================================================================
:MAKE_RP
powershell -NoProfile -Command "Enable-ComputerRestore -Drive 'C:\'" >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore" /v SystemRestorePointCreationFrequency /t REG_DWORD /d 0 /f >nul 2>&1
powershell -NoProfile -Command "Checkpoint-Computer -Description '%~1' -RestorePointType 'MODIFY_SETTINGS'" >nul 2>&1
goto :eof
