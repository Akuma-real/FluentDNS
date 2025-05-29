@echo off
chcp 65001 >nul
echo ========================================
echo FluentDNS 自动打包脚本
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

echo [2/5] 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo [3/5] 安装PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo 错误: PyInstaller安装失败
    pause
    exit /b 1
)

echo [4/5] 清理旧的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo [5/5] 开始打包（使用图标）...
echo 使用配置文件: build.spec
pyinstaller build.spec
if %errorlevel% neq 0 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo 可执行文件位置: dist\FluentDNS.exe
echo.

if exist "dist\FluentDNS.exe" (
    echo 文件信息:
    dir "dist\FluentDNS.exe"
    echo.
    echo 是否要运行程序进行测试？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo 启动程序...
        start "" "dist\FluentDNS.exe"
    )
) else (
    echo 警告: 未找到生成的exe文件
)

echo.
echo 按任意键退出...
pause >nul