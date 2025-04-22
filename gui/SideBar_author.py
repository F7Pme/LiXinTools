from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from gui.styles import FontConfig

# 导入log_window为全局变量
global log_window
try:
    from gui.LoginWindow import log_window
except ImportError:
    log_window = None

class SideBarAuthor(QWidget):
    def __init__(self):
        super().__init__()
        # 记录初始化
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBarAuthor", "初始化")
        except Exception:
            pass
        
        self.setup_ui()

    def setup_ui(self):
        # 设置样式
        self.setStyleSheet("""
            background: #FDFDFD;
        """)
        
        # 创建主布局 - 更紧凑的边距
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(8)  # 增加间距防止文本被遮挡
        main_layout.setContentsMargins(20, 15, 10, 10)  # 减小顶部和左侧边距
        
        # 创建标题 - 参照账单查询的样式
        title_label = QLabel("作者信息")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        main_layout.addWidget(title_label)
        
        # 创建内容区域（不使用卡片边框）
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            background: white;
            padding: 8px 0px;  /* 增加上下内边距 */
        """)
        
        # 内容区域布局
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(6)  # 增加行间距避免文本被遮挡
        content_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        
        # 作者详细信息
        info_items = [
            ("作者:", "顾佳俊 上海立信会计金融学院 2023级金融科技5班"),
            ("作者微信:", "AL-0729-zK"),
            ("电子邮件:", "3298732438@qq.com"),
            ("版权信息:", "© 2024-2025 顾佳俊 保留所有权利"),
            ("软件版本:", "1.0.0 alpha 测试版"),
            ("项目地址:", "https://github.com/xxx(暂未开源)")
        ]
        
        # 添加信息项 - 使用更小字体和间距
        for label, value in info_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(3)  # 减少标签和值之间的间距
            
            # 标签 - 使用更小字体
            label_widget = QLabel(label)
            label_font = FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=13)
            label_widget.setFont(label_font)
            label_widget.setMinimumWidth(70)  # 减小最小宽度
            # 移除最大高度限制以防止文本被截断
            label_widget.setStyleSheet("color: #000000;")
            
            # 值 - 使用更小字体
            value_widget = QLabel(value)
            value_font = FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=13)
            value_widget.setFont(value_font)
            value_widget.setWordWrap(True)
            value_widget.setStyleSheet("color: #000000;")
            
            if "https://" in value:
                value_widget.setStyleSheet("color: #0078D4; text-decoration: underline;")
                value_widget.setCursor(Qt.PointingHandCursor)
                
            # 添加到布局，使用小的垂直边距
            item_layout.setContentsMargins(0, 2, 0, 2)  # 添加少量上下边距
            item_layout.addWidget(label_widget)
            item_layout.addWidget(value_widget, 1)
            content_layout.addLayout(item_layout)
            
        # 添加版权声明 - 更小
        copyright_label = QLabel("本程序是免费软件，欢迎合法使用和传播。")
        copyright_font = FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=11)
        copyright_label.setFont(copyright_font)
        copyright_label.setAlignment(Qt.AlignLeft)
        copyright_label.setStyleSheet("color: #000000;")
        
        # 添加组件到主布局 - 减少版权声明与内容间的距离
        main_layout.addWidget(content_widget)
        main_layout.addSpacing(4)  # 增加间距以避免遮挡
        main_layout.addWidget(copyright_label)
        main_layout.addStretch(1)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 记录UI设置完成
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBarAuthor", "UI设置完成")
        except Exception:
            pass 