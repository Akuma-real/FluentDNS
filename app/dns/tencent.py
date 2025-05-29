# -*- coding: utf-8 -*-
"""
腾讯云DNS提供商实现
"""

import json
import hmac
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any
import requests
from .base import DNSProviderBase, DNSRecord, DNSProviderFactory


class TencentDNSProvider(DNSProviderBase):
    """腾讯云DNS提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        self.secret_id = config.get('secret_id', '')
        self.secret_key = config.get('secret_key', '')
        self.region = config.get('region', 'ap-beijing')
        super().__init__(config)
        self.endpoint = 'dnspod.tencentcloudapi.com'
        self.service = 'dnspod'
        self.version = '2021-03-23'
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.secret_id or not self.secret_key:
            raise ValueError("腾讯云DNS配置缺少SecretId或SecretKey")
        return True
    
    def _sign_request(self, payload: str, timestamp: int) -> str:
        """生成请求签名"""
        # 步骤1：拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{self.endpoint}\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (http_request_method + "\n" +
                           canonical_uri + "\n" +
                           canonical_querystring + "\n" +
                           canonical_headers + "\n" +
                           signed_headers + "\n" +
                           hashed_request_payload)
        
        # 步骤2：拼接待签名字符串
        algorithm = "TC3-HMAC-SHA256"
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = f"{date}/{self.service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (algorithm + "\n" +
                         str(timestamp) + "\n" +
                         credential_scope + "\n" +
                         hashed_canonical_request)
        
        # 步骤3：计算签名
        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
        
        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, self.service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # 步骤4：拼接Authorization
        authorization = (algorithm + " " +
                        "Credential=" + self.secret_id + "/" + credential_scope + ", " +
                        "SignedHeaders=" + signed_headers + ", " +
                        "Signature=" + signature)
        
        return authorization
    
    def _make_request(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发起API请求"""
        if params is None:
            params = {}
        
        timestamp = int(time.time())
        payload = json.dumps(params)
        
        headers = {
            'Authorization': self._sign_request(payload, timestamp),
            'Content-Type': 'application/json; charset=utf-8',
            'Host': self.endpoint,
            'X-TC-Action': action,
            'X-TC-Timestamp': str(timestamp),
            'X-TC-Version': self.version,
            'X-TC-Region': self.region
        }
        
        url = f"https://{self.endpoint}"
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'Error' in result.get('Response', {}):
            error = result['Response']['Error']
            raise Exception(f"腾讯云DNS API错误: {error.get('Message', '未知错误')}")
        
        return result.get('Response', {})
    
    def get_domains(self) -> List[str]:
        """获取域名列表"""
        domains = []
        offset = 0
        limit = 20
        
        while True:
            result = self._make_request('DescribeDomainList', {
                'Offset': offset,
                'Limit': limit
            })
            
            domain_list = result.get('DomainList', [])
            if not domain_list:
                break
            
            domains.extend([domain['Name'] for domain in domain_list])
            
            if len(domain_list) < limit:
                break
            
            offset += limit
        
        return domains
    
    def get_records(self, domain: str) -> List[DNSRecord]:
        """获取DNS记录"""
        records = []
        offset = 0
        limit = 20
        
        while True:
            result = self._make_request('DescribeRecordList', {
                'Domain': domain,
                'Offset': offset,
                'Limit': limit
            })
            
            record_list = result.get('RecordList', [])
            if not record_list:
                break
            
            for record in record_list:
                dns_record = DNSRecord(
                    id=str(record['RecordId']),
                    name=record['Name'],
                    type=record['Type'],
                    value=record['Value'],
                    ttl=int(record['TTL']),
                    priority=int(record.get('MX', 0)),
                    enabled=record['Status'] == 'ENABLE'
                )
                records.append(dns_record)
            
            if len(record_list) < limit:
                break
            
            offset += limit
        
        return records
    
    def add_record(self, domain: str, record: DNSRecord) -> str:
        """添加DNS记录"""
        params = {
            'Domain': domain,
            'RecordType': record.type,
            'RecordLine': '默认',
            'Value': record.value,
            'TTL': record.ttl
        }
        
        if record.name and record.name != '@':
            params['SubDomain'] = record.name
        
        if record.type == 'MX' and record.priority > 0:
            params['MX'] = record.priority
        
        result = self._make_request('CreateRecord', params)
        return str(result['RecordId'])
    
    def update_record(self, domain: str, record: DNSRecord) -> bool:
        """更新DNS记录"""
        params = {
            'Domain': domain,
            'RecordId': int(record.id),
            'RecordType': record.type,
            'RecordLine': '默认',
            'Value': record.value,
            'TTL': record.ttl
        }
        
        if record.name and record.name != '@':
            params['SubDomain'] = record.name
        
        if record.type == 'MX' and record.priority > 0:
            params['MX'] = record.priority
        
        self._make_request('ModifyRecord', params)
        return True
    
    def delete_record(self, domain: str, record_id: str) -> bool:
        """删除DNS记录"""
        self._make_request('DeleteRecord', {
            'Domain': domain,
            'RecordId': int(record_id)
        })
        return True
    
    def get_record_types(self) -> List[str]:
        """获取支持的记录类型"""
        return ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA']


# 注册腾讯云DNS提供商
DNSProviderFactory.register('tencent', TencentDNSProvider)