from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from gui.styles import FontConfig
from gui.LoginWindow import log_window

class SideBarInfo(QWidget):
    def __init__(self):
        super().__init__()
        if log_window:
            log_window.log_ui_event("SideBarInfo", "初始化")
        self.setup_ui()

    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 10, 10) 

        # 个人信息标题
        self.personal_title = QLabel("个人信息")
        self.personal_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        self.personal_title.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", size=18, bold=True))
        layout.addWidget(self.personal_title)

        # 个人信息内容
        self.name_label = self._create_info_label("姓名: ")
        self.id_label = self._create_info_label("学工号: ")
        self.balance_label = self._create_info_label("账户余额: ")
        layout.addWidget(self.name_label)
        layout.addWidget(self.id_label)
        layout.addWidget(self.balance_label)

        # 学业信息标题
        self.school_title = QLabel("学业信息")
        self.school_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4; margin-top: 15px;")
        self.school_title.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", size=18, bold=True))
        layout.addWidget(self.school_title)

        # 学业信息内容
        self.school_label = self._create_info_label("学校: ")
        self.major_label = self._create_info_label("专业: ")
        self.class_label = self._create_info_label("班级: ")
        layout.addWidget(self.school_label)
        layout.addWidget(self.major_label)
        layout.addWidget(self.class_label)

        self.setLayout(layout)
        
        if log_window:
            log_window.log_ui_event("SideBarInfo", "UI设置完成")

    def _create_info_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 16px; color: #333333; margin-left: 5px;")
        label.setFont(FontConfig.get_high_quality_font("Microsoft YaHei", size=16))
        return label

    def update_data(self, data):
        """外部接口：更新显示数据"""
        if log_window:
            log_window.log_data_event("用户信息", "更新", "更新个人与学业信息")
            
        if 'personal' in data:
            personal = data['personal']
            self.name_label.setText(f"姓名: {personal.get('姓名', '')}")
            self.id_label.setText(f"学工号: {personal.get('学工号', '')}")
            self.balance_label.setText(f"账户余额: ￥{personal.get('账户余额', '0.00')}")
            
            if log_window:
                log_window.log_data_event("个人信息", "更新", f"姓名: {personal.get('姓名', '')}, 学工号: {personal.get('学工号', '')}")
        
        if 'school' in data:
            school = data['school']
            self.school_label.setText(f"学校: {school.get('学校', '')}")
            self.major_label.setText(f"专业: {school.get('专业', '')}")
            self.class_label.setText(f"班级: {school.get('班级', '')}")
            
            if log_window:
                log_window.log_data_event("学业信息", "更新", f"学校: {school.get('学校', '')}, 专业: {school.get('专业', '')}")
                
        if log_window:
            log_window.log_ui_event("SideBarInfo", "数据更新完成")
