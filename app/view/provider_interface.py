# -*- coding: utf-8 -*-
"""
DNS提供商管理界面
"""

import json
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QDialog, QTableWidgetItem
from qfluentwidgets import (
    TableWidget, PushButton, FluentIcon as FIF, InfoBar, InfoBarPosition,
    MessageBox, LineEdit, ComboBox, TextEdit, CardWidget, 
    StrongBodyLabel, BodyLabel, PrimaryPushButton, TransparentPushButton
)

from ..common.database import db
from ..dns.base import DNSProviderFactory
from ..dns import aliyun, tencent, cloudflare  # 导入所有提供商实现


class ProviderConfigDialog(QDialog):
    """DNS提供商配置对话框"""
    
    def __init__(self, parent=None, provider_data=None):
        super().__init__(parent)
        self.provider_data = provider_data
        self.init_ui()
        
        if provider_data:
            self.load_provider_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('DNS提供商配置')
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 提供商名称
        layout.addWidget(BodyLabel('提供商名称:'))
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText('请输入提供商名称')
        layout.addWidget(self.name_edit)
        
        # 提供商类型
        layout.addWidget(BodyLabel('提供商类型:'))
        self.type_combo = ComboBox()
        self.type_combo.addItems(['aliyun', 'tencent', 'cloudflare'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)
        
        # 配置信息容器
        self.config_widget = CardWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        layout.addWidget(self.config_widget)
        
        # 初始化不同提供商的配置界面
        self.init_config_widgets()
        
        # 配置示例
        self.example_label = BodyLabel()
        layout.addWidget(self.example_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.test_button = PushButton('测试连接', self)
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        self.cancel_button = TransparentPushButton('取消', self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = PrimaryPushButton('保存', self)
        self.save_button.clicked.connect(self.save_provider)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 初始化配置示例
        self.on_type_changed(self.type_combo.currentText())
    
    def init_config_widgets(self):
        """初始化不同提供商的配置界面"""
        # CloudFlare配置界面
        self.cloudflare_widget = QWidget()
        cloudflare_layout = QVBoxLayout(self.cloudflare_widget)
        cloudflare_layout.addWidget(BodyLabel('API Token:'))
        self.cloudflare_token_edit = LineEdit()
        self.cloudflare_token_edit.setPlaceholderText('请输入CloudFlare API Token')
        cloudflare_layout.addWidget(self.cloudflare_token_edit)
        
        # 阿里云配置界面
        self.aliyun_widget = QWidget()
        aliyun_layout = QVBoxLayout(self.aliyun_widget)
        aliyun_layout.addWidget(BodyLabel('Access Key ID:'))
        self.aliyun_key_id_edit = LineEdit()
        self.aliyun_key_id_edit.setPlaceholderText('请输入Access Key ID')
        aliyun_layout.addWidget(self.aliyun_key_id_edit)
        aliyun_layout.addWidget(BodyLabel('Access Key Secret:'))
        self.aliyun_key_secret_edit = LineEdit()
        self.aliyun_key_secret_edit.setPlaceholderText('请输入Access Key Secret')
        aliyun_layout.addWidget(self.aliyun_key_secret_edit)
        
        # 腾讯云配置界面
        self.tencent_widget = QWidget()
        tencent_layout = QVBoxLayout(self.tencent_widget)
        tencent_layout.addWidget(BodyLabel('Secret ID:'))
        self.tencent_secret_id_edit = LineEdit()
        self.tencent_secret_id_edit.setPlaceholderText('请输入Secret ID')
        tencent_layout.addWidget(self.tencent_secret_id_edit)
        tencent_layout.addWidget(BodyLabel('Secret Key:'))
        self.tencent_secret_key_edit = LineEdit()
        self.tencent_secret_key_edit.setPlaceholderText('请输入Secret Key')
        tencent_layout.addWidget(self.tencent_secret_key_edit)
        
        # 将所有配置界面添加到布局中，但先隐藏
        self.config_layout.addWidget(self.cloudflare_widget)
        self.config_layout.addWidget(self.aliyun_widget)
        self.config_layout.addWidget(self.tencent_widget)
        
        # 初始时隐藏所有配置界面
        self.cloudflare_widget.hide()
        self.aliyun_widget.hide()
        self.tencent_widget.hide()
    
    def on_type_changed(self, provider_type):
        """提供商类型改变"""
        # 隐藏所有配置界面
        self.cloudflare_widget.hide()
        self.aliyun_widget.hide()
        self.tencent_widget.hide()
        
        # 根据提供商类型显示对应的配置界面
        if provider_type == 'cloudflare':
            self.cloudflare_widget.show()
            self.example_label.setText('请输入您的CloudFlare API Token，可在CloudFlare控制台的"My Profile" → "API Tokens"中创建。')
        elif provider_type == 'aliyun':
            self.aliyun_widget.show()
            self.example_label.setText('请输入您的阿里云Access Key ID和Secret，可在阿里云控制台的"AccessKey管理"中获取。')
        elif provider_type == 'tencent':
            self.tencent_widget.show()
            self.example_label.setText('请输入您的腾讯云Secret ID和Key，可在腾讯云控制台的"访问管理" → "API密钥管理"中获取。')
        else:
            self.example_label.setText('请选择DNS提供商类型。')
    
    def load_provider_data(self):
        """加载提供商数据"""
        if self.provider_data:
            self.name_edit.setText(self.provider_data.get('name', ''))
            provider_type = self.provider_data.get('type', 'aliyun')
            self.type_combo.setCurrentText(provider_type)
            
            config_str = self.provider_data.get('config', '{}')
            try:
                config = json.loads(config_str) if isinstance(config_str, str) else config_str
            except json.JSONDecodeError:
                config = {}
            
            # 根据提供商类型加载对应的配置数据
            if provider_type == 'cloudflare':
                self.cloudflare_token_edit.setText(config.get('api_token', ''))
            elif provider_type == 'aliyun':
                self.aliyun_key_id_edit.setText(config.get('access_key_id', ''))
                self.aliyun_key_secret_edit.setText(config.get('access_key_secret', ''))
            elif provider_type == 'tencent':
                self.tencent_secret_id_edit.setText(config.get('secret_id', ''))
                self.tencent_secret_key_edit.setText(config.get('secret_key', ''))
    
    def test_connection(self):
        """测试连接"""
        try:
            provider_type = self.type_combo.currentText()
            
            # 根据提供商类型收集配置数据
            config = {}
            if provider_type == 'cloudflare':
                api_token = self.cloudflare_token_edit.text().strip()
                if not api_token:
                    InfoBar.warning('警告', '请输入CloudFlare API Token', parent=self)
                    return
                config['api_token'] = api_token
            elif provider_type == 'aliyun':
                access_key_id = self.aliyun_key_id_edit.text().strip()
                access_key_secret = self.aliyun_key_secret_edit.text().strip()
                if not access_key_id or not access_key_secret:
                    InfoBar.warning('警告', '请输入完整的阿里云Access Key信息', parent=self)
                    return
                config['access_key_id'] = access_key_id
                config['access_key_secret'] = access_key_secret
            elif provider_type == 'tencent':
                secret_id = self.tencent_secret_id_edit.text().strip()
                secret_key = self.tencent_secret_key_edit.text().strip()
                if not secret_id or not secret_key:
                    InfoBar.warning('警告', '请输入完整的腾讯云Secret信息', parent=self)
                    return
                config['secret_id'] = secret_id
                config['secret_key'] = secret_key
            
            provider = DNSProviderFactory.create(provider_type, config)
            if provider.test_connection():
                InfoBar.success('成功', '连接测试成功', parent=self)
            else:
                InfoBar.error('失败', '连接测试失败', parent=self)
                
        except Exception as e:
            InfoBar.error('错误', f'连接测试失败: {str(e)}', parent=self)
    
    def save_provider(self):
        """保存提供商"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                InfoBar.warning('警告', '请输入提供商名称', parent=self)
                return
            
            provider_type = self.type_combo.currentText()
            
            # 根据提供商类型收集配置数据
            config = {}
            if provider_type == 'cloudflare':
                api_token = self.cloudflare_token_edit.text().strip()
                if not api_token:
                    InfoBar.warning('警告', '请输入CloudFlare API Token', parent=self)
                    return
                config['api_token'] = api_token
            elif provider_type == 'aliyun':
                access_key_id = self.aliyun_key_id_edit.text().strip()
                access_key_secret = self.aliyun_key_secret_edit.text().strip()
                if not access_key_id or not access_key_secret:
                    InfoBar.warning('警告', '请输入完整的阿里云Access Key信息', parent=self)
                    return
                config['access_key_id'] = access_key_id
                config['access_key_secret'] = access_key_secret
            elif provider_type == 'tencent':
                secret_id = self.tencent_secret_id_edit.text().strip()
                secret_key = self.tencent_secret_key_edit.text().strip()
                if not secret_id or not secret_key:
                    InfoBar.warning('警告', '请输入完整的腾讯云Secret信息', parent=self)
                    return
                config['secret_id'] = secret_id
                config['secret_key'] = secret_key
            
            # 验证配置
            provider = DNSProviderFactory.create(provider_type, config)
            
            config_text = json.dumps(config, ensure_ascii=False)
            
            if self.provider_data:
                # 更新
                db.update_dns_provider(
                    self.provider_data['id'],
                    name=name,
                    type=provider_type,
                    config=config_text
                )
                db.add_operation_log('update', 'provider', self.provider_data['id'], f'更新提供商: {name}')
            else:
                # 新增
                provider_id = db.add_dns_provider(name, provider_type, config_text)
                db.add_operation_log('create', 'provider', provider_id, f'创建提供商: {name}')
            
            self.accept()
            
        except Exception as e:
            InfoBar.error('错误', f'保存失败: {str(e)}', parent=self)


class ProviderInterface(QWidget):
    """DNS提供商管理界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_providers()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题和按钮
        header_layout = QHBoxLayout()
        header_layout.addWidget(StrongBodyLabel('DNS提供商管理'))
        header_layout.addStretch()
        
        self.add_button = PrimaryPushButton('添加提供商', self)
        self.add_button.setIcon(FIF.ADD)
        self.add_button.clicked.connect(self.add_provider)
        header_layout.addWidget(self.add_button)
        
        self.refresh_button = PushButton('刷新', self)
        self.refresh_button.setIcon(FIF.SYNC)
        self.refresh_button.clicked.connect(self.load_providers)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # 提供商表格
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['名称', '类型', '状态', '创建时间', '操作'])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
    
    def load_providers(self):
        """加载提供商列表"""
        providers = db.get_dns_providers()
        self.table.setRowCount(len(providers))
        
        for row, provider in enumerate(providers):
            # 名称
            self.table.setItem(row, 0, QTableWidgetItem(provider['name']))
            
            # 类型
            self.table.setItem(row, 1, QTableWidgetItem(provider['type']))
            
            # 状态
            status = '启用' if provider['enabled'] else '禁用'
            self.table.setItem(row, 2, QTableWidgetItem(status))
            
            # 创建时间
            create_time = provider['created_at'][:19] if provider['created_at'] else ''
            self.table.setItem(row, 3, QTableWidgetItem(create_time))
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 0, 5, 0)
            
            edit_button = PushButton('编辑')
            edit_button.setFixedSize(60, 30)
            edit_button.clicked.connect(lambda checked, p=provider: self.edit_provider(p))
            button_layout.addWidget(edit_button)
            
            test_button = PushButton('测试')
            test_button.setFixedSize(60, 30)
            test_button.clicked.connect(lambda checked, p=provider: self.test_provider(p))
            button_layout.addWidget(test_button)
            
            delete_button = PushButton('删除')
            delete_button.setFixedSize(60, 30)
            delete_button.clicked.connect(lambda checked, p=provider: self.delete_provider(p))
            button_layout.addWidget(delete_button)
            
            self.table.setCellWidget(row, 4, button_widget)
    
    def add_provider(self):
        """添加提供商"""
        dialog = ProviderConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_providers()
            InfoBar.success('成功', '提供商添加成功', parent=self)
    
    def edit_provider(self, provider):
        """编辑提供商"""
        dialog = ProviderConfigDialog(self, provider)
        if dialog.exec_() == QDialog.Accepted:
            self.load_providers()
            InfoBar.success('成功', '提供商更新成功', parent=self)
    
    def test_provider(self, provider):
        """测试提供商连接"""
        try:
            config = json.loads(provider['config'])
            dns_provider = DNSProviderFactory.create(provider['type'], config)
            
            if dns_provider.test_connection():
                InfoBar.success('成功', f'提供商 {provider["name"]} 连接测试成功', parent=self)
            else:
                InfoBar.error('失败', f'提供商 {provider["name"]} 连接测试失败', parent=self)
                
        except Exception as e:
            InfoBar.error('错误', f'连接测试失败: {str(e)}', parent=self)
    
    def delete_provider(self, provider):
        """删除提供商"""
        msg_box = MessageBox(
            '确认删除',
            f'确定要删除提供商 "{provider["name"]}" 吗？\n此操作不可撤销。',
            self
        )
        
        if msg_box.exec_() == MessageBox.Yes:
            try:
                db.delete_dns_provider(provider['id'])
                db.add_operation_log('delete', 'provider', provider['id'], f'删除提供商: {provider["name"]}')
                self.load_providers()
                InfoBar.success('成功', '提供商删除成功', parent=self)
            except Exception as e:
                InfoBar.error('错误', f'删除失败: {str(e)}', parent=self)