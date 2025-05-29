# FluentDNS 构建指南

本文档介绍如何构建 FluentDNS 桌面应用程序的可执行文件。

## 🚀 GitHub Actions 自动构建

### 触发构建

1. **推送代码触发**：推送到 `main` 或 `master` 分支
2. **标签发布**：创建以 `v` 开头的标签（如 `v1.0.0`）
3. **手动触发**：在 GitHub Actions 页面手动运行工作流
4. **Pull Request**：创建 PR 时自动构建测试

### 工作流文件

- `.github/workflows/build.yml` - 完整的多平台构建（Windows + Linux）
- `.github/workflows/build-windows.yml` - 专门的 Windows 构建

### 构建产物

- **开发构建**：每次推送都会生成 Artifacts，保留 30 天
- **正式发布**：标签推送会自动创建 GitHub Release

## 🔧 本地构建

### 方法一：使用批处理脚本（推荐）

```bash
# Windows
build.bat
```

这个脚本会自动：
1. 检查 Python 环境
2. 安装依赖包
3. 安装 PyInstaller
4. 清理旧文件
5. 执行打包
6. 提供测试选项

### 方法二：使用 PyInstaller spec 文件

```bash
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 使用 spec 文件构建
pyinstaller build.spec
```

### 方法三：直接使用 PyInstaller

```bash
pyinstaller --clean --onefile --windowed ^
  --name="FluentDNS" ^
  --add-data="app;app" ^
  --hidden-import=PyQt5.sip ^
  --hidden-import=qfluentwidgets ^
  --version-file=version_info.txt ^
  main.py
```

## 📁 构建文件说明

### 核心文件

- `build.spec` - PyInstaller 配置文件，定义打包参数
- `version_info.txt` - Windows 可执行文件版本信息
- `build.bat` - Windows 本地构建脚本

### GitHub Actions 配置

- `.github/workflows/build.yml` - 多平台构建工作流
- `.github/workflows/build-windows.yml` - Windows 专用构建工作流

## ⚙️ 构建配置详解

### PyInstaller 参数

- `--onefile` - 打包成单个可执行文件
- `--windowed` - 无控制台窗口（GUI 应用）
- `--add-data="app;app"` - 包含 app 目录
- `--hidden-import` - 显式导入模块
- `--exclude-module` - 排除不需要的模块
- `--version-file` - 添加版本信息

### 隐式导入模块

```python
hiddenimports=[
    'PyQt5.sip',
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'qfluentwidgets',
    'requests',
    'yaml',
    'cryptography',
]
```

### 排除模块

```python
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
]
```

## 🐛 常见问题

### 1. 模块导入错误

**问题**：运行时提示找不到某个模块

**解决**：在 `build.spec` 的 `hiddenimports` 中添加缺失的模块

### 2. 文件路径错误

**问题**：程序无法找到配置文件或资源文件

**解决**：检查 `--add-data` 参数，确保资源文件被正确包含

### 3. 启动缓慢

**问题**：exe 文件启动需要很长时间

**解决**：这是正常现象，PyInstaller 打包的程序首次启动需要解压临时文件

### 4. 杀毒软件误报

**问题**：杀毒软件将 exe 文件识别为病毒

**解决**：添加白名单，或使用代码签名证书

## 📦 发布流程

### 1. 准备发布

```bash
# 更新版本号
# 编辑 version_info.txt 中的版本信息

# 测试本地构建
build.bat

# 测试运行
dist\FluentDNS.exe
```

### 2. 创建标签

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3. 自动发布

GitHub Actions 会自动：
1. 构建可执行文件
2. 创建 GitHub Release
3. 上传构建产物
4. 生成发布说明

## 🔍 构建验证

### 本地验证

1. 检查文件大小（通常 50-100MB）
2. 运行程序测试基本功能
3. 检查是否能正常创建配置文件
4. 测试 DNS 提供商连接功能

### CI/CD 验证

1. 查看 GitHub Actions 构建日志
2. 下载 Artifacts 进行测试
3. 检查 Release 页面的文件

## 📋 系统要求

### 开发环境

- Python 3.7+
- Windows 10/11
- Git

### 运行环境

- Windows 10/11
- 无需安装 Python
- 无需安装其他依赖

## 🎯 优化建议

1. **减小文件大小**：排除不必要的模块
2. **提高启动速度**：使用 `--onedir` 模式（但会生成多个文件）
3. **添加图标**：使用 `--icon` 参数添加应用图标
4. **代码签名**：使用证书签名提高安全性

---

如有问题，请查看 GitHub Actions 的构建日志或提交 Issue。