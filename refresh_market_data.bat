@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo   APIFY MARKET INTELLIGENCE - AUTO UPDATE
echo ==================================================

:: Change directory to the script's location
cd /d "%~dp0"

:: 1. Fetch fresh data from Apify Store
echo [1/3] Fetching latest actors from Apify Store...
node fetch_actors.js
if %errorlevel% neq 0 (
    echo [ERROR] Failed to fetch data from Apify.
)

:: 2. Process data with Python
echo [2/3] Calibrating and analyzing market data...
python script.py
if %errorlevel% neq 0 (
    echo [ERROR] Python analysis failed.
)

:: 3. Push to GitHub
echo [3/3] Pushing updates to GitHub...

:: Safety validation: Check if data.js exists and is large enough (verify 15k+ entries)
if not exist data.js (
    echo [ERROR] data.js was not generated. Aborting push.
    exit /b 1
)

:: Use PowerShell to count occurrences of "id" in data.js as a proxy for actor count
set "count=0"
for /f "delims=" %%i in ('powershell -command "(Select-String -Path 'data.js' -Pattern '\"id\":' -AllMatches).Matches.Count"') do set "count=%%i"

:: Ensure count is a number (removes potential whitespace)
set /a count=%count% 2>nul
echo [INFO] Detected %count% actors in processed data.

if %count% LSS 15000 (
    echo [ERROR] Data count %count% is below the 15,000 threshold.
    echo [ERROR] This usually means the fetch was incomplete. Aborting push.
    exit /b 1
)

echo [SUCCESS] Validation passed (%count% actors). Proceeding with push...

:: Fix dubious ownership if needed
git config --global --add safe.directory "%cd:\=/%"
git add .
set "datestr=%date% %time%"
git commit -m "Automated Market Update: %datestr% (!count! actors)"
git push origin main

echo ==================================================
echo   SUCCESS: Dashboard updated and pushed!
echo ==================================================
pause
