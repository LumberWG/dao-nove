@echo off
schtasks /create /tn "NoveServer" /tr "node.exe f:\Study\dao-nove\server\server.js" /sc onlogon /rl limited /f
if %errorlevel% equ 0 (
    echo [OK] 开机自启任务已创建: NoveServer
    echo [OK] 每次登录 Windows 后自动启动: http://localhost:3000
) else (
    echo [FAIL] 创建失败，请以管理员身份运行
)
pause
