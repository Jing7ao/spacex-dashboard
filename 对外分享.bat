@echo off
title Public Share via Cloudflare
echo.
echo   Starting Cloudflare Tunnel (free)...
echo   A public URL will appear below.
echo   Share that URL with anyone.
echo   Requires: node proxy.js already running on port 8080
echo.
npx cloudflared tunnel --url http://localhost:8080
pause
