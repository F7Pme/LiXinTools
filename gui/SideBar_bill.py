from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                              QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QAbstractItemView, QApplication, QTextEdit)
from PySide6.QtCore import Qt, Signal, QObject, QThread, QTimer, QEvent
from PySide6.QtGui import QIntValidator
from utils.query_bill import BillQuery
from utils.analysis_bill import BillAnalysisWorker, BillAnalyzer
from gui.LoadWindow import show_loading
from gui.styles import FontConfig
from config.config import Config

# 确保log_window可以被所有类使用
global log_window
from gui.LoginWindow import log_window

class BillQueryWorker(QObject):
    """账单查询工作线程信号对象"""
    finished = Signal(list, int)
    
    def __init__(self, bill_query, page):
        super().__init__()
        self.bill_query = bill_query
        self.page = page
        
    def run(self):
        """执行查询操作"""
        # 重新导入log_window以确保获取最新实例
        from gui.LoginWindow import log_window
        
        # 尝试记录日志，处理log_window可能为None的情况
        try:
            if log_window:
                log_window.log_network_event("账单查询", "查询账单数据", f"页码: {self.page}")
        except Exception:
            pass
        
        try:
            items, total_pages = self.bill_query.query_page(self.page)
            
            try:
                if log_window:
                    log_window.log_network_event("账单查询", "查询成功", f"获取到 {len(items)} 条记录，总页数: {total_pages}")
            except Exception:
                pass
            
            self.finished.emit(items, total_pages)
        except Exception as e:
            try:
                if log_window:
                    log_window.log_network_event("账单查询", "查询失败", f"错误: {str(e)}", "ERROR")
            except Exception:
                pass
            # 返回空结果防止崩溃
            self.finished.emit([], 0)

