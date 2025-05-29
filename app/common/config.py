# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import json
from typing import Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from qfluentwidgets import qconfig, ConfigItem, Theme, BoolValidator


class Config(QObject):
    """应用配置类"""
    
    configChanged = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.config_file = "config.json"
        self.data = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "theme": "auto",
            "language": "zh_CN",
            "auto_save": True,
            "dns_providers": {},
            "window": {
                "width": 1200,
                "height": 800,
                "maximized": False
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        old_value = data.get(keys[-1])
        data[keys[-1]] = value
        
        if old_value != value:
            self.configChanged.emit(key, value)
            if self.get('auto_save', True):
                self.save_config()


# 全局配置实例
cfg = Config()