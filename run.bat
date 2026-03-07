@echo off
color 0A
echo =======================================================
echo    🚀 Auto-Media-Agent 工业级流水线一键点火程序 🚀
echo =======================================================
echo.

REM ==========================================
REM ⚠️【核心配置区】：请修改下方的 Redis 路径！
REM ==========================================
REM 将这里的 D:\Redis 改成你昨天实际解压 Redis 的那个文件夹路径
set REDIS_DIR=D:\

REM 获取当前项目根目录
set PROJECT_DIR=%cd%
REM 虚拟环境激活脚本路径
set VENV_ACTIVATE="%PROJECT_DIR%\.venv\Scripts\activate.bat"

echo [1/4] 🟢 正在点亮底层消息中枢 (Redis)...
REM start 命令会新开一个独立窗口，/D 指定运行目录，cmd /k 保证窗口运行后不自动关闭
start "1号引擎 - Redis Server" /D "%REDIS_DIR%" cmd /k "redis-server.exe redis.windows.conf"

REM 稍微等 2 秒，让 Redis 先跑起来
timeout /t 2 /nobreak >nul

echo [2/4] 🟡 正在启动核心收银台 (FastAPI)...
start "2号引擎 - FastAPI Backend" cmd /k "%VENV_ACTIVATE% && uvicorn main:app --reload"

echo [3/4] 🔴 正在唤醒任务调度后厨 (Celery Worker)...
start "3号引擎 - Celery Worker" cmd /k "%VENV_ACTIVATE% && celery -A app.celery_worker worker -l info -P threads -c 4"

echo [4/4] 🔵 正在加载现代化控制台 (Vue3 Frontend)...
start "4号引擎 - Vue3 Frontend" /D "%PROJECT_DIR%\web-ui" cmd /k "npm run dev"

echo.
echo =======================================================
echo    ✅ 所有引擎点火指令发送完毕！系统正在急速拉起...
echo    👀 请检查任务栏弹出的 4 个黑色终端窗口是否正常报错。
echo    🌐 请在浏览器打开: http://localhost:5173
echo =======================================================
echo.
pause