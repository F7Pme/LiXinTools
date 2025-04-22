from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from gui.styles import FontConfig
import os
import sys

# 导入log_window为全局变量
global log_window
try:
    from gui.LoginWindow import log_window
except ImportError:
    log_window = None

class SideBar(QWidget):
    def __init__(self):
        super().__init__()
        # 记录侧边栏初始化
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "初始化")
        except Exception:
            pass
        
        # 添加对账单侧边栏的引用
        self.sidebar_bill = None
        
        self.setup_ui()

    def setup_ui(self):
        # 设置侧边栏样式和固定宽度
        self.setFixedWidth(50)  # 修改为50px以适应左右各5px的内边距
        self.setStyleSheet("""
            background: #FFFFFF;
            border-right: 1px solid #F6EAEA;
        """)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)  # 设置按钮间距为5px
        layout.setContentsMargins(5, 5, 5, 5)  # 设置布局边距为5px
        
        # 添加功能按钮
        self.btn_dashboard = QPushButton("\uE700")  # 导航
        self.btn_info = QPushButton("\uE7EE")  # 个人信息
        self.btn_bill = QPushButton("\uEE92")  # 账单
        self.btn_electricity = QPushButton("\uE945")  # 电费
        self.btn_author = QPushButton("\uE946")  # 图表/作者信息
        
        # 添加学习通按钮 - 使用PNG图标
        self.btn_xxt = QPushButton()
        
        # 修改图标路径逻辑，确保在打包后也能找到图标
        # 方法1: 使用当前文件所在目录作为基准
        current_dir = os.path.dirname(os.path.abspath(__file__))
        xxt_icon_path = os.path.join(current_dir, "pic", "xxt_icon.png")
        
        # 方法2: 如果打包后在临时目录，尝试相对于执行目录的路径
        if not os.path.exists(xxt_icon_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
            xxt_icon_path = os.path.join(base_dir, "gui", "pic", "xxt_icon.png")
        
        # 方法3: 尝试相对于当前工作目录的路径
        if not os.path.exists(xxt_icon_path):
            xxt_icon_path = os.path.join(os.getcwd(), "gui", "pic", "xxt_icon.png")
            
        if os.path.exists(xxt_icon_path):
            # 记录成功找到图标的路径
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"加载学习通图标: {xxt_icon_path}", "INFO")
            except Exception:
                pass
                
            self.btn_xxt.setIcon(QIcon(xxt_icon_path))
            self.btn_xxt.setIconSize(QSize(18, 18))  # 使用正确的QSize
        else:
            # 图标不存在时的备用文字
            self.btn_xxt.setText("学")
            
            # 记录未找到图标
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"未找到学习通图标，尝试路径: {xxt_icon_path}", "WARNING")
            except Exception:
                pass
        
        # 设置高质量字体渲染
        icon_font = FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=18)
        
        self.btn_dashboard.setFont(icon_font)
        self.btn_info.setFont(icon_font)
        self.btn_bill.setFont(icon_font)
        self.btn_electricity.setFont(icon_font)
        self.btn_author.setFont(icon_font)
        
        # 设置按钮为可选中
        self.btn_dashboard.setCheckable(True)
        self.btn_info.setCheckable(True)
        self.btn_bill.setCheckable(True)
        self.btn_electricity.setCheckable(True)
        self.btn_author.setCheckable(True)
        self.btn_xxt.setCheckable(True)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background: transparent;
                border: none;
                min-width: 40px;
                min-height: 40px;
                max-width: 40px;
                max-height: 40px;
                padding: 0;
                text-align: center;
                color: #000000;
                font-family: 'Segoe MDL2 Assets';
                font-size: 18px;
            }
            QPushButton:hover {
                background: #E6E6E6;
            }
            QPushButton:checked {
                background: #E6E6E6;
                border-left: 5px solid #0078D4;
                /* 移除font-weight: bold; 保持图标大小不变 */
            }
        """
        # 第一个按钮单独样式
        first_button_style = """
            QPushButton {
                background: transparent;
                border: none;
                min-width: 40px;
                height: 22px;
                max-width: 40px;
                padding: 0;
                text-align: center;
                color: #000000;
                font-family: 'Segoe MDL2 Assets';
                font-size: 18px;
            }
            QPushButton:hover, QPushButton:pressed {
                background: transparent;
            }
        """
        self.btn_dashboard.setStyleSheet(first_button_style)
        # 为btn_dashboard添加鼠标事件，使其可以用于拖拽窗口
        self.btn_dashboard.mousePressEvent = self.dashboard_mouse_press_event
        self.btn_dashboard.mouseMoveEvent = self.dashboard_mouse_move_event
        self.btn_dashboard.mouseReleaseEvent = self.dashboard_mouse_release_event
        self.btn_info.setStyleSheet(button_style)
        self.btn_info.setCursor(Qt.PointingHandCursor)
        self.btn_bill.setStyleSheet(button_style)
        self.btn_bill.setCursor(Qt.PointingHandCursor)
        self.btn_electricity.setStyleSheet(button_style)
        self.btn_electricity.setCursor(Qt.PointingHandCursor)
        self.btn_author.setStyleSheet(button_style)
        self.btn_author.setCursor(Qt.PointingHandCursor)
        self.btn_xxt.setStyleSheet(button_style)
        self.btn_xxt.setCursor(Qt.PointingHandCursor)
        
        # 添加点击事件日志记录
        self.btn_info.clicked.connect(self.on_info_clicked)
        self.btn_bill.clicked.connect(self.on_bill_clicked)
        self.btn_electricity.clicked.connect(self.on_electricity_clicked)
        self.btn_author.clicked.connect(self.on_author_clicked)
        self.btn_xxt.clicked.connect(self.on_xxt_clicked)
        
        # 添加到布局
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_info)
        layout.addWidget(self.btn_bill)
        layout.addWidget(self.btn_electricity)
        layout.addWidget(self.btn_xxt)  # 添加学习通按钮
        
        # 添加弹性空间，使author按钮位于底部
        layout.addStretch(1)
        layout.addWidget(self.btn_author)
        
        self.setLayout(layout)
        
        # 记录UI设置完成
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "UI设置完成")
        except Exception:
            pass

    def on_info_clicked(self):
        """个人信息按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "按钮点击", "个人信息按钮")
        except Exception:
            pass

    def on_bill_clicked(self):
        """账单按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "按钮点击", "账单按钮")
        except Exception:
            pass
            
        # 不在这里触发查询，而是交由MainWindow处理
        # 只在第一次或用户点击刷新按钮时查询

    def on_electricity_clicked(self):
        """电费按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "按钮点击", "电费按钮")
        except Exception:
            pass
            
    def on_author_clicked(self):
        """作者信息按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "按钮点击", "作者信息按钮")
        except Exception:
            pass
            
    def on_xxt_clicked(self):
        """学习通按钮点击事件"""
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBar", "按钮点击", "学习通按钮")
        except Exception:
            pass

    def dashboard_mouse_press_event(self, event):
        """dashboard按钮鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
        # 不调用super().mousePressEvent，因为这是动态添加的方法

    def dashboard_mouse_move_event(self, event):
        """dashboard按钮鼠标移动事件"""
        if hasattr(self, 'drag_start_position') and event.buttons() & Qt.LeftButton:
            # 移动整个窗口
            window = self.window()
            delta = event.globalPosition().toPoint() - self.drag_start_position
            window.move(window.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()
        # 不调用super().mouseMoveEvent，因为这是动态添加的方法

    def dashboard_mouse_release_event(self, event):
        """dashboard按钮鼠标释放事件，清除拖拽状态"""
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
        # 不调用super().mouseReleaseEvent，因为这是动态添加的方法

    def set_sidebar_bill(self, sidebar_bill):
        """设置账单侧边栏引用"""
        self.sidebar_bill = sidebar_bill