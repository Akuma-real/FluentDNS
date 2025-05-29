# -*- coding: utf-8 -*-
"""
DNS提供商基类
定义统一的DNS操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DNSRecord:
    """DNS记录数据类"""
    id: Optional[str] = None
    name: str = ""
    type: str = "A"
    value: str = ""
    ttl: int = 600
    priority: int = 0
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'value': self.value,
            'ttl': self.ttl,
            'priority': self.priority,
            'enabled': self.enabled
        }


class DNSProviderBase(ABC):
    """DNS提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', '')
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        pass
    
    @abstractmethod
    def get_domains(self) -> List[str]:
        """获取域名列表"""
        pass
    
    @abstractmethod
    def get_records(self, domain: str) -> List[DNSRecord]:
        """获取域名的DNS记录"""
        pass
    
    @abstractmethod
    def add_record(self, domain: str, record: DNSRecord) -> str:
        """添加DNS记录，返回记录ID"""
        pass
    
    @abstractmethod
    def update_record(self, domain: str, record: DNSRecord) -> bool:
        """更新DNS记录"""
        pass
    
    @abstractmethod
    def delete_record(self, domain: str, record_id: str) -> bool:
        """删除DNS记录"""
        pass
    
    @abstractmethod
    def get_record_types(self) -> List[str]:
        """获取支持的记录类型"""
        pass
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            domains = self.get_domains()
            return True
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


class DNSProviderFactory:
    """DNS提供商工厂类"""
    
    _providers = {}
    
    @classmethod
    def register(cls, provider_type: str, provider_class):
        """注册DNS提供商"""
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> DNSProviderBase:
        """创建DNS提供商实例"""
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的DNS提供商类型: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        return provider_class(config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的提供商类型"""
        return list(cls._providers.keys())