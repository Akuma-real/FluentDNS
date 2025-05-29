# -*- coding: utf-8 -*-
"""
主窗口实现
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationWidget,
    qrouter, FluentIcon as FIF, FluentWindow, SplashScreen
)

from .provider_interface import ProviderInterface
from .domain_interface import DomainInterface
from .record_interface import RecordInterface
from .log_interface import LogInterface
from .setting_interface import SettingInterface
from ..common.config import cfg


class MainWindow(FluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_window()
        self.init_navigation()
        
    def init_window(self):
        """初始化窗口"""
        self.resize(cfg.get('window.width', 1200), cfg.get('window.height', 800))
        self.setWindowTitle('DNS管理器')
        
        # 设置窗口图标
        self.setWindowIcon(FIF.GLOBE.icon())
        
        # 如果配置中窗口是最大化的，则最大化窗口
        if cfg.get('window.maximized', False):
            self.showMaximized()
    
    def create_interfaces(self):
        """创建所有子界面"""
        self.provider_interface = ProviderInterface(self)
        self.provider_interface.setObjectName('providerInterface')
        
        self.domain_interface = DomainInterface(self)
        self.domain_interface.setObjectName('domainInterface')
        
        self.record_interface = RecordInterface(self)
        self.record_interface.setObjectName('recordInterface')
        
        self.log_interface = LogInterface(self)
        self.log_interface.setObjectName('logInterface')
        
        self.setting_interface = SettingInterface(self)
        self.setting_interface.setObjectName('settingInterface')
    
    def setup_navigation(self):
        """设置导航栏"""
        # 添加导航项
        self.addSubInterface(self.provider_interface, FIF.CLOUD, 'DNS提供商')
        self.addSubInterface(self.domain_interface, FIF.GLOBE, '域名管理')
        self.addSubInterface(self.record_interface, FIF.EDIT, 'DNS记录')
        
        self.navigationInterface.addSeparator()
        
        self.addSubInterface(self.log_interface, FIF.HISTORY, '操作日志')
        
        # 添加设置页面到底部
        self.addSubInterface(
            self.setting_interface, FIF.SETTING, '设置', 
            NavigationItemPosition.BOTTOM
        )
        
        # 设置默认界面
        self.stackedWidget.setCurrentWidget(self.provider_interface)
        self.navigationInterface.setCurrentItem(self.provider_interface.objectName())
    
    def init_navigation(self):
        """初始化导航栏"""
        self.create_interfaces()
        self.setup_navigation()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口状态
        if self.isMaximized():
            cfg.set('window.maximized', True)
        else:
            cfg.set('window.maximized', False)
            cfg.set('window.width', self.width())
            cfg.set('window.height', self.height())
        
        cfg.save_config()
        event.accept()