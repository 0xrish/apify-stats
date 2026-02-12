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
:: Fix dubious ownership if needed
git config --global --add safe.directory "%cd:\=/%"
git add .
set "datestr=%date% %time%"
git commit -m "Automated Market Update: %datestr%"
git push origin main

echo ==================================================
echo   SUCCESS: Dashboard updated and pushed!
echo ==================================================
pause
