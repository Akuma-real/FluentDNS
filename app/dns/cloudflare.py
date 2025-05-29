# -*- coding: utf-8 -*-
"""
CloudFlare DNS提供商实现
"""

import requests
from typing import List, Dict, Any
from .base import DNSProviderBase, DNSRecord, DNSProviderFactory


class CloudFlareDNSProvider(DNSProviderBase):
    """CloudFlare DNS提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_token = config.get('api_token', '')
        self.email = config.get('email', '')
        self.api_key = config.get('api_key', '')
        self.base_url = 'https://api.cloudflare.com/client/v4'
        super().__init__(config)
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.api_token and not (self.email and self.api_key):
            raise ValueError("CloudFlare DNS配置缺少API Token或Email+API Key")
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        else:
            headers['X-Auth-Email'] = self.email
            headers['X-Auth-Key'] = self.api_key
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """发起API请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('success', False):
            errors = result.get('errors', [])
            error_msg = ', '.join([error.get('message', '未知错误') for error in errors])
            raise Exception(f"CloudFlare API错误: {error_msg}")
        
        return result
    
    def get_domains(self) -> List[str]:
        """获取域名列表"""
        domains = []
        page = 1
        per_page = 20
        
        while True:
            result = self._make_request('GET', '/zones', {
                'page': page,
                'per_page': per_page
            })
            
            zone_list = result.get('result', [])
            if not zone_list:
                break
            
            domains.extend([zone['name'] for zone in zone_list])
            
            # 检查是否还有更多页面
            result_info = result.get('result_info', {})
            if page >= result_info.get('total_pages', 1):
                break
            
            page += 1
        
        return domains
    
    def _get_zone_id(self, domain: str) -> str:
        """获取域名的Zone ID"""
        result = self._make_request('GET', '/zones', {'name': domain})
        zones = result.get('result', [])
        
        if not zones:
            raise Exception(f"未找到域名: {domain}")
        
        return zones[0]['id']
    
    def get_records(self, domain: str) -> List[DNSRecord]:
        """获取DNS记录"""
        zone_id = self._get_zone_id(domain)
        records = []
        page = 1
        per_page = 20
        
        while True:
            result = self._make_request('GET', f'/zones/{zone_id}/dns_records', {
                'page': page,
                'per_page': per_page
            })
            
            record_list = result.get('result', [])
            if not record_list:
                break
            
            for record in record_list:
                # 处理记录名称
                name = record['name']
                if name == domain:
                    name = '@'
                elif name.endswith(f'.{domain}'):
                    name = name[:-len(domain)-1]
                
                dns_record = DNSRecord(
                    id=record['id'],
                    name=name,
                    type=record['type'],
                    value=record['content'],
                    ttl=int(record['ttl']) if record['ttl'] != 1 else 1,  # CloudFlare自动TTL为1
                    priority=int(record.get('priority', 0)),
                    enabled=not record.get('proxied', False)  # CloudFlare的代理状态
                )
                records.append(dns_record)
            
            # 检查是否还有更多页面
            result_info = result.get('result_info', {})
            if page >= result_info.get('total_pages', 1):
                break
            
            page += 1
        
        return records
    
    def add_record(self, domain: str, record: DNSRecord) -> str:
        """添加DNS记录"""
        zone_id = self._get_zone_id(domain)
        
        # 处理记录名称
        name = record.name
        if name == '@':
            name = domain
        elif not name.endswith(f'.{domain}'):
            name = f"{name}.{domain}"
        
        data = {
            'type': record.type,
            'name': name,
            'content': record.value,
            'ttl': record.ttl if record.ttl > 1 else 1
        }
        
        if record.type == 'MX' and record.priority > 0:
            data['priority'] = record.priority
        
        result = self._make_request('POST', f'/zones/{zone_id}/dns_records', data)
        return result['result']['id']
    
    def update_record(self, domain: str, record: DNSRecord) -> bool:
        """更新DNS记录"""
        zone_id = self._get_zone_id(domain)
        
        # 处理记录名称
        name = record.name
        if name == '@':
            name = domain
        elif not name.endswith(f'.{domain}'):
            name = f"{name}.{domain}"
        
        data = {
            'type': record.type,
            'name': name,
            'content': record.value,
            'ttl': record.ttl if record.ttl > 1 else 1
        }
        
        if record.type == 'MX' and record.priority > 0:
            data['priority'] = record.priority
        
        self._make_request('PUT', f'/zones/{zone_id}/dns_records/{record.id}', data)
        return True
    
    def delete_record(self, domain: str, record_id: str) -> bool:
        """删除DNS记录"""
        zone_id = self._get_zone_id(domain)
        self._make_request('DELETE', f'/zones/{zone_id}/dns_records/{record_id}')
        return True
    
    def get_record_types(self) -> List[str]:
        """获取支持的记录类型"""
        return ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA', 'PTR']


# 注册CloudFlare DNS提供商
DNSProviderFactory.register('cloudflare', CloudFlareDNSProvider)