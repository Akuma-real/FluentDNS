# -*- coding: utf-8 -*-
"""
DNS记录管理界面
"""

import json
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QSplitter, QTreeWidgetItem, QTableWidgetItem, QDialog
from qfluentwidgets import (
    TableWidget, PushButton, FluentIcon as FIF, InfoBar, InfoBarPosition,
    MessageBox, Dialog, LineEdit, ComboBox, CardWidget, TreeWidget,
    StrongBodyLabel, BodyLabel, PrimaryPushButton, TransparentPushButton,
    SpinBox, TextEdit, IndeterminateProgressBar
)

from ..common.database import db
from ..dns.base import DNSProviderFactory, DNSRecord


def get_provider_config(domain_data):
    """获取DNS提供商配置的公共方法"""
    providers = db.get_dns_providers()
    for provider in providers:
        if provider['id'] == domain_data['provider_id']:
            return provider
    return None


class RecordSaveWorker(QThread):
    """DNS记录保存工作线程"""
    
    finished = pyqtSignal(bool, str)
    
    def __init__(self, domain_data, record_data, name, record_type, value, ttl, priority, is_update=False):
        super().__init__()
        self.domain_data = domain_data
        self.record_data = record_data
        self.name = name
        self.record_type = record_type
        self.value = value
        self.ttl = ttl
        self.priority = priority
        self.is_update = is_update
    
    def run(self):
        try:
            # 获取DNS提供商配置
            provider_data = get_provider_config(self.domain_data)
            if not provider_data:
                self.finished.emit(False, [], '未找到DNS提供商配置')
                return
            
            # 创建DNS提供商实例
            config = json.loads(provider_data['config'])
            provider = DNSProviderFactory.create(provider_data['type'], config)
            
            # 创建DNS记录对象
            dns_record = DNSRecord(
                id=self.record_data.get('id') if self.record_data else None,
                name=self.name,
                type=self.record_type,
                value=self.value,
                ttl=self.ttl,
                priority=self.priority
            )
            
            if self.is_update:
                # 更新DNS记录到服务商
                success = provider.update_record(self.domain_data['domain'], dns_record)
                if success:
                    # 记录操作日志
                    db.add_operation_log('update', 'record', self.record_data.get('id', 0), 
                                       f'更新DNS记录: {self.name}.{self.domain_data["domain"]}')
                    self.finished.emit(True, 'DNS记录已更新到服务商')
                else:
                    self.finished.emit(False, 'DNS记录更新失败')
            else:
                # 添加DNS记录到服务商
                remote_record_id = provider.add_record(self.domain_data['domain'], dns_record)
                if remote_record_id:
                    # 记录操作日志
                    db.add_operation_log('create', 'record', 0, 
                                       f'创建DNS记录: {self.name}.{self.domain_data["domain"]}')
                    self.finished.emit(True, 'DNS记录已添加到服务商')
                else:
                    self.finished.emit(False, 'DNS记录添加失败')
                    
        except Exception as e:
            self.finished.emit(False, f'保存失败: {str(e)}')


class RecordLoadWorker(QThread):
    """DNS记录加载工作线程"""
    
    finished = pyqtSignal(bool, list, str)
    
    def __init__(self, domain_data):
        super().__init__()
        self.domain_data = domain_data
    
    def run(self):
        try:
            # 获取DNS提供商配置
            provider_data = get_provider_config(self.domain_data)
            if not provider_data:
                self.finished.emit(False, [], '未找到DNS提供商配置')
                return
            
            # 创建DNS提供商实例并获取记录
            config = json.loads(provider_data['config'])
            provider = DNSProviderFactory.create(provider_data['type'], config)
            records = provider.get_records(self.domain_data['domain'])
            
            # 转换为字典格式以兼容现有代码
            record_list = []
            for record in records:
                record_dict = {
                    'id': record.id,
                    'name': record.name,
                    'type': record.type,
                    'value': record.value,
                    'ttl': record.ttl,
                    'priority': record.priority
                }
                record_list.append(record_dict)
            
            self.finished.emit(True, record_list, '')
            
        except Exception as e:
            self.finished.emit(False, [], f'获取DNS记录失败: {str(e)}')


