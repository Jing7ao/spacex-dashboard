@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=C:\Users\13639\.local\bin\python3.12.exe
set PY314=C:\Users\13639\AppData\Local\Python\pythoncore-3.14-64\python.exe

echo ========================================
echo   Quant Model Startup
echo ========================================

echo [1/7] Northbound flow...
"%PY%" fetch_northbound.py

echo [2/7] IC weights...
"%PY%" ic_decay.py

echo [2/6] Margin data...
"%PY314%" fetch_margin.py

echo [3/6] Investor Relations...
"%PY%" fetch_irm_backup.py

echo [4/6] Supply chain news...
"%PY%" news_monitor.py

echo [5/6] Policy monitor...
"%PY%" policy_monitor.py

echo [6/6] Risk check + Starting proxy...
start /B node risk-check.js
echo ========================================
echo.
echo   Proxy: http://localhost:8080
echo   Monitor: http://localhost:8080/monitor.html
echo   Predict: http://localhost:8080/predict.html
echo   Calendar: http://localhost:8080/index.html
echo.
echo   Ctrl+C to stop
echo.
node proxy.js
pause
