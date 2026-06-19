@echo off
echo [INFO] 正在启动 ChatGPT Clone 开发环境 (Docker Compose)...

:: 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker 未启动，请先启动 Docker Desktop。
    pause
    exit /b
)

:: 启动容器
echo [INFO] 执行 docker-compose up...
docker-compose up --build

pause
