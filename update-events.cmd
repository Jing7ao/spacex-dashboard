@echo off
cd /d "%~dp0"
echo === Daily Auto-Update ===
echo.
echo [1/3] Scanning supply chain events...
call node update-events.js 30
echo.
echo [2/3] Fetching shareholder + institutional data...
call python fetch-extra-data.py
echo.
echo [3/3] Done
pause
