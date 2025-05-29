#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS管理器桌面客户端
基于PyQt-Fluent-Widgets开发的DNS管理工具
参考dnsmgr项目功能
"""

import sys
import os
from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF, setTheme, Theme

from app.view.main_window import MainWindow
from app.common.config import cfg


def main():
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # 设置主题
    setTheme(Theme.AUTO)

    # 创建主窗口
    w = MainWindow()
    w.show()

    app.exec_()


if __name__ == '__main__':
    main()