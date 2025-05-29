# -*- coding: utf-8 -*-
"""
操作日志界面
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import (
    TableWidget, PushButton, FluentIcon as FIF, InfoBar,
    StrongBodyLabel, BodyLabel, ComboBox, LineEdit, DatePicker,
    CardWidget, ScrollArea
)

from ..common.database import db


class LogInterface(QWidget):
    """操作日志界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_logs()
        
        # 设置自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_logs)
        self.refresh_timer.start(30000)  # 30秒刷新一次
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题和控制区域
        header_layout = QHBoxLayout()
        header_layout.addWidget(StrongBodyLabel('操作日志'))
        header_layout.addStretch()
        
        # 筛选控件
        self.operation_combo = ComboBox()
        self.operation_combo.addItems(['全部操作', 'create', 'update', 'delete', 'sync'])
        self.operation_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(BodyLabel('操作类型:'))
        header_layout.addWidget(self.operation_combo)
        
        self.target_combo = ComboBox()
        self.target_combo.addItems(['全部类型', 'provider', 'domain', 'record'])
        self.target_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(BodyLabel('目标类型:'))
        header_layout.addWidget(self.target_combo)
        
        self.status_combo = ComboBox()
        self.status_combo.addItems(['全部状态', 'success', 'error'])
        self.status_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(BodyLabel('状态:'))
        header_layout.addWidget(self.status_combo)
        
        # 刷新按钮
        self.refresh_button = PushButton('刷新', self)
        self.refresh_button.setIcon(FIF.SYNC)
        self.refresh_button.clicked.connect(self.load_logs)
        header_layout.addWidget(self.refresh_button)
        
        # 清空日志按钮
        self.clear_button = PushButton('清空日志', self)
        self.clear_button.setIcon(FIF.DELETE)
        self.clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_button)
        
        layout.addLayout(header_layout)
        
        # 统计信息卡片
        self.stats_card = self.create_stats_card()
        layout.addWidget(self.stats_card)
        
        # 日志表格
        self.table = TableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            '时间', '操作', '目标类型', '目标ID', '详情', '状态', '错误信息'
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        # 存储原始日志数据用于筛选
        self.all_logs = []
    
    def create_stats_card(self):
        """创建统计信息卡片"""
        card = CardWidget()
        card.setFixedHeight(80)
        
        layout = QHBoxLayout(card)
        
        # 总操作数
        self.total_label = BodyLabel('总操作: 0')
        layout.addWidget(self.total_label)
        
        layout.addWidget(BodyLabel('|'))
        
        # 成功操作数
        self.success_label = BodyLabel('成功: 0')
        layout.addWidget(self.success_label)
        
        layout.addWidget(BodyLabel('|'))
        
        # 失败操作数
        self.error_label = BodyLabel('失败: 0')
        layout.addWidget(self.error_label)
        
        layout.addWidget(BodyLabel('|'))
        
        # 今日操作数
        self.today_label = BodyLabel('今日: 0')
        layout.addWidget(self.today_label)
        
        layout.addStretch()
        
        return card
    
    def load_logs(self):
        """加载操作日志"""
        try:
            self.all_logs = db.get_operation_logs(1000)  # 获取最近1000条日志
            self.update_stats()
            self.filter_logs()
        except Exception as e:
            InfoBar.error('错误', f'加载日志失败: {str(e)}', parent=self)
    
    def update_stats(self):
        """更新统计信息"""
        if not self.all_logs:
            self.total_label.setText('总操作: 0')
            self.success_label.setText('成功: 0')
            self.error_label.setText('失败: 0')
            self.today_label.setText('今日: 0')
            return
        
        total = len(self.all_logs)
        success = len([log for log in self.all_logs if log['status'] == 'success'])
        error = len([log for log in self.all_logs if log['status'] == 'error'])
        
        # 计算今日操作数
        from datetime import datetime, date
        today = date.today().strftime('%Y-%m-%d')
        today_count = len([
            log for log in self.all_logs 
            if log['created_at'].startswith(today)
        ])
        
        self.total_label.setText(f'总操作: {total}')
        self.success_label.setText(f'成功: {success}')
        self.error_label.setText(f'失败: {error}')
        self.today_label.setText(f'今日: {today_count}')
    
    def filter_logs(self):
        """筛选日志"""
        operation_filter = self.operation_combo.currentText()
        target_filter = self.target_combo.currentText()
        status_filter = self.status_combo.currentText()
        
        filtered_logs = self.all_logs
        
        # 按操作类型筛选
        if operation_filter != '全部操作':
            filtered_logs = [
                log for log in filtered_logs 
                if log['operation'] == operation_filter
            ]
        
        # 按目标类型筛选
        if target_filter != '全部类型':
            filtered_logs = [
                log for log in filtered_logs 
                if log['target_type'] == target_filter
            ]
        
        # 按状态筛选
        if status_filter != '全部状态':
            filtered_logs = [
                log for log in filtered_logs 
                if log['status'] == status_filter
            ]
        
        self.display_logs(filtered_logs)
    
    def display_logs(self, logs):
        """显示日志"""
        self.table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # 时间
            time_str = log['created_at']
            if 'T' in time_str:
                time_str = time_str.replace('T', ' ').split('.')[0]
            self.table.setItem(row, 0, QTableWidgetItem(time_str))
            
            # 操作
            operation_text = self.get_operation_text(log['operation'])
            self.table.setItem(row, 1, QTableWidgetItem(operation_text))
            
            # 目标类型
            target_text = self.get_target_text(log['target_type'])
            self.table.setItem(row, 2, QTableWidgetItem(target_text))
            
            # 目标ID
            target_id = str(log['target_id']) if log['target_id'] else '-'
            self.table.setItem(row, 3, QTableWidgetItem(target_id))
            
            # 详情
            details = log['details'] or '-'
            self.table.setItem(row, 4, QTableWidgetItem(details))
            
            # 状态
            status_text = '成功' if log['status'] == 'success' else '失败'
            status_item = QTableWidgetItem(status_text)
            if log['status'] == 'error':
                status_item.setForeground(Qt.red)
            else:
                status_item.setForeground(Qt.green)
            self.table.setItem(row, 5, status_item)
            
            # 错误信息
            error_msg = log['error_message'] or '-'
            self.table.setItem(row, 6, QTableWidgetItem(error_msg))
    
    def get_operation_text(self, operation):
        """获取操作文本"""
        operation_map = {
            'create': '创建',
            'update': '更新',
            'delete': '删除',
            'sync': '同步'
        }
        return operation_map.get(operation, operation)
    
    def get_target_text(self, target_type):
        """获取目标类型文本"""
        target_map = {
            'provider': 'DNS提供商',
            'domain': '域名',
            'record': 'DNS记录'
        }
        return target_map.get(target_type, target_type)
    
    def clear_logs(self):
        """清空日志"""
        from qfluentwidgets import MessageBox
        
        msg_box = MessageBox(
            '确认清空',
            '确定要清空所有操作日志吗？\n此操作不可撤销。',
            self
        )
        
        if msg_box.exec_():
            try:
                # 清空数据库中的操作日志
                deleted_count = db.clear_operation_logs()
                # 刷新界面显示
                self.load_logs()
                InfoBar.success('成功', f'已清空 {deleted_count} 条操作日志', parent=self)
            except Exception as e:
                InfoBar.error('错误', f'清空失败: {str(e)}', parent=self)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        event.accept()