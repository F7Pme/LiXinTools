from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, 
                            QHBoxLayout, QStackedWidget, QTabBar, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from gui.styles import FontConfig, ColorPalette
from gui.MessageWindow import show_message
from bs4 import BeautifulSoup
import html
from utils.data_parser import DataParser

# 导入log_window为全局变量
global log_window
try:
    from gui.LoginWindow import log_window
except ImportError:
    log_window = None

class SideBarXxt(QWidget):
    def __init__(self):
        super().__init__()
        # 记录初始化
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBarXxt", "初始化")
        except Exception:
            pass
        
        # 初始化数据
        self.courses_data = []
        self.notices_data = []
        
        self.setup_ui()

    def setup_ui(self):
        # 设置样式
        self.setStyleSheet("""
            background: #FDFDFD;
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)  # 顶部对齐
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距以紧贴titlebar
        main_layout.setSpacing(0)  # 减少间距
        
        # 创建现代化选项卡
        tab_container = QFrame()
        tab_container.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #E0E0E0;
        """)
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用TabBar替代按钮
        self.tab_bar = QTabBar()
        self.tab_bar.setStyleSheet("""
            QTabBar {
                background-color: #F0F0F0;
                border-bottom: 1px solid #DDDDDD;
            }
            QTabBar::tab {
                background-color: #F0F0F0;
                color: #333333;
                min-width: 140px;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-right: 1px solid #DDDDDD;
                margin: 0;
            }
            QTabBar::tab:selected {
                color: #0066CC;
                background-color: #FFFFFF;
                border-top: 3px solid #0066CC;
                padding-top: 7px;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E5E5;
            }
            QTabBar::tab:last {
                border-right: none;
            }
        """)
        
        # 添加选项卡
        self.tab_bar.addTab("课程列表")
        self.tab_bar.addTab("作业和通知")
        
        # 添加选项卡变化事件
        self.tab_bar.currentChanged.connect(self.handle_tab_changed)
        
        tab_layout.addWidget(self.tab_bar, 1, Qt.AlignLeft)
        main_layout.addWidget(tab_container)
        
        # 创建堆叠小部件用于切换内容
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")
        
        # 创建课程和通知内容区域
        self.courses_display = QTextEdit()
        self.notices_display = QTextEdit()
        
        # 设置两个文本区域样式
        text_style = """
            QTextEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                padding: 20px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F0F0F0;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #AAAAAA;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888888;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        self.courses_display.setStyleSheet(text_style)
        self.notices_display.setStyleSheet(text_style)
        
        # 设置为只读
        self.courses_display.setReadOnly(True)
        self.notices_display.setReadOnly(True)
        
        # 设置字体
        font = FontConfig.get_high_quality_font("Microsoft YaHei", pixel_size=14)
        self.courses_display.setFont(font)
        self.notices_display.setFont(font)
        
        # 设置初始内容
        init_html = "<html><body><div style='text-align:center; margin-top:50px; color:#000000; font-size:16px;'>学习通内容将在登录后显示</div></body></html>"
        self.courses_display.setHtml(init_html)
        self.notices_display.setHtml(init_html)
        
        # 设置最小高度
        self.courses_display.setMinimumHeight(300)
        self.notices_display.setMinimumHeight(300)
        
        # 添加到堆叠小部件
        self.stacked_widget.addWidget(self.courses_display)
        self.stacked_widget.addWidget(self.notices_display)
        
        # 添加堆叠小部件到主布局
        main_layout.addWidget(self.stacked_widget, 1)  # 添加拉伸因子，使内容区域填充剩余空间
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 记录UI设置完成
        try:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_ui_event("SideBarXxt", "UI设置完成")
        except Exception:
            pass
    
    def handle_tab_changed(self, index):
        """处理选项卡切换事件"""
        if index == 0:
            self.show_courses_tab()
        else:
            self.show_notices_tab()
    
    def show_courses_tab(self):
        """显示课程列表选项卡"""
        self.tab_bar.setCurrentIndex(0)
        self.stacked_widget.setCurrentIndex(0)
        
        # 不要在这里调用update_courses_data，避免递归调用
        # 当点击按钮时，仅切换视图，不重新加载数据
    
    def show_notices_tab(self):
        """显示作业通知选项卡"""
        self.tab_bar.setCurrentIndex(1)
        self.stacked_widget.setCurrentIndex(1)
        
        # 不要在这里调用update_notices，避免递归调用
        # 当点击按钮时，仅切换视图，不重新加载数据
    
    def update_content(self, html_content, is_success=True):
        """更新学习通内容"""
        try:
            # 更新当前显示的文本内容
            if self.stacked_widget.currentIndex() == 0:
                self.courses_display.setHtml(html_content)
            else:
                self.notices_display.setHtml(html_content)
            
            # 记录更新事件
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_ui_event("SideBarXxt", "内容更新", 
                                           f"状态: {'成功' if is_success else '失败'}")
            except Exception:
                pass
                
        except Exception as e:
            # 记录错误
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"更新学习通内容失败: {str(e)}", "ERROR")
            except Exception:
                pass
                
    def update_courses(self, html_content, is_success=True):
        """解析并展示学习通课程列表"""
        try:
            if not is_success:
                self.courses_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>获取课程列表失败</div></body></html>")
                return
            
            # 解析HTML获取课程列表
            courses = DataParser.parse_xxt_courses(html_content)
            
            # 保存课程数据
            self.courses_data = courses
            
            if not courses:
                self.courses_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#000000; font-size:16px;'>未找到课程信息</div></body></html>")
                return
            
            # 构建课程列表HTML
            courses_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #F5F7FA;
                        font-family: 'Microsoft YaHei', sans-serif;
                        padding: 15px;
                        margin: 0;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                    }
                    .course-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                        gap: 20px;
                    }
                    .course-item {
                        border: none;
                        border-radius: 12px;
                        overflow: hidden;
                        background-color: #FFFFFF;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                        transition: all 0.3s ease;
                        position: relative;
                    }
                    .course-item:hover {
                        box-shadow: 0 8px 18px rgba(0,120,215,0.15);
                        transform: translateY(-5px);
                    }
                    .course-header {
                        padding: 15px;
                        background: #F0F7FF;
                        border-bottom: 1px solid #E0E8F0;
                    }
                    .course-title {
                        font-size: 18px;
                        font-weight: bold;
                        margin: 0;
                        color: #000000;
                        line-height: 1.4;
                    }
                    .course-body {
                        padding: 15px;
                    }
                    .course-info {
                        font-size: 14px;
                        color: #000000;
                        margin-bottom: 8px;
                        display: flex;
                        align-items: center;
                    }
                    .course-info:before {
                        content: '•';
                        color: #0066CC;
                        margin-right: 8px;
                        font-weight: bold;
                    }
                    .course-link {
                        font-size: 13px;
                        color: #0066CC;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 10px;
                        padding: 5px 0;
                        font-weight: bold;
                        transition: color 0.2s;
                    }
                    .course-link:hover {
                        color: #004C99;
                    }
                    .course-time {
                        position: absolute;
                        top: 15px;
                        right: 15px;
                        background-color: #0066CC;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        color: white;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="course-grid">
            """
            
            for course in courses:
                try:
                    # 提取年份学期信息
                    time_info = html.escape(course.get('time', '未知学期'))
                    
                    # 构建课程项HTML
                    courses_html += f"""
                    <div class="course-item">
                        <div class="course-header">
                            <h2 class="course-title">{html.escape(course.get('name', '未知课程'))}</h2>
                            <div class="course-time">{time_info}</div>
                        </div>
                        <div class="course-body">
                            <div class="course-info">学校: {html.escape(course.get('school', '未知学校'))}</div>
                            <div class="course-info">教师: {html.escape(course.get('teacher', '未知教师'))}</div>
                            <a href="{html.escape(course.get('link', '#'))}" class="course-link">查看课程详情 →</a>
                        </div>
                    </div>
                    """
                except Exception as e:
                    courses_html += f"""
                    <div class="course-item">
                        <div class="course-header">
                            <h2 class="course-title">解析课程信息出错</h2>
                        </div>
                        <div class="course-body">
                            <div class="course-info">错误信息: {html.escape(str(e))}</div>
                        </div>
                    </div>
                    """
            
            courses_html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 更新显示并切换到课程选项卡
            self.courses_display.setHtml(courses_html)
            self.show_courses_tab()
            
            # 记录更新事件
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_ui_event("SideBarXxt", "课程列表更新", 
                                           f"共{len(courses)}门课程")
            except Exception:
                pass
                
        except Exception as e:
            # 记录错误
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"解析课程列表失败: {str(e)}", "ERROR")
            except Exception:
                pass
            
            # 在文本框中显示错误信息
            error_html = f"<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>解析课程列表失败: {html.escape(str(e))}</div></body></html>"
            self.courses_display.setHtml(error_html)
    
    def update_notices(self, notices, is_success=True):
        """展示学习通作业和通知列表
        
        Args:
            notices (list): 通知列表对象
            is_success (bool): 是否成功获取通知
        """
        try:
            if not is_success:
                self.notices_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>获取通知列表失败</div></body></html>")
                return
            
            # 保存通知数据
            self.notices_data = notices
            
            if not notices:
                self.notices_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#000000; font-size:16px;'>未找到通知信息</div></body></html>")
                return
            
            # 分类通知和作业
            homework_list = [n for n in notices if n.get("type") == "作业"]
            notice_list = [n for n in notices if n.get("type") == "通知"]
            
            # 构建通知列表HTML
            notices_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #F5F7FA;
                        font-family: 'Microsoft YaHei', sans-serif;
                        padding: 15px;
                        margin: 0;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                    }
                    .tabs {
                        display: flex;
                        margin-bottom: 20px;
                        background-color: #F0F0F0;
                        border-radius: 0;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }
                    .tab {
                        padding: 12px 20px;
                        font-size: 14px;
                        cursor: pointer;
                        color: #333333;
                        text-align: center;
                        flex: 1;
                        transition: all 0.2s ease;
                        position: relative;
                        border-right: 1px solid #DDDDDD;
                    }
                    .tab:last-child {
                        border-right: none;
                    }
                    .tab.active {
                        color: #0066CC;
                        background-color: #FFFFFF;
                    }
                    .tab.active:after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 3px;
                        background: #0066CC;
                    }
                    .tab:hover:not(.active) {
                        background-color: #E5E5E5;
                    }
                    .tab-content {
                        display: none;
                    }
                    .tab-content.active {
                        display: block;
                    }
                    .notice-list {
                        display: flex;
                        flex-direction: column;
                        gap: 15px;
                    }
                    .notice-item, .homework-item {
                        border: none;
                        border-radius: 8px;
                        padding: 20px;
                        background-color: #FFFFFF;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                        transition: all 0.3s ease;
                    }
                    .notice-item:hover, .homework-item:hover {
                        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
                        transform: translateY(-3px);
                    }
                    .notice-title, .homework-title {
                        font-size: 16px;
                        font-weight: bold;
                        margin-bottom: 10px;
                        color: #000000;
                    }
                    .homework-title {
                        color: #107C10;
                    }
                    .notice-time, .homework-time {
                        font-size: 13px;
                        color: #000000;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                    }
                    .notice-time:before, .homework-time:before {
                        content: '🕒';
                        margin-right: 8px;
                        font-size: 14px;
                    }
                    .notice-content, .homework-content {
                        font-size: 15px;
                        color: #000000;
                        line-height: 1.5;
                        margin-bottom: 10px;
                        padding: 10px;
                        background-color: #F9F9F9;
                        border-radius: 8px;
                    }
                    .homework-link {
                        font-size: 14px;
                        color: #107C10;
                        text-decoration: none;
                        margin-top: 15px;
                        display: inline-block;
                        font-weight: bold;
                        padding: 8px 15px;
                        background-color: #F0F7F0;
                        border-radius: 4px;
                        transition: all 0.2s;
                    }
                    .homework-link:hover {
                        background-color: #E0F0E0;
                    }
                    .badge {
                        display: inline-block;
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-size: 12px;
                        color: white;
                        margin-left: 8px;
                    }
                    .badge-homework {
                        background-color: #107C10;
                    }
                    .badge-notice {
                        background-color: #0066CC;
                    }
                    .empty-message {
                        text-align: center;
                        padding: 40px 0;
                        color: #000000;
                        font-size: 16px;
                    }
                </style>
                <script>
                function switchTab(tabName) {
                    // 隐藏所有内容
                    var contents = document.getElementsByClassName('tab-content');
                    for (var i = 0; i < contents.length; i++) {
                        contents[i].className = contents[i].className.replace(' active', '');
                    }
                    
                    // 移除所有标签的active状态
                    var tabs = document.getElementsByClassName('tab');
                    for (var i = 0; i < tabs.length; i++) {
                        tabs[i].className = tabs[i].className.replace(' active', '');
                    }
                    
                    // 显示选定的内容和标签
                    document.getElementById(tabName).className += ' active';
                    document.getElementById('tab-' + tabName).className += ' active';
                }
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="tabs">
            """
            
            # 添加标签和数量，将f-string分开处理
            homework_tab = f'<div id="tab-homework" class="tab active" onclick="switchTab(\'homework\')">作业 <span class="badge badge-homework">{len(homework_list)}</span></div>'
            notice_tab = f'<div id="tab-notices" class="tab" onclick="switchTab(\'notices\')">通知 <span class="badge badge-notice">{len(notice_list)}</span></div>'
            notices_html += homework_tab + notice_tab
            
            notices_html += """
                    </div>
                    
                    <div id="homework" class="tab-content active">
                        <div class="notice-list">
            """
            
            # 添加作业列表
            if homework_list:
                for hw in homework_list:
                    try:
                        notices_html += f"""
                        <div class="homework-item">
                            <div class="homework-title">{html.escape(hw.get('title', '未知作业'))}</div>
                            <div class="homework-time">发布时间: {html.escape(hw.get('send_time', '未知时间'))}</div>
                            <div class="homework-content">{hw.get('content', '无作业内容')}</div>
                        """
                        
                        # 如果有作业链接
                        if hw.get('work_url'):
                            notices_html += f"""
                            <a href="{html.escape(hw.get('work_url', ''))}" class="homework-link" target="_blank">查看作业详情 →</a>
                            """
                            
                        notices_html += """
                        </div>
                        """
                    except Exception as e:
                        notices_html += f"""
                        <div class="homework-item">
                            <div class="homework-title">解析作业信息出错</div>
                            <div class="homework-content">错误信息: {html.escape(str(e))}</div>
                        </div>
                        """
            else:
                notices_html += """
                <div class="empty-message">暂无作业信息</div>
                """
            
            notices_html += """
                        </div>
                    </div>
                    
                    <div id="notices" class="tab-content">
                        <div class="notice-list">
            """
            
            # 添加通知列表
            if notice_list:
                for notice in notice_list:
                    try:
                        notices_html += f"""
                        <div class="notice-item">
                            <div class="notice-title">{html.escape(notice.get('title', '未知通知'))}</div>
                            <div class="notice-time">发布时间: {html.escape(notice.get('send_time', '未知时间'))}</div>
                            <div class="notice-content">{notice.get('content', '无通知内容')}</div>
                        </div>
                        """
                    except Exception as e:
                        notices_html += f"""
                        <div class="notice-item">
                            <div class="notice-title">解析通知信息出错</div>
                            <div class="notice-content">错误信息: {html.escape(str(e))}</div>
                        </div>
                        """
            else:
                notices_html += """
                <div class="empty-message">暂无通知信息</div>
                """
            
            notices_html += """
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 更新显示并切换到通知选项卡
            self.notices_display.setHtml(notices_html)
            self.show_notices_tab()
            
            # 记录更新事件
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_ui_event("SideBarXxt", "通知列表更新", 
                                           f"共{len(notices)}条信息({len(homework_list)}作业/{len(notice_list)}通知)")
            except Exception:
                pass
                
        except Exception as e:
            # 记录错误
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"显示通知列表失败: {str(e)}", "ERROR")
            except Exception:
                pass
            
            # 在文本框中显示错误信息
            error_html = f"<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>显示通知列表失败: {html.escape(str(e))}</div></body></html>"
            self.notices_display.setHtml(error_html)
            
    def update_courses_data(self, courses, is_success=True):
        """直接展示学习通课程列表对象
        
        Args:
            courses (list): 课程列表对象
            is_success (bool): 是否成功获取课程
        """
        try:
            if not is_success:
                self.courses_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>获取课程列表失败</div></body></html>")
                return
            
            # 保存课程数据
            self.courses_data = courses
            
            if not courses:
                self.courses_display.setHtml("<html><body><div style='text-align:center; margin-top:50px; color:#000000; font-size:16px;'>未找到课程信息</div></body></html>")
                return
            
            # 构建课程列表HTML
            courses_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #F5F7FA;
                        font-family: 'Microsoft YaHei', sans-serif;
                        padding: 15px;
                        margin: 0;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                    }
                    .course-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                        gap: 20px;
                    }
                    .course-item {
                        border: none;
                        border-radius: 12px;
                        overflow: hidden;
                        background-color: #FFFFFF;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                        transition: all 0.3s ease;
                        position: relative;
                    }
                    .course-item:hover {
                        box-shadow: 0 8px 18px rgba(0,120,215,0.15);
                        transform: translateY(-5px);
                    }
                    .course-header {
                        padding: 15px;
                        background: #F0F7FF;
                        border-bottom: 1px solid #E0E8F0;
                    }
                    .course-title {
                        font-size: 18px;
                        font-weight: bold;
                        margin: 0;
                        color: #000000;
                        line-height: 1.4;
                    }
                    .course-body {
                        padding: 15px;
                    }
                    .course-info {
                        font-size: 14px;
                        color: #000000;
                        margin-bottom: 8px;
                        display: flex;
                        align-items: center;
                    }
                    .course-info:before {
                        content: '•';
                        color: #0066CC;
                        margin-right: 8px;
                        font-weight: bold;
                    }
                    .course-link {
                        font-size: 13px;
                        color: #0066CC;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 10px;
                        padding: 5px 0;
                        font-weight: bold;
                        transition: color 0.2s;
                    }
                    .course-link:hover {
                        color: #004C99;
                    }
                    .course-time {
                        position: absolute;
                        top: 15px;
                        right: 15px;
                        background-color: #0066CC;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        color: white;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="course-grid">
            """
            
            for course in courses:
                try:
                    # 提取年份学期信息
                    time_info = html.escape(course.get('time', '未知学期'))
                    
                    # 构建课程项HTML
                    courses_html += f"""
                    <div class="course-item">
                        <div class="course-header">
                            <h2 class="course-title">{html.escape(course.get('name', '未知课程'))}</h2>
                            <div class="course-time">{time_info}</div>
                        </div>
                        <div class="course-body">
                            <div class="course-info">学校: {html.escape(course.get('school', '未知学校'))}</div>
                            <div class="course-info">教师: {html.escape(course.get('teacher', '未知教师'))}</div>
                            <a href="{html.escape(course.get('link', '#'))}" class="course-link">查看课程详情 →</a>
                        </div>
                    </div>
                    """
                except Exception as e:
                    courses_html += f"""
                    <div class="course-item">
                        <div class="course-header">
                            <h2 class="course-title">解析课程信息出错</h2>
                        </div>
                        <div class="course-body">
                            <div class="course-info">错误信息: {html.escape(str(e))}</div>
                        </div>
                    </div>
                    """
            
            courses_html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 更新显示并切换到课程选项卡
            self.courses_display.setHtml(courses_html)
            self.show_courses_tab()
            
            # 记录更新事件
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_ui_event("SideBarXxt", "课程列表更新", 
                                           f"共{len(courses)}门课程")
            except Exception:
                pass
                
        except Exception as e:
            # 记录错误
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"显示课程列表失败: {str(e)}", "ERROR")
            except Exception:
                pass
            
            # 在文本框中显示错误信息
            error_html = f"<html><body><div style='text-align:center; margin-top:50px; color:#D83B01; font-size:16px;'>显示课程列表失败: {html.escape(str(e))}</div></body></html>"
            self.courses_display.setHtml(error_html) 