class RecordDeleteWorker(QThread):
    """DNS记录删除工作线程"""
    
    finished = pyqtSignal(bool, str)
    
    def __init__(self, domain_data, record):
        super().__init__()
        self.domain_data = domain_data
        self.record = record
    
    def run(self):
        try:
            # 获取DNS提供商配置
            provider_data = get_provider_config(self.domain_data)
            if not provider_data:
                self.finished.emit(False, [], '未找到DNS提供商配置')
                return
            
            # 创建DNS提供商实例
            config = json.loads(provider_data['config'])
            provider = DNSProviderFactory.create(provider_data['type'], config)
            
            # 从DNS服务商删除记录
            if self.record.get('id'):
                success = provider.delete_record(self.domain_data['domain'], self.record['id'])
                if success:
                    # 记录操作日志
                    name = self.record['name'] if self.record['name'] else '@'
                    db.add_operation_log('delete', 'record', 0, 
                                       f'删除DNS记录: {name}.{self.domain_data["domain"]}')
                    self.finished.emit(True, 'DNS记录已从服务商删除')
                else:
                    self.finished.emit(False, 'DNS记录删除失败')
            else:
                self.finished.emit(False, '无法删除记录：缺少记录ID')
                
        except Exception as e:
            self.finished.emit(False, f'删除失败: {str(e)}')


