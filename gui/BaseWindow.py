from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from .styles import StyleSheet, Dimensions, ColorPalette

class BaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_main_container()
        self.setup_shadow_effect()

    def setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(850, 550)

    def setup_main_container(self):
        self.main_container = QWidget()
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet(StyleSheet.window_style())
        self.setCentralWidget(self.main_container)

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def setup_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(Dimensions.SHADOW_BLUR)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.main_container.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.childAt(event.position().toPoint()) is None:
                self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_start_position') and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
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

    def paintEvent(self, event):
        # 启用抗锯齿绘制
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 创建圆角路径
        path = QPainterPath()
        rect = self.rect()
        radius = Dimensions.WINDOW_RADIUS
        path.addRoundedRect(rect, radius, radius)
        
        # 填充背景
        painter.fillPath(path, QColor(ColorPalette.BACKGROUND.value))