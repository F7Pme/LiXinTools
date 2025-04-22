from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                              QLabel, QPushButton, QListWidget, QSizePolicy,QListWidgetItem, QGraphicsView, QGraphicsScene, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QObject, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QMovie, QTransform, QPainter, QColor, QPen, QBrush
from gui.BaseWindow import BaseWindow
from gui.TitleBar import TitleBar
from gui.styles import StyleSheet, Dimensions, ColorPalette, FontConfig
from gui.LoadWindow import show_loading
from gui.MessageWindow import show_message
from gui.LogWindow import LogWindow
from config.config import Config
import requests
import threading
import math
import os
import sys
from PySide6.QtSvgWidgets import QSvgWidget
import gc
import psutil
import time
import traceback
import platform
import socket
import ctypes


class AccountLoaderSignals(QObject):
    """用于线程通信的信号类"""
    finished = Signal(dict)

# 全局日志窗口实例
log_window = None

# 存储LoginWindow的单例实例
_login_window_instance = None

class LoginWindow(BaseWindow):
    def __init__(self):
        # 检查是否已经存在实例
        global _login_window_instance
        if _login_window_instance is not None:
            raise RuntimeError("LoginWindow实例已经存在，请使用get_instance()获取")
            
        super().__init__()
        self.setMinimumSize(550, 330)
        self.account_window = None  # 添加成员变量
        self.loading_indicator = None  # 加载指示器
        self.main_window = None  # 保存MainWindow实例的引用
        
        # 初始化日志窗口但不显示
        global log_window
        if log_window is None:
            log_window = LogWindow()
            # 确保日志窗口初始化后可用
            if log_window:
                log_window.log("日志窗口初始化成功", "INFO")
        
        # 设置全局异常钩子
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.exception_handler
        
        self.setup_ui()
        self.resize(550, 330)
        
        # 从配置中恢复开发者模式状态
        self.restore_developer_mode()
        
        # 保存单例引用
        _login_window_instance = self

    @staticmethod
    def get_instance():
        """获取LoginWindow的单例实例"""
        global _login_window_instance
        if _login_window_instance is None:
            _login_window_instance = LoginWindow()
        return _login_window_instance

    def exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局异常处理函数"""
        global log_window
        if log_window and self.developer_mode_checkbox.isChecked():
            log_window.exception_hook(exc_type, exc_value, exc_traceback)
        else:
            self.original_excepthook(exc_type, exc_value, exc_traceback)

    def setup_ui(self):
        # 添加标题栏
        self.title_bar = TitleBar(show_back_button=False)
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.closeClicked.connect(self.close)

        # 主内容区域
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")

        # 创建表单容器
        form_widget = QWidget()
        form_widget.setFixedWidth(400)

        # 输入框
        # 学号输入框及标签
        student_id_label = self.create_input_label("立信一卡通学号")
        self.student_id_input = self.create_input_field(
            icon_code="\uE715", 
            placeholder="学号"
        )
        
        # 密码输入框及标签
        password_label = self.create_input_label("立信OA系统密码")
        self.password_input = self.create_input_field(
            icon_code="\uE8D7",
            placeholder="密码",
            is_password=True
        )

        # 登录按钮和开发者模式复选框的容器
        login_container = QWidget()
        login_container.setFixedWidth(400)
        login_container.setFixedHeight(50)  # 固定高度以便布局

        # 使用绝对定位
        login_container.setLayout(None)  # 移除现有布局

        # 设置登录按钮位置 - 水平居中
        login_container.setLayout(None)  # 移除现有布局

        # 登录按钮
        # 创建带图标的登录按钮
        self.login_btn = QPushButton()
        self.login_btn.setFixedSize(90, 40)
        
        # 创建内容容器
        btn_content = QWidget()
        btn_content.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_content)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        
        # 添加图标
        icon_label = QLabel("\uE77B")
        icon_label.setStyleSheet("""
            background: transparent;
            color: white;
        """)
        icon_label.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=16, bold=True))
        btn_layout.addWidget(icon_label)
        
        # 添加文字
        text_label = QLabel("登录")
        text_label.setStyleSheet(f"""
            background: transparent; 
            color: white;
            font: bold 14px '{FontConfig.TITLE[0]}';
        """)
        text_label.setFont(FontConfig.get_high_quality_font(FontConfig.TITLE[0], pixel_size=14, bold=True))
        btn_layout.addWidget(text_label)
        
        # 将内容容器居中在按钮中
        btn_main_layout = QHBoxLayout(self.login_btn)
        btn_main_layout.addWidget(btn_content, 0, Qt.AlignCenter)
        
        self.login_btn.clicked.connect(self.handle_login)
        
        # 使用自定义的QCheckBox类，用于显示Segoe MDL2 Assets图标
        class CheckBoxWithIcon(QCheckBox):
            def paintEvent(self, event):
                super().paintEvent(event)
                if self.isChecked():
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setRenderHint(QPainter.TextAntialiasing)
                    painter.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=11))
                    painter.setPen(QColor("#FFFFFF"))
                    painter.drawText(4, 14, "\uE73E")  # 使用Segoe MDL2 Assets中的勾选图标
        
        # 创建自定义复选框实例
        self.developer_mode_checkbox = CheckBoxWithIcon("开发者模式")
        self.developer_mode_checkbox.setFixedWidth(120)  # 设置固定宽度
        self.developer_mode_checkbox.setFont(FontConfig.get_high_quality_font(FontConfig.TITLE[0], pixel_size=12))
        self.developer_mode_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333333;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #999999;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #3072F6;
                border: 1px solid #3072F6;
            }
        """)
        
        # 连接复选框的状态改变信号
        self.developer_mode_checkbox.stateChanged.connect(self.on_developer_mode_changed)
        
        # 连接额外的鼠标点击事件，以确保信号触发
        original_mouse_release = self.developer_mode_checkbox.mouseReleaseEvent
        
        def custom_mouse_release(event):
            # 调用原始方法
            if original_mouse_release:
                original_mouse_release(event)
            
            # 强制触发日志窗口显示/隐藏
            self.on_developer_mode_changed(Qt.Checked if self.developer_mode_checkbox.isChecked() else Qt.Unchecked)
            
        self.developer_mode_checkbox.mouseReleaseEvent = custom_mouse_release
        
        # 删除工具提示
        # self.developer_mode_checkbox.setToolTip("勾选此项以显示开发者日志窗口")

        # 创建表单布局，包含输入框和登录按钮
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # 添加学号输入框
        form_layout.addWidget(student_id_label, 0, Qt.AlignLeft)
        form_layout.addSpacing(2)  # 缩小标签与输入框间距
        form_layout.addWidget(self.student_id_input, 0, Qt.AlignCenter)
        form_layout.addSpacing(8)  # 输入框间距

        # 添加密码输入框
        form_layout.addWidget(password_label, 0, Qt.AlignLeft)
        form_layout.addSpacing(2)  # 缩小标签与输入框间距
        form_layout.addWidget(self.password_input, 0, Qt.AlignCenter)
        form_layout.addSpacing(16)  # 上移登录按钮

        # 登录按钮居中
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.login_btn)
        btn_layout.addStretch(1)
        form_layout.addLayout(btn_layout)

        form_layout.addSpacing(10)  # 登录按钮和开发者模式之间的间距

        # 开发者模式稍微右移一点点
        dev_layout = QHBoxLayout()
        dev_layout.addStretch(13)  # 左侧权重略大一点
        dev_layout.addWidget(self.developer_mode_checkbox)
        dev_layout.addStretch(10)  # 右侧权重
        form_layout.addLayout(dev_layout)

        # 主内容布局
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.addStretch()
        content_layout.addWidget(form_widget, 0, Qt.AlignCenter)
        content_layout.addStretch()

        # 主窗口布局
        main_layout = self.centralWidget().layout()
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(self.content_widget)

        # 设置样式
        self.setup_styles()

    def create_input_label(self, text):
        """创建输入框上方的独立标签"""
        label_widget = QWidget()
        label_widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(label_widget)
        layout.setContentsMargins(60, 0, 0, 0)  # 向左移动标签
        layout.setSpacing(8)
        
        # 添加图标
        icon_label = QLabel("\uE840")
        icon_label.setStyleSheet("""
            background: transparent;
            color: #000000;
        """)
        icon_label.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=18))
        layout.addWidget(icon_label)
        
        # 添加文字
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #000000;")
        text_label.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", size=12, bold=True))
        layout.addWidget(text_label)
        
        return label_widget

    def create_input_field(self, icon_code, placeholder, is_password=False):
        """创建输入框组件（包含图标、输入框和可选的密码显示按钮）"""
        input_row = QWidget()
        input_row.setFixedSize(280, 36)
        
        # 图标标签（黑色）
        icon_label = QLabel(icon_code)
        icon_label.setStyleSheet("""
            background: transparent;
            color: #000000;
            border: none;
            padding: 0;
            margin: 0;
        """)
        icon_label.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=20))
        
        # 输入框
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFrame(False)
        line_edit.setStyleSheet(f"""
            background: transparent;
            border: none;
            padding-right: 25px;
            font: 14px '{FontConfig.TITLE[0]}';
        """)
        line_edit.setFont(FontConfig.get_high_quality_font(FontConfig.TITLE[0], pixel_size=14))
        
        # 连接回车键信号到登录函数
        line_edit.returnPressed.connect(self.handle_login)
        
        # 添加右侧图标
        right_icon = QLabel("\uE779")
        right_icon.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #666666;
                border: none;
                padding: 0;
                margin: 0;
                font-family: 'Segoe MDL2 Assets';
                font-size: 18px;
                font-weight: bold;
            }
            QLabel:hover {
                color: #333333;
            }
        """)
        right_icon.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=18, bold=True))
        right_icon.mousePressEvent = self.show_account_menu
        right_icon.setCursor(Qt.PointingHandCursor)
        
        # 如果是密码输入框，添加显示/隐藏按钮
        if is_password:
            # 使用Segoe MDL2 Assets字体中的眼睛图标编码
            toggle_btn = QPushButton("\uE7B3")  # 尝试使用另一个眼睛图标
            toggle_btn.setCursor(Qt.PointingHandCursor)
            toggle_btn.setStyleSheet(
                "QPushButton {"
                "background: transparent;"
                "border: none;"
                "padding: 0;"
                "margin: 0;"
                "width: 24px;"  # 增大按钮尺寸
                "height: 24px;"
                "font-family: 'Segoe MDL2 Assets';"
                "font-size: 16px;"  # 增大字体大小
                "font-weight: bold;"
                "color: #666666;"
                "}"
                "QPushButton:hover {"
                "color: #333333;"
                "}"
            )
            toggle_btn.setFixedSize(24, 24)
            
            # 设置更高质量的字体渲染
            toggle_btn.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=16, bold=True))
            
            # 点击切换密码显示状态
            def toggle_password():
                if line_edit.echoMode() == QLineEdit.Password:
                    line_edit.setEchoMode(QLineEdit.Normal)
                    toggle_btn.setText("\uE1F6")  # 睁眼图标
                else:
                    line_edit.setEchoMode(QLineEdit.Password)
                    toggle_btn.setText("\uE7B3")  
            
            toggle_btn.clicked.connect(toggle_password)
            line_edit.setEchoMode(QLineEdit.Password)
        
        # 布局
        layout = QHBoxLayout(input_row)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(8)
        layout.addWidget(icon_label)
        layout.addWidget(line_edit)
        
        # 添加右侧图标或密码切换按钮
        if is_password:
            # 将按钮放在输入框右侧
            layout.addWidget(toggle_btn)
            layout.setAlignment(toggle_btn, Qt.AlignRight)
        else:
            # 添加右侧图标
            layout.addWidget(right_icon)
            layout.setAlignment(right_icon, Qt.AlignRight)
        
        return input_row

    def setup_styles(self):
        # 通用输入框样式
        input_style = (
            "QWidget {"
            "background: #FFFFFF;"
            "border: 1.3px solid #EBEBEB;"
            "border-radius: 0px;"
            "}"
            "QLineEdit {"
            "background: transparent;"
            "border: none;"
            "font: 14px 'Microsoft YaHei';"
            "color: #333333;"
            "margin: 0;"
            "padding: 0;"
            "selection-background-color: #0078D4;"
            "selection-color: white;"
            "}"
            "QWidget:hover {"
            "border: 1.3px solid #DCDCDC;"  
            "}"
        )

        # 登录按钮样式
        btn_style = (
            "QPushButton {"
            "background: #0078D4;"
            "color: white;"
            "border: none;"
            "border-radius: 4px;"
            "font: 14px 'Microsoft YaHei';"
            "}"
            "QPushButton:hover {"
            "background: #499DDD;"
            "}"
            "QPushButton:pressed {"
            "background: #005A9E;"
            "}"
        )

        # 应用样式
        self.student_id_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)
        self.login_btn.setStyleSheet(btn_style)
        self.login_btn.setCursor(Qt.PointingHandCursor)

    def handle_login(self):
        from PySide6.QtWidgets import QLineEdit
        
        # 获取输入的用户名密码
        student_id_line_edit = self.student_id_input.findChild(QLineEdit)
        password_line_edit = self.password_input.findChild(QLineEdit)
        
        if not student_id_line_edit or not password_line_edit:
            show_message(self, "无法获取输入组件", "error", True, 3000)
            return
            
        username = student_id_line_edit.text().strip()
        password = password_line_edit.text().strip()
        
        if not username or not password:
            show_message(self, "账号密码不能为空", "warning", True, 3000)
            return
        
        # 显示加载指示器
        self.loading_indicator = show_loading(self, "正在加载账户数据...")
        
        # 创建信号对象
        self.direct_login_signals = AccountLoaderSignals()
        
        # 连接信号到槽，使用单次连接模式
        self.direct_login_signals.finished.connect(
            self.on_direct_login_completed,
            type=Qt.SingleShotConnection  # 使用SingleShotConnection确保回调只被触发一次
        )
        
        # 存储账号密码
        self.login_username = username
        self.login_password = password
        
        # 在后台线程中执行登录
        threading.Thread(
            target=self.direct_login_thread,
            daemon=True
        ).start()

    def direct_login_thread(self):
        """在后台线程中执行直接登录"""
        try:
            from core.auth import SessionManager
            from utils.data_parser import DataParser
            
            # 结果数据
            result = {
                'success': False,
                'error': None,
                'user_data': None,
                'session_mgr': None
            }
            
            try:
                # 创建会话管理器
                session_mgr = SessionManager()
                
                # 执行登录
                if not session_mgr.login_with_credentials(self.login_username, self.login_password):
                    result['error'] = "用户名或密码错误"
                    self.direct_login_signals.finished.emit(result)
                    return
                    
                # 获取用户信息
                response = session_mgr.session.get(
                    "https://yktepay.lixin.edu.cn/ykt/h5/accountinfo",
                    timeout=10
                )
                response.raise_for_status()
                
                # 解析用户信息
                user_data = DataParser.parse_account(response.text)
                
                # 保存会话
                session_mgr.save_cookies(self.login_username)
                
                # 准备结果数据
                result['success'] = True
                result['user_data'] = user_data
                result['session_mgr'] = session_mgr
                
            except Exception as e:
                result['error'] = f"登录过程中发生错误: {str(e)}"
                
            # 发送结果信号
            self.direct_login_signals.finished.emit(result)
            
        except Exception as e:
            # 发送错误信号
            self.direct_login_signals.finished.emit({
                'success': False,
                'error': f"登录线程发生错误: {str(e)}"
            })

    def on_direct_login_completed(self, result):
        """直接登录完成后的处理"""
        # 关闭可能存在的加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
            
        if result.get("success", False):
            try:
                # 获取学号
                student_id_line_edit = self.student_id_input.findChild(QLineEdit)
                student_id = student_id_line_edit.text() if student_id_line_edit else ""
                
                # 记录登录成功信息到日志窗口(如果已启用)
                if self.developer_mode_checkbox.isChecked():
                    global log_window
                    if log_window:
                        log_window.log("用户登录成功", "SUCCESS")
                        log_window.log(f"学号: {student_id}", "INFO")
                
                # 保存当前登录的账户到配置文件
                Config.save_current_account(student_id)
                
                # 不需要断开SingleShotConnection，它会在回调后自动断开
                
                # 创建或显示主窗口
                self.switch_to_main_window(result['session_mgr'], result['user_data'])
                
            except Exception as e:
                # 确保关闭加载指示器
                if self.loading_indicator:
                    self.loading_indicator.close()
                    self.loading_indicator = None
                
                # 记录错误到日志窗口
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"创建主窗口失败: {str(e)}", "ERROR")
                
                # 显示错误信息
                show_message(
                    parent=self,
                    message=f"打开主窗口失败: {str(e)}",
                    icon_type="error"
                )
        else:
            error_reason = result.get("error", "未知错误")
            show_message(
                parent=self,
                message=f"登录失败: {error_reason}",
                icon_type="error"
            )
            
            # 记录错误到日志窗口
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log(f"登录失败: {error_reason}", "ERROR")

    def show_account_menu(self, event):
        """显示账户选择窗口"""
        try:
            # 如果窗口已存在则先关闭
            if self.account_window:
                self.account_window.close()
                self.account_window = None
            
            # 直接从文件中加载所有账户，不验证有效性
            from core.auth import SessionManager
            import json
            import os
            from config.config import Config
            
            try:
                # 确保文件存在
                if os.path.exists(Config.COOKIE_FILE):
                    with open(Config.COOKIE_FILE, "r") as f:
                        all_accounts = json.load(f)
                else:
                    all_accounts = {}
            except Exception as e:
                print(f"加载账户文件出错: {str(e)}")
                all_accounts = {}
            
            # 创建账户选择窗口并显示所有账户
            self.account_window = AccountSelectionWindow(self, all_accounts, auto_refresh=True)
            
            # 确保窗口标志正确
            self.account_window.setWindowFlags(
                Qt.Window | 
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint
            )
            
            # 计算屏幕居中位置
            screen_geometry = self.screen().availableGeometry()
            x = (screen_geometry.width() - self.account_window.width()) // 2
            y = (screen_geometry.height() - self.account_window.height()) // 2
            
            self.account_window.move(x, y)
            self.account_window.show()
            self.account_window.activateWindow()  # 强制获得焦点
            self.account_window.raise_()  # 置顶显示
            
        except Exception as e:
            print(f"显示账户菜单出错: {str(e)}")

    def add_new_account(self):
        """添加新账户"""
        from core.auth import SessionManager
        from PySide6.QtWidgets import QInputDialog
        
        session_mgr = SessionManager()
        
        # 获取账号密码
        student_id, ok = QInputDialog.getText(
            self, "添加账户", "请输入一卡通账号:"
        )
        if not ok or not student_id:
            return
            
        password, ok = QInputDialog.getText(
            self, "添加账户", "请输入密码:", QLineEdit.Password
        )
        if not ok or not password:
            return
        
        # 尝试登录
        if session_mgr.login_with_credentials(student_id, password):
            session_mgr.current_user = student_id
            session_mgr.save_cookies(student_id)
            self.student_id_input.findChild(QLineEdit).setText(student_id)
            self.password_input.findChild(QLineEdit).clear()

    def validate_temp_session(self, cookies_dict):
        """验证临时会话有效性"""
        try:
            # 创建新的Session对象
            session = requests.Session()
            session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            session.headers.update({"User-Agent": Config.USER_AGENT})
            
            # 发送请求验证会话
            resp = session.get("https://yktepay.lixin.edu.cn/ykt/h5/index")
            return resp.ok and "一卡通" in resp.text
        except Exception:
            return False

    def switch_account(self, account_id):
        """切换账户并直接登录"""
        from PySide6.QtWidgets import QMessageBox
        
        # 关闭可能存在的加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 关闭账户选择窗口
        if self.account_window and hasattr(self.account_window, 'loading_indicator') and self.account_window.loading_indicator:
            self.account_window.loading_indicator.close()
            self.account_window.loading_indicator = None
        
        # 显示加载指示器
        self.loading_indicator = show_loading(self, "正在加载账户数据...")
        
        # 创建信号对象用于线程通信
        self.login_signals = AccountLoaderSignals()
        
        # 连接信号到槽，使用单次连接模式
        self.login_signals.finished.connect(
            self.on_account_login_completed,
            type=Qt.SingleShotConnection  # 使用SingleShotConnection确保回调只被触发一次
        )
        
        # 存储需要登录的账户ID
        self.login_account_id = account_id
        
        # 在后台线程中执行登录
        threading.Thread(
            target=self.login_account_thread,
            args=(account_id,),
            daemon=True
        ).start()

    def login_account_thread(self, account_id):
        """在后台线程中执行账户登录"""
        try:
            from core.auth import SessionManager
            from utils.data_parser import DataParser
            
            # 结果数据
            result = {
                'success': False,
                'error': None,
                'user_data': None,
                'session_mgr': None
            }
            
            session_mgr = SessionManager()
            accounts = session_mgr.load_cookies()
            
            if account_id in accounts:
                try:
                    # 恢复会话
                    session_mgr.session.cookies = requests.utils.cookiejar_from_dict(
                        accounts[account_id]["cookies"]
                    )
                    session_mgr.current_user = account_id
                    
                    # 验证会话有效性
                    if not session_mgr.validate_session():
                        result['error'] = "会话已过期，请重新登录"
                        self.login_signals.finished.emit(result)
                        return
                    
                    # 获取用户信息
                    response = session_mgr.session.get(
                        "https://yktepay.lixin.edu.cn/ykt/h5/accountinfo",
                        timeout=10
                    )
                    response.raise_for_status()
                    
                    # 解析用户信息
                    user_data = DataParser.parse_account(response.text)
                    
                    # 准备结果数据
                    result['success'] = True
                    result['user_data'] = user_data
                    result['session_mgr'] = session_mgr
                    
                except Exception as e:
                    result['error'] = f"自动登录失败: {str(e)}"
            else:
                result['error'] = "账户不存在"
            
            # 发送结果信号
            self.login_signals.finished.emit(result)
            
        except Exception as e:
            # 发送错误信号
            self.login_signals.finished.emit({
                'success': False,
                'error': f"登录过程发生错误: {str(e)}"
            })

    def on_account_login_completed(self, result):
        """账号登录完成后的处理"""
        # 关闭可能存在的加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
            
        if result.get("success", False):
            try:
                # 获取学号
                student_id = result.get("student_id", self.login_account_id)
                
                # 记录登录成功信息到日志窗口(如果已启用)
                if self.developer_mode_checkbox.isChecked():
                    global log_window
                    if log_window:
                        log_window.log("用户通过选择账号登录成功", "SUCCESS")
                        log_window.log(f"学号: {student_id}", "INFO")
                
                # 保存当前登录的账户到配置文件
                Config.save_current_account(student_id)
                
                # 不需要断开SingleShotConnection，它会在回调后自动断开
                
                # 创建或显示主窗口
                self.switch_to_main_window(result['session_mgr'], result['user_data'])
                
            except Exception as e:
                # 确保关闭加载指示器
                if self.loading_indicator:
                    self.loading_indicator.close()
                    self.loading_indicator = None
                
                # 记录错误到日志窗口
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"创建主窗口失败: {str(e)}", "ERROR")
                
                # 显示错误信息
                show_message(
                    parent=self,
                    message=f"打开主窗口失败: {str(e)}",
                    icon_type="error"
                )
        else:
            error_reason = result.get("error", "未知错误")
            show_message(
                parent=self,
                message=f"登录失败: {error_reason}",
                icon_type="error"
            )
            
            # 记录错误到日志窗口
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log(f"登录失败: {error_reason}", "ERROR")

    def switch_to_main_window(self, session_mgr, user_data):
        """切换到主窗口"""
        from gui.MainWindow import MainWindow
        from utils.query_bill import BillQuery
        from utils.query_xxt import XxtQuery
        from gui.LoadWindow import show_loading
        import threading
        
        # 创建学习通查询工具
        xxt_query = XxtQuery(session_mgr.session)
        
        # 创建或获取主窗口实例
        if self.main_window is None:
            bill_query = BillQuery(session_mgr.session)
            self.main_window = MainWindow(bill_query=bill_query)
            self.main_window.login_window = self  # 反向引用
        else:
            # 如果已存在实例，则刷新会话和账单查询
            bill_query = BillQuery(session_mgr.session)
            self.main_window.refresh_bill_query(bill_query)
            
        # 更新用户数据
        self.main_window.side_bar_info.update_data(user_data)
        
        # 显示主窗口并隐藏登录窗口
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()
        self.hide()  # 只隐藏，不关闭
        
        # 显示加载窗口
        self.xxt_loading_indicator = show_loading(self.main_window, "正在加载学习通数据...")
        
        # 创建信号对象用于与线程通信
        self.xxt_signals = AccountLoaderSignals()
        self.xxt_signals.finished.connect(self.on_xxt_login_completed)
        
        # 在后台线程中执行学习通登录
        threading.Thread(
            target=self.xxt_login_thread,
            args=(xxt_query, session_mgr),
            daemon=True
        ).start()

    def xxt_login_thread(self, xxt_query, session_mgr):
        """在后台线程中执行学习通登录和课程获取"""
        result = {
            'xxt_html': "",
            'xxt_login_success': False,
            'courses': [],
            'courses_html': None,
            'courses_success': False,
            'notices': [],
            'notices_json': None,
            'notices_success': False,
            'avatar_url': None,
            'user_name': None
        }
        
        try:
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log("尝试登录学习通", "INFO")
            
            # 登录学习通
            result['xxt_html'] = xxt_query.login_to_xxt()
            result['xxt_login_success'] = True
            
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log("学习通登录成功", "SUCCESS")
            
            # 获取用户头像和用户名
            try:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log("尝试获取学习通用户头像", "INFO")
                
                avatar_url, user_name = session_mgr.get_user_avatar_url()
                result['avatar_url'] = avatar_url
                result['user_name'] = user_name
                
                if self.developer_mode_checkbox.isChecked() and log_window:
                    if avatar_url:
                        log_window.log(f"学习通用户头像获取成功: {avatar_url}", "SUCCESS")
                    else:
                        log_window.log("未能获取学习通用户头像", "WARNING")
            except Exception as e:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"获取学习通用户头像失败: {str(e)}", "ERROR")
                
            # 获取学习通课程列表
            try:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log("尝试获取学习通课程列表", "INFO")
                    
                courses, courses_html = xxt_query.get_courses()
                result['courses'] = courses
                result['courses_html'] = courses_html
                result['courses_success'] = True
                
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"学习通课程列表获取成功，共{len(courses)}门课程", "SUCCESS")
            except Exception as e:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"获取学习通课程列表失败: {str(e)}", "ERROR")
            
            # 获取学习通作业和通知列表
            try:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log("尝试获取学习通作业和通知列表", "INFO")
                    
                notices, notices_json = xxt_query.get_notices()
                result['notices'] = notices
                result['notices_json'] = notices_json
                result['notices_success'] = True
                
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"学习通作业和通知列表获取成功，共{len(notices)}条信息", "SUCCESS")
            except Exception as e:
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"获取学习通作业和通知列表失败: {str(e)}", "ERROR")
                
        except Exception as e:
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log(f"学习通登录失败: {str(e)}", "ERROR")
            result['xxt_html'] = f"<html><body><h1>登录失败</h1><p>{str(e)}</p></body></html>"
            result['xxt_login_success'] = False
        
        # 发送完成信号
        self.xxt_signals.finished.emit(result)
        
    def on_xxt_login_completed(self, result):
        """学习通登录完成后的回调"""
        # 关闭加载窗口
        if hasattr(self, 'xxt_loading_indicator') and self.xxt_loading_indicator:
            self.xxt_loading_indicator.close()
            self.xxt_loading_indicator = None
        
        # 更新学习通界面
        if hasattr(self, 'main_window') and self.main_window:
            # 更新学习通内容
            self.main_window.side_bar_xxt.update_content(result['xxt_html'], result['xxt_login_success'])
            
            # 如果成功获取到课程列表，则更新课程显示
            if result['courses_success']:
                if result['courses_html']:  # 兼容旧版本方法
                    self.main_window.side_bar_xxt.update_courses(result['courses_html'], True)
                if result['courses']:  # 使用新版本方法
                    self.main_window.side_bar_xxt.update_courses_data(result['courses'], True)
            
            # 如果成功获取到通知列表，则更新通知显示
            if result['notices_success'] and result['notices']:
                self.main_window.side_bar_xxt.update_notices(result['notices'], True)
            
            # 延迟500毫秒更新头像，确保侧边栏信息已完全加载
            from PySide6.QtCore import QTimer
            if result['avatar_url']:
                # 创建定时器延迟执行头像更新
                QTimer.singleShot(500, lambda: self._delayed_update_avatar(result['avatar_url'], result['user_name']))
                
                if self.developer_mode_checkbox.isChecked() and log_window:
                    log_window.log(f"已安排延迟更新标题栏用户头像", "INFO")
    
    def _delayed_update_avatar(self, avatar_url, user_name):
        """延迟执行头像更新，确保侧边栏信息已加载"""
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'title_bar'):
            self.main_window.update_avatar(avatar_url, user_name)
            
            if self.developer_mode_checkbox.isChecked() and log_window:
                log_window.log(f"已更新标题栏用户头像", "SUCCESS")

    def closeEvent(self, event):
        # 关闭可能存在的加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 关闭可能存在的账号选择窗口
        if self.account_window:
            self.account_window.close()
            self.account_window = None
        
        # 关闭主窗口
        if self.main_window:
            self.main_window.close()
            self.main_window = None
            
        # 仅在主程序退出时才会保存日志
        if log_window:
            log_window.save_log()
            
        # 清理单例引用
        global _login_window_instance
        _login_window_instance = None
        
        event.accept()

    def on_developer_mode_changed(self, state):
        """处理开发者模式复选框状态改变事件"""
        global log_window
        
        # 导入配置
        from config.config import Config
        
        # 保存状态到配置
        is_checked = (state == Qt.Checked)
        Config.save_developer_mode(is_checked)
        
        if log_window:
            if state == Qt.Checked:
                log_window.log("开发者模式已启用", "INFO")
                log_window.show()
                # 强制窗口最前显示
                log_window.raise_()
                log_window.activateWindow()
            else:
                log_window.log("开发者模式已禁用", "INFO")
                log_window.hide()
        else:
            # 如果日志窗口未初始化，重新创建
            log_window = LogWindow()
            if state == Qt.Checked:
                log_window.show()
                log_window.raise_()
                log_window.activateWindow()

    def restore_developer_mode(self):
        """从配置中恢复开发者模式状态"""
        try:
            # 导入配置
            from config.config import Config
            
            # 获取开发者模式状态
            dev_mode_enabled = Config.get_developer_mode()
            
            # 应用状态到复选框，但暂时阻断信号传递
            if dev_mode_enabled and hasattr(self, 'developer_mode_checkbox'):
                # 暂时阻断信号，避免触发状态改变事件
                self.developer_mode_checkbox.blockSignals(True)
                self.developer_mode_checkbox.setChecked(True)
                self.developer_mode_checkbox.blockSignals(False)
                
                # 直接显示日志窗口，而不通过状态改变事件
                global log_window
                if log_window:
                    log_window.show()
                    log_window.raise_()
                    log_window.activateWindow()
        except Exception as e:
            print(f"恢复开发者模式状态失败: {e}")

class AccountSelectionWindow(BaseWindow):
    """多账户选择窗口"""
    def __init__(self, parent=None, all_accounts=None, auto_refresh=False):
        super().__init__()
        self.parent_window = parent
        self.all_accounts = all_accounts or {}
        self.valid_accounts = {}  # 有效账户将在验证后填充
        self.auto_refresh = auto_refresh
        self.setup_ui()
        self.load_accounts(False)  # 先加载所有账户，不验证
        
        # 记录窗口初始化日志
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "初始化", f"加载账户数: {len(self.all_accounts)}")
        except Exception:
            pass

    def setup_ui(self):
        # 设置窗口大小
        self.setFixedSize(240, 300)  # 增加宽度以便显示账户ID

        # 创建主容器并设置边框
        container = QWidget()
        container.setObjectName("AccountSelectionContainer")
        container.setStyleSheet("""
            QWidget#AccountSelectionContainer {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: #FFFFFF;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建自定义标题栏(只保留关闭按钮)
        self.title_bar = QWidget()
        self.title_bar.setObjectName("AccountSelectionTitleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(4, 0, 0, 0)  # 与TitleBar相同的内边距
        title_layout.setSpacing(0)  # 与TitleBar相同的间距
        
        # 为标题栏添加鼠标事件，使其可以用于拖拽窗口
        self.title_bar.mousePressEvent = self.title_bar_mouse_press_event
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release_event
        self.title_bar.leaveEvent = self.title_bar_leave_event
        
        # 添加图标 - 与TitleBar相同
        icon_path = os.path.join(os.path.dirname(__file__), "pic", "app_icon.svg")
        icon = QSvgWidget(icon_path)
        icon.setFixedSize(24, 24)
        
        # 启用抗锯齿和高品质渲染
        renderer = icon.renderer()
        renderer.setAspectRatioMode(Qt.KeepAspectRatio)
        renderer.setViewBox(renderer.viewBox())  # 保持原始视图
        # 设置高质量缩放
        icon.setContentsMargins(0, 0, 0, 0)
        icon.setStyleSheet("border: none; outline: none;")
        title_layout.addWidget(icon)
        title_layout.addSpacing(6)
        
        # 标题 - 与TitleBar相同的样式
        title_label = QLabel("选择账户")
        title_label.setStyleSheet(f"""
            font: {FontConfig.TITLE[1]}px '{FontConfig.TITLE[0]}';
            color: {ColorPalette.TEXT.value};
        """)
        title_layout.addWidget(title_label, 1, alignment=Qt.AlignLeft)
        
        # 关闭按钮 - 与TitleBar完全一致
        close_btn = QPushButton("\uE8BB")  # 使用相同的关闭图标
        close_btn.setFixedSize(30, 30)
        # 设置相同的字体
        btn_font = close_btn.font()
        btn_font.setFamily("Segoe MDL2 Assets")
        btn_font.setPointSize(10)
        close_btn.setFont(btn_font)
        # 使用相同的样式组合
        close_btn.setStyleSheet(
            StyleSheet.button_style() + 
            StyleSheet.close_button_style()
        )
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        # 主内容区域
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)

        # 账户列表
        self.account_list = QListWidget()
        self.account_list.setCursor(Qt.PointingHandCursor)
        self.account_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: #FFFFFF;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
                background: #FFFFFF;
                color: #000000;
            }
            QListWidget::item:hover {
                background: #E6E6E6;
            }
        """)
        content_layout.addWidget(self.account_list)

        # 刷新所有账户会话按钮
        refresh_btn = QPushButton("\uE72C 刷新所有账户会话")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe MDL2 Assets', 'Microsoft YaHei';
                font-size: 12px;
            }
            QPushButton:hover {
                background: #499DDD;
            }
        """)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_all_sessions)
        content_layout.addWidget(refresh_btn)

        # 添加组件到主布局
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(self.content_widget)

        # 设置中央部件
        self.setCentralWidget(container)
        
        # 加载指示器
        self.loading_indicator = None

    def load_accounts(self, show_valid_only=True):
        """加载账户列表
        
        Args:
            show_valid_only: 如果为True，只显示有效的账户；否则显示所有账户
        """
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "加载账户列表", 
                                       f"显示有效账户: {show_valid_only}, 总账户数: {len(self.all_accounts)}, 有效账户数: {len(self.valid_accounts)}")
        except Exception:
            pass
            
        try:
            self.account_list.clear()
            
            # 决定要显示的账户集合
            accounts_to_show = self.valid_accounts if show_valid_only else self.all_accounts
            
            for account_id, account_data in accounts_to_show.items():
                # 创建包含勾号的列表项
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 5, 10, 5)
                item_layout.setSpacing(10)
                
                # 账户ID文本
                label = QLabel(account_id)
                label.setStyleSheet("""
                    font: 12px 'Microsoft YaHei';
                    color: #333333;
                    padding-left: 5px;
                """)
                # 确保标签能显示完整的文本
                label.setMinimumWidth(120)
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                
                # 绿色勾标记（只在已验证的账户上显示）
                check_label = QLabel()
                if account_id in self.valid_accounts:
                    check_label.setText("\uE73E")  # 使用勾号图标
                    check_font = QFont("Segoe MDL2 Assets")
                    check_font.setPixelSize(14)
                    check_label.setFont(check_font)
                    check_label.setStyleSheet("""
                        color: #107C10;  /* 微软绿色 */
                    """)
                check_label.setFixedWidth(20)
                
                # 添加到布局
                item_layout.addWidget(label)
                item_layout.addWidget(check_label, 0, Qt.AlignRight)
                
                # 创建列表项并设置自定义控件
                item = QListWidgetItem()
                item.setData(Qt.UserRole, account_id)  # 存储账户ID
                self.account_list.addItem(item)
                self.account_list.setItemWidget(item, item_widget)
                
                # 设置合适的大小
                item.setSizeHint(QSize(170, 36))
            
            # 连接点击事件
            self.account_list.itemClicked.connect(self.on_account_selected)
            
            try:
                if log_window:
                    log_window.log_ui_event("AccountSelectionWindow", "加载账户完成", f"显示账户数: {self.account_list.count()}")
            except Exception:
                pass
        except Exception as e:
            print(f"加载账户列表出错: {str(e)}")
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"加载账户列表出错: {str(e)}", "ERROR")
            except Exception:
                pass

    def on_account_selected(self, item):
        """处理账户选择"""
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
            account_id = item.data(Qt.UserRole)
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "选择账户", f"账户ID: {account_id}")
        except Exception:
            pass
            
        # 关闭可能存在的加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
            
        account_id = item.data(Qt.UserRole)
        self.parent_window.switch_account(account_id)
        self.close()
        
    def refresh_all_sessions(self):
        """刷新所有账户会话"""
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("账户管理", "刷新会话", f"账户数: {len(self.all_accounts)}")
        except Exception:
            pass
            
        import datetime
        from PySide6.QtWidgets import QMessageBox
        
        # 显示加载指示器
        self.loading_indicator = show_loading(self, "正在刷新账户会话...")
        
        # 创建信号对象
        self.refresh_signals = AccountLoaderSignals()
        self.refresh_signals.finished.connect(self.on_refresh_completed)
        
        # 在后台线程中刷新会话
        threading.Thread(
            target=self.refresh_thread,
            daemon=True
        ).start()
    
    def refresh_thread(self):
        """在后台线程中刷新所有账户会话"""
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
        except Exception:
            log_window = None
            
        try:
            from core.auth import SessionManager
            import json
            import datetime
            
            session_mgr = SessionManager()
            
            # 使用当前加载的账户，而不是重新加载
            accounts = self.all_accounts
            
            # 记录开始刷新
            try:
                if log_window:
                    log_window.log_network_event("账户管理", "开始刷新", f"账户数: {len(accounts)}")
            except Exception:
                pass
            
            # 尝试刷新每个账户的会话
            refreshed_accounts = {}
            for account_id, account_data in accounts.items():
                try:
                    # 创建临时会话
                    temp_session = requests.Session()
                    temp_session.cookies = requests.utils.cookiejar_from_dict(account_data["cookies"])
                    temp_session.headers.update({"User-Agent": Config.USER_AGENT})
                    
                    # 访问首页刷新会话
                    resp = temp_session.get("https://yktepay.lixin.edu.cn/ykt/h5/index", timeout=10)
                    if resp.ok and "一卡通" in resp.text:
                        # 更新cookies
                        account_data["cookies"] = requests.utils.dict_from_cookiejar(temp_session.cookies)
                        account_data["last_update"] = datetime.datetime.now().isoformat()
                        refreshed_accounts[account_id] = account_data
                        
                        # 记录成功刷新
                        try:
                            if log_window:
                                log_window.log_network_event("账户管理", "刷新成功", f"账户: {account_id}")
                        except Exception:
                            pass
                except Exception as e:
                    print(f"刷新会话 {account_id} 失败: {str(e)}")
                    # 记录刷新失败
                    try:
                        if log_window:
                            log_window.log_network_event("账户管理", "刷新失败", f"账户: {account_id}, 错误: {str(e)}", "ERROR")
                    except Exception:
                        pass
            
            # 保存刷新后的cookies
            if refreshed_accounts:
                os.makedirs(os.path.dirname(Config.COOKIE_FILE), exist_ok=True)
                with open(Config.COOKIE_FILE, "w") as f:
                    json.dump(refreshed_accounts, f, indent=2)
                    
                # 记录保存cookies
                try:
                    if log_window:
                        log_window.log_data_event("Cookies", "保存", f"账户数: {len(refreshed_accounts)}")
                except Exception:
                    pass
            
            # 重新验证会话
            valid_accounts = {}
            for account_id, account_data in refreshed_accounts.items():
                if self.parent_window.validate_temp_session(account_data["cookies"]):
                    valid_accounts[account_id] = account_data
            
            # 记录验证结果
            try:
                if log_window:
                    log_window.log_network_event("账户管理", "验证完成", f"刷新账户数: {len(refreshed_accounts)}, 有效账户数: {len(valid_accounts)}")
            except Exception:
                pass
                
            # 发送完成信号
            self.refresh_signals.finished.emit(valid_accounts)
        except Exception as e:
            print(f"刷新会话线程出错: {str(e)}")
            # 记录刷新出错
            try:
                if log_window:
                    log_window.log(f"刷新会话线程出错: {str(e)}", "ERROR")
            except Exception:
                pass
            self.refresh_signals.finished.emit({})
    
    def on_refresh_completed(self, valid_accounts):
        """会话刷新完成的回调"""
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "刷新完成", f"有效账户数: {len(valid_accounts)}")
        except Exception:
            pass
            
        # 关闭加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 更新有效账户列表
        self.valid_accounts = valid_accounts
        
        # 重新加载账户列表，现在显示勾号标记
        self.load_accounts(False)  # 继续显示所有账户

    def showEvent(self, event):
        # 记录窗口显示
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "显示窗口")
        except Exception:
            pass
            
        super().showEvent(event)
        
        # 如果设置了自动刷新，则在窗口显示后立即刷新会话
        if self.auto_refresh:
            # 使用计时器延迟一小段时间后刷新，确保界面已完全显示
            QTimer.singleShot(100, self.refresh_all_sessions)

    def closeEvent(self, event):
        # 记录窗口关闭
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("AccountSelectionWindow", "关闭窗口")
        except Exception:
            pass
            
        # 关闭加载指示器
        if hasattr(self, 'loading_indicator') and self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        super().closeEvent(event)

    def title_bar_mouse_press_event(self, event):
        """标题栏鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 获取点击位置的控件
            child = self.title_bar.childAt(event.position().toPoint())
            # 只有当点击的不是按钮时才开始拖拽
            if not isinstance(child, QPushButton):
                self.drag_start_position = event.globalPosition().toPoint()
        # 不调用super().mousePressEvent，因为这是动态添加的方法

    def title_bar_mouse_move_event(self, event):
        """标题栏鼠标移动事件"""
        if hasattr(self, 'drag_start_position') and event.buttons() & Qt.LeftButton:
            # 获取当前鼠标位置下的控件
            child = self.title_bar.childAt(event.position().toPoint())
            # 如果当前鼠标位置在按钮上，则忽略移动事件，防止拖拽按钮导致窗口瞬移
            if not isinstance(child, QPushButton):
                # 移动整个窗口
                delta = event.globalPosition().toPoint() - self.drag_start_position
                self.move(self.pos() + delta)
                self.drag_start_position = event.globalPosition().toPoint()
        # 不调用super().mouseMoveEvent，因为这是动态添加的方法

    def title_bar_mouse_release_event(self, event):
        """标题栏鼠标释放事件，清除拖拽状态"""
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
        # 不调用super().mouseReleaseEvent，因为这是动态添加的方法
    
    def title_bar_leave_event(self, event):
        """标题栏鼠标离开事件，清除拖拽状态"""
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
        # 不调用super().leaveEvent，因为这是动态添加的方法
