# DNS管理器桌面客户端

基于 [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 开发的DNS管理桌面应用，参考了 [dnsmgr](https://github.com/netcccyun/dnsmgr) 项目的功能设计。

## 功能特性

### 🌐 多平台DNS支持
- **阿里云DNS** - 支持阿里云域名解析管理
- **腾讯云DNS** - 支持腾讯云域名解析管理  
- **CloudFlare DNS** - 支持CloudFlare域名解析管理
- 可扩展的DNS提供商架构，便于添加新的DNS服务商

### 📋 核心功能
- **DNS提供商管理** - 添加、编辑、测试和删除DNS服务商配置
- **域名管理** - 同步和管理多个DNS提供商的域名
- **DNS记录管理** - 增删改查DNS记录，支持A、AAAA、CNAME、MX、TXT等记录类型
- **操作日志** - 记录所有DNS操作，便于审计和故障排查
- **数据导入导出** - 支持配置和记录的备份与恢复

### 🎨 界面特性
- **现代化UI** - 基于Fluent Design设计语言
- **主题支持** - 支持浅色、深色和跟随系统主题
- **多语言** - 支持中文和英文界面
- **响应式布局** - 适配不同屏幕尺寸

## 安装要求

### 系统要求
- Windows 10/11
- Python 3.7+

### 依赖包
```
PyQt5>=5.15.0
PyQt-Fluent-Widgets>=1.1.0
requests>=2.25.0
PyYAML>=5.4.0
cryptography>=3.4.0
```

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd dnsmgr-semi-sqlite
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python main.py
```

## 使用指南

### DNS提供商配置

#### 阿里云DNS
1. 在阿里云控制台获取AccessKey ID和AccessKey Secret
2. 在应用中添加DNS提供商，选择"阿里云"
3. 填入AccessKey信息并测试连接

#### 腾讯云DNS
1. 在腾讯云控制台获取SecretId和SecretKey
2. 在应用中添加DNS提供商，选择"腾讯云"
3. 填入密钥信息并测试连接

#### CloudFlare DNS
1. 在CloudFlare获取API Token或Email+API Key
2. 在应用中添加DNS提供商，选择"CloudFlare"
3. 填入认证信息并测试连接

### 域名管理
1. 配置好DNS提供商后，点击"同步域名"获取域名列表
2. 可以手动添加域名或从DNS提供商同步
3. 选择域名查看和管理DNS记录

### DNS记录操作
1. 选择域名后，点击"同步记录"获取现有DNS记录
2. 使用"添加记录"按钮创建新的DNS记录
3. 双击记录可以编辑，右键可以删除
4. 所有操作都会记录在操作日志中

## 项目结构

```
dnsmgr-semi-sqlite/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
└── app/
    ├── __init__.py
    ├── common/            # 公共模块
    │   ├── config.py      # 配置管理
    │   └── database.py    # 数据库操作
    ├── dns/              # DNS提供商实现
    │   ├── __init__.py
    │   ├── base.py       # DNS提供商基类
    │   ├── aliyun.py     # 阿里云DNS
    │   ├── tencent.py    # 腾讯云DNS
    │   └── cloudflare.py # CloudFlare DNS
    └── view/             # 界面模块
        ├── __init__.py
        ├── main_window.py      # 主窗口
        ├── provider_interface.py # DNS提供商界面
        ├── domain_interface.py   # 域名管理界面
        ├── record_interface.py   # DNS记录界面
        ├── log_interface.py      # 操作日志界面
        └── setting_interface.py  # 设置界面
```

## 开发说明

### 添加新的DNS提供商

1. 在 `app/dns/` 目录下创建新的提供商文件
2. 继承 `DNSProviderBase` 基类
3. 实现必要的抽象方法
4. 在 `DNSProviderFactory` 中注册新提供商

示例：
```python
from .base import DNSProviderBase, DNSProviderFactory

class NewDNSProvider(DNSProviderBase):
    def validate_config(self, config):
        # 验证配置
        pass
    
    def get_domains(self):
        # 获取域名列表
        pass
    
    # 实现其他必要方法...

# 注册提供商
DNSProviderFactory.register('new_provider', NewDNSProvider)
```

### 数据库扩展

应用使用SQLite数据库存储配置和记录，数据库文件位于 `dns_manager.db`。

主要表结构：
- `dns_providers` - DNS提供商配置
- `domains` - 域名信息
- `dns_records` - DNS记录
- `operation_logs` - 操作日志

## 安全说明

- DNS提供商的API密钥使用加密存储
- 建议定期备份配置数据
- 请妥善保管API密钥，避免泄露

## 许可证

本项目基于 MIT 许可证开源。

## 致谢

- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - 提供现代化的UI组件
- [dnsmgr](https://github.com/netcccyun/dnsmgr) - 功能设计参考

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持阿里云、腾讯云、CloudFlare DNS
- 基础的域名和记录管理功能
- 现代化的Fluent Design界面