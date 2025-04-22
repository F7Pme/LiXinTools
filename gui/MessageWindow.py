from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QColor
from gui.styles import FontConfig


class MessageBox(QWidget):
    """自定义消息框，支持自动渐隐关闭"""
    def __init__(self, parent=None, message="", icon_type="error", auto_close=True, duration=2000):
        """
        初始化消息框
        
        Args:
            parent: 父窗口
            message: 显示的消息
            icon_type: 图标类型，可选 "error", "warning", "info", "success"
            auto_close: 是否自动关闭
            duration: 显示持续时间（毫秒）
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 150)
        
        self.message = message
        self.icon_type = icon_type
        self.auto_close = auto_close
        self.duration = duration
        self.opacity = 1.0
        self.fast_fade = False
        
        # 设置渐隐动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.setup_fade_animation(500)  # 500毫秒淡出
        
        self.setup_ui()
        
    def setup_fade_animation(self, duration):
        """设置渐隐动画参数"""
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.finished.connect(self.close)
    
    def enterEvent(self, event):
        """鼠标进入窗口时触发渐隐动画"""
        # 无论auto_close设置如何，鼠标进入时都启动渐隐动画
        self.start_fade_out()
        super().enterEvent(event)
    
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # 背景容器
        container = QWidget()
        container.setObjectName("MessageContainer")
        
        # 根据类型选择颜色
        border_color = "#EBEBEB"  # 默认边框颜色
        if self.icon_type == "error":
            border_color = "#E74C3C"  # 红色
        elif self.icon_type == "warning":
            border_color = "#F39C12"  # 黄色
        elif self.icon_type == "success":
            border_color = "#2ECC71"  # 绿色
        
        container.setStyleSheet(f"""
            QWidget#MessageContainer {{
                background-color: white;
                border-radius: 10px;
                border: 2px solid {border_color};
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # 设置图标和文字
        icon_code = "\uE783"  # 默认错误图标
        icon_color = "#E74C3C"  # 红色
        
        if self.icon_type == "warning":
            icon_code = "\uE7BA"  # 警告图标
            icon_color = "#F39C12"  # 黄色
        elif self.icon_type == "info":
            icon_code = "\uE946"  # 信息图标
            icon_color = "#3498DB"  # 蓝色
        elif self.icon_type == "success":
            icon_code = "\uE73E"  # 成功图标
            icon_color = "#2ECC71"  # 绿色
        
        # 图标
        icon_label = QLabel(icon_code)
        icon_label.setStyleSheet(f"""
            color: {icon_color};
            font-family: 'Segoe MDL2 Assets';
            font-size: 32px;
        """)
        icon_label.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=32))
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 文字标签
        text_label = QLabel(self.message)
        text_label.setStyleSheet("""
            font: 14px 'Microsoft YaHei';
            color: #333333;
            margin-top: 10px;
        """)
        text_label.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=14))
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        
        # 添加组件到容器
        container_layout.addWidget(icon_label, 0, Qt.AlignCenter)
        container_layout.addWidget(text_label, 0, Qt.AlignCenter)
        
        # 添加容器到主布局
        layout.addWidget(container)
    
    def showEvent(self, event):
        # 居中显示在父窗口上
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        
        # 设置初始不透明度
        self.setWindowOpacity(1.0)
        
        # 如果设置了自动关闭，则启动定时器
        if self.auto_close:
            QTimer.singleShot(self.duration, self.start_fade_out)
        
        super().showEvent(event)
    
    def start_fade_out(self):
        """开始淡出动画"""
        self.fade_animation.start()


def show_message(parent=None, message="", icon_type="error", auto_close=True, duration=2000):
    """
    创建并显示一个消息框
    
    Args:
        parent: 父窗口
        message: 显示的消息
        icon_type: 图标类型，可选 "error", "warning", "info", "success"
        auto_close: 是否自动关闭
        duration: 显示持续时间（毫秒）
        
    Returns:
        MessageBox: 创建的消息框实例
    """
    msg_box = MessageBox(parent, message, icon_type, auto_close, duration)
    
    # 计算父窗口居中位置
    if parent:
        parent_geometry = parent.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - msg_box.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - msg_box.height()) // 2
        msg_box.move(x, y)
    
    msg_box.show()
    return msg_box 