class SideBarBill(QWidget):
    def __init__(self):
        super().__init__()
        self.bill_query = None
        self.current_page = 1
        self.total_pages = 1
        self.loading_indicator = None
        self.columns_sized = False
        self.column_widths = [40, 150, 200, 120, 80]  # 预设各列宽度：序号、时间、交易类型、金额、状态
        self.has_template = False  # 是否已有表格模板
        self.template_height = 250  # 模板表格高度默认值
        self.template_widths = self.column_widths.copy()  # 模板列宽默认值
        self.analysis_thread = None  # 账单分析线程
        self.analysis_worker = None  # 账单分析工作对象
        
        # 新增：缓存全部账单数据
        self.all_bills_cache = []  # 缓存所有账单数据
        self.has_all_bills = False  # 是否已查询全部账单
        self.cached_page_size = 10  # 每页显示的数据条数
        
        self.setup_ui()

    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 10, 10)

        # 标题区域布局更改为水平布局
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignLeft)
        title_layout.setSpacing(15)
        
        # 标题
        self.bill_title = QLabel("账单查询")
        self.bill_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        title_layout.addWidget(self.bill_title)
        
        # 添加一个标签显示分析结果摘要
        self.analysis_summary = QLabel("")
        self.analysis_summary.setStyleSheet("font-size: 14px; color: #000000;")
        title_layout.addWidget(self.analysis_summary)
        
        # 添加标题布局到主布局
        layout.addLayout(title_layout)
        
        # 创建表格容器用于确保对齐 - 改为垂直布局
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)  # 将上边距从10改为0，上移整个容器
        table_layout.setSpacing(0)  # 消除组件之间的空白
        
        # 添加分析结果显示区域到表格容器内
        self.analysis_result_area = QTextEdit()
        self.analysis_result_area.setReadOnly(True)
        self.analysis_result_area.setFixedHeight(0)  # 初始高度为0，避免占用空间
        self.analysis_result_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 默认隐藏水平滚动条
        self.analysis_result_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)    # 默认隐藏垂直滚动条
        
        # 创建一个事件过滤器，用于处理鼠标进入和离开事件
        class ScrollBarEventFilter(QObject):
            def __init__(self, parent=None):
                super().__init__(parent)
                
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Enter:
                    # 鼠标进入时显示滚动条
                    obj.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                    obj.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                    return True
                elif event.type() == QEvent.Leave:
                    # 鼠标离开时隐藏滚动条
                    obj.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    obj.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    return True
                return False
                
        # 创建并安装事件过滤器
        self.scroll_filter = ScrollBarEventFilter(self)
        self.analysis_result_area.installEventFilter(self.scroll_filter)
        
        self.analysis_result_area.setStyleSheet("""
            QTextEdit {
                background-color: #F0F8FF;
                color: #333333;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #BBBBBB;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                height: 8px;
                background: transparent;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #BBBBBB;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.analysis_result_area.setVisible(False)  # 初始时隐藏
        table_layout.addWidget(self.analysis_result_area)
        
        # 账单表格区域
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(5)  # 序号、时间、类型、金额、状态
        self.bill_table.setHorizontalHeaderLabels(["序号", "时间", "交易类型", "金额", "状态"])
        
        # 设置表格初始大小为紧凑尺寸
        self.bill_table.setFixedHeight(250)  # 限制初始高度
        
        # 禁用表头点击排序
        self.bill_table.setSortingEnabled(False)
        
        # 应用预设列宽
        for col, width in enumerate(self.column_widths):
            self.bill_table.setColumnWidth(col, width)
        
        # 修改表格的列宽设置方式为固定宽度，防止自动扩展
        for col in range(5):
            self.bill_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
        
        # 禁止通过表头调整列宽
        self.bill_table.horizontalHeader().setSectionsClickable(False)
        self.bill_table.horizontalHeader().setSectionsMovable(False)
        
        # 设置更紧凑的表格样式，移除外部框架
        self.bill_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: black;
                border: none;  /* 移除边框 */
                gridline-color: #F0F0F0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #333333;
                padding: 3px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
            QTableWidget::item {
                color: black;
                padding: 2px;
                border-bottom: 1px solid #F0F0F0;
            }
            /* 移除外部滚动条边框 */
            QTableWidget QScrollBar {
                border: none;
            }
        """)
        
        # 设置表格更紧凑
        self.bill_table.verticalHeader().setDefaultSectionSize(25)  # 设置更小的行高
        self.bill_table.setWordWrap(False)  # 禁止文本换行
        self.bill_table.setFrameShape(QTableWidget.NoFrame)  # 明确指定无边框
        self.bill_table.setShowGrid(True)  # 保留内部网格线
        
        # 设置表格为只读
        self.bill_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置整行选择
        self.bill_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 隐藏行号
        self.bill_table.verticalHeader().setVisible(False)
        
        # 将表格添加到容器中央
        table_layout.addWidget(self.bill_table)
        
        # 添加表格容器到主布局
        layout.addWidget(table_container)
        
        # 创建控件组
        control_group = QWidget()
        control_group_layout = QHBoxLayout(control_group)
        control_group_layout.setContentsMargins(0, 0, 0, 0)
        control_group_layout.setSpacing(10)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(60, 30)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #499DDD;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.handle_query)
        
        # 添加查询全部账单并分析按钮
        self.analyze_btn = QPushButton("查询全部账单并分析")
        self.analyze_btn.setFixedSize(150, 30)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A751A;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2A852A;
            }
            QPushButton:pressed {
                background-color: #0A650A;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(self.handle_analyze)
        
        # 上一页按钮
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setFixedSize(60, 30)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                color: #000000;
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E6E6E6;
            }
            QPushButton:disabled {
                color: #888888;
                border: 1px solid #DDDDDD;
            }
        """)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_page)
        
        # 页码显示
        self.page_info_label = QLabel("页码: 0/0")
        self.page_info_label.setFixedHeight(30)
        self.page_info_label.setStyleSheet("color: #333333; font-size: 14px;")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        
        # 下一页按钮
        self.next_btn = QPushButton("下一页")
        self.next_btn.setFixedSize(60, 30)
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                color: #000000;
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E6E6E6;
            }
            QPushButton:disabled {
                color: #888888;
                border: 1px solid #DDDDDD;
            }
        """)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_page)
        
        # 页码输入框
        self.page_input = QLineEdit()
        self.page_input.setFixedSize(40, 30)
        self.page_input.setValidator(QIntValidator(1, 9999))  # 只允许输入数字
        self.page_input.setPlaceholderText("页码")
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 3px;
                color: black;
            }
        """)
        
        # 跳转按钮
        self.goto_btn = QPushButton("跳转")
        self.goto_btn.setFixedSize(50, 30)
        self.goto_btn.setCursor(Qt.PointingHandCursor)
        self.goto_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                color: white;
                background-color: #0078D4;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1A88E0;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.goto_btn.clicked.connect(self.goto_page)
        
        # 将控件按顺序添加到控件组
        control_group_layout.addWidget(self.refresh_btn)
        control_group_layout.addWidget(self.analyze_btn)
        control_group_layout.addWidget(self.prev_btn)
        control_group_layout.addWidget(self.page_info_label)
        control_group_layout.addWidget(self.next_btn)
        control_group_layout.addWidget(self.page_input)
        control_group_layout.addWidget(self.goto_btn)
        
        # 创建控制面板来放置控件组，并确保与表格中线对齐
        self.control_container = QWidget()
        control_layout = QHBoxLayout(self.control_container)
        control_layout.setContentsMargins(0, 5, 190, 0)  # 顶部留5像素间距
        
  
        # 添加控件组并确保对齐
        control_layout.addWidget(control_group, 0, Qt.AlignHCenter)
        
        # 添加控制容器到主布局
        layout.addWidget(self.control_container)
        
        self.setLayout(layout)
        
        # 初始化状态
        self.update_page_controls()
        
        # 尝试从本地恢复模板
        self.load_template_from_local()
        
        # 如果已有模板，应用到初始表格
        if self.has_template:
            self.apply_template()
            # 清空表格并显示提示
            self.bill_table.setRowCount(0)
            self.bill_table.setRowCount(1)
            empty_item = QTableWidgetItem("请点击刷新按钮获取账单数据")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.bill_table.setItem(0, 0, empty_item)
            self.bill_table.setSpan(0, 0, 1, 5)  # 合并单元格以显示提示信息

    def set_bill_query(self, bill_query):
        """设置账单查询实例"""
        self.bill_query = bill_query

    def handle_query(self):
        """处理查询按钮点击"""
        if not self.bill_query:
            # 清空表格并显示错误信息
            self.bill_table.setRowCount(0)
            self.bill_table.setRowCount(1)
            error_item = QTableWidgetItem("账单查询服务未初始化")
            error_item.setTextAlignment(Qt.AlignCenter)
            self.bill_table.setItem(0, 0, error_item)
            self.bill_table.setSpan(0, 0, 1, 5)  # 合并单元格以显示错误信息
            return
            
        # 重置列宽调整标志，允许第一次加载时调整列宽
        self.columns_sized = False
        self.current_page = 1
        
        try:
            # 在查询前确保窗口已完全显示
            if self.window() and not self.window().isVisible():
                return
            
            # 防止非活动窗口查询导致错误
            if QApplication.activeWindow() != self.window():
                return
                
            self.query_bill_data()
            
        except Exception as e:
            # 查询出错时记录日志但不中断程序
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("账单查询启动异常", f"错误: {str(e)}", "ERROR")
            except Exception:
                pass

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            # 如果已有全部数据缓存，直接使用缓存
            if self.has_all_bills and self.all_bills_cache:
                self.display_cached_page(self.current_page)
            else:
                self.query_bill_data()

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            # 如果已有全部数据缓存，直接使用缓存
            if self.has_all_bills and self.all_bills_cache:
                self.display_cached_page(self.current_page)
            else:
                self.query_bill_data()
            
    def goto_page(self):
        """跳转到指定页"""
        try:
            page = int(self.page_input.text())
            if 1 <= page <= self.total_pages:
                self.current_page = page
                # 如果已有全部数据缓存，直接使用缓存
                if self.has_all_bills and self.all_bills_cache:
                    self.display_cached_page(self.current_page)
                else:
                    self.query_bill_data()
            else:
                # 输入的页码超出范围，清空输入
                self.page_input.clear()
        except ValueError:
            # 输入不是有效的数字，清空输入
            self.page_input.clear()

    def query_bill_data(self):
        """执行账单查询"""
        if not self.bill_query:
            return
        
        try:
            # 禁用分页按钮，防止用户重复点击
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.goto_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            
            # 清空表格并显示加载信息
            self.bill_table.setRowCount(0)
            self.bill_table.setRowCount(1)
            loading_item = QTableWidgetItem("正在加载账单数据...")
            loading_item.setTextAlignment(Qt.AlignCenter)
            self.bill_table.setItem(0, 0, loading_item)
            self.bill_table.setSpan(0, 0, 1, 5)  # 合并5个单元格以显示加载信息
            
            # 使用QTimer延迟显示加载指示器，避免窗口未完全显示时创建指示器
            QTimer.singleShot(50, self._show_loading_and_query)
            
        except Exception as e:
            # 发生异常时记录日志并恢复按钮状态
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("账单查询初始化异常", f"错误: {str(e)}", "ERROR")
            except Exception:
                pass
                
            # 恢复按钮状态
            self.goto_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            
    def _show_loading_and_query(self):
        """显示加载指示器并执行查询，在query_bill_data中通过Timer调用"""
        try:
            # 创建加载指示器前确保窗口可见
            if not self.window().isVisible():
                self.refresh_btn.setEnabled(True)
                return
                
            # 显示加载指示器 - 设置更宽的窗口大小以显示较长的文本
            loading_text = "正在加载账单数据..."
            self.loading_indicator = show_loading(self.window(), loading_text, width=300)
            
            # 创建查询工作线程
            self.thread = QThread()
            self.worker = BillQueryWorker(self.bill_query, self.current_page)
            self.worker.moveToThread(self.thread)
            
            # 连接信号
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_query_completed)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            # 启动线程
            self.thread.start()
            
        except Exception as e:
            # 如果创建加载指示器失败，也要恢复按钮状态
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("加载指示器创建失败", f"错误: {str(e)}", "ERROR")
            except Exception:
                pass
                
            # 恢复按钮状态
            self.goto_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)

    def on_query_completed(self, items, total_pages):
        """查询完成后的回调"""
        # 关闭加载指示器
        if self.loading_indicator:
            try:
                self.loading_indicator.close()
            except Exception:
                pass
            self.loading_indicator = None
        
        # 更新数据
        self.total_pages = total_pages
        self.update_bill_data(items, self.current_page, total_pages)
        self.update_page_controls()
        
        # 根据数据条数调整表格高度
        if self.bill_table.rowCount() > 0:
            # 计算适当的表格高度：标题行高 + 所有数据行的高度总和 + 一些边距
            header_height = self.bill_table.horizontalHeader().height()
            total_row_height = self.bill_table.rowCount() * self.bill_table.verticalHeader().defaultSectionSize()
            proper_height = header_height + total_row_height + 2  # 加2像素作为边距
            self.bill_table.setFixedHeight(min(proper_height, 300))  # 设置最大高度为300像素
            
            # 如果是第一页且没有模板，保存当前表格大小作为模板
            if self.current_page == 1 and not self.has_template:
                self.save_template()
        
        # 重新启用按钮
        if self.total_pages > 0:
            self.goto_btn.setEnabled(True)
            self.page_input.setEnabled(True)
            
            # 根据页码启用前进后退按钮
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
        else:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.goto_btn.setEnabled(False)
            self.page_input.setEnabled(False)
            
        # 恢复刷新按钮
        self.refresh_btn.setEnabled(True)

    def update_page_controls(self):
        """更新分页控制按钮状态"""
        # 更新页码信息
        self.page_info_label.setText(f"页码: {self.current_page}/{self.total_pages}")
        
        # 根据页码控制按钮状态
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        
        # 如果总页数小于1，禁用分页相关控件
        if self.total_pages < 1:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.page_input.setEnabled(False)
            self.goto_btn.setEnabled(False)
        else:
            self.page_input.setEnabled(True)
            self.goto_btn.setEnabled(True)

    def update_bill_data(self, items, current_page, total_pages):
        """更新账单数据表格"""
        # 保存当前表格高度
        current_height = self.bill_table.height()
        
        # 清空表格
        self.bill_table.setRowCount(0)
        
        if not items:
            # 如果没有数据，显示提示信息
            self.bill_table.setRowCount(1)
            empty_item = QTableWidgetItem(f"第 {current_page} 页无账单记录")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.bill_table.setItem(0, 0, empty_item)
            self.bill_table.setSpan(0, 0, 1, 5)  # 合并单元格以显示提示信息
            self.has_data = False
            
            # 尝试应用模板
            if self.has_template:
                self.apply_template()
        else:
            # 填充表格数据
            self.has_data = True
            self.bill_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                # 创建序号单元格
                index_item = QTableWidgetItem(str(row + 1 + (current_page - 1) * 10))
                
                # 创建表格单元格并设置数据
                time_item = QTableWidgetItem(item['time'])
                type_item = QTableWidgetItem(item['type'])
                amount_item = QTableWidgetItem(item['amount'])
                status_item = QTableWidgetItem(item['status'])
                
                # 设置对齐方式
                index_item.setTextAlignment(Qt.AlignCenter)
                time_item.setTextAlignment(Qt.AlignCenter)
                type_item.setTextAlignment(Qt.AlignCenter)
                amount_item.setTextAlignment(Qt.AlignCenter)
                status_item.setTextAlignment(Qt.AlignCenter)
                
                # 确保单元格内容不自动换行
                index_item.setTextAlignment(Qt.AlignCenter | Qt.TextSingleLine)
                time_item.setTextAlignment(Qt.AlignCenter | Qt.TextSingleLine)
                type_item.setTextAlignment(Qt.AlignCenter | Qt.TextSingleLine)
                amount_item.setTextAlignment(Qt.AlignCenter | Qt.TextSingleLine)
                status_item.setTextAlignment(Qt.AlignCenter | Qt.TextSingleLine)
                
                # 将单元格添加到表格
                self.bill_table.setItem(row, 0, index_item)
                self.bill_table.setItem(row, 1, time_item)
                self.bill_table.setItem(row, 2, type_item)
                self.bill_table.setItem(row, 3, amount_item)
                self.bill_table.setItem(row, 4, status_item)
            
            # 如果有模板并且不是第一页，直接应用模板
            if self.has_template and current_page != 1:
                self.apply_template()
            else:
                # 在每次加载数据时调整列宽，而不仅仅是第一次
                # 先根据内容调整一次列宽
                self.bill_table.resizeColumnsToContents()
                
                # 保存调整后的列宽，但确保金额列始终保持足够宽度
                for col in range(5):
                    if col == 3:  # 金额列索引为3
                        # 获取自动调整后的宽度和预设宽度中的较大值
                        auto_width = self.bill_table.columnWidth(col)
                        self.column_widths[col] = max(auto_width, 120)  # 确保金额列至少120像素宽
                    else:
                        self.column_widths[col] = self.bill_table.columnWidth(col)
                    
                # 应用保存的列宽
                for col, width in enumerate(self.column_widths):
                    self.bill_table.setColumnWidth(col, width)
                    
                # 如果是第一页，更新模板
                if current_page == 1:
                    self.save_template()
        
        # 确保表格高度不变，除非有特殊处理
        if not self.has_template:
            self.bill_table.setFixedHeight(current_height)
        
        # 更新分页控件状态
        self.update_page_controls()

    def clear_cache(self):
        """清理缓存和存储的状态"""
        self.bill_table.setRowCount(0)
        self.current_page = 1
        self.total_pages = 1
        self.update_page_controls()
        
        # 清空并隐藏分析结果区域
        self.analysis_result_area.clear()
        self.analysis_result_area.setVisible(False)
        self.analysis_result_area.setFixedHeight(0)  # 重置高度为0
        
        # 清空标题旁的摘要信息
        self.analysis_summary.setText("")
        
        # 新增：清空账单数据缓存
        self.all_bills_cache = []
        self.has_all_bills = False
        
        # 如果存在分析线程，停止并清理
        if self.analysis_worker:
            try:
                self.analysis_worker.stop()
            except:
                pass
        
    def save_template(self):
        """保存当前表格大小作为模板"""
        try:
            # 记录当前表格高度
            self.template_height = self.bill_table.height()
            
            # 记录当前各列宽度
            for col in range(5):
                self.template_widths[col] = self.bill_table.columnWidth(col)
                
            self.has_template = True
            
            # 保存模板到本地
            self.save_template_to_local()
            
            # 输出调试信息
            from gui.LoginWindow import log_window
            if log_window:
                log_widths_str = ", ".join([f"{w}px" for w in self.template_widths])
                log_window.log_network_event("表格模板", "保存成功", f"高度: {self.template_height}px, 列宽: [{log_widths_str}]")
                
        except Exception as e:
            # 记录异常
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("表格模板", "保存失败", f"错误: {str(e)}", "ERROR")
                
    def save_template_to_local(self):
        """将模板保存到本地文件"""
        try:
            import os
            import json
            
            # 创建模板对象
            template_data = {
                "height": self.template_height,
                "widths": self.template_widths
            }
            
            # 更新配置类中的常量（非持久化，仅在运行期间有效）
            Config.BILL_TABLE_TEMPLATE = template_data
            
            # 记录模板保存日志
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("表格模板", "保存到配置", "成功")
                
        except Exception as e:
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("表格模板", "保存失败", f"错误: {str(e)}", "WARNING")
    
    def load_template_from_local(self):
        """从配置加载模板"""
        try:
            # 直接从配置类获取模板数据
            template_data = Config.BILL_TABLE_TEMPLATE
            
            # 设置模板数据
            self.template_height = template_data.get("height", 250)
            self.template_widths = template_data.get("widths", self.column_widths.copy())
            self.has_template = True
            
            # 记录日志
            from gui.LoginWindow import log_window
            if log_window:
                log_widths_str = ", ".join([f"{w}px" for w in self.template_widths])
                log_window.log_network_event("表格模板", "配置加载成功", f"高度: {self.template_height}px, 列宽: [{log_widths_str}]")
                
            return True
            
        except Exception as e:
            # 记录异常但不中断流程
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log_network_event("表格模板", "配置加载失败", f"错误: {str(e)}", "WARNING")
            except:
                pass
            return False

    def apply_template(self):
        """应用保存的表格模板大小"""
        if not self.has_template:
            return False
            
        try:
            # 应用表格高度
            self.bill_table.setFixedHeight(self.template_height)
            
            # 应用各列宽度
            for col, width in enumerate(self.template_widths):
                self.bill_table.setColumnWidth(col, width)
                
            # 输出调试信息
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("表格模板", "应用成功", "已应用表格模板")
                
            return True
                
        except Exception as e:
            # 记录异常
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("表格模板", "应用失败", f"错误: {str(e)}", "ERROR")
            return False

    def handle_analyze(self):
        """处理查询全部账单并分析按钮点击"""
        if not self.bill_query:
            # 提示账单查询服务未初始化
            self.bill_table.setRowCount(0)
            self.bill_table.setRowCount(1)
            error_item = QTableWidgetItem("账单查询服务未初始化")
            error_item.setTextAlignment(Qt.AlignCenter)
            self.bill_table.setItem(0, 0, error_item)
            self.bill_table.setSpan(0, 0, 1, 5)  # 合并单元格以显示错误信息
            
            # 记录错误日志
            try:
                if log_window:
                    log_window.log("无法执行账单分析", "账单查询服务未初始化", "ERROR")
            except Exception:
                pass
            
            return
            
        try:
            # 记录开始日志
            try:
                if log_window:
                    log_window.log("用户请求", "开始执行全部账单查询与分析", "INFO")
            except Exception:
                pass
            
            # 禁用所有按钮，防止重复操作
            self.refresh_btn.setEnabled(False)
            self.analyze_btn.setEnabled(False)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.goto_btn.setEnabled(False)
            
            # 清空结果区域并显示
            self.analysis_result_area.clear()
            self.analysis_result_area.setText("正在查询并分析所有账单数据...")
            self.analysis_result_area.setFixedHeight(100)  # 设置为显示状态的高度
            self.analysis_result_area.setVisible(True)
            
            # 显示加载指示器 - 设置更宽的窗口以确保文字显示完整
            self.loading_indicator = show_loading(self.window(), "正在查询并分析\n所有账单数据...", width=350)
            
            # 创建分析线程
            self.analysis_thread = QThread()
            self.analysis_worker = BillAnalysisWorker(self.bill_query)
            self.analysis_worker.moveToThread(self.analysis_thread)
            
            # 连接信号
            self.analysis_thread.started.connect(self.analysis_worker.run)
            self.analysis_worker.progress.connect(self.on_analysis_progress)
            self.analysis_worker.finished.connect(self.on_analysis_completed)
            self.analysis_worker.finished.connect(self.analysis_thread.quit)
            self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
            self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
            
            # 连接日志信号到日志处理函数
            self.analysis_worker.log_signal.connect(self.handle_log_message)
            
            # 记录线程启动日志
            try:
                if log_window:
                    log_window.log("系统操作", "账单分析线程已创建并启动", "INFO")
            except Exception:
                pass
            
            # 启动线程
            self.analysis_thread.start()
            
        except Exception as e:
            # 显示错误信息
            if self.loading_indicator:
                self.loading_indicator.close()
                self.loading_indicator = None
            
            # 恢复按钮状态
            self.refresh_btn.setEnabled(True)
            self.analyze_btn.setEnabled(True)
            self.update_page_controls()
            
            # 记录日志
            try:
                if log_window:
                    log_window.log("账单分析启动失败", f"错误: {str(e)}", "ERROR")
            except Exception:
                pass
            
    def on_analysis_progress(self, current_page, total_pages):
        """分析进度更新回调"""
        if self.loading_indicator:
            try:
                progress_text = f"正在查询账单...\n({current_page}/{total_pages}页)"
                self.loading_indicator.set_text(progress_text)
                
                # 更新分析结果区域
                self.analysis_result_area.setText(progress_text)
                
                # 记录进度日志 - 直接使用handle_log_message确保日志显示
                if current_page % 5 == 0 or current_page == total_pages:  # 每5页或最后一页记录一次
                    self.handle_log_message(
                        f"账单分析进度: 已完成 {current_page}/{total_pages} 页查询", 
                        "INFO"
                    )
            except Exception:
                # 发生异常也不输出到终端
                pass
            
    def on_analysis_completed(self, analysis_result):
        """分析完成回调"""
        # 记录分析完成日志
        self.handle_log_message("账单分析状态: 分析过程已完成，准备展示结果", "INFO")
        
        # 关闭加载指示器
        if self.loading_indicator:
            try:
                self.loading_indicator.close()
            except Exception:
                pass
            self.loading_indicator = None
        
        # 恢复按钮状态
        self.refresh_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.update_page_controls()
        
        # 处理分析结果
        if not analysis_result:
            # 分析失败，显示错误信息
            self.handle_log_message("账单分析: 分析失败，未获取到有效数据", "ERROR")
            self.analysis_result_area.setText("分析失败，未获取到有效数据")
            return
        
        # 新增：缓存全部账单数据（如果存在）
        if "raw_data" in analysis_result and analysis_result["raw_data"]:
            self.all_bills_cache = analysis_result["raw_data"]
            self.has_all_bills = True
            
            # 计算总页数
            total_items = len(self.all_bills_cache)
            self.total_pages = (total_items + self.cached_page_size - 1) // self.cached_page_size
            
            # 记录缓存状态
            self.handle_log_message(f"账单数据已缓存: {total_items}条记录，共{self.total_pages}页", "INFO")
        
        # 展示文本分析结果
        try:
            # 获取基本统计信息
            total_count = analysis_result.get("total_count", 0)
            total_amount = analysis_result.get("total_amount", 0)
            
            # 获取交易类型统计
            type_stats = analysis_result.get("type_stats", {})
            type_amount = analysis_result.get("type_amount", {})
            
            # 获取交易状态统计
            status_stats = analysis_result.get("status_stats", {})
            
            # 生成标题右侧显示的摘要信息，使用HTML格式以便设置颜色
            summary_text = f"账单分析结果：共 {total_count} 条记录，总金额: ￥{total_amount:.2f}  "
            
            # 添加交易状态统计信息
            for status, count in status_stats.items():
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                summary_text += f" {status}: {count}笔 ({percentage:.1f}%)"
            
            # 更新标题旁的分析结果摘要标签
            self.analysis_summary.setText(summary_text)
            
            # 生成分析结果区域内的交易类型统计，按一行两列布局
            result_html = "<table width='100%' cellspacing='0' cellpadding='0' style='border:none;'>"
            
            # 将交易类型列表按一行两个排列
            type_items = list(type_stats.items())
            for i in range(0, len(type_items), 2):
                result_html += "<tr style='line-height:85%;'>"
                
                # 第一列
                trans_type, count = type_items[i]
                amount = type_amount.get(trans_type, 0)
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                result_html += f"<td style='padding:0px; white-space:nowrap;'>- {trans_type}: {count}笔 (￥{amount:.2f}, {percentage:.1f}%)</td>"
                
                # 第二列（如果有）
                if i + 1 < len(type_items):
                    trans_type, count = type_items[i + 1]
                    amount = type_amount.get(trans_type, 0)
                    percentage = (count / total_count) * 100 if total_count > 0 else 0
                    result_html += f"<td style='padding:0px; white-space:nowrap;'>- {trans_type}: {count}笔 (￥{amount:.2f}, {percentage:.1f}%)</td>"
                else:
                    result_html += "<td></td>"  # 空单元格保持布局平衡
                
                result_html += "</tr>"
            
            result_html += "</table>"
            
            # 更新分析结果区域
            self.analysis_result_area.setHtml(result_html)
            self.analysis_result_area.setVisible(True)
            
            # 记录图表显示日志
            self.handle_log_message("账单分析: 文本分析结果已显示", "INFO")
            
        except Exception as e:
            # 记录结果显示错误
            self.handle_log_message(f"账单分析结果: 显示失败: {str(e)}", "ERROR")
            self.analysis_result_area.setText(f"分析结果显示失败: {str(e)}")
            self.analysis_summary.setText("")

    def handle_log_message(self, message, level="INFO", extra_info=""):
        """处理从工作线程发送的日志消息"""
        try:
            # 直接调用全局日志窗口
            from gui.LoginWindow import log_window
            
            # 强制确保日志窗口存在，如果存在则记录日志
            if log_window is not None:
                if extra_info:
                    log_window.log(message, extra_info, level)
                else:
                    log_window.log(message, level)
                # 尝试强制更新日志窗口
                log_window.update()
        except Exception:
            # 发生异常时也不输出到终端
            pass

    def display_cached_page(self, page):
        """从缓存中显示指定页的数据"""
        if not self.has_all_bills or not self.all_bills_cache:
            return
            
        try:
            # 计算当前页的数据范围
            start_idx = (page - 1) * self.cached_page_size
            end_idx = min(start_idx + self.cached_page_size, len(self.all_bills_cache))
            
            # 获取当前页的数据
            current_page_data = self.all_bills_cache[start_idx:end_idx]
            
            # 更新表格
            self.update_bill_data(current_page_data, page, self.total_pages)
            self.update_page_controls()
            
            # 记录日志
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log_network_event("账单显示", "使用缓存数据", f"显示第 {page} 页，无需重新查询")
                
        except Exception as e:
            # 出错时记录日志
            from gui.LoginWindow import log_window
            if log_window:
                log_window.log("缓存数据显示失败", f"错误: {str(e)}", "ERROR")
            # 如果出错，回退到正常查询
            self.query_bill_data()
