@echo off
echo 🚀 量化系统启动中...
start "量化代理" /min cmd /c "node proxy.js"
timeout /t 3 /nobreak >nul
start http://localhost:8080/index.html
echo ✅ 面板已打开，微信推送已就绪。可关闭此窗口。
timeout /t 2 /nobreak >nul
exit
