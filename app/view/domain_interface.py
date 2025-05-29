# -*- coding: utf-8 -*-
"""
域名管理界面
"""

import json
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon  # Import QIcon
from PyQt5.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QListWidgetItem, QHBoxLayout, QDialog
from qfluentwidgets import (
    TableWidget, PushButton, FluentIcon as FIF, InfoBar, InfoBarPosition,
    MessageBox, LineEdit, ComboBox, CardWidget, 
    StrongBodyLabel, BodyLabel, PrimaryPushButton, TransparentPushButton,
    IndeterminateProgressBar, VBoxLayout, ListWidget
)

from ..common.database import db
from ..dns.base import DNSProviderFactory


def get_provider_config(provider_id):
    """获取DNS提供商配置的公共方法"""
    providers = db.get_dns_providers()
    for provider in providers:
        if provider['id'] == provider_id:
            return provider
    return None


class DomainFetchWorker(QThread):
    """获取域名列表工作线程"""
    
    finished = pyqtSignal(bool, list, str)
    
    def __init__(self, provider_data):
        super().__init__()
        self.provider_data = provider_data
    
    def run(self):
        try:
            # 创建DNS提供商实例
            config = json.loads(self.provider_data['config'])
            provider = DNSProviderFactory.create(self.provider_data['type'], config)
            
            # 获取域名列表
            domains = provider.get_domains()
            
            self.finished.emit(True, domains, '')
        except Exception as e:
            self.finished.emit(False, [], str(e))


class RecordCountWorker(QThread):
    """获取域名记录数量工作线程"""
    
    finished = pyqtSignal(int, int, str)  # row, count, error_message
    
    def __init__(self, row, domain_data, provider_data):
        super().__init__()
        self.row = row
        self.domain_data = domain_data
        self.provider_data = provider_data
    
    def run(self):
        try:
            # 创建DNS提供商实例
            config = json.loads(self.provider_data['config'])
            provider = DNSProviderFactory.create(self.provider_data['type'], config)
            
            # 获取记录列表
            records = provider.get_records(self.domain_data['domain'])
            
            self.finished.emit(self.row, len(records), '')
        except Exception as e:
            self.finished.emit(self.row, -1, str(e))


