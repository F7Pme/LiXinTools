from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal,Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QFont, QPixmap
import os
import requests
from io import BytesIO
from PySide6.QtCore import QSize
from .styles import StyleSheet, Dimensions, ColorPalette, FontConfig

# 导入log_window为全局变量
global log_window
try:
    from gui.LoginWindow import log_window
except ImportError:
    log_window = None

class TitleBar(QWidget):
    minimizeClicked = Signal()
    closeClicked = Signal()
    backClicked = Signal()

    def __init__(self, parent=None, show_back_button=False, avatar_url=None, user_name=None):
        super().__init__(parent)
        self.show_back_button = show_back_button
        self.avatar_url = avatar_url
        self.user_name = user_name
        
        # 记录标题栏初始化
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("TitleBar", "初始化", f"显示返回按钮: {show_back_button}")
        except Exception:
            pass
            
        self.setup_ui()
        self.setup_style()
        
        # 连接按钮事件到日志记录函数
        self.min_btn.clicked.connect(self.on_minimize_clicked)
        self.close_btn.clicked.connect(self.on_close_clicked)
        if self.show_back_button:
            self.back_btn.clicked.connect(self.on_back_clicked)

    def setup_ui(self):
        self.setFixedHeight(Dimensions.TITLEBAR_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(0)

        # 图标
        self.icon = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "pic", "app_icon.svg")
        self.icon = QSvgWidget(icon_path)
        self.icon.setFixedSize(24, 24)

        # 启用抗锯齿和高品质渲染
        renderer = self.icon.renderer()
        renderer.setAspectRatioMode(Qt.KeepAspectRatio)
        renderer.setViewBox(renderer.viewBox())  # 保持原始视图
        # 设置高质量缩放
        self.icon.setContentsMargins(0, 0, 0, 0)
        self.icon.setStyleSheet("border: none; outline: none;")
        layout.addWidget(self.icon)
        layout.addSpacing(6)

        # 标题
        self.title = QLabel("立信工具箱 v1.0.0 alpha测试版")
        layout.addWidget(self.title, 1)
        
        # 返回按钮
        if self.show_back_button:
            self.back_btn = QPushButton()
            self.back_btn.setText("\uE748")  # 返回图标
            self.back_btn.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", size=12))
            self.back_btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(self.back_btn)
            self.back_btn.setStyleSheet(
                StyleSheet.button_style() +
                """
                QPushButton {
                    font-family: 'Segoe MDL2 Assets';
                    font-size: 14px;
                    font-weight: normal;
                    padding: 2px 8px 6px 8px;
                    min-width: 24px;
                    text-align: center;
                    line-height: 14px;
                    margin-right: 0;
                }
                """
            )

        self.min_btn = QPushButton()
        self.close_btn = QPushButton()

        # 设置图标字体和字符
        self.min_btn.setText("\uE921")  # 最小化图标
        self.close_btn.setText("\uE8BB")  # 关闭图标

        # 设置字体
        self.min_btn.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", size=10))
        self.close_btn.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", size=10))
        
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)
        
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("TitleBar", "UI设置完成")
        except Exception:
            pass

    def load_avatar_image(self, url):
        """从URL加载头像并显示"""
        try:
            # 下载头像图片 - 添加适当的头部以绕过防盗链
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://lixin.fanya.chaoxing.com/portal",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # 创建QPixmap并加载图片数据
            avatar_pixmap = QPixmap()
            avatar_pixmap.loadFromData(response.content)
            
            # 调整大小为正方形，不再裁剪为圆形
            size = 28
            avatar_pixmap = avatar_pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 设置头像
            self.avatar_label.setPixmap(avatar_pixmap)
            self.avatar_label.setFixedSize(size, size)
            
            # 确保头像没有任何边框
            self.avatar_label.setStyleSheet("""
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            """)
            
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_ui_event("TitleBar", "头像加载成功", url)
            except Exception:
                pass
                
        except Exception as e:
            print(f"[!] 加载头像失败: {str(e)}")
            # 如果加载失败，使用默认图标并去掉边框和圆角
            self.avatar_label.setText("👤")
            self.avatar_label.setStyleSheet("""
                font-size: 16px;
                color: #666666;
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            """)

    def on_minimize_clicked(self):
        """最小化按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("TitleBar", "按钮点击", "最小化按钮")
        except Exception:
            pass
        # 发送最小化信号
        self.minimizeClicked.emit()
    
    def on_close_clicked(self):
        """关闭按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("TitleBar", "按钮点击", "关闭按钮")
        except Exception:
            pass
        # 发送关闭信号
        self.closeClicked.emit()
    
    def on_back_clicked(self):
        """返回按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("TitleBar", "按钮点击", "返回按钮")
        except Exception:
            pass
        # 发送返回信号
        self.backClicked.emit()

    def setup_style(self):
        self.setStyleSheet(StyleSheet.titlebar_style())
        self.title.setStyleSheet(f"""
            font: {FontConfig.TITLE[1]}px '{FontConfig.TITLE[0]}';
            color: {ColorPalette.TEXT.value};
        """)
        self.min_btn.setStyleSheet(StyleSheet.button_style())
        self.close_btn.setStyleSheet(
            StyleSheet.button_style() + 
            StyleSheet.close_button_style()
        )

    def update_avatar(self, avatar_url, user_name=None):
        """更新用户头像"""
        self.avatar_url = avatar_url
        self.user_name = user_name
        
        # 如果头像标签不存在，则创建（不重新设置整个UI）
        if not hasattr(self, 'avatar_container'):
            # 创建包含头像和用户名的容器
            layout = self.layout()
            
            # 用户信息容器（头像+用户名）
            self.avatar_container = QWidget()
            
            # 使用简单的QHBoxLayout布局
            container_layout = QHBoxLayout(self.avatar_container)
            container_layout.setContentsMargins(2, 1, 2, 1)
            container_layout.setSpacing(4)
            
            # 创建头像标签，确保无边框
            self.avatar_label = QLabel()
            self.avatar_label.setStyleSheet("border: none; background: transparent;")
            container_layout.addWidget(self.avatar_label)
            
            # 如果有用户名，创建并添加用户名标签，确保无边框
            if user_name:
                self.username_label = QLabel(user_name)
                self.username_label.setStyleSheet(f"""
                    font: {FontConfig.TITLE[1]}px '{FontConfig.TITLE[0]}';
                    color: {ColorPalette.TEXT.value};
                    background: transparent;
                    border: none;
                """)
                # 设置适当的宽度
                self.username_label.setMinimumWidth(120)
                self.username_label.setMaximumWidth(200)
                container_layout.addWidget(self.username_label)
            
            # 设置容器样式 - 上边框下移一个像素，颜色变浅
            self.avatar_container.setStyleSheet("""
                background-color: transparent;
                border: 0.5px solid #999999;
                border-radius: 0px;
                padding-top: 2px;
                padding-left: 1px;
                padding-right: 1px;
                padding-bottom: 1px;
                margin-top: 1px;
            """)
            
            # 添加容器到标题栏布局中，放在标题后面
            layout.insertWidget(layout.indexOf(self.title) + 1, self.avatar_container)
            
            # 加载头像
            self.load_avatar_image(avatar_url)
        else:
            # 更新头像
            self.load_avatar_image(avatar_url)
            
            # 更新用户名
            if user_name and hasattr(self, 'username_label'):
                self.username_label.setText(user_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 获取点击位置的控件
            child = self.childAt(event.position().toPoint())
            # 只有当点击的不是按钮时才开始拖拽（防止拖拽按钮导致窗口瞬移）
            if not isinstance(child, QPushButton):
                self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_start_position') and event.buttons() & Qt.LeftButton:
            # 获取当前鼠标位置下的控件
            child = self.childAt(event.position().toPoint())
            # 如果当前鼠标位置在按钮上，则忽略移动事件，防止拖拽按钮导致窗口瞬移
            if not isinstance(child, QPushButton):
                # 如果标题栏被拖拽，移动整个窗口
                window = self.window()
                delta = event.globalPosition().toPoint() - self.drag_start_position
                window.move(window.pos() + delta)
                self.drag_start_position = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，清除拖拽状态"""
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
        super().mouseReleaseEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件，清除拖拽状态"""
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
        super().leaveEvent(event)