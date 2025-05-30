# -*- coding: utf-8 -*-
"""
数据库管理模块
使用SQLite存储DNS记录和配置信息
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "dnsmgr.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # DNS提供商配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dns_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 域名表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    provider_id INTEGER NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES dns_providers (id),
                    UNIQUE(domain, provider_id)
                )
            """)
            
            # DNS记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dns_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    record_id TEXT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    ttl INTEGER DEFAULT 600,
                    priority INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (domain_id) REFERENCES domains (id)
                )
            """)
            
            # 操作日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER,
                    details TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_dns_provider(self, name: str, provider_type: str, config: str) -> int:
        """添加DNS提供商"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dns_providers (name, type, config)
                VALUES (?, ?, ?)
            """, (name, provider_type, config))
            conn.commit()
            return cursor.lastrowid
    
    def get_dns_providers(self) -> List[Dict[str, Any]]:
        """获取所有DNS提供商"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dns_providers WHERE enabled = 1")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_dns_provider(self, provider_id: int, **kwargs):
        """更新DNS提供商"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(provider_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE dns_providers 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            conn.commit()
    
    def delete_dns_provider(self, provider_id: int):
        """删除DNS提供商（软删除）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dns_providers 
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (provider_id,))
            conn.commit()
    
    def add_domain(self, domain: str, provider_id: int) -> int:
        """添加域名"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO domains (domain, provider_id)
                VALUES (?, ?)
            """, (domain, provider_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_domains(self, provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取域名列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if provider_id:
                cursor.execute("""
                    SELECT d.*, p.name as provider_name, p.type as provider_type
                    FROM domains d
                    JOIN dns_providers p ON d.provider_id = p.id
                    WHERE d.enabled = 1 AND d.provider_id = ?
                    ORDER BY d.domain
                """, (provider_id,))
            else:
                cursor.execute("""
                    SELECT d.*, p.name as provider_name, p.type as provider_type
                    FROM domains d
                    JOIN dns_providers p ON d.provider_id = p.id
                    WHERE d.enabled = 1
                    ORDER BY d.domain
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    

    
    def delete_domain(self, domain_id: int):
        """删除域名（物理删除）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM domains 
                WHERE id = ?
            """, (domain_id,))
            conn.commit()
    
    def add_dns_record(self, domain_id: int, record_id: str, name: str, 
                      record_type: str, value: str, ttl: int = 600, 
                      priority: int = 0) -> int:
        """添加DNS记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dns_records (domain_id, record_id, name, type, value, ttl, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (domain_id, record_id, name, record_type, value, ttl, priority))
            conn.commit()
            return cursor.lastrowid
    
    def get_dns_records(self, domain_id: int) -> List[Dict[str, Any]]:
        """获取DNS记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dns_records 
                WHERE domain_id = ? AND enabled = 1
                ORDER BY name, type
            """, (domain_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_dns_record(self, record_id: int, **kwargs):
        """更新DNS记录"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(record_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE dns_records 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            conn.commit()
    
    def delete_dns_record(self, record_id: int):
        """删除DNS记录（软删除）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dns_records 
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (record_id,))
            conn.commit()
    
    def add_operation_log(self, operation: str, target_type: str, 
                         target_id: Optional[int] = None, details: Optional[str] = None,
                         status: str = "success", error_message: Optional[str] = None):
        """添加操作日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operation_logs (operation, target_type, target_id, details, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (operation, target_type, target_id, details, status, error_message))
            conn.commit()
    
    def get_operation_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取操作日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM operation_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_operation_logs(self):
        """清空所有操作日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM operation_logs")
            conn.commit()
            return cursor.rowcount


# 全局数据库实例
db = DatabaseManager()