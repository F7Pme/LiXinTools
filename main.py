import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from config.config import Config
from gui.LoginWindow import LoginWindow, log_window


if __name__ == "__main__":
    # 确保所有必要的目录存在
    os.makedirs("Log", exist_ok=True)
    os.makedirs(os.path.dirname(Config.COOKIE_FILE), exist_ok=True)
    
    # 读取开发者模式配置
    developer_mode = Config.get_developer_mode()
    # 确保保存配置正确
    Config.save_developer_mode(developer_mode)

    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # 应用样式
    from gui.styles import StyleSheet
    app.setStyleSheet(StyleSheet.window_style())
    
    # 确保应用程序在所有窗口关闭后退出
    app.setQuitOnLastWindowClosed(True)
    
    # 创建登录窗口 - 使用单例模式
    window = LoginWindow.get_instance()
    window.show()
    
    # 如果开发者日志窗口存在，设置定时更新并显示
    if log_window:
        log_window.log("主程序初始化完成", "INFO")
        # 设置日志窗口为非主窗口，这样关闭主窗口时应用程序会退出
        log_window.setAttribute(Qt.WA_QuitOnClose, False)
        
        # 如果开发者模式已启用，显示日志窗口
        if developer_mode:
            log_window.show()
            log_window.raise_()
            log_window.activateWindow()
    
    # 程序退出前保存日志
    exit_code = app.exec()
    if log_window:
        log_window.log("应用程序正常退出", "INFO")
        log_window.save_log()
    sys.exit(exit_code)