class RecordEditDialog(QDialog):
    """DNS记录编辑对话框"""
    
    def __init__(self, parent=None, domain_data=None, record_data=None):
        super().__init__(parent)
        self.domain_data = domain_data
        self.record_data = record_data
        self.save_worker = None
        self.init_ui()
        
        if record_data:
            self.load_record_data()
    
    def init_ui(self):
        """初始化UI"""
        title = '编辑DNS记录' if self.record_data else '添加DNS记录'
        self.setWindowTitle(title)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 域名信息
        if self.domain_data:
            layout.addWidget(BodyLabel(f'域名: {self.domain_data["domain"]}'))
            layout.addWidget(BodyLabel(f'提供商: {self.domain_data["provider_name"]}'))
        
        # 记录名称
        layout.addWidget(BodyLabel('记录名称:'))
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText('如: www, mail, @ (根域名)')
        layout.addWidget(self.name_edit)
        
        # 记录类型
        layout.addWidget(BodyLabel('记录类型:'))
        self.type_combo = ComboBox()
        self.type_combo.addItems(['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)
        
        # 记录值
        layout.addWidget(BodyLabel('记录值:'))
        self.value_edit = TextEdit()
        self.value_edit.setMaximumHeight(100)
        layout.addWidget(self.value_edit)
        
        # TTL
        layout.addWidget(BodyLabel('TTL (秒):'))
        self.ttl_spin = SpinBox()
        self.ttl_spin.setRange(1, 86400)
        self.ttl_spin.setValue(600)
        layout.addWidget(self.ttl_spin)
        
        # 优先级（MX记录用）
        self.priority_label = BodyLabel('优先级:')
        layout.addWidget(self.priority_label)
        self.priority_spin = SpinBox()
        self.priority_spin.setRange(0, 65535)
        self.priority_spin.setValue(10)
        layout.addWidget(self.priority_spin)
        
        # 示例文本
        self.example_label = BodyLabel()
        layout.addWidget(self.example_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = TransparentPushButton('取消', self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = PrimaryPushButton('保存', self)
        self.save_button.clicked.connect(self.save_record)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 初始化类型相关UI
        self.on_type_changed(self.type_combo.currentText())
    
    def on_type_changed(self, record_type):
        """记录类型改变"""
        # 显示/隐藏优先级字段
        show_priority = record_type in ['MX', 'SRV']
        self.priority_label.setVisible(show_priority)
        self.priority_spin.setVisible(show_priority)
        
        # 更新示例
        examples = {
            'A': '192.168.1.1',
            'AAAA': '2001:db8::1',
            'CNAME': 'example.com',
            'MX': 'mail.example.com',
            'TXT': 'v=spf1 include:_spf.example.com ~all',
            'NS': 'ns1.example.com',
            'SRV': '10 5060 sip.example.com',
            'CAA': '0 issue "letsencrypt.org"'
        }
        
        example = examples.get(record_type, '')
        self.example_label.setText(f'示例: {example}' if example else '')
    
    def load_record_data(self):
        """加载记录数据"""
        self.name_edit.setText(self.record_data['name'])
        self.type_combo.setCurrentText(self.record_data['type'])
        self.value_edit.setText(self.record_data['value'])
        self.ttl_spin.setValue(self.record_data['ttl'])
        self.priority_spin.setValue(self.record_data['priority'])
    
    def validate_form(self):
        """验证表单输入"""
        value = self.value_edit.toPlainText().strip()
        if not value:
            InfoBar.warning('警告', '请输入记录值', parent=self)
            return False
        return True
    
    def save_record(self):
        """保存记录"""
        if not self.validate_form():
            return
            
        name = self.name_edit.text().strip()
        record_type = self.type_combo.currentText()
        value = self.value_edit.toPlainText().strip()
        ttl = self.ttl_spin.value()
        priority = self.priority_spin.value() if record_type in ['MX', 'SRV'] else 0
        
        # 检查是否有正在运行的保存任务
        if self.save_worker and self.save_worker.isRunning():
            InfoBar.warning('警告', '正在保存中，请稍候', parent=self)
            return
        
        # 禁用保存按钮，显示加载状态
        self.save_button.setEnabled(False)
        self.save_button.setText('保存中...')
        
        # 创建并启动保存工作线程
        is_update = self.record_data is not None
        self.save_worker = RecordSaveWorker(
            self.domain_data, self.record_data, name, record_type, 
            value, ttl, priority, is_update
        )
        self.save_worker.finished.connect(self.on_save_finished)
        self.save_worker.start()
    
    def on_save_finished(self, success, message):
        """保存完成回调"""
        # 恢复保存按钮状态
        self.save_button.setEnabled(True)
        self.save_button.setText('保存')
        
        if success:
            InfoBar.success('成功', message, parent=self)
            self.accept()
        else:
            InfoBar.error('错误', message, parent=self)


class RecordInterface(QWidget):
    """DNS记录管理界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_domain = None
        self.load_worker = None
        self.delete_worker = None
        self.init_ui()
        self.load_domains()
    
    def create_left_panel(self):
        """创建左侧域名列表面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(StrongBodyLabel('域名列表'))
        
        self.domain_tree = TreeWidget()
        self.domain_tree.setHeaderHidden(True)
        self.domain_tree.itemClicked.connect(self.on_domain_selected)
        left_layout.addWidget(self.domain_tree)
        
        return left_widget
    
    def create_header_layout(self):
        """创建右侧面板的标题和按钮布局"""
        header_layout = QHBoxLayout()
        self.title_label = StrongBodyLabel('请选择域名')
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        self.add_button = PrimaryPushButton('添加记录', self)
        self.add_button.setIcon(FIF.ADD)
        self.add_button.clicked.connect(self.add_record)
        self.add_button.setEnabled(False)
        header_layout.addWidget(self.add_button)
        
        self.refresh_button = PushButton('刷新', self)
        self.refresh_button.setIcon(FIF.SYNC)
        self.refresh_button.clicked.connect(self.load_records)
        self.refresh_button.setEnabled(False)
        header_layout.addWidget(self.refresh_button)
        
        return header_layout
    
    def create_right_panel(self):
        """创建右侧记录列表面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 添加标题和按钮
        right_layout.addLayout(self.create_header_layout())
        
        # 进度条
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = BodyLabel('')
        self.status_label.hide()
        right_layout.addWidget(self.status_label)
        
        # DNS记录表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['名称', '类型', '值', 'TTL', '优先级', '操作'])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        right_layout.addWidget(self.table)
        
        return right_widget
    
    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 添加左右面板
        splitter.addWidget(self.create_left_panel())
        splitter.addWidget(self.create_right_panel())
        
        # 设置分割器比例
        splitter.setSizes([300, 800])
    
    def load_domains(self):
        """加载域名列表"""
        self.domain_tree.clear()
        
        # 平铺显示所有域名，不按提供商分组
        domains = db.get_domains()
        for domain in domains:
            # 显示格式：域名 (提供商名称)
            display_text = f"{domain['domain']} ({domain['provider_name']})"
            domain_item = QTreeWidgetItem([display_text])
            self.domain_tree.addTopLevelItem(domain_item)
            domain_item.setData(0, Qt.UserRole, {'type': 'domain', 'data': domain})
    
    def on_domain_selected(self, item, column):
        """域名选择事件"""
        data = item.data(0, Qt.UserRole)
        if data and data['type'] == 'domain':
            self.set_current_domain(data['data'])
    
    def set_current_domain(self, domain_data):
        """设置当前域名"""
        self.current_domain = domain_data
        self.title_label.setText(f'DNS记录 - {domain_data["domain"]}')
        
        # 启用按钮
        self.add_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        # 加载记录
        self.load_records()
    
    def load_records(self):
        """加载DNS记录"""
        if not self.current_domain:
            return
        
        # 检查是否有正在运行的加载任务
        if self.load_worker and self.load_worker.isRunning():
            return
        
        # 显示加载状态
        self.progress_bar.show()
        self.status_label.setText('正在加载DNS记录...')
        self.status_label.show()
        self.refresh_button.setEnabled(False)
        
        # 创建并启动加载工作线程
        self.load_worker = RecordLoadWorker(self.current_domain)
        self.load_worker.finished.connect(self.on_load_finished)
        self.load_worker.start()
    
    def on_load_finished(self, success, records, message):
        """加载完成回调"""
        # 隐藏加载状态
        self.progress_bar.hide()
        self.status_label.hide()
        self.refresh_button.setEnabled(True)
        
        if not success:
            InfoBar.error('错误', message, parent=self)
            self.table.setRowCount(0)
            return
        
        # 更新表格
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # 名称
            name = record['name'] if record['name'] else '@'
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            # 类型
            self.table.setItem(row, 1, QTableWidgetItem(record['type']))
            
            # 值
            self.table.setItem(row, 2, QTableWidgetItem(record['value']))
            
            # TTL
            self.table.setItem(row, 3, QTableWidgetItem(str(record['ttl'])))
            
            # 优先级
            priority = str(record['priority']) if record['priority'] > 0 else '-'
            self.table.setItem(row, 4, QTableWidgetItem(priority))
            
            # 操作按钮
            self.table.setCellWidget(row, 5, self.create_action_buttons(record))
    
    def create_action_buttons(self, record):
        """创建操作按钮组件"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 0, 5, 0)
        
        edit_button = PushButton('编辑')
        edit_button.setFixedSize(60, 30)
        edit_button.clicked.connect(lambda checked, r=record: self.edit_record(r))
        button_layout.addWidget(edit_button)
        
        delete_button = PushButton('删除')
        delete_button.setFixedSize(60, 30)
        delete_button.clicked.connect(lambda checked, r=record: self.delete_record(r))
        button_layout.addWidget(delete_button)
        
        return button_widget
    
    def add_record(self):
        """添加DNS记录"""
        if not self.current_domain:
            return
        
        dialog = RecordEditDialog(self, self.current_domain)
        if dialog.exec_() == Dialog.Accepted:
            self.load_records()
            InfoBar.success('成功', 'DNS记录添加成功', parent=self)
    
    def edit_record(self, record):
        """编辑DNS记录"""
        dialog = RecordEditDialog(self, self.current_domain, record)
        if dialog.exec_() == Dialog.Accepted:
            self.load_records()
            InfoBar.success('成功', 'DNS记录更新成功', parent=self)
    
    def delete_record(self, record):
        """删除DNS记录"""
        name = record['name'] if record['name'] else '@'
        msg_box = MessageBox(
            '确认删除',
            f'确定要删除DNS记录 "{name}.{self.current_domain["domain"]}" ({record["type"]}) 吗？\n\n注意：这将从DNS服务商中永久删除该记录！',
            self
        )
        
        if msg_box.exec_() == MessageBox.Yes:
            # 检查是否有正在运行的删除任务
            if self.delete_worker and self.delete_worker.isRunning():
                return
            
            # 显示删除状态
            self.progress_bar.show()
            self.status_label.setText('正在删除DNS记录...')
            self.status_label.show()
            
            # 创建并启动删除工作线程
            self.delete_worker = RecordDeleteWorker(self.current_domain, record)
            self.delete_worker.finished.connect(self.on_delete_finished)
            self.delete_worker.start()
    
    def on_delete_finished(self, success, message):
        """删除完成回调"""
        # 隐藏删除状态
        self.progress_bar.hide()
        self.status_label.hide()
        
        if success:
            InfoBar.success('成功', message, parent=self)
            self.load_records()  # 重新加载记录列表
        else:
            InfoBar.error('错误', message, parent=self)
    
    # 移除同步相关方法，现在直接从DNS服务商获取实时数据