# -*- coding: utf-8 -*-
"""
设置界面
"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, PushSettingCard, 
    HyperlinkCard, PrimaryPushSettingCard, ComboBox,
    FluentIcon as FIF, InfoBar, MessageBox, ScrollArea,
    ExpandLayout, Theme, setTheme, isDarkTheme, SettingCard
)

from ..common.config import cfg
from ..common.database import db


class SettingInterface(ScrollArea):
    """设置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scroll_widget = QWidget()
        self.expand_layout = ExpandLayout(self.scroll_widget)
        
        # 设置滚动区域
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 个性化设置组
        self.personalization_group = SettingCardGroup('个性化', self.scroll_widget)
        
        # 主题设置
        self.theme_card = SettingCard(
            FIF.BRUSH,
            '应用主题',
            '调整应用的外观主题',
            parent=self.personalization_group
        )
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(['浅色', '深色', '跟随系统'])
        current_theme = cfg.get('theme', 'auto')
        theme_index = {'light': 0, 'dark': 1, 'auto': 2}.get(current_theme, 2)
        self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.theme_card.hBoxLayout.addWidget(self.theme_combo)
        
        # 语言设置
        self.language_card = SettingCard(
            FIF.LANGUAGE,
            '语言',
            '选择应用界面语言',
            parent=self.personalization_group
        )
        self.language_combo = ComboBox()
        self.language_combo.addItems(['简体中文', 'English'])
        current_language = cfg.get('language', 'zh_CN')
        language_index = {'zh_CN': 0, 'en_US': 1}.get(current_language, 0)
        self.language_combo.setCurrentIndex(language_index)
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        self.language_card.hBoxLayout.addWidget(self.language_combo)
        
        self.personalization_group.addSettingCard(self.theme_card)
        self.personalization_group.addSettingCard(self.language_card)
        
        # 应用设置组
        self.app_group = SettingCardGroup('应用设置', self.scroll_widget)
        
        # 自动保存设置
        self.auto_save_card = SwitchSettingCard(
            FIF.SAVE,
            '自动保存',
            '配置更改时自动保存',
            parent=self.app_group
        )
        self.auto_save_card.switchButton.setChecked(cfg.get('auto_save', True))
        self.auto_save_card.switchButton.checkedChanged.connect(
            lambda checked: cfg.set('auto_save', checked)
        )
        
        # 启动时检查更新
        self.check_update_card = SwitchSettingCard(
            FIF.UPDATE,
            '启动时检查更新',
            '应用启动时自动检查是否有新版本',
            parent=self.app_group
        )
        self.check_update_card.switchButton.setChecked(cfg.get('check_update', True))
        self.check_update_card.switchButton.checkedChanged.connect(
            lambda checked: cfg.set('check_update', checked)
        )
        
        self.app_group.addSettingCard(self.auto_save_card)
        self.app_group.addSettingCard(self.check_update_card)
        
        # 数据管理组
        self.data_group = SettingCardGroup('数据管理', self.scroll_widget)
        
        # 导出数据
        self.export_card = PushSettingCard(
            '导出',
            FIF.DOWNLOAD,
            '导出数据',
            '将DNS配置和记录导出为JSON文件'
        )
        self.export_card.clicked.connect(self.export_data)
        
        # 导入数据
        self.import_card = PushSettingCard(
            '导入',
            FIF.FOLDER,
            '导入数据',
            '从JSON文件导入DNS配置和记录'
        )
        self.import_card.clicked.connect(self.import_data)
        
        # 清空数据
        self.clear_card = PushSettingCard(
            '清空',
            FIF.DELETE,
            '清空所有数据',
            '删除所有DNS提供商、域名和记录数据'
        )
        self.clear_card.clicked.connect(self.clear_data)
        
        self.data_group.addSettingCard(self.export_card)
        self.data_group.addSettingCard(self.import_card)
        self.data_group.addSettingCard(self.clear_card)
        
        # 关于组
        self.about_group = SettingCardGroup('关于', self.scroll_widget)
        
        # 项目主页
        self.repo_card = HyperlinkCard(
            'https://github.com/netcccyun/dnsmgr',
            '项目主页',
            FIF.LINK,
            '项目主页',
            '查看项目源代码和文档'
        )
        
        # 反馈问题
        self.feedback_card = PrimaryPushSettingCard(
            '反馈',
            FIF.FEEDBACK,
            '反馈问题',
            '报告bug或提出功能建议'
        )
        self.feedback_card.clicked.connect(self.open_feedback)
        
        # 版本信息
        self.version_card = HyperlinkCard(
            'https://github.com/netcccyun/dnsmgr/releases',
            '检查更新',
            FIF.INFO,
            'DNS管理器',
            'v1.0.0 - 基于PyQt-Fluent-Widgets的DNS管理工具'
        )
        
        self.about_group.addSettingCard(self.repo_card)
        self.about_group.addSettingCard(self.feedback_card)
        self.about_group.addSettingCard(self.version_card)
        
        # 添加到布局
        self.expand_layout.setSpacing(28)
        self.expand_layout.setContentsMargins(36, 10, 36, 0)
        self.expand_layout.addWidget(self.personalization_group)
        self.expand_layout.addWidget(self.app_group)
        self.expand_layout.addWidget(self.data_group)
        self.expand_layout.addWidget(self.about_group)
    
    def on_theme_changed(self, theme_text):
        """主题改变事件"""
        theme_map = {
            '浅色': 'light',
            '深色': 'dark',
            '跟随系统': 'auto'
        }
        
        theme_value = theme_map.get(theme_text, 'auto')
        cfg.set('theme', theme_value)
        
        # 应用主题
        if theme_value == 'light':
            setTheme(Theme.LIGHT)
        elif theme_value == 'dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)
        
        InfoBar.success('成功', '主题已更改', parent=self)
    
    def on_language_changed(self, language_text):
        """语言改变事件"""
        language_map = {
            '简体中文': 'zh_CN',
            'English': 'en_US'
        }
        
        language_value = language_map.get(language_text, 'zh_CN')
        cfg.set('language', language_value)
        
        InfoBar.info('提示', '语言设置将在重启应用后生效', parent=self)
    
    def export_data(self):
        """导出数据"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                '导出数据',
                'dns_data.json',
                'JSON文件 (*.json)'
            )
            
            if not file_path:
                return
            
            # 获取所有数据
            data = {
                'providers': db.get_dns_providers(),
                'domains': db.get_domains(),
                'records': []
            }
            
            # 获取所有记录
            for domain in data['domains']:
                records = db.get_dns_records(domain['id'])
                for record in records:
                    record['domain_name'] = domain['domain']
                    data['records'].append(record)
            
            # 写入文件
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            InfoBar.success('成功', f'数据已导出到: {file_path}', parent=self)
            
        except Exception as e:
            InfoBar.error('错误', f'导出失败: {str(e)}', parent=self)
    
    def import_data(self):
        """导入数据"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                '导入数据',
                '',
                'JSON文件 (*.json)'
            )
            
            if not file_path:
                return
            
            # 确认导入
            msg_box = MessageBox(
                '确认导入',
                '导入数据将覆盖现有配置，确定要继续吗？',
                self
            )
            
            if msg_box.exec_() != MessageBox.Yes:
                return
            
            # 读取文件
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 导入提供商
            provider_map = {}
            for provider in data.get('providers', []):
                new_id = db.add_dns_provider(
                    provider['name'] + '_imported',
                    provider['type'],
                    provider['config']
                )
                provider_map[provider['id']] = new_id
            
            # 导入域名
            domain_map = {}
            for domain in data.get('domains', []):
                if domain['provider_id'] in provider_map:
                    new_id = db.add_domain(
                        domain['domain'],
                        provider_map[domain['provider_id']]
                    )
                    domain_map[domain['id']] = new_id
            
            # 导入记录
            for record in data.get('records', []):
                if record['domain_id'] in domain_map:
                    db.add_dns_record(
                        domain_map[record['domain_id']],
                        record.get('record_id', ''),
                        record['name'],
                        record['type'],
                        record['value'],
                        record['ttl'],
                        record['priority']
                    )
            
            InfoBar.success('成功', '数据导入完成', parent=self)
            
        except Exception as e:
            InfoBar.error('错误', f'导入失败: {str(e)}', parent=self)
    
    def clear_data(self):
        """清空数据"""
        msg_box = MessageBox(
            '确认清空',
            '确定要清空所有数据吗？\n此操作将删除所有DNS提供商、域名和记录，且不可撤销。',
            self
        )
        
        if msg_box.exec_() == MessageBox.Yes:
            try:
                # 这里需要在数据库中添加清空所有数据的方法
                InfoBar.warning('提示', '清空数据功能正在开发中', parent=self)
            except Exception as e:
                InfoBar.error('错误', f'清空失败: {str(e)}', parent=self)
    
    def open_feedback(self):
        """打开反馈页面"""
        import webbrowser
        webbrowser.open('https://github.com/netcccyun/dnsmgr/issues')