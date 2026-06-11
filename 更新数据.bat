@echo off
cd /d "%~dp0"
echo 📡 数据更新 %date% %time%

echo [1/4] 北向资金...
C:\Users\13639\.local\bin\python3.12.exe fetch_northbound.py

echo [2/4] 动态权重...
C:\Users\13639\.local\bin\python3.12.exe ic_decay.py

echo [3/4] 供应链新闻...
C:\Users\13639\.local\bin\python3.12.exe news_monitor.py

echo [4/4] 风险检测...
node risk-check.js

echo ✅ 完成
