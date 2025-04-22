from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QIcon
from gui.styles import FontConfig
from gui.MessageWindow import MessageBox, show_message
import math


class SpinnerWidget(QWidget):
    """自定义旋转加载控件"""
    def __init__(self, parent=None, size=40, dots=8, width=3, color="#0078D4"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._size = size
        self._dots = dots
        self._width = width
        self._color = QColor(color)
        
        # 设置属性动画
        self._animation = QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)  # 1秒转一圈
        self._animation.setStartValue(0)
        self._animation.setEndValue(360)
        self._animation.setLoopCount(-1)  # 无限循环
        self._animation.setEasingCurve(QEasingCurve.Linear)
        self._animation.start()
    
    def get_rotation(self):
        return self._angle
    
    def set_rotation(self, angle):
        self._angle = angle
        self.update()  # 触发重绘
    
    # 定义Qt属性，用于动画
    rotation = Property(float, get_rotation, set_rotation)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算中心点和半径
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - self._width
        
        # 根据当前旋转角度绘制点
        for i in range(self._dots):
            # 计算当前点的角度和不透明度
            angle = math.radians(i * (360 / self._dots) + self._angle)
            opacity = 0.2 + 0.8 * (1 - (i % self._dots) / self._dots)
            
            # 设置点的颜色和不透明度
            color = QColor(self._color)
            color.setAlphaF(opacity)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            
            # 计算点的位置
            x = center_x + radius * math.cos(angle) - self._width/2
            y = center_y + radius * math.sin(angle) - self._width/2
            
            # 绘制点
            painter.drawEllipse(int(x), int(y), self._width, self._width)


class LoadingIndicator(QWidget):
    """加载指示器，显示旋转动画"""
    def __init__(self, parent=None, message="正在加载账户数据..."):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 200)
        self.message = message
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # 背景容器
        container = QWidget()
        container.setObjectName("LoadingContainer")
        container.setStyleSheet("""
            QWidget#LoadingContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EBEBEB;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # 创建旋转控件
        self.spinner = SpinnerWidget(size=48, dots=12, width=4, color="#0078D4")
        
        # 文字标签
        text_label = QLabel(self.message)
        text_label.setStyleSheet("""
            font: 14px 'Microsoft YaHei';
            color: #333333;
            margin-top: 10px;
        """)
        text_label.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=14))
        text_label.setAlignment(Qt.AlignCenter)
        
        # 添加组件到容器
        container_layout.addWidget(self.spinner, 0, Qt.AlignCenter)
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
        super().showEvent(event)
    
    def closeEvent(self, event):
        # 停止动画
        if hasattr(self, 'spinner') and hasattr(self.spinner, '_animation'):
            self.spinner._animation.stop()
        super().closeEvent(event)


# 方便直接使用的简便函数
def show_loading(parent=None, text="正在加载...", progress_bar=False, width=250):
    """
    显示加载指示窗口
    :param parent: 父窗口
    :param text: 显示文本
    :param progress_bar: 是否显示进度条
    :param width: 窗口宽度（新增参数）
    :return: 加载窗口实例
    """
    try:
        from gui.LoadWindow import LoadingWindow
        
        # 创建加载窗口
        loading_window = LoadingWindow(parent, text, progress_bar)
        
        # 如果指定了宽度，则设置窗口宽度
        if width and width > 0:
            loading_window.setMinimumWidth(width)
            
        # 显示窗口
        loading_window.show()
        return loading_window
    except ImportError:
        # 处理LoadingWindow导入错误
        import traceback
        print(f"加载窗口创建失败: {traceback.format_exc()}")
        return None
    except Exception as e:
        # 处理其他错误
        import traceback
        print(f"加载窗口显示错误: {str(e)}\n{traceback.format_exc()}")
        return None


class LoadingWindow(QWidget):
    """可调整大小的加载窗口类"""
    def __init__(self, parent=None, message="正在加载...", show_progress=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(250, 200)  # 默认大小，可通过setMinimumWidth调整
        self.message = message
        self.show_progress = show_progress
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # 背景容器
        self.container = QWidget()
        self.container.setObjectName("LoadingContainer")
        self.container.setStyleSheet("""
            QWidget#LoadingContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EBEBEB;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # 创建旋转控件
        self.spinner = SpinnerWidget(size=48, dots=12, width=4, color="#0078D4")
        
        # 文字标签 - 使用自动换行
        self.text_label = QLabel(self.message)
        self.text_label.setStyleSheet("""
            font: 14px 'Microsoft YaHei';
            color: #333333;
            margin-top: 10px;
        """)
        self.text_label.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=14))
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)  # 允许文本自动换行
        
        # 添加组件到容器
        container_layout.addWidget(self.spinner, 0, Qt.AlignCenter)
        container_layout.addWidget(self.text_label, 0, Qt.AlignCenter)
        
        # 添加容器到主布局
        layout.addWidget(self.container)
        
    def showEvent(self, event):
        # 居中显示在父窗口上
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        super().showEvent(event)
    
    def closeEvent(self, event):
        # 停止动画
        if hasattr(self, 'spinner') and hasattr(self.spinner, '_animation'):
            self.spinner._animation.stop()
        super().closeEvent(event)
        
    def set_text(self, text):
        """更新显示文本"""
        if hasattr(self, 'text_label'):
            self.text_label.setText(text)
            
    def setMinimumWidth(self, width):
        """重写设置最小宽度方法，同时调整容器大小"""
        super().setMinimumWidth(width)
        # 更新固定大小，保持高度不变
        self.setFixedSize(width, self.height())
        # 调整容器大小
        self.container.adjustSize() 