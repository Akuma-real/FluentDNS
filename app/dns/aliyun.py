# -*- coding: utf-8 -*-
"""
阿里云DNS提供商实现
"""

import json
import hmac
import hashlib
import base64
import urllib.parse
import requests
from datetime import datetime
from typing import List, Dict, Any
from .base import DNSProviderBase, DNSRecord, DNSProviderFactory


class AliyunDNSProvider(DNSProviderBase):
    """阿里云DNS提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        self.access_key_id = config.get('access_key_id', '')
        self.access_key_secret = config.get('access_key_secret', '')
        self.region = config.get('region', 'cn-hangzhou')
        super().__init__(config)
        self.endpoint = 'https://alidns.aliyuncs.com'
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.access_key_id or not self.access_key_secret:
            raise ValueError("阿里云DNS配置缺少AccessKey信息")
        return True
    
    def _sign_request(self, params: Dict[str, str]) -> str:
        """生成请求签名"""
        # 添加公共参数
        params.update({
            'Format': 'JSON',
            'Version': '2015-01-09',
            'AccessKeyId': self.access_key_id,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(int(datetime.now().timestamp() * 1000))
        })
        
        # 排序参数
        sorted_params = sorted(params.items())
        
        # 构造待签名字符串
        query_string = '&'.join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
        string_to_sign = f"GET&%2F&{urllib.parse.quote(query_string, safe='')}"
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                (self.access_key_secret + '&').encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        params['Signature'] = signature
        return '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted(params.items())])
    
    def _make_request(self, action: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        """发起API请求"""
        if params is None:
            params = {}
        
        params['Action'] = action
        query_string = self._sign_request(params)
        url = f"{self.endpoint}/?{query_string}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'Code' in result:
            raise Exception(f"阿里云DNS API错误: {result.get('Message', '未知错误')}")
        
        return result
    
    def get_domains(self) -> List[str]:
        """获取域名列表"""
        domains = []
        page_number = 1
        page_size = 20
        
        while True:
            result = self._make_request('DescribeDomains', {
                'PageNumber': str(page_number),
                'PageSize': str(page_size)
            })
            
            domain_list = result.get('Domains', {}).get('Domain', [])
            if not domain_list:
                break
            
            domains.extend([domain['DomainName'] for domain in domain_list])
            
            if len(domain_list) < page_size:
                break
            
            page_number += 1
        
        return domains
    
    def get_records(self, domain: str) -> List[DNSRecord]:
        """获取DNS记录"""
        records = []
        page_number = 1
        page_size = 20
        
        while True:
            result = self._make_request('DescribeDomainRecords', {
                'DomainName': domain,
                'PageNumber': str(page_number),
                'PageSize': str(page_size)
            })
            
            record_list = result.get('DomainRecords', {}).get('Record', [])
            if not record_list:
                break
            
            for record in record_list:
                dns_record = DNSRecord(
                    id=record['RecordId'],
                    name=record['RR'],
                    type=record['Type'],
                    value=record['Value'],
                    ttl=int(record['TTL']),
                    priority=int(record.get('Priority', 0)),
                    enabled=record['Status'] == 'ENABLE'
                )
                records.append(dns_record)
            
            if len(record_list) < page_size:
                break
            
            page_number += 1
        
        return records
    
    def add_record(self, domain: str, record: DNSRecord) -> str:
        """添加DNS记录"""
        params = {
            'DomainName': domain,
            'RR': record.name,
            'Type': record.type,
            'Value': record.value,
            'TTL': str(record.ttl)
        }
        
        if record.type in ['MX', 'SRV'] and record.priority > 0:
            params['Priority'] = str(record.priority)
        
        result = self._make_request('AddDomainRecord', params)
        return result['RecordId']
    
    def update_record(self, domain: str, record: DNSRecord) -> bool:
        """更新DNS记录"""
        params = {
            'RecordId': record.id,
            'RR': record.name,
            'Type': record.type,
            'Value': record.value,
            'TTL': str(record.ttl)
        }
        
        if record.type in ['MX', 'SRV'] and record.priority > 0:
            params['Priority'] = str(record.priority)
        
        self._make_request('UpdateDomainRecord', params)
        return True
    
    def delete_record(self, domain: str, record_id: str) -> bool:
        """删除DNS记录"""
        self._make_request('DeleteDomainRecord', {'RecordId': record_id})
        return True
    
    def get_record_types(self) -> List[str]:
        """获取支持的记录类型"""
        return ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA', 'REDIRECT_URL', 'FORWARD_URL']


# 注册阿里云DNS提供商
DNSProviderFactory.register('aliyun', AliyunDNSProvider)