@echo off
title Dashboard Proxy Server
cd /d "%~dp0"
echo.
echo   Dashboard Proxy starting...
echo   Open: http://localhost:8080
echo   Press Ctrl+C to stop
echo.
node proxy.js
pause