class DomainAddDialog(QDialog):
    """添加域名对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fetch_worker = None
        self.current_provider_data = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('添加域名')
        self.resize(500, 400)
        
        layout = VBoxLayout(self)
        
        # DNS提供商选择
        layout.addWidget(BodyLabel('选择DNS提供商:'))
        self.provider_combo = ComboBox()
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        self.load_providers()
        layout.addWidget(self.provider_combo)
        
        # 获取域名按钮
        self.fetch_button = PrimaryPushButton('获取域名列表', self)
        self.fetch_button.setIcon(FIF.DOWNLOAD)
        self.fetch_button.clicked.connect(self.fetch_domains)
        layout.addWidget(self.fetch_button)
        
        # 进度条
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 域名列表
        layout.addWidget(BodyLabel('选择要添加的域名:'))
        self.domain_list = ListWidget()
        self.domain_list.setSelectionMode(ListWidget.MultiSelection)
        layout.addWidget(self.domain_list)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = TransparentPushButton('取消', self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = PrimaryPushButton('添加选中域名', self)
        self.save_button.clicked.connect(self.add_selected_domains)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_providers(self):
        """加载DNS提供商"""
        providers = db.get_dns_providers()
        self.provider_combo.clear()
        
        if not providers:
            InfoBar.warning('警告', '请先添加DNS提供商', parent=self)
            return
        
        for provider in providers:
            self.provider_combo.addItem(text=provider['name'], icon=QIcon(), userData=provider)
    
    def on_provider_changed(self):
        """提供商选择改变"""
        if hasattr(self, 'domain_list'):
            self.domain_list.clear()
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(False)
        self.current_provider_data = self.provider_combo.currentData()
    
    def fetch_domains(self):
        """获取域名列表"""
        if not self.current_provider_data:
            InfoBar.warning('警告', '请选择DNS提供商', parent=self)
            return
        
        if self.fetch_worker and self.fetch_worker.isRunning():
            InfoBar.warning('警告', '正在获取域名列表，请稍候', parent=self)
            return
        
        self.fetch_worker = DomainFetchWorker(self.current_provider_data)
        self.fetch_worker.finished.connect(self.on_fetch_finished)
        
        self.progress_bar.show()
        self.fetch_button.setEnabled(False)
        
        self.fetch_worker.start()
    
    def on_fetch_finished(self, success, domains, error_msg):
        """获取域名完成"""
        self.progress_bar.hide()
        self.fetch_button.setEnabled(True)
        
        if not success:
            InfoBar.error('错误', f'获取域名列表失败: {error_msg}', parent=self)
            return
        
        if not domains:
            InfoBar.info('提示', '该DNS提供商下没有域名', parent=self)
            return
        
        # 获取已存在的域名
        existing_domains = db.get_domains(self.current_provider_data['id'])
        existing_domain_names = {d['domain'] for d in existing_domains}
        
        # 填充域名列表
        self.domain_list.clear()
        for domain in domains:
            item = QListWidgetItem(domain)
            if domain in existing_domain_names:
                item.setText(f"{domain} (已存在)")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            else:
                item.setData(Qt.UserRole, domain)
            self.domain_list.addItem(item)
        
        self.save_button.setEnabled(True)
        InfoBar.success('成功', f'获取到 {len(domains)} 个域名', parent=self)
    
    def add_selected_domains(self):
        """添加选中的域名"""
        selected_items = self.domain_list.selectedItems()
        if not selected_items:
            InfoBar.warning('警告', '请选择要添加的域名', parent=self)
            return
        
        provider_id = self.current_provider_data['id']
        added_count = 0
        
        try:
            for item in selected_items:
                if item.flags() & Qt.ItemIsEnabled:  # 只处理可用的项目
                    domain = item.data(Qt.UserRole)
                    if domain:
                        db.add_domain(domain, provider_id)
                        added_count += 1
            
            if added_count > 0:
                db.add_operation_log('create', 'domain', None, f'批量添加域名: {added_count} 个')
                InfoBar.success('成功', f'成功添加 {added_count} 个域名', parent=self)
                self.accept()
            else:
                InfoBar.warning('警告', '没有可添加的域名', parent=self)
        except Exception as e:
            InfoBar.error('错误', f'添加失败: {str(e)}', parent=self)


class DomainInterface(QWidget):
    """域名管理界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.record_count_workers = {}  # 存储记录数量工作线程
        self.init_ui()
        self.load_domains()
    
    def create_header_layout(self):
        """创建标题和按钮布局"""
        header_layout = QHBoxLayout()
        header_layout.addWidget(StrongBodyLabel('域名管理'))
        header_layout.addStretch()
        
        self.add_button = PrimaryPushButton('添加域名', self)
        self.add_button.setIcon(FIF.ADD)
        self.add_button.clicked.connect(self.add_domain)
        header_layout.addWidget(self.add_button)
        
        self.refresh_button = PushButton('刷新', self)
        self.refresh_button.setIcon(FIF.SYNC)
        self.refresh_button.clicked.connect(self.load_domains)
        header_layout.addWidget(self.refresh_button)
        
        return header_layout
    
    def create_table(self):
        """创建域名表格"""
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['域名', 'DNS提供商', '记录数量', '创建时间', '操作'])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 设置DNS提供商列的最小宽度，确保完整显示
        self.table.setColumnWidth(1, 150)
        
        return self.table
    
    def init_ui(self):
        """初始化UI"""
        layout = VBoxLayout(self)
        
        # 添加标题和按钮
        layout.addLayout(self.create_header_layout())
        
        # 添加域名表格
        layout.addWidget(self.create_table())
    
    def load_domains(self):
        """加载域名列表"""
        domains = db.get_domains()
        self.table.setRowCount(len(domains))
        
        # 清理之前的工作线程
        for worker in self.record_count_workers.values():
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.record_count_workers.clear()
        
        for row, domain in enumerate(domains):
            # 域名
            self.table.setItem(row, 0, QTableWidgetItem(domain['domain']))
            
            # DNS提供商
            provider_text = f"{domain['provider_name']} ({domain['provider_type']})"
            self.table.setItem(row, 1, QTableWidgetItem(provider_text))
            
            # 记录数量 - 初始显示为加载中
            self.table.setItem(row, 2, QTableWidgetItem('加载中...'))
            
            # 创建时间
            self.table.setItem(row, 3, QTableWidgetItem(domain['created_at']))
            
            # 操作按钮
            self.table.setCellWidget(row, 4, self.create_action_buttons(domain))
            
            # 异步获取记录数量
            self.load_record_count(row, domain)
    
    def create_action_buttons(self, domain):
        """创建操作按钮组件"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 0, 5, 0)
        
        manage_button = PushButton('管理记录')
        manage_button.setFixedSize(80, 30)
        manage_button.clicked.connect(lambda checked, d=domain: self.manage_records(d))
        button_layout.addWidget(manage_button)
        
        delete_button = PushButton('删除')
        delete_button.setFixedSize(60, 30)
        delete_button.clicked.connect(lambda checked, d=domain: self.delete_domain(d))
        button_layout.addWidget(delete_button)
        
        return button_widget
    
    def load_record_count(self, row, domain):
        """异步加载域名记录数量"""
        try:
            # 获取DNS提供商配置
            provider_data = get_provider_config(domain['provider_id'])
            if not provider_data:
                self.table.setItem(row, 2, QTableWidgetItem('配置错误'))
                return
            
            # 创建并启动记录数量工作线程
            worker = RecordCountWorker(row, domain, provider_data)
            worker.finished.connect(self.on_record_count_finished)
            self.record_count_workers[row] = worker
            worker.start()
            
        except Exception as e:
            self.table.setItem(row, 2, QTableWidgetItem('加载失败'))
    
    def on_record_count_finished(self, row, count, error_message):
        """记录数量加载完成回调"""
        if row in self.record_count_workers:
            del self.record_count_workers[row]
        
        if error_message:
            self.table.setItem(row, 2, QTableWidgetItem('加载失败'))
        elif count >= 0:
            self.table.setItem(row, 2, QTableWidgetItem(str(count)))
        else:
            self.table.setItem(row, 2, QTableWidgetItem('未知'))
    
    def add_domain(self):
        """添加域名"""
        dialog = DomainAddDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_domains()
            # 同时刷新记录管理界面的域名列表
            main_window = self.window()
            if hasattr(main_window, 'record_interface'):
                main_window.record_interface.load_domains()
            InfoBar.success('成功', '域名添加成功', parent=self)
    

    
    def manage_records(self, domain):
        """管理DNS记录"""
        # 切换到DNS记录界面，并传递域名信息
        main_window = self.window()  # 使用window()方法获取顶级窗口
        if hasattr(main_window, 'record_interface'):
            main_window.record_interface.set_current_domain(domain)
            main_window.stackedWidget.setCurrentWidget(main_window.record_interface)
            main_window.navigationInterface.setCurrentItem(main_window.record_interface.objectName())
        else:
            InfoBar.error('错误', '无法找到记录管理界面', parent=self)
    
    # 已移除sync_records方法 - 该功能不需要
    
    def delete_domain(self, domain):
        """删除域名"""
        msg_box = MessageBox(
            '确认删除',
            f'确定要删除域名 "{domain["domain"]}" 吗？\n此操作将同时删除该域名下的所有DNS记录。',
            self
        )
        
        if msg_box.exec_():
            try:
                # 删除域名下的所有记录
                records = db.get_dns_records(domain['id'])
                for record in records:
                    db.delete_dns_record(record['id'])
                
                # 删除域名
                db.delete_domain(domain['id'])
                
                db.add_operation_log('delete', 'domain', domain['id'], f'本地删除域名: {domain["domain"]}')
                self.load_domains()
                # 同时刷新记录管理界面的域名列表
                main_window = self.window()
                if hasattr(main_window, 'record_interface'):
                    main_window.record_interface.load_domains()
                InfoBar.success('成功', '域名删除成功', parent=self)
            except Exception as e:
                InfoBar.error('错误', f'删除失败: {str(e)}', parent